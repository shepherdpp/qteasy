# coding=utf-8
# ======================================
# File:     history.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-02-16
# Desc:
#   HistoryPanel Class, and more history
# data manipulating functions.
# ======================================

import operator
from numbers import Number

import pandas as pd
import numpy as np
from typing import Union, Iterable, Any, Optional, Callable, Sequence, List, Tuple, Dict

from qteasy.database import DataSource

from qteasy.utilfuncs import (
    str_to_list,
    list_to_str_format,
    list_or_slice,
    labels_to_dict,
    ffill_3d_data,
    fill_nan_data,
    fill_inf_data,
    pandas_freq_alias_version_conversion,
    regulate_date_format,
)

from qteasy.datatypes import (
    DataType,
    get_history_data_from_source,
    get_reference_data_from_source,
    infer_data_types,
)

# overlay 布局默认仅对两只标的启用，预留常量便于后续调整
HP_OVERLAY_GROUP_SHARE_COUNT: int = 2


class _HistoryPanelLocIndexer:
    """只读索引器：沿 ``hdates`` 时间轴选取，``hp.loc[key]`` 等价于 ``hp[:, :, key]``。

    与 pandas ``DataFrame.loc`` 仅 **类比**（按「行」筛日期）；本类 **只接受单参数**
    时间轴键，**不**实现二维 ``loc[row, col]`` 全语义。

    不接受 ``where()`` 产生的 ``(M, L, N)`` 三维布尔掩码；格点级条件请使用
    :meth:`HistoryPanel.where` 与后续 API 的 ``mask=``。

    Notes
    -----
    更多约定见类 :class:`HistoryPanel` 概述及 Sphinx **HistoryPanel** 文档中「列属性访问、比较与 loc」小节。
    """

    __slots__ = ('_hp',)

    def __init__(self, hp: 'HistoryPanel') -> None:
        self._hp = hp

    def __getitem__(self, key: Any) -> 'HistoryPanel':
        """按时间轴键取出子面板，语义与 ``HistoryPanel[:, :, key]`` 一致。

        Parameters
        ----------
        key : slice, list, 或 numpy.ndarray 等
            与第三轴（``hdates``）上 ``list_or_slice`` 支持的输入一致；一维 ``bool``
            列表或 ``ndarray`` 长度须等于 ``row_count``。禁止传入 ``(M, L, N)`` 布尔数组。

        Returns
        -------
        HistoryPanel
            子面板；视图语义与 ``__getitem__`` 的 ``copy=False`` 一致。

        Raises
        ------
        TypeError
            传入与 ``where`` 输出同形的格点级三维布尔掩码时抛出（英文）。
        ValueError
            布尔轴长度不匹配、或二维布尔数组等非法形状时抛出（英文）。
        """
        hp = self._hp
        if isinstance(key, list) and len(key) > 0 and isinstance(key[0], (bool, np.bool_)):
            L = int(hp.row_count)
            if len(key) != L:
                raise ValueError(
                    f'Boolean mask length {len(key)} does not match number of hdates ({L}).'
                )
        if isinstance(key, np.ndarray) and key.dtype == bool:
            if key.ndim == 3:
                if (not hp.is_empty) and key.shape == hp.shape:
                    raise TypeError(
                        'Use HistoryPanel.where(...) and mask= for per-cell boolean masks, not loc.'
                    )
                raise ValueError(
                    'Boolean array for loc must be one-dimensional with length equal to the '
                    'number of dates (hdates). Use where() and mask= for (M,L,N) masks.'
                )
            if key.ndim == 2:
                raise ValueError(
                    'Boolean array for loc must be one-dimensional with length equal to the '
                    'number of dates (hdates). Use where() and mask= for (M,L) or (M,L,N) masks.'
                )
            if key.ndim != 1:
                raise ValueError(
                    'Boolean array for loc must be one-dimensional with length equal to the '
                    'number of dates (hdates).'
                )
            L = int(hp.row_count)
            if key.size != L:
                raise ValueError(
                    f'Boolean mask length {key.size} does not match number of hdates ({L}).'
                )
            key = key.tolist()
        return hp[:, :, key]


class HistoryPanel():
    """qteasy 中用于统一管理多标的、多时间点、多数据类型历史数据的三维数据容器。

    HistoryPanel 本质是一个三维 ``numpy.ndarray``，三条轴分别表示标的（shares）、时间
    （hdates）和历史数据类型（htypes），支持按任意轴灵活切片、重标记以及与
    pandas DataFrame 之间的互相转换，并作为 get_history_data 与可视化栈
    （如 ``HistoryPanel.plot()`` 与 ``qt.candle``）之间的核心桥梁。

    **索引与数组出口**：``__getitem__`` 始终返回带正确轴标签的子 ``HistoryPanel``；需要
    裸 ``ndarray`` 时用 ``.values`` 或 ``.to_numpy(copy=...)``。**单列原地赋值**
    ``panel['列名'] = value`` 由 ``__setitem__`` 实现（仅非空面板、仅 ``str`` 键），
    值广播为 ``(标的数, 时间长度)`` 并以 ``float64`` 存储；覆盖已有列或追加新列。
    子面板与父对象共享缓冲时的语义见 ``__getitem__`` / ``subpanel`` / ``__setitem__`` 各方法说明。

    **体验向 API**：合法 Python 标识符且存在于 ``htypes`` 的列名可用属性只读访问（如 ``panel.close``，
    等价 ``panel['close']``）；比较运算（如 ``panel.close > panel.open``）返回 ``numpy`` 布尔数组；
    ``panel.loc[key]`` 等价 ``panel[:, :, key]``，仅沿时间轴筛选（不接 ``where`` 的三维掩码）。
    用户文档见 Sphinx **HistoryPanel** 页与教程「使用 HistoryPanel 操作和分析历史数据」（§6 及 §6.1）。

    更详细的结构说明（轴标签、切片示例、标签管理等）见文档「HistoryPanel 类」相关章节。
    """

    def __init__(self, values: np.ndarray = None, levels=None, rows=None, columns=None):
        """初始化 HistoryPanel 对象，并根据输入的数据与轴标签构建三维历史数据结构。

        可以在创建时同时给出标的（levels）、时间（rows）和数据类型（columns）标签，
        若未显式给出则按数据形状自动补全；当仅给出部分标签或数组维度不足三维时，会根据
        输入自动推断缺失维度并重塑为 ``(level, row, column)`` 结构。关于标签约定与
        典型创建方式，详见文档「HistoryPanel 类」章节。

        Parameters
        ----------
        values : numpy.ndarray, optional
            历史数据数组，维度不能超过三维；若维度不足三维，将根据标签数量自动补齐维度。
            为 None 或空数组时创建一个空的 HistoryPanel（其 ``is_empty`` 为 True）。
        levels : str or sequence of str, optional
            标的标签，数量应等于 ``values`` 第一维长度，每一层代表一种股票或资产。
        rows : str or sequence of str, optional
            时间标签，可以是可转换为 ``pandas.Timestamp`` 的字符串序列或 DatetimeIndex，
            每个标签对应一条时间记录。
        columns : str or sequence of str, optional
            历史数据类型标签，每一列代表一种数据类型（如 open、high、close、volume 等）。

        Returns
        -------
        HistoryPanel
            新构建的 HistoryPanel 对象。
        """

        # TODO: 在生成HistoryPanel时如果只给出data或者只给出data+columns，生成HistoryPanel打印时会报错，问题出在to_dataFrame()上
        #  在生成HistoryPanel时传入的ndarray会被直接用于HistoryPanel，如果事后修改这个ndarray，HistoryPanel也会改变
        #  应该考虑是否在创建HistoryPanel时生成ndarray的一个copy而不是使用其自身 。
        if (not isinstance(values, np.ndarray)) and (values is not None):
            raise TypeError(f'input value type should be numpy ndarray, got {type(values)}')

        self._levels = None
        self._columns = None
        self._rows = None
        if values is None or values.size == 0:
            self._l_count, self._r_count, self._c_count = (0, 0, 0)
            self._values = None
            self._is_empty = True
        else:
            assert values.ndim <= 3, \
                f'input array should be equal to or less than 3 dimensions, got {len(values.shape)}'

            if isinstance(levels, str):
                levels = str_to_list(levels)
            if isinstance(columns, str):
                columns = str_to_list(columns)
            if isinstance(rows, str):
                rows = str_to_list(rows)
            # 处理输入数据，补齐缺失的维度，根据输入数据的维度以及各维度的标签数据数量确定缺失的维度
            if values.ndim == 1:
                values = values.reshape(1, values.shape[0], 1)
            elif values.ndim == 2:
                if (levels is None) or (len(levels) == 1):
                    values = values.reshape(1, *values.shape)
                else:
                    values = values.reshape(*values.T.shape, 1)
            self._l_count, self._r_count, self._c_count = values.shape
            self._values = values
            self._is_empty = False

            # 检查输入数据的标签，处理标签数据以确认标签代表的数据各维度的数据量
            if levels is None:
                levels = range(self._l_count)
            if rows is None:
                rows = pd.date_range(periods=self._r_count, end='2020-08-08', freq='d')
            if columns is None:
                columns = range(self._c_count)

            assert (len(levels), len(rows), len(columns)) == values.shape, \
                f'ValueError, value shape does not match, input data: ({(values.shape)}) while given axis' \
                f' imply ({(len(levels), len(rows), len(columns))})'

            # 建立三个纬度的标签配对——建立标签序号字典，通过labels_to_dict()函数将标签和该纬度数据序号一一匹配
            # 首先建立层标签序号字典：
            self._levels = labels_to_dict(levels, range(self._l_count))

            # 再建立行标签序号字典，即日期序号字典，再生成字典之前，检查输入标签数据的类型，并将数据转化为pd.Timestamp格式
            assert isinstance(rows, (list, dict, pd.DatetimeIndex)), \
                f'TypeError, input_hdates should be a list or DatetimeIndex, got {type(rows)} instead'
            try:
                new_rows = [pd.to_datetime(date) for date in rows]
            except:
                raise ValueError('one or more item in hdate list can not be converted to Timestamp')
            self._rows = labels_to_dict(new_rows, range(self._r_count))

            # 建立列标签序号字典
            self._columns = labels_to_dict(columns, range(self._c_count))

    @property
    def is_empty(self):
        """判断HistoryPanel是否为空"""
        return self._is_empty

    @property
    def values(self):
        """返回当前对象内部的三维数据缓冲区（与 ``_values`` 同一引用）。

        非空时与 ``to_numpy(copy=False)`` 指向同一块内存；修改返回值会直接改动本对象数据。
        通过 ``__setitem__`` 追加新列时，内部可能 **替换** 整块数组，此前由子视图
        （``__getitem__`` / ``subpanel(copy=False)``）持有的 ``values`` 可能仍指向扩列前的旧缓冲，
        且不会自动出现新列。需要稳定快照请使用 ``subpanel(..., copy=True)`` 或 ``to_numpy(copy=True)``。
        原地写入列时，若原数组非 ``float64``，内部会升级为 ``float64`` 再存储。

        Returns
        -------
        numpy.ndarray or None
            形状 ``(level_count, row_count, column_count)``；空面板为 ``None``。
        """
        return self._values

    @property
    def levels(self):
        """返回HistoryPanel的层标签字典，也是HistoryPanel的股票代码字典

        这个字典在level的标签与level的id之间建立了一个联系，因此，如果需要通过层标签来快速地访问某一层的数据，可以非常容易地通过：
            data = HP.values[levels[level_name[a], :, :]
        来访问，不过这是HistoryPanel内部的处理机制，在HistoryPanel的外部，可以通过切片的方式快速访问不同的数据。
        """
        return self._levels

    @property
    def shares(self):
        """返回HistoryPanel的层标签——股票列表"""
        if self.is_empty:
            return 0
        else:
            return list(self._levels.keys())

    @shares.setter
    def shares(self, input_shares):
        if not self.is_empty:
            if isinstance(input_shares, str):
                input_shares = str_to_list(input_string=input_shares)
            assert len(input_shares) == self.level_count, \
                f'ValueError, the number of input shares ({len(input_shares)}) does not match level ' \
                f'count ({self.level_count})'
            self._levels = labels_to_dict(input_shares, self.shares)

    @property
    def level_count(self):
        """返回HistoryPanel中股票或资产品种的数量"""
        return self._l_count

    @property
    def share_count(self):
        """获取HistoryPanel中股票或资产品种的数量"""
        return self._l_count

    @property
    def rows(self):
        """ 返回Hi storyPanel的日期字典，通过这个字典建立日期与行号的联系：
        因此内部可以较快地进行数据切片或数据访问

        Returns
        -------
        dict
            日期字典
        """
        return self._rows

    @property
    def hdates(self):
        """获取HistoryPanel的历史日期时间戳list"""
        # TODO: Maybe: 可以将返回值包装成一个pandas.Index对象，
        #  这样有更多方便好用的方法和属性可用
        #  例如
        #  return pd.Index(self._rows.keys())
        #  这样就可以用 HP.hdates.date / HP.hdates.where()
        #  等等方法和属性了
        #  shares 和 htypes 属性也可以如法炮制
        if self.is_empty:
            return 0
        else:
            # return pd.Index(self._rows.keys(), dtype='datetime64')
            return list(self._rows.keys())

    @hdates.setter
    def hdates(self, input_hdates: list):
        if not self.is_empty:
            if not isinstance(input_hdates, list):
                error = f'input_hdates should be a list, got {type(input_hdates)} instead'
                raise TypeError(error)
            if not len(input_hdates) == self.row_count:
                error = f'the number of input shares ({len(input_hdates)}) does not match level count ({self.row_count})'
                raise ValueError(error)
            try:
                new_hdates = [pd.to_datetime(date) for date in input_hdates]
            except Exception as e:
                error = f'{e} one or more item in hdate list can not be converted to Timestamp'
                raise ValueError(error)
            self._rows = labels_to_dict(new_hdates, self.hdates)

    @property
    def row_count(self):
        """获取HistoryPanel的行数量"""
        return self._r_count

    @property
    def hdate_count(self):
        """获取HistoryPanel的历史数据类型数量"""
        return self._r_count

    @property
    def htypes(self):
        """获取HistoryPanel的历史数据类型列表"""
        if self.is_empty:
            return 0
        else:
            return list(self._columns.keys())

    @htypes.setter
    def htypes(self, input_htypes: Union[str, list]):
        """修改HistoryPanel的历史数据类型"""
        if not self.is_empty:
            if isinstance(input_htypes, str):
                input_htypes = str_to_list(input_string=input_htypes)
            if isinstance(input_htypes, list):
                assert len(input_htypes) == self.column_count, \
                    f'ValueError, the number of input shares ({len(input_htypes)}) does not match level ' \
                    f'count ({self.column_count})'
                self._columns = labels_to_dict(input_htypes, self.htypes)
            else:
                raise TypeError(f'Expect string or list as input htypes, got {type(input_htypes)} instead')

    @property
    def columns(self):
        """返回一个字典，代表HistoryPanel的历史数据，将历史数据与列号进行对应
        这样便于内部根据股票代码对数据进行切片
        """
        return self._columns

    @property
    def column_count(self):
        """获取HistoryPanel的列数量或历史数据数量"""
        return self._c_count

    @property
    def htype_count(self):
        """获取HistoryPanel的历史数据类型数量"""
        return self._c_count

    @property
    def loc(self) -> _HistoryPanelLocIndexer:
        """沿 ``hdates``（时间轴）选取子面板的只读索引器。

        ``hp.loc[key]`` 与 ``hp[:, :, key]`` 等价，用于切片、时间标签、标签列表、``:`` 或
        长度等于 ``row_count`` 的一维布尔掩码。格点级 ``(M,L,N)`` 布尔条件请用
        :meth:`where` 与后续 ``mask=``，**不要**传入 ``loc``。

        Returns
        -------
        _HistoryPanelLocIndexer
            轻量代理；对其使用 ``[...]`` 即按时间轴取子面板。

        Examples
        --------
        >>> import pandas as pd
        >>> import numpy as np
        >>> hp = HistoryPanel(
        ...     np.ones((2, 4, 1)),
        ...     levels=['A', 'B'],
        ...     rows=pd.date_range('2020-01-01', periods=4),
        ...     columns=['close'],
        ... )
        >>> sub = hp.loc[0:2]
        >>> sub.shape[1] == 2
        True
        """
        return _HistoryPanelLocIndexer(self)

    @property
    def shape(self):
        """获取HistoryPanel的各个维度的尺寸"""
        return self._l_count, self._r_count, self._c_count

    def __len__(self):
        """获取HistoryPanel的历史数据长度

        Examples
        --------

        """
        return self._r_count

    @staticmethod
    def _axis_labels_subset(
            ordered: Sequence[Any],
            spec: Union[slice, list, np.ndarray],
    ) -> List[Any]:
        """根据 ``list_or_slice`` 产出的下标规格，从有序轴标签列表中取子序列。

        Parameters
        ----------
        ordered : sequence
            与轴顺序一致的标签序列（如 ``shares`` / ``hdates`` / ``htypes`` 列表）。
        spec : slice, list of int, or ndarray
            ``list_or_slice`` 的返回值。

        Returns
        -------
        list
            子集标签，顺序与切片后的数组第一维（或对应维）一致。
        """
        if isinstance(spec, slice):
            return list(ordered[spec])
        if isinstance(spec, list):
            return [ordered[int(i)] for i in spec]
        if isinstance(spec, np.ndarray):
            if spec.dtype == bool:
                return [ordered[i] for i in range(len(ordered)) if bool(spec.flat[i])]
            return [ordered[int(i)] for i in spec.flatten().tolist()]
        raise TypeError(f'Unsupported index spec type: {type(spec)}')

    def _parse_getitem_keys(self, keys: Any) -> Tuple[Any, Any, Any]:
        """将 ``__getitem__`` 的 keys 解析为 (htype 轴, share 轴, hdate 轴) 三段的原始切片输入。"""
        key_is_none = keys is None
        key_is_tuple = isinstance(keys, tuple)
        key_is_list = isinstance(keys, list)
        key_is_slice = isinstance(keys, slice)
        key_is_string = isinstance(keys, str)
        key_is_number = isinstance(keys, int)

        htype_slice: Any
        share_slice: Any
        hdate_slice: Any
        if key_is_tuple:
            if len(keys) == 2:
                htype_slice, share_slice = keys
                hdate_slice = slice(None, None, None)
            elif len(keys) == 3:
                htype_slice, share_slice, hdate_slice = keys
            else:
                htype_slice = slice(None, None, None)
                share_slice = slice(None, None, None)
                hdate_slice = slice(None, None, None)
        elif key_is_slice or key_is_list or key_is_string or key_is_number:
            htype_slice = keys
            share_slice = slice(None, None, None)
            hdate_slice = slice(None, None, None)
        elif key_is_none:
            htype_slice = slice(None, None, None)
            share_slice = slice(None, None, None)
            hdate_slice = slice(None, None, None)
        else:
            htype_slice = slice(None, None, None)
            share_slice = slice(None, None, None)
            hdate_slice = slice(None, None, None)

        htype_slice = list_or_slice(htype_slice, self.columns)
        share_slice = list_or_slice(share_slice, self.levels)
        hdate_slice = list_or_slice(hdate_slice, self.rows)
        return htype_slice, share_slice, hdate_slice

    def _select_subpanel(
            self,
            htype_slice: Any,
            share_slice: Any,
            hdate_slice: Any,
            *,
            copy: bool,
    ) -> 'HistoryPanel':
        """按已解析的三轴下标取出子面板；``copy=True`` 时对数据数组做拷贝，与父数组脱钩。

        ``copy=False`` 时结果可能与父对象共享底层缓冲；父对象后续 ``__setitem__`` **追加** 列会替换
        父级 ``_values``，已存在的子面板通常 **不会** 自动带上新列，详见 ``__getitem__`` / ``__setitem__``。
        """
        out_arr = self.values[share_slice][:, hdate_slice][:, :, htype_slice]
        if copy:
            out_arr = np.array(out_arr, copy=True)
        share_labels = self._axis_labels_subset(self.shares, share_slice)
        hdate_labels = self._axis_labels_subset(self.hdates, hdate_slice)
        htype_labels = self._axis_labels_subset(self.htypes, htype_slice)
        return HistoryPanel(values=out_arr, levels=share_labels, rows=hdate_labels, columns=htype_labels)

    def to_numpy(self, copy: bool = False) -> np.ndarray:
        """返回与 ``values`` 相同形状的 ndarray；需要独立副本时使用 ``copy=True``。

        空面板返回形状为 ``(0, 0, 0)`` 的 float 数组。非空时 ``copy=False`` 与 ``numpy.asarray(self.values)``
        语义一致，可与内部缓冲区共享内存。若之后在父对象上用 ``__setitem__`` **追加** 新列，父对象会替换
        整块缓冲；此前用 ``copy=False`` 拿到的数组 **不会** 自动带上新列，不宜再视为当前面板的权威快照。

        Parameters
        ----------
        copy : bool, default False
            为 True 时返回数组拷贝，修改返回值不影响本对象数据。

        Returns
        -------
        numpy.ndarray
            与 ``values`` 同形状的三维数组；空面板时为 ``(0, 0, 0)``。
        """
        if self.is_empty:
            return np.empty((0, 0, 0), dtype=float)
        if copy:
            return np.array(self._values, copy=True)
        return np.asarray(self._values)

    def where(
            self,
            condition: Union[np.ndarray, Callable[['HistoryPanel'], np.ndarray]],
    ) -> np.ndarray:
        """将条件广播为与 ``values`` 同形的 bool 掩码，供研究 API 的 ``mask=`` 等参数使用。

        不改变本对象。返回数组为 ``dtype=bool``、形状 ``(share 数, 时间长度, htype 数)``，与
        ``panel.values`` 一致。条件可为数组（可广播到上述形状）或 ``callable(panel)`` 返回类数组。

        研究向掩码与 Backtester 中 NaN 价格处理无关。整数 ``0``/``1`` 等会按 numpy 规则转为 bool。

        形状 **恰好为** ``(M, L)`` 的数组视为「每个 ``(share, 时间)`` 对所有 ``htype`` 共用同一布尔值」，
        内部会先变为 ``(M, L, 1)`` 再广播到 ``(M, L, N)``（因标准 numpy 无法将二维 ``(M,L)`` 直接广播到三维）。
        一维 ``(M,)`` 与二维 ``(M, 1)`` 视为仅随标的变化，会展开为 ``(M, 1, 1)`` 再广播。

        Parameters
        ----------
        condition : numpy.ndarray or callable
            类数组：先 ``np.asarray(..., dtype=bool)`` 再广播到 ``self.shape``。
            若为 ``callable``，则调用 ``condition(self)`` 得到数组后再处理。
            裸 ``str`` 不接受，将引发 ``TypeError``（英文）。

        Returns
        -------
        numpy.ndarray
            与 ``self.shape`` 相同的三维 bool 数组（拷贝，与内部 ``values`` 不共享写缓冲）。

        Raises
        ------
        TypeError
            ``condition`` 为 ``str`` 时抛出（英文）。
        ValueError
            无法将返回值转为 bool 数组或无法广播到 ``self.shape`` 时抛出（英文）。

        Notes
        -----
        ``condition`` 可为 **富比较** 的直接结果（自 2.2.8 起）：例如 ``panel.where(panel.close > 100.0)``
        或 ``panel.where(panel['close'] > panel['open'])``，其中 ``>`` 等对 ``HistoryPanel`` 与标量 /
        可广播数组 / 另一面板（须满足对齐规则）返回 ``numpy.ndarray``（``dtype=bool``），再由本方法
        广播到与 ``panel.values`` 同形。

        ``cum_return``、``normalize`` 与 ``portfolio`` 的 ``mask=`` 可直接使用本方法返回值或与其同形、
        ``dtype=bool`` 的数组。
        更多场景见文档「使用 HistoryPanel 操作和分析历史数据」教程与 Sphinx **HistoryPanel** API 中
        「研究与掩码（where）」小节。

        Examples
        --------
        空面板得到 ``(0,0,0)`` 的 bool 数组：

        >>> empty = HistoryPanel()
        >>> empty.where(True).shape
        (0, 0, 0)

        与 ``values`` 同形的比较结果可直接传入：

        >>> import pandas as pd
        >>> hp = HistoryPanel(
        ...     np.arange(24, dtype=float).reshape(2, 3, 4),
        ...     levels=['A', 'B'],
        ...     rows=pd.date_range('2020-01-01', periods=3),
        ...     columns=['a', 'b', 'c', 'd'],
        ... )
        >>> m = hp.where(hp.values > 10)
        >>> m.shape == hp.shape
        True
        >>> not bool(m[0, 0, 0]) and bool(m[-1, -1, -1])
        True

        标量 ``True`` / ``False`` 填满整块：

        >>> import numpy as np
        >>> hp.where(True).all() and not hp.where(False).any()
        True

        ``(M, L)`` 条件沿 htype 轴广播（例如事件日）：

        >>> ev = np.zeros((2, 3), dtype=bool)
        >>> ev[:, 1] = True
        >>> m2 = hp.where(ev)
        >>> bool(m2[0, 1, 0]) and bool(m2[0, 1, 3])
        True

        ``(M, L, 1)`` 与 ``(M, L)`` 语义一致，沿 htype 维复制：

        >>> c_ml1 = (hp.values[:, :, :1] > 10)
        >>> m2b = hp.where(c_ml1)
        >>> m2b.shape == hp.shape
        True

        使用 ``lambda`` 基于面板数据构造条件：

        >>> m3 = hp.where(lambda p: p.values[:, :, 0] >= 3)
        >>> m3.shape == hp.shape
        True

        复合布尔条件：

        >>> m4 = hp.where(lambda p: (p.values >= 5) & (p.values <= 18))
        >>> m4.dtype == bool
        True
        """
        if self.is_empty:
            return np.empty((0, 0, 0), dtype=bool)
        if isinstance(condition, str):
            raise TypeError(
                'HistoryPanel.where() does not accept str conditions; '
                'pass a numpy array or a callable that returns an array.'
            )
        if callable(condition):
            raw = condition(self)
        else:
            raw = condition
        try:
            b = np.asarray(raw, dtype=bool)
        except (TypeError, ValueError) as e:
            raise ValueError(
                f'Cannot convert where() condition to a boolean array: {e}'
            ) from e
        m, l_count, n = self._l_count, self._r_count, self._c_count
        target = (m, l_count, n)
        if b.shape == target:
            return np.array(b, dtype=bool, copy=True)
        if b.ndim == 0:
            broad = np.broadcast_to(b, target)
            return np.array(broad, dtype=bool, copy=True)
        # (M,L) 与 (M,)、(M,1)：沿 htype 轴复制（numpy 无法把二维 (M,L) 直接广播到 (M,L,N)）
        if b.ndim == 2 and b.shape == (m, l_count):
            b = b[:, :, np.newaxis]
        elif b.ndim == 1 and b.shape == (m,):
            b = b.reshape(m, 1, 1)
        elif b.ndim == 2 and b.shape == (m, 1):
            b = b.reshape(m, 1, 1)
        try:
            broad = np.broadcast_to(b, target)
        except ValueError:
            raise ValueError(
                f'Cannot broadcast condition with shape {getattr(b, "shape", ())} '
                f'to panel shape {target}.'
            ) from None
        return np.array(broad, dtype=bool, copy=True)

    def subpanel(
            self,
            htypes: Optional[Union[str, Sequence[str], slice, int, list]] = None,
            shares: Optional[Union[str, Sequence[str], slice, int, list]] = None,
            hdates: Optional[Union[str, slice, Sequence[Any], int, list]] = None,
            *,
            copy: bool = True,
    ) -> 'HistoryPanel':
        """按具名参数沿 htypes / shares / hdates 取子面板，避免三元组轴顺序混淆。

        ``None`` 表示该轴全选。默认 ``copy=True``，得到与父对象数据缓冲区脱钩的副本；需要零拷贝时可设
        ``copy=False``（子面板 ``values`` 可能与父面板共享内存）。父对象上 ``__setitem__`` 追加新列时会
        替换父面板整块 ``values``，``copy=False`` 子面板通常 **不会** 自动带上新列，且可能仍引用扩列前的缓冲区。

        Parameters
        ----------
        htypes : str, sequence, slice or int, optional
            列（数据类型）选择，语义与 ``panel[htypes, ...]`` 第一段一致。
        shares : str, sequence, slice or int, optional
            标的层选择，语义与 ``panel[:, shares, ...]`` 第二段一致。
        hdates : str, sequence, slice or int, optional
            时间轴选择，语义与 ``panel[..., hdates]`` 第三段一致。
        copy : bool, default True
            为 True 时对切片结果做数组拷贝。

        Returns
        -------
        HistoryPanel
            所选轴子集构成的子面板；空输入对应空面板。

        Notes
        -----
        与 ``__getitem__`` 的 ``copy=False`` 切片类似：父级 ``__setitem__`` **追加列**后，``copy=False``
        子对象通常不含新列；需要稳定快照请保持 ``copy=True``（默认）。
        """
        if self.is_empty:
            return HistoryPanel()
        hs = slice(None, None, None) if htypes is None else htypes
        ss = slice(None, None, None) if shares is None else shares
        ds = slice(None, None, None) if hdates is None else hdates
        htype_slice = list_or_slice(hs, self.columns)
        share_slice = list_or_slice(ss, self.levels)
        hdate_slice = list_or_slice(ds, self.rows)
        return self._select_subpanel(htype_slice, share_slice, hdate_slice, copy=copy)

    def __getitem__(self, keys=None) -> 'HistoryPanel':
        """按 htypes / shares / hdates 三轴切片，返回带正确轴标签的子 ``HistoryPanel``。

        第一个切片为数据类型（htypes），第二个为标的（shares），第三个为时间（hdates）；省略时该轴为全选。
        需要裸 ``ndarray`` 时请使用 ``sub.values`` 或 ``sub.to_numpy()``。子面板 ``values`` 可能与父面板
        共享内存（numpy 视图规则）；需要独立副本请用 ``subpanel(..., copy=True)`` 或 ``sub.copy()``。

        在 **父对象** 上使用 ``__setitem__`` 追加新列时，会替换父面板整块 ``values``：默认
        ``copy=False`` 的子面板 **不会** 出现新列名，且其 ``values`` 可能仍指向扩列前的旧数组；
        ``subpanel(copy=True)`` 得到的子对象不受影响。在父面板上 **覆盖** 已有列时，与子视图共享的
        切片数据会随父缓冲一并更新（仍为同一底层块上的视图时）。

        空面板（``is_empty``）上任意索引均返回空的 ``HistoryPanel``。

        Notes
        -----
        **时间轴（第三段 ``hdates``）** 除 ``slice`` / 整数 / 区间字符串外，还支持：在 ``rows``
        字典中可查的 **单个时间标签**（如 ``pandas.Timestamp``）、**时间标签列表**，以及
        长度等于 ``row_count`` 的一维 ``bool`` 列表或一维 ``bool`` ``ndarray``；与
        :attr:`loc` 所接受的 ``key`` 一致。格点级 ``(M, L, N)`` 布尔数组 **不** 用作第三轴索引，
        请使用 :meth:`where`。

        Parameters
        ----------
        keys : list, tuple, slice, str, int or None
            切片键；三元组 ``(htypes, shares, hdates)`` 与历史行为一致。

        Returns
        -------
        HistoryPanel
            子面板；取矩阵请用其 ``.values`` / ``.to_numpy()``。

        Examples
        --------
        >>> hp = HistoryPanel(np.array([[[10, 20, 30, 40, 50]]*10]*3),
        ...                   levels=['000001', '000002', '000003'],
        ...                   rows=pd.date_range('2015-01-05', periods=10),
        ...                   columns=['open', 'high', 'low', 'close', 'volume'])
        >>> sub = hp['close']
        >>> isinstance(sub, HistoryPanel)
        True
        >>> sub.shape
        (3, 10, 1)
        >>> sub.htypes
        ['close']
        >>> np.all(sub.values == 40)
        True
        """
        if self.is_empty:
            return HistoryPanel()
        htype_slice, share_slice, hdate_slice = self._parse_getitem_keys(keys)
        return self._select_subpanel(htype_slice, share_slice, hdate_slice, copy=False)

    def __getattr__(self, name: str) -> Any:
        """将合法标识符列名解析为 ``self[name]``（只读）；非标识符或未知列名请用方括号索引。

        列赋值仍请使用 ``hp['col'] = ...``；不与 pandas 的属性写路径对齐。

        Parameters
        ----------
        name : str
            属性名；须为合法 Python 标识符才可能对应到 ``htypes`` 列（非空面板）。

        Returns
        -------
        HistoryPanel
            与 ``self[name]`` 相同的子面板；空面板上委托 ``__getitem__``，返回空子面板。

        Raises
        ------
        AttributeError
            非法标识符、或当前面板中不存在的列名（英文，提示使用 bracket indexing）。

        Notes
        -----
        已有方法名 / 描述符（如 ``where``、``values``）优先于列名：同名列仍须用
        ``hp['where']`` 等形式访问。非标识符列名（如 ``close|b``）不可用点号。

        Examples
        --------
        >>> import pandas as pd
        >>> import numpy as np
        >>> hp = HistoryPanel(
        ...     np.arange(24, dtype=float).reshape(2, 3, 4),
        ...     levels=['A', 'B'],
        ...     rows=pd.date_range('2020-01-01', periods=3),
        ...     columns=['a', 'b', 'c', 'd'],
        ... )
        >>> np.allclose(hp.a.values, hp['a'].values)
        True
        """
        if not isinstance(name, str):
            raise AttributeError(name)
        if not name.isidentifier():
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'. "
                'Use bracket indexing for non-identifier htype names, e.g. hp["close|b"].'
            )
        if self.is_empty:
            return self[name]
        htypes = self.htypes
        if isinstance(htypes, list) and name not in htypes:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'. "
                'Use bracket indexing for htype columns, e.g. hp["column_name"].'
            )
        return self[name]

    def _prepare_column_array_for_inplace(self, value: Any) -> np.ndarray:
        """将赋值右侧解析并广播为与当前面板 ``(level_count, row_count)`` 一致的 float64 二维数组。

        仅供非空面板在 ``__setitem__`` 等内部路径调用；空面板应在入口处拒绝赋值。

        Parameters
        ----------
        value : Any
            标量、可转为 ``ndarray`` 的序列，或可广播到 ``(M, L)`` 的数组；若形状恰为 ``(M, L, 1)``，
            会先规整为 ``(M, L)`` 再广播。

        Returns
        -------
        numpy.ndarray
            形状为 ``(level_count, row_count)``、``dtype=float64``、C 连续的数组副本。

        Raises
        ------
        ValueError
            无法广播到当前面板的 ``(M, L)`` 时抛出；用户可见信息为英文。
        """
        m, l_count = self._l_count, self._r_count
        arr = np.asarray(value, dtype=np.float64)
        if arr.ndim == 3 and arr.shape == (m, l_count, 1):
            arr = arr.reshape(m, l_count)
        try:
            b = np.broadcast_to(arr, (m, l_count))
        except ValueError:
            raise ValueError(
                f'Cannot broadcast assignment value to shape ({m}, {l_count}) for column.'
            ) from None
        return np.array(b, dtype=np.float64, copy=True)

    def _set_htype_column_inplace(self, name: str, column_2d: np.ndarray) -> None:
        """在原地覆盖已有 htype 列或沿第三轴追加新列，并在必要时把 ``_values`` 提升为 float64。

        供 ``__setitem__`` 与后续 ``kline(..., inplace=True)`` 等路径复用，避免重复拼接逻辑。

        Parameters
        ----------
        name : str
            列名（htype）；调用方须已校验非空且与 ``self`` 轴一致。
        column_2d : numpy.ndarray
            与 ``(level_count, row_count)`` 同形的二维数据（通常为 float64）。

        Returns
        -------
        None
            直接修改 ``self._values``、``self._columns`` 与 ``self._c_count``，无返回值。

        Raises
        ------
        ValueError
            当 ``column_2d.shape`` 与 ``(level_count, row_count)`` 不一致时抛出（英文信息，属内部一致性检查）。
        """
        if column_2d.shape != (self._l_count, self._r_count):
            raise ValueError(
                f'Internal error: column array shape {column_2d.shape} != '
                f'{(self._l_count, self._r_count)}'
            )
        if self._values.dtype != np.float64:
            self._values = np.asarray(self._values, dtype=np.float64)
        if name in self._columns:
            idx = self._columns[name]
            self._values[:, :, idx] = column_2d
            return
        base = self._values
        new_values = np.concatenate([base, column_2d[:, :, np.newaxis]], axis=2)
        self._values = new_values
        self._c_count = int(new_values.shape[2])
        new_htypes = list(self.htypes) + [name]
        self._columns = labels_to_dict(new_htypes, range(self._c_count))

    def __setitem__(self, key: Any, value: Any) -> None:
        """按列名原地追加一列或覆盖已有列（``htypes`` 第三轴）。

        仅接受运行期为 **非空** 字符串的 ``key``；多列批量赋值由后续 ``assign`` 等 API 提供。
        ``value`` 将广播到 ``(share 数, 时间长度)`` 并以 ``float64`` 落盘；已存在列名 **静默覆盖**，
        语义对齐 pandas 单列赋值。父面板上 **追加** 新列会替换整块 ``values``：``subpanel(copy=False)``
        / ``__getitem__`` 子视图通常 **看不到** 新列且可能仍指向旧缓冲；``subpanel(..., copy=True)``
        与 ``to_numpy(copy=True)`` 不受影响。父 **覆盖** 已有列时，与父共享底层块的子视图会随父更新。

        Parameters
        ----------
        key : Any
            列名（htype）。须为 ``str``；非 ``str`` 抛 ``TypeError``，空字符串抛 ``ValueError``（英文信息）。
        value : Any
            可 ``np.asarray`` 且可广播到 ``(M, L)`` 的数值（标量、``(M, L)``、``(M, L, 1)`` 等）。

        Returns
        -------
        None
            原地修改本对象，无返回值。

        Raises
        ------
        TypeError
            ``key`` 不是 ``str`` 时抛出（英文信息）。
        ValueError
            面板为空、``key`` 为空字符串、或 ``value`` 无法广播到 ``(M, L)`` 时抛出（英文信息）。

        Examples
        --------
        >>> hp = HistoryPanel(np.ones((2, 5, 2)), levels=['A', 'B'],
        ...                   rows=pd.date_range('2020-01-01', periods=5),
        ...                   columns=['open', 'close'])
        >>> hp['twice_close'] = hp['close'].values * 2
        >>> 'twice_close' in hp.htypes
        True
        >>> hp['const'] = 0.5
        >>> np.all(hp.values[:, :, hp.htypes.index('const')] == 0.5)
        True
        """
        if not isinstance(key, str):
            raise TypeError(
                'HistoryPanel column assignment only accepts str column names; '
                f'got {type(key).__name__}.'
            )
        if not key:
            raise ValueError('Column name must be a non-empty string.')
        if self.is_empty:
            raise ValueError(
                'Cannot assign columns to an empty HistoryPanel; construct a non-empty panel first.'
            )
        col = self._prepare_column_array_for_inplace(value)
        self._set_htype_column_inplace(key, col)

    def __str__(self):
        """打印HistoryPanel"""
        res = []
        if self.is_empty:
            res.append(f'{type(self)} \nEmpty History Panel at {hex(id(self))}')
        else:
            if self.level_count <= 7:
                display_shares = self.shares
            else:
                display_shares = self.shares[0:3]
            for share in display_shares:
                res.append(f'\nshare {self.levels[share]}, label: {share}\n')
                df = self.slice_to_dataframe(share=share)
                res.append(df.__str__())
                res.append('\n')
            if self.level_count > 7:
                res.append('\n ...  \n')
                for share in self.shares[-2:]:
                    res.append(f'\nshare {self.levels[share]}, label: {share}\n')
                    df = self.slice_to_dataframe(share=share)
                    res.append(df.__str__())
                    res.append('\n')
                res.append('Only first 3 and last 3 shares are displayed\n')
        return ''.join(res)

    def __repr__(self):
        return self.__str__()

    def _history_panel_compare(
            self,
            other: Any,
            op: Callable[[Any, Any], Any],
    ) -> Any:
        """对 ``self.values`` 与另一面板或标量/可广播数组做逐元素比较。

        Parameters
        ----------
        other : HistoryPanel, numbers.Number, numpy.ndarray 等
            右操作数；不支持的类型返回 ``NotImplemented``。
        op : callable
            二元比较函数（如 ``operator.lt``）。

        Returns
        -------
        numpy.ndarray
            ``dtype=bool``，与广播后的数值形状一致。
        NotImplemented
            左操作数无法与 ``other`` 比较时交由 Python 反射协议处理。

        Notes
        -----
        两侧均为面板时：``shares``、``hdates`` 须一致；``htypes`` 须相同，或两侧均为单列切片
        （``shape[2] == 1``）以便安全比较两列。与标量、``numpy`` 数组比较时按广播规则。
        """
        if isinstance(other, HistoryPanel):
            if self.is_empty and other.is_empty:
                return np.asarray(op(self.to_numpy(copy=False), other.to_numpy(copy=False)), dtype=bool)
            if self.is_empty or other.is_empty:
                raise ValueError(
                    'Cannot compare HistoryPanel objects when only one is empty.'
                )
            if self.shares != other.shares or self.hdates != other.hdates:
                raise ValueError(
                    'HistoryPanel comparisons require identical shares and hdates order.'
                )
            if self.htypes != other.htypes:
                if not (self.shape[2] == 1 and other.shape[2] == 1):
                    raise ValueError(
                        'HistoryPanel comparisons require identical htypes order unless both '
                        'operands are single-column slices (e.g. hp["close"] vs hp["open"]).'
                    )
            try:
                left, right = np.broadcast_arrays(self.values, other.values)
            except ValueError as err:
                raise ValueError(
                    'Cannot broadcast the two HistoryPanel value arrays for comparison.'
                ) from err
            return np.asarray(op(left, right), dtype=bool)
        if other is None:
            return NotImplemented
        if isinstance(other, np.ndarray):
            try:
                left = self.to_numpy(copy=False) if self.is_empty else self.values
                return np.asarray(op(left, other), dtype=bool)
            except ValueError as err:
                raise ValueError(
                    'Cannot broadcast comparison between HistoryPanel values and the given array.'
                ) from err
        if isinstance(other, Number):
            left = self.to_numpy(copy=False) if self.is_empty else self.values
            return np.asarray(op(left, other), dtype=bool)
        return NotImplemented

    def __lt__(self, other: Any) -> np.ndarray:
        """逐元素 ``self < other``，返回 ``bool`` ``ndarray``（非子面板）。

        Parameters
        ----------
        other : Any
            标量、可广播 ``ndarray`` 或另一 ``HistoryPanel``（须满足对齐规则）。

        Returns
        -------
        numpy.ndarray
            布尔结果数组。

        Raises
        ------
        TypeError
            不支持的操作数类型（英文）。
        ValueError
            两面板无法按规则对齐或广播时抛出（英文）。
        """
        out = self._history_panel_compare(other, operator.lt)
        if out is NotImplemented:
            raise TypeError(
                f'Unsupported operand type(s) for <: '
                f'{type(self).__name__!r} and {type(other).__name__!r}.'
            )
        return out

    def __le__(self, other: Any) -> np.ndarray:
        """逐元素 ``self <= other``，返回 ``bool`` ``ndarray``（非子面板）。

        Parameters
        ----------
        other : Any
            右操作数；语义同 :meth:`__lt__`。

        Returns
        -------
        numpy.ndarray
            布尔结果数组。
        """
        out = self._history_panel_compare(other, operator.le)
        if out is NotImplemented:
            raise TypeError(
                f'Unsupported operand type(s) for <=: '
                f'{type(self).__name__!r} and {type(other).__name__!r}.'
            )
        return out

    def __gt__(self, other: Any) -> np.ndarray:
        """逐元素 ``self > other``，返回 ``bool`` ``ndarray``（非子面板）。

        Parameters
        ----------
        other : Any
            右操作数；语义同 :meth:`__lt__`。

        Returns
        -------
        numpy.ndarray
            布尔结果数组。
        """
        out = self._history_panel_compare(other, operator.gt)
        if out is NotImplemented:
            raise TypeError(
                f'Unsupported operand type(s) for >: '
                f'{type(self).__name__!r} and {type(other).__name__!r}.'
            )
        return out

    def __ge__(self, other: Any) -> np.ndarray:
        """逐元素 ``self >= other``，返回 ``bool`` ``ndarray``（非子面板）。

        Parameters
        ----------
        other : Any
            右操作数；语义同 :meth:`__lt__`。

        Returns
        -------
        numpy.ndarray
            布尔结果数组。
        """
        out = self._history_panel_compare(other, operator.ge)
        if out is NotImplemented:
            raise TypeError(
                f'Unsupported operand type(s) for >=: '
                f'{type(self).__name__!r} and {type(other).__name__!r}.'
            )
        return out

    def __eq__(self, other: Any) -> Any:
        """逐元素 ``self == other``；不支持的类型返回 ``NotImplemented``。

        Parameters
        ----------
        other : Any
            右操作数。

        Returns
        -------
        numpy.ndarray or NotImplemented
            可比较时为 ``bool`` 数组；否则 ``NotImplemented``。
        """
        out = self._history_panel_compare(other, operator.eq)
        if out is NotImplemented:
            return NotImplemented
        return out

    def __ne__(self, other: Any) -> Any:
        """逐元素 ``self != other``；不支持的类型返回 ``NotImplemented``。

        Parameters
        ----------
        other : Any
            右操作数。

        Returns
        -------
        numpy.ndarray or NotImplemented
            可比较时为 ``bool`` 数组；否则 ``NotImplemented``。
        """
        out = self._history_panel_compare(other, operator.ne)
        if out is NotImplemented:
            return NotImplemented
        return out

    def __add__(self, other):
        if isinstance(other, (float, int, np.ndarray)):
            self._values += other

    def __sub__(self, other):
        if isinstance(other, (float, int, np.ndarray)):
            self._values -= other

    def __mul__(self, other):
        if isinstance(other, (float, int, np.ndarray)):
            self._values *= other

    def __truediv__(self, other):
        if isinstance(other, (float, int, np.ndarray)):
            self._values /= other

    def __floordiv__(self, other):
        if isinstance(other, (float, int, np.ndarray)):
            self._values //= other

    def __mod__(self, other):
        if isinstance(other, (float, int, np.ndarray)):
            self._values %= other

    def __pow__(self, other):
        if isinstance(other, (float, int, np.ndarray)):
            self._values **= other

    def segment(self, start_date=None, end_date=None):
        """ 获取HistoryPanel的一个日期片段，start_date和end_date都是日期型数据，返回
            这两个日期之间的所有数据，返回的类型为一个HistoryPanel，包含所有share和
            htypes的数据

        Parameters
        ----------
        start_date: 开始日期
        end_date: 结束日期

        Returns
        -------
        out : HistoryPanel
            一个HistoryPanel，包含start_date到end_date之间所有share和htypes的数据

        Examples
        --------
        >>> hp = HistoryPanel(np.array([[[10, 20, 30, 40, 50]]*10]*3),
        ...                          levels=['000001', '000002', '000003'],
        ...                          rows=pd.date_range('2015-01-05', periods=10),
        ...                          columns=['open', 'high', 'low', 'close', 'volume'])
        >>> hp.segment('2015-01-07', '2015-01-10')
        share 0, label: 000100
                    open  high  low  close  volume
        2015-01-07    10    20   30     40      50
        2015-01-08    10    20   30     40      50
        2015-01-09    10    20   30     40      50
        2015-01-10    10    20   30     40      50
        share 1, label: 000200
                    open  high  low  close  volume
        2015-01-07    10    20   30     40      50
        2015-01-08    10    20   30     40      50
        2015-01-09    10    20   30     40      50
        2015-01-10    10    20   30     40      50
        share 2, label: 000300
                    open  high  low  close  volume
        2015-01-07    10    20   30     40      50
        2015-01-08    10    20   30     40      50
        2015-01-09    10    20   30     40      50
        2015-01-10    10    20   30     40      50
        """
        hdates = np.array(self.hdates)
        if start_date is None:
            start_date = hdates[0]
        if end_date is None:
            end_date = hdates[-1]
        sd = pd.to_datetime(start_date)
        ed = pd.to_datetime(end_date)
        sd_index = hdates.searchsorted(sd)
        ed_index = hdates.searchsorted(ed, side='right')
        new_dates = list(hdates[sd_index:ed_index])
        new_values = self[:, :, sd_index:ed_index].values
        return HistoryPanel(new_values, levels=self.shares, rows=new_dates, columns=self.htypes)

    def isegment(self, start_index=None, end_index=None):
        """ 获取HistoryPanel的一个片段，start_index和end_index都是int数，表示日期序号，返回
            这两个序号代表的日期之间的所有数据，返回的类型为一个HistoryPanel，包含所有share和
            htypes的数据

        Parameters
        ----------
        start_index: pd.TimeStamp
            开始日期序号
        end_index: pd.TimeStamp
            结束日期序号

        Returns
        -------
        out : HistoryPanel
            一个HistoryPanel，包含start_date到end_date之间所有share和htypes的数据

        Examples
        --------
        >>> hp = HistoryPanel(np.array([[[10, 20, 30, 40, 50]]*10]*3),
        ...                          levels=['000001', '000002', '000003'],
        ...                          rows=pd.date_range('2015-01-05', periods=10),
        ...                          columns=['open', 'high', 'low', 'close', 'volume'])
        >>> hp.isegment(2, 5)
        share 0, label: 000100
                    open  high  low  close  volume
        2015-01-07    10    20   30     40      50
        2015-01-08    10    20   30     40      50
        2015-01-09    10    20   30     40      50
        share 1, label: 000200
                    open  high  low  close  volume
        2015-01-07    10    20   30     40      50
        2015-01-08    10    20   30     40      50
        2015-01-09    10    20   30     40      50
        share 2, label: 000300
                    open  high  low  close  volume
        2015-01-07    10    20   30     40      50
        2015-01-08    10    20   30     40      50
        2015-01-09    10    20   30     40      50
        """
        hdates = np.array(self.hdates)
        new_dates = list(hdates[start_index:end_index])
        new_values = self[:, :, start_index:end_index].values
        return HistoryPanel(new_values, levels=self.shares, rows=new_dates, columns=self.htypes)

    def slice(self, shares=None, htypes=None):
        """ 获取HistoryPanel的一个股票或数据种类片段，shares和htypes可以为列表或逗号分隔字符
            串，表示需要获取的股票或数据的种类。

        Parameters
        ----------
        shares: str or list of str
            需要的股票列表
        htypes: str or list of str
            需要的数据类型列表

        Returns
        -------
        out : HistoryPanel
            一个HistoryPanel，包含shares和htypes中指定的股票和数据类型的数据

        Examples
        --------
        >>> hp = HistoryPanel(np.array([[[10, 20, 30, 40, 50]]*10]*3),
        ...                   levels=['000001', '000002', '000003'],
        ...                   rows=pd.date_range('2015-01-05', periods=10),
        ...                   columns=['open', 'high', 'low', 'close', 'volume'])
        >>> hp.slice(shares='000001,000003', htypes='close, open')
        share 0, label: 000001
                    close  open
        2015-01-05     40    10
        2015-01-06     40    10
        2015-01-07     40    10
        2015-01-08     40    10
        2015-01-09     40    10
        2015-01-10     40    10
        2015-01-11     40    10
        2015-01-12     40    10
        2015-01-13     40    10
        2015-01-14     40    10
        share 2, label: 000003
                    close  open
        2015-01-05     40    10
        2015-01-06     40    10
        2015-01-07     40    10
        2015-01-08     40    10
        2015-01-09     40    10
        2015-01-10     40    10
        2015-01-11     40    10
        2015-01-12     40    10
        2015-01-13     40    10
        2015-01-14     40    10
        """
        if self.is_empty:
            return self
        if shares is None:
            shares = self.shares
        if isinstance(shares, str):
            shares = str_to_list(shares)
        if not isinstance(shares, list):
            raise KeyError(f'wrong shares are given!')

        if htypes is None:
            htypes = self.htypes
        if isinstance(htypes, str):
            htypes = str_to_list(htypes)
        if not isinstance(htypes, list):
            raise KeyError(f'wrong htypes are given!')
        new_values = self[htypes, shares].values
        return HistoryPanel(new_values, levels=shares, columns=htypes, rows=self.hdates)

    def info(self):
        """ 打印本HistoryPanel对象的信息

        Returns
        -------
        None

        Examples
        --------
        >>> hp = HistoryPanel(np.array([[[10, 20, 30, 40, 50]]*10]*3),
        ...                          levels=['000001', '000002', '000003'],
        ...                          rows=pd.date_range('2015-01-05', periods=10),
        ...                          columns=['open', 'high', 'low', 'close', 'volume'])
        >>> hp.info()
        <class 'qteasy.history.HistoryPanel'>
        History Panel at 0x12215a850
        Datetime Range: 10 entries, 2015-01-05 00:00:00 to 2015-01-14 00:00:00
        Historical Data Types (total 5 data types):
        ['open', 'high', 'low', 'close', 'volume']
        Shares (total 3 shares):
        ['000001', '000002', '000003']
        non-null values for each share and data type:
                open  high  low  close  volume
        000001    10    10   10     10      10
        000002    10    10   10     10      10
        000003    10    10   10     10      10
        memory usage: 1344 bytes
        """
        import sys
        print(f'\n{type(self)}')
        if self.is_empty:
            print(f'Empty History Panel at {hex(id(self))}')
        else:
            print(f'History Panel at {hex(id(self))}')
            if self.row_count != 0:
                print(f'Datetime Range: {self.row_count} entries, {self.hdates[0]} to {self.hdates[-1]}')
            print(f'Historical Data Types (total {self.column_count} data types):')
            if self.column_count <= 10:
                print(f'{self.htypes}')
            else:
                print(f'{self.htypes[0:3]} ... {self.htypes[-3:-1]}')
            print(f'Shares (total {self.level_count} shares):')
            if self.level_count <= 10:
                print(f'{self.shares}')
            else:
                print(f'{self.shares[0:3]} ... {self.shares[-3:-1]}')
            sum_nnan = np.sum(~np.isnan(self.values), 1)
            df = pd.DataFrame(sum_nnan, index=self.shares, columns=self.htypes)
            print('non-null values for each share and data type:')
            print(df)
            print(f'memory usage: {sys.getsizeof(self.values)} bytes\n')

    def copy(self):
        """ 返回一个新的HistoryPanel对象，其值和本对象相同"""
        # TODO: 应该考虑使用copy模块的copy(deep=True)代替下面的代码
        return HistoryPanel(values=self.values, levels=self.levels, rows=self.rows, columns=self.columns)

    def len(self):
        """ 返回HistoryPanel对象的长度，即日期个数

        Returns
        -------
        int
            日期个数

        Examples
        --------
        >>> hp = HistoryPanel(np.array([[[10, 20, 30, 40, 50]]*10]*3),
        ...                          levels=['000001', '000002', '000003'],
        ...                          rows=pd.date_range('2015-01-05', periods=10),
        ...                          columns=['open', 'high', 'low', 'close', 'volume'])
        >>> hp.len()
        10
        """
        return self.row_count

    def re_label(self,
                 shares: Union[str, list] = None,
                 htypes: Union[str, list] = None,
                 hdates: Union[str, list] = None) -> None:
        """ 给HistoryPanel对象的层、行、列标签重新赋值

        Parameters
        ----------
        shares: str or list of str
            股票列表
        htypes: str or list of str
            数据类型列表
        hdates: str or list of str
            日期列表

        Returns
        -------
        None

        Examples
        --------
        >>> hp = HistoryPanel(np.array([[[10, 20, 30, 40, 50]]*10]*3),
        ...                          levels=['000001', '000002', '000003'],
        ...                          rows=pd.date_range('2015-01-05', periods=10),
        ...                          columns=['open', 'high', 'low', 'close', 'volume'])
        >>> hp.re_label(shares=['000100', '000200', '000300'], htypes=['typeA', 'typeB', 'typeC', 'typeD', 'typeE'])
        >>> hp
        share 0, label: 000100
                    typeA  typeB  typeC  typeD  typeE
        2015-01-05     10     20     30     40     50
        2015-01-06     10     20     30     40     50
        2015-01-07     10     20     30     40     50
        2015-01-08     10     20     30     40     50
        2015-01-09     10     20     30     40     50
        2015-01-10     10     20     30     40     50
        2015-01-11     10     20     30     40     50
        2015-01-12     10     20     30     40     50
        2015-01-13     10     20     30     40     50
        2015-01-14     10     20     30     40     50
        share 1, label: 000200
                    typeA  typeB  typeC  typeD  typeE
        2015-01-05     10     20     30     40     50
        2015-01-06     10     20     30     40     50
        2015-01-07     10     20     30     40     50
        2015-01-08     10     20     30     40     50
        2015-01-09     10     20     30     40     50
        2015-01-10     10     20     30     40     50
        2015-01-11     10     20     30     40     50
        2015-01-12     10     20     30     40     50
        2015-01-13     10     20     30     40     50
        2015-01-14     10     20     30     40     50
        share 2, label: 000300
                    typeA  typeB  typeC  typeD  typeE
        2015-01-05     10     20     30     40     50
        2015-01-06     10     20     30     40     50
        2015-01-07     10     20     30     40     50
        2015-01-08     10     20     30     40     50
        2015-01-09     10     20     30     40     50
        2015-01-10     10     20     30     40     50
        2015-01-11     10     20     30     40     50
        2015-01-12     10     20     30     40     50
        2015-01-13     10     20     30     40     50
        2015-01-14     10     20     30     40     50
        """
        if not self.is_empty:
            if shares is not None:
                self.shares = shares
            if htypes is not None:
                self.htypes = htypes
            if hdates is not None:
                self.hdates = hdates

    def fillna(self, with_val: Union[int, float]):
        """ 使用with_value来填充HistoryPanel中的所有nan值

        Parameters
        ----------
        with_val: float or int
            填充的值

        Returns
        -------
        out : HistoryPanel, 填充后的HistoryPanel对象
        """
        if not self.is_empty:
            self._values = fill_nan_data(self._values, with_val)
        return self

    def fillinf(self, with_val: Union[int, float]):
        """ 使用with_value来填充HistoryPanel中的所有inf值

        Parameters
        ----------
        with_val: float or int
            填充的值

        Returns
        -------
        out : HistoryPanel, 填充后的HistoryPanel对象
        """
        if not self.is_empty:
            self._values = fill_inf_data(self._values, with_val)
        return self

    def ffill(self, init_val=np.nan):
        """ 前向填充缺失值，当历史数据中存在缺失值时，使用缺失值以前
        的最近有效数据填充缺失值

        Parameters
        ----------
        init_val: float, 如果Nan值出现在第一行时，没有前序有效数据，则使用这个值来填充，默认为np.nan

        Returns
        -------
        out : HistoryPanel, 填充后的HistoryPanel对象

        Examples
        --------
        >>> hp = HistoryPanel(np.array([[[1, 2, 3], [4, np.nan, 6]], [[np.nan, 8, 9], [np.nan, np.nan, 12]]]),
        ...                   levels=['000001', '000002'], rows=['2015-01-01', '2015-01-02'],
        ...                   columns=['open', 'high', 'low'])
        >>> hp
        share 0, label: 000001
                    open  high  low
        2015-01-01   1.0   2.0  3.0
        2015-01-02   4.0   NaN  6.0
        share 1, label: 000002
                    open  high   low
        2015-01-01   NaN   8.0   9.0
        2015-01-02   NaN   NaN  12.0

        >>> hp.ffill()
        share 0, label: 000001
                    open  high  low
        2015-01-01   1.0   2.0  3.0
        2015-01-02   4.0   2.0  6.0
        share 1, label: 000002
                    open  high   low
        2015-01-01   NaN   8.0   9.0
        2015-01-02   NaN   8.0  12.0

        >>> hp.ffill(init_val=3)
        share 0, label: 000001
                    open  high  low
        2015-01-01   1.0   2.0  3.0
        2015-01-02   4.0   2.0  6.0
        share 1, label: 000002
                    open  high   low
        2015-01-01   3.0   8.0   9.0
        2015-01-02   3.0   8.0  12.0
        """

        if not self.is_empty:
            val = self.values
            if np.all(~np.isnan(val)):
                return self
            self._values = ffill_3d_data(val, init_val)
        return self

    def join(self,
             other,
             same_shares: bool = False,
             same_htypes: bool = False,
             same_hdates: bool = False,
             fill_value: float = np.nan):
        """ 将一个HistoryPanel对象与另一个HistoryPanel对象连接起来，生成一个新的HistoryPanel：

        新HistoryPanel的行、列、层标签分别是两个原始HistoryPanel的行、列、层标签的并集，也就是说，新的HistoryPanel的行、列
        层标签完全包含两个HistoryPanel对象的对应标签。

        Parameters
        ----------
        other: HistoryPanel
            需要合并的另一个HistoryPanel
        same_shares: bool, Default False
            两个HP的shares是否相同，如果相同，可以省去shares维度的标签合并，以节省时间。默认False，
        same_htypes: bool, Default False
            两个HP的htypes是否相同，如果相同，可以省去htypes维度的标签合并，以节省时间。默认False，
        same_hdates: bool, Default False
            两个HP的hdates是否相同，如果相同，可以省去hdates维度的标签合并，以节省时间。默认False，
        fill_value: float, Default np.nan

            空数据填充值，当组合后的HP存在空数据时，应该以什么值填充，默认为np.nan

        Returns
        -------
        HistoryPanel, 一个新的History Panel对象

        Examples
        --------
        >>> # 如果两个HistoryPanel中包含标签相同的数据，那么新的HistoryPanel中将包含调用join方法的HistoryPanel对象的相应数据。例如：
        >>> hp1 = HistoryPanel(np.array([[[8, 9, 9], [7, 5, 5], [4, 8, 4], [1, 0, 7], [8, 7, 9]],
        ...                                     [[2, 3, 3], [5, 4, 6], [2, 8, 7], [3, 3, 4], [8, 8, 7]]]),
        ...                           levels=['000200', '000300'],
        ...                           rows=pd.date_range('2020-01-01', periods=5),
        ...                           columns=['close', 'open', 'high'])
        >>> hp2 = HistoryPanel(np.array([[[8, 9, 9], [7, 5, 5], [4, 8, 4], [1, 0, 7], [8, 7, 9]],
        ...                                     [[2, 3, 3], [5, 4, 6], [2, 8, 7], [3, 3, 4], [8, 8, 7]]]),
        ...                           levels=['000400', '000500'],
        ...                           rows=pd.date_range('2020-01-01', periods=5),
        ...                           columns=['close', 'open', 'high'])
        >>> hp1
        share 0, label: 000200
                    close  open  high
        2020-01-01      8     9     9
        2020-01-02      7     5     5
        2020-01-03      4     8     4
        2020-01-04      1     0     7
        2020-01-05      8     7     9
        share 1, label: 000300
                    close  open  high
        2020-01-01      2     3     3
        2020-01-02      5     4     6
        2020-01-03      2     8     7
        2020-01-04      3     3     4
        2020-01-05      8     8     7

        >>> hp2
        share 0, label: 000400
                    close  open  high
        2020-01-01      8     9     9
        2020-01-02      7     5     5
        2020-01-03      4     8     4
        2020-01-04      1     0     7
        2020-01-05      8     7     9
        share 1, label: 000500
                    close  open  high
        2020-01-01      2     3     3
        2020-01-02      5     4     6
        2020-01-03      2     8     7
        2020-01-04      3     3     4
        2020-01-05      8     8     7

        >>> hp1.join(hp2)
        share 0, label: 000200
        """

        assert isinstance(other, HistoryPanel), \
            f'TypeError, HistoryPanel can only be joined with other HistoryPanel.'
        if self.is_empty:
            return other
        elif other.is_empty:
            return self
        else:
            other_shares = other.shares
            other_htypes = other.htypes
            other_hdates = other.hdates
            this_shares = self.shares
            this_htypes = self.htypes
            this_hdates = self.hdates
            if not same_shares:
                combined_shares = list(set(this_shares).union(set(other_shares)))
                combined_shares.sort()
            else:
                assert this_shares == other_shares, f'Assertion Error, shares of two HistoryPanels are different!'
                combined_shares = self.shares
            if not same_htypes:
                combined_htypes = list(set(this_htypes).union(set(other_htypes)))
                combined_htypes.sort()
            else:
                assert this_htypes == other_htypes, f'Assertion Error, htypes of two HistoryPanels are different!'
                combined_htypes = self.htypes
            if not same_hdates:
                combined_hdates = list(set(this_hdates).union(set(other_hdates)))
                combined_hdates.sort()
            else:
                assert this_hdates == other_hdates, f'Assertion Error, hdates of two HistoryPanels are different!'
                combined_hdates = self.hdates
            combined_values = np.empty(shape=(len(combined_shares),
                                              len(combined_hdates),
                                              len(combined_htypes)))
            combined_values.fill(fill_value)
            if same_shares:
                if same_htypes:
                    for hdate in combined_hdates:
                        combined_hdate_id = labels_to_dict(combined_hdates, combined_hdates)
                        this_hdate_id = labels_to_dict(this_hdates, this_hdates)
                        other_hdate_id = labels_to_dict(other_hdates, other_hdates)
                        if hdate in this_hdates:
                            combined_values[:, combined_hdate_id[hdate], :] = self.values[:, this_hdate_id[hdate], :]
                        else:
                            combined_values[:, combined_hdate_id[hdate], :] = other.values[:, other_hdate_id[hdate], :]
                elif same_hdates:
                    for htype in combined_htypes:
                        combined_htype_id = labels_to_dict(combined_htypes, combined_htypes)
                        this_htype_id = labels_to_dict(this_htypes, this_htypes)
                        other_htype_id = labels_to_dict(other_htypes, other_htypes)
                        if htype in this_htypes:
                            combined_values[:, :, combined_htype_id[htype]] = self.values[:, :, this_htype_id[htype]]
                        else:
                            combined_values[:, :, combined_htype_id[htype]] = other.values[:, :, other_htype_id[htype]]
                else:
                    for hdate in combined_hdates:
                        for htype in combined_htypes:
                            combined_hdate_id = labels_to_dict(combined_hdates, combined_hdates)
                            this_hdate_id = labels_to_dict(this_hdates, this_hdates)
                            other_hdate_id = labels_to_dict(other_hdates, other_hdates)
                            combined_htype_id = labels_to_dict(combined_htypes, combined_htypes)
                            this_htype_id = labels_to_dict(this_htypes, this_htypes)
                            other_htype_id = labels_to_dict(other_htypes, other_htypes)
                            if htype in this_htypes and hdate in this_hdates:
                                combined_values[:, combined_hdate_id[hdate], combined_htype_id[htype]] = \
                                    self.values[:, this_hdate_id[hdate], this_htype_id[htype]]
                            elif htype in other_htypes and hdate in other_hdates:
                                combined_values[:, combined_hdate_id[hdate], combined_htype_id[htype]] = \
                                    other.values[:, other_hdate_id[hdate], other_htype_id[htype]]
            # TODO: implement this section 实现相同htype的HistoryPanel合并
            elif same_htypes:
                raise NotImplementedError
            # TODO: implement this section 实现相同数据历史时间戳的HistoryPanel合并
            else:
                raise NotImplementedError
            return HistoryPanel(values=combined_values,
                                levels=combined_shares,
                                rows=combined_hdates,
                                columns=combined_htypes)

    def as_type(self, dtype):
        """ 将HistoryPanel的数据类型转换为dtype类型，dtype只能为'float'或'int'

        Parameters
        ----------
        dtype: str, {'float', 'int'}
            需要转换的目标数据类型

        Returns
        -------
        self

        Raises
        ______
        AssertionError
            当输入的数据类型不正确或输入除float/int外的其他数据类型时
        """
        ALL_DTYPES = ['float', 'int']
        if not self.is_empty:
            assert isinstance(dtype, str), f'InputError, dtype should be a string, got {type(dtype)}'
            assert dtype in ALL_DTYPES, f'data type {dtype} is not recognized or not supported!'
            self._values = self.values.astype(dtype)
        return self

    def slice_to_dataframe(self,
                           htype: Union[str, int] = None,
                           share: Union[str, int] = None,
                           dropna: bool = False,
                           inf_as_na: bool = False) -> pd.DataFrame:
        """ 将HistoryPanel对象中的指定片段转化为DataFrame

        指定htype或者share，将这个htype或share对应的数据切片转化为一个DataFrame。
        由于HistoryPanel对象包含三维数据，因此在转化时必须指定htype或者share参数中的一个

        Parameters
        ----------
        htype:   str or int，
            表示需要生成DataFrame的数据类型切片
            如果给出此参数，定位该htype对应的切片后，将该htype对应的所有股票所有日期的数据转化为一个DataFrame
            如果类型为str，表示htype的名称，如果类型为int，代表该htype所在的列序号
        share:   str or int，
            表示需要生成DataFrame的股票代码切片
            如果给出此参数，定位该share对应的切片后，将该share对应的所有数据类型所有日期的数据转化为一个DataFrame
            如果类型为str，表示股票代码，如果类型为int，代表该share所在的层序号
        dropna: bool, Default False
            是否去除NaN值
        inf_as_na: bool, Default False
            是否将inf值当成NaN值一同去掉，当dropna为False时无效

        Returns
        -------
        pandas.DataFrame

        Examples
        --------
        >>> hp = HistoryPanel(values=np.array([[[1, 2, np.nan], [4, 5, 6]],
        ...                                    [[7, 8, np.nan], [np.inf, 11, 12]]]),
        ...                   levels=['000001', '000002'],
        ...                   rows=['2019-01-01', '2019-01-02'],
        ...                   columns=['open', 'high', 'low']))
        >>> hp
        share 0, label: 000001
                    open  high  low
        2019-01-01   1.0   2.0  NaN
        2019-01-02   4.0   5.0  NaN
        share 1, label: 000002
                    open  high   low
        2019-01-01   7.0   8.0   9.0
        2019-01-02   inf  11.0  12.0

        >>> hp.slice_to_dataframe(htype='open')
        000001  000002
        2019-01-01  1.0  7.0
        2019-01-02  4.0  inf

        >>> hp.slice_to_dataframe(share='000001')
        open  high  low
        2019-01-01  1.0  2.0  NaN
        2019-01-02  4.0  5.0  6.0

        >>> hp.slice_to_dataframe(htype='low', dropna=True)
                    000001  000002
        2019-01-02     6.0    12.0

        """

        if self.is_empty:
            return pd.DataFrame()
        if all(par is not None for par in (htype, share)) or all(par is None for par in (htype, share)):
            # 两个参数都是非None或都是None，应该弹出警告信息
            raise KeyError(f'Only and exactly one of the parameters htype and share should be given, '
                           f'got both or none')
        res_df = pd.DataFrame()
        if htype is not None:
            assert isinstance(htype, (str, int)), f'htype must be a string or an integer, got {type(htype)}'
            if isinstance(htype, int):
                htype = self.htypes[htype]
            if not htype in self.htypes:
                raise KeyError(f'htype {htype} is not found!')
            # 在生成DataFrame之前，需要把数据降低一个维度，例如shape(1, 24, 5) -> shape(24, 5)
            v = self[htype].values.T
            v = v.reshape(v.shape[-2:])
            res_df = pd.DataFrame(v, index=self.hdates, columns=self.shares)

        if share is not None:
            assert isinstance(share, (str, int)), f'share must be a string or an integer, got {type(share)}'
            if isinstance(share, int):
                share = self.shares[share]
            if not share in self.shares:
                raise KeyError(f'share {share} is not found!')
            # 在生成DataFrame之前，需要把数据降低一个维度，例如shape(1, 24, 5) -> shape(24, 5)
            v = self[:, share].values
            v = v.reshape(v.shape[-2:])
            res_df = pd.DataFrame(v, index=self.hdates, columns=self.htypes)

        if dropna and inf_as_na:
            with pd.option_context('mode.use_inf_as_na', True):
                return res_df.dropna(how='all')
        if dropna:
            return res_df.dropna(how='all')

        return res_df

    def flatten_to_dataframe(self, along='row'):
        """ 将一个HistoryPanel"展平"成为一个DataFrame

        HistoryPanel的多层数据会被"平铺"到DataFrame的列，变成一个MultiIndex，或者多层数据
        会被平铺到DataFrame的行，同样变成一个MultiIndex，平铺到行还是列取决于along参数

        Parameters
        ----------
        along: str, {'col', 'row', 'column'} Default: 'row'
            平铺HistoryPanel的每一层时，沿行方向还是列方向平铺，
            'col'或'column'表示沿列方向平铺，'row'表示沿行方向平铺

        Returns
        -------
        pandas.DataFrame

        Examples
        --------
        >>> hp = HistoryPanel(np.array([[[12.3, 12.5, 1020010], [12.6, 13.2, 1020020]],
        ...                                    [[2.3, 2.5, 20010], [2.6, 3.2, 20020]]]),
        ...                          levels=['000300', '000001'],
        ...                          rows=['2020-01-01', '2020-01-02'],
        ...                          columns=['close', 'open', 'vol'])
        >>> hp
        share 0, label: 000300
                    close  open        vol
        2020-01-01   12.3  12.5  1020010.0
        2020-01-02   12.6  13.2  1020020.0
        share 1, label: 000001
                    close  open      vol
        2020-01-01    2.3   2.5  20010.0
        2020-01-02    2.6   3.2  20020.0

        >>> hp.flatten_to_dataframe(along='col')
                   000300                  000001
                    close  open        vol  close open      vol
        2020-01-01   12.3  12.5  1020010.0    2.3  2.5  20010.0
        2020-01-02   12.6  13.2  1020020.0    2.6  3.2  20020.0

        >>> hp.flatten_to_dataframe(along='row')
                           close  open        vol
        000300 2020-01-01   12.3  12.5  1020010.0
               2020-01-02   12.6  13.2  1020020.0
        000001 2020-01-01    2.3   2.5    20010.0
               2020-01-02    2.6   3.2    20020.0
        """
        if not isinstance(along, str):
            raise TypeError(f'along must be a string, got {type(along)} instead')
        if along not in ('col', 'row', 'column'):
            raise ValueError(f'along must be "col" or "row", got {along}')

        df_dict = self.to_df_dict(by='share')
        if self.is_empty:
            return pd.DataFrame()
        if along in ('col', 'column'):
            return pd.concat(df_dict, axis=1, keys=df_dict.keys())
        if along == 'row':
            return pd.concat(df_dict, axis=0, keys=df_dict.keys())

    def to_share_frame(self, share: Union[str, int]) -> pd.DataFrame:
        """ 将单一股票在 HistoryPanel 中的所有数据类型切片为一个 DataFrame。

        该方法是 ``slice_to_dataframe(share=...)`` 的语法糖，返回的 DataFrame
        以时间为索引、以全部 ``htypes`` 为列，适合做单股票全指标分析。

        Parameters
        ----------
        share : str or int
            股票代码或层序号，语义与 ``slice_to_dataframe(share=...)`` 中的 ``share``
            参数一致。

        Returns
        -------
        pandas.DataFrame
            行索引为 ``hdates``，列为 ``htypes``，包含该股票在所有时间点上的全部
            历史数据。
        """
        return self.slice_to_dataframe(share=share)

    def to_multi_index_dataframe(self, along=None):
        """ 等同于HistoryPanel.flatten_to_dataframe()

        Parameters
        ----------
        along: str, {'col', 'row', 'column'} Default: 'row'
            平铺HistoryPanel的每一层时，沿行方向还是列方向平铺，
            'col'或'column'表示沿列方向平铺，'row'表示沿行方向平铺

        Returns
        -------
        pandas.DataFrame

        Examples
        --------
        >>> hp = HistoryPanel(np.array([[[12.3, 12.5, 1020010], [12.6, 13.2, 1020020]],
        ...                                    [[2.3, 2.5, 20010], [2.6, 3.2, 20020]]]),
        ...                          levels=['000300', '000001'],
        ...                          rows=['2020-01-01', '2020-01-02'],
        ...                          columns=['close', 'open', 'vol'])
        >>> hp
        share 0, label: 000300
                    close  open        vol
        2020-01-01   12.3  12.5  1020010.0
        2020-01-02   12.6  13.2  1020020.0
        share 1, label: 000001
                    close  open      vol
        2020-01-01    2.3   2.5  20010.0
        2020-01-02    2.6   3.2  20020.0

        >>> hp.to_multi_index_dataframe(along='col')
                   000300                  000001
                    close  open        vol  close open      vol
        2020-01-01   12.3  12.5  1020010.0    2.3  2.5  20010.0
        2020-01-02   12.6  13.2  1020020.0    2.6  3.2  20020.0

        >>> hp.to_multi_index_dataframe(along='row')
                           close  open        vol
        000300 2020-01-01   12.3  12.5  1020010.0
               2020-01-02   12.6  13.2  1020020.0
        000001 2020-01-01    2.3   2.5    20010.0
               2020-01-02    2.6   3.2    20020.0
        """
        return self.flatten_to_dataframe(along=along)

    def flatten(self, along=None):
        """ 等同于HistoryPanel.flatten_to_dataframe()

        Parameters
        ----------
        along: str, {'col', 'row', 'column'} Default: 'row'
            平铺HistoryPanel的每一层时，沿行方向还是列方向平铺，
            'col'或'column'表示沿列方向平铺，'row'表示沿行方向平铺

        Returns
        -------
        pandas.DataFrame

        Examples
        --------
        >>> hp = HistoryPanel(np.array([[[12.3, 12.5, 1020010], [12.6, 13.2, 1020020]],
        ...                                    [[2.3, 2.5, 20010], [2.6, 3.2, 20020]]]),
        ...                          levels=['000300', '000001'],
        ...                          rows=['2020-01-01', '2020-01-02'],
        ...                          columns=['close', 'open', 'vol'])
        >>> hp
        share 0, label: 000300
                    close  open        vol
        2020-01-01   12.3  12.5  1020010.0
        2020-01-02   12.6  13.2  1020020.0
        share 1, label: 000001
                    close  open      vol
        2020-01-01    2.3   2.5  20010.0
        2020-01-02    2.6   3.2  20020.0

        >>> hp.flatten(along='col')
                   000300                  000001
                    close  open        vol  close open      vol
        2020-01-01   12.3  12.5  1020010.0    2.3  2.5  20010.0
        2020-01-02   12.6  13.2  1020020.0    2.6  3.2  20020.0

        >>> hp.flatten(along='row')
                           close  open        vol
        000300 2020-01-01   12.3  12.5  1020010.0
               2020-01-02   12.6  13.2  1020020.0
        000001 2020-01-01    2.3   2.5    20010.0
               2020-01-02    2.6   3.2    20020.0
        """
        return self.flatten_to_dataframe(along=along)

    def mean(self, by: str = 'share', skipna: bool = True) -> pd.DataFrame:
        """按标的或数据类型对 HistoryPanel 进行均值统计。

        Parameters
        ----------
        by : {'share', 'htype'}, default 'share'
            统计维度：
            - 'share'：对每只股票在时间轴上的均值，返回 index 为 shares、columns 为 htypes 的 DataFrame；
            - 'htype'：对每个 htype 在所有股票上的均值，返回转置后的 DataFrame。
        skipna : bool, default True
            是否在计算均值时忽略 NaN。

        Returns
        -------
        pandas.DataFrame
            按指定维度聚合后的均值结果表。

        Examples
        --------
        >>> hp = HistoryPanel(np.random.rand(2, 3, 2),
        ...                   levels=['000001.SZ', '000002.SZ'],
        ...                   rows=pd.date_range('2020-01-01', periods=3),
        ...                   columns=['open', 'close'])
        >>> hp.mean()
                    open     close
        000001.SZ  0.456789  0.567890
        000002.SZ  0.345678  0.456789
        """
        if self.is_empty:
            return pd.DataFrame()
        if by not in ('share', 'htype'):
            raise ValueError(f'parameter "by" must be "share" or "htype", got {by}')

        values = self.values.astype(float)
        if skipna:
            agg_share = np.nanmean(values, axis=1)
        else:
            agg_share = values.mean(axis=1)
        df_share = pd.DataFrame(agg_share, index=self.shares, columns=self.htypes)
        if by == 'share':
            return df_share
        return df_share.T

    def std(self, by: str = 'share', skipna: bool = True) -> pd.DataFrame:
        """按标的或数据类型对 HistoryPanel 进行标准差统计（ddof=1）。

        Parameters
        ----------
        by : {'share', 'htype'}, default 'share'
            统计维度，语义同 ``mean()``。
        skipna : bool, default True
            是否在计算标准差时忽略 NaN。

        Returns
        -------
        pandas.DataFrame
            按指定维度聚合后的标准差结果表。

        Examples
        --------
        >>> hp = HistoryPanel(np.random.rand(2, 4, 2),
        ...                   levels=['000001.SZ', '000002.SZ'],
        ...                   rows=pd.date_range('2020-01-01', periods=4),
        ...                   columns=['open', 'close'])
        >>> hp.std()
                    open     close
        000001.SZ  0.129099  0.086603
        000002.SZ  0.149361  0.110769
        """
        if self.is_empty:
            return pd.DataFrame()
        if by not in ('share', 'htype'):
            raise ValueError(f'parameter "by" must be "share" or "htype", got {by}')

        values = self.values.astype(float)
        if skipna:
            agg_share = np.nanstd(values, axis=1, ddof=1)
        else:
            agg_share = values.std(axis=1, ddof=1)
        df_share = pd.DataFrame(agg_share, index=self.shares, columns=self.htypes)
        if by == 'share':
            return df_share
        return df_share.T

    def min(self, by: str = 'share', skipna: bool = True) -> pd.DataFrame:
        """按标的或数据类型对 HistoryPanel 进行最小值统计。

        Parameters
        ----------
        by : {'share', 'htype'}, default 'share'
            统计维度，语义同 ``mean()``。
        skipna : bool, default True
            是否在计算最小值时忽略 NaN。

        Returns
        -------
        pandas.DataFrame
            按指定维度聚合后的最小值结果表。

        Examples
        --------
        >>> data = np.array([[[1., 2.], [3., 4.]],
        ...                  [[5., 6.], [7., 8.]]])
        >>> hp = HistoryPanel(values=data,
        ...                   levels=['000001.SZ', '000002.SZ'],
        ...                   rows=pd.date_range('2020-01-01', periods=2),
        ...                   columns=['open', 'close'])
        >>> hp.min()
                    open  close
        000001.SZ   1.0    2.0
        000002.SZ   5.0    6.0
        """
        if self.is_empty:
            return pd.DataFrame()
        if by not in ('share', 'htype'):
            raise ValueError(f'parameter "by" must be "share" or "htype", got {by}')

        values = self.values.astype(float)
        if skipna:
            agg_share = np.nanmin(values, axis=1)
        else:
            agg_share = values.min(axis=1)
        df_share = pd.DataFrame(agg_share, index=self.shares, columns=self.htypes)
        if by == 'share':
            return df_share
        return df_share.T

    def max(self, by: str = 'share', skipna: bool = True) -> pd.DataFrame:
        """按标的或数据类型对 HistoryPanel 进行最大值统计。

        Parameters
        ----------
        by : {'share', 'htype'}, default 'share'
            统计维度，语义同 ``mean()``。
        skipna : bool, default True
            是否在计算最大值时忽略 NaN。

        Returns
        -------
        pandas.DataFrame
            按指定维度聚合后的最大值结果表。

        Examples
        --------
        >>> data = np.array([[[1., 2.], [3., 4.]],
        ...                  [[5., 6.], [7., 8.]]])
        >>> hp = HistoryPanel(values=data,
        ...                   levels=['000001.SZ', '000002.SZ'],
        ...                   rows=pd.date_range('2020-01-01', periods=2),
        ...                   columns=['open', 'close'])
        >>> hp.max()
                    open  close
        000001.SZ   3.0    4.0
        000002.SZ   7.0    8.0
        """
        if self.is_empty:
            return pd.DataFrame()
        if by not in ('share', 'htype'):
            raise ValueError(f'parameter "by" must be "share" or "htype", got {by}')

        values = self.values.astype(float)
        if skipna:
            agg_share = np.nanmax(values, axis=1)
        else:
            agg_share = values.max(axis=1)
        df_share = pd.DataFrame(agg_share, index=self.shares, columns=self.htypes)
        if by == 'share':
            return df_share
        return df_share.T

    def describe(
            self,
            by: Optional[str] = 'share',
            percentiles: tuple = (0.25, 0.5, 0.75),
            include: str = 'numeric',
            ddof: int = 1,
    ) -> pd.DataFrame:
        """对 HistoryPanel 进行基础统计描述，类似 pandas.DataFrame.describe。

        可以按标的（share）、历史数据类型（htype）或全局视角对数值数据做 count、
        mean、std、min、max 及给定分位数等统计描述。

        Parameters
        ----------
        by : {'share', 'htype', None}, default 'share'
            统计视角：
            - 'share'：每只股票一个 describe 结果，拼接成列为 (htype, stat) 的 MultiIndex；
            - 'htype'：每个 htype 在所有股票与时间上的分布；
            - None：将全部数值视作一个整体样本池。
        percentiles : tuple of float, default (0.25, 0.5, 0.75)
            需要计算的分位数列表，值应在 (0, 1) 区间。
        include : {'numeric', None}, default 'numeric'
            当前仅支持数值型统计，非数值列会被自动忽略。
        ddof : int, default 1
            计算标准差时的自由度参数，仅在 ``by is None`` 时生效。

        Returns
        -------
        pandas.DataFrame
            描述性统计结果表，其 index/columns 结构取决于 by 的取值。

        Examples
        --------
        >>> hp = HistoryPanel(np.random.rand(2, 10, 2),
        ...                   levels=['000001.SZ', '000002.SZ'],
        ...                   rows=pd.date_range('2020-01-01', periods=10),
        ...                   columns=['open', 'close'])
        >>> desc_share = hp.describe(by='share')
        >>> desc_share
        share 0, label: 000001.SZ
                    open      close
        count  10.000000  10.000000
        mean    0.456789   0.567890
        std     0.129099   0.086603
        min     0.123456   0.234567
        25%     0.234567   0.345678
        50%     0.345678   0.456789
        75%     0.567890   0.678901
        share 1, label: 000002.SZ
                    open      close
        count  10.000000  10.000000
        mean    0.345678   0.456789
        std     0.149361   0.110769
        min     0.012345   0.123456
        25%     0.123456   0.234567
        50%     0.234567   0.345678
        75%     0.456789   0.567890

        >>> sorted(desc_share.columns.get_level_values('stat').unique().tolist())
        ['25%', '50%', '75%', 'count', 'max', 'mean', 'min', 'std']

        >>> desc_htype = hp.describe(by='htype')
        >>> 'open' in desc_htype.index
        True
        """
        if self.is_empty:
            return pd.DataFrame()
        # 目前仅支持数值型统计，兼容老版本 pandas，这里不直接将 include 透传给 pandas.describe
        if include not in ('numeric', None):
            raise ValueError('only numeric include is supported for HistoryPanel.describe')

        # by='share'：对每只股票的 DataFrame 做 describe，拼接为 MultiIndex 列
        if by == 'share':
            rows = {}
            col_tuples = []
            first = True
            for share in self.shares:
                df = self.slice_to_dataframe(share=share)
                # DataFrame 仅包含数值列，不再传递 include 参数，以兼容当前 pandas 版本
                desc = df.describe(percentiles=percentiles)
                if first:
                    stats_order = list(desc.index)
                    for htype in df.columns:
                        for stat in stats_order:
                            col_tuples.append((htype, stat))
                    first = False
                values = []
                for htype in df.columns:
                    for stat in stats_order:
                        values.append(desc.loc[stat, htype])
                rows[share] = values
            desc_df = pd.DataFrame.from_dict(rows, orient='index')
            desc_df.columns = pd.MultiIndex.from_tuples(col_tuples, names=['htype', 'stat'])
            return desc_df

        # by='htype'：每个 htype 在所有股票与时间上的分布
        if by == 'htype':
            rows = {}
            stats_index = None
            for i, htype in enumerate(self.htypes):
                arr = self.values[:, :, i].astype(float).ravel()
                arr = arr[~np.isnan(arr)]
                series = pd.Series(arr)
                desc = series.describe(percentiles=percentiles)
                if stats_index is None:
                    stats_index = desc.index
                rows[htype] = desc.values
            desc_df = pd.DataFrame.from_dict(rows, orient='index', columns=stats_index)
            return desc_df

        # 全局 describe：所有数值视作一个整体样本池
        if by is None:
            arr = self.values.astype(float).ravel()
            arr = arr[~np.isnan(arr)]
            series = pd.Series(arr)
            desc = series.describe(percentiles=percentiles)
            if 'std' in desc.index:
                desc['std'] = series.std(ddof=ddof)
            return desc.to_frame().T

        raise ValueError(f'parameter \"by\" must be \"share\", \"htype\" or None, got {by}')

    def rolling(
            self,
            window: int,
            min_periods: Optional[int] = None,
            center: bool = False,
            by: str = 'share',
    ) -> "HistoryPanelRolling":
        """基于 HistoryPanel 构造滚动窗口统计对象。

        滚动仅沿时间轴（rows / hdates）进行，``window`` 为整数 bar 数。

        Parameters
        ----------
        window : int
            滚动窗口长度。
        min_periods : int, optional
            最小有效观测数，小于该数时结果为 ``NaN``。默认与 ``window`` 相同。
        center : bool, default False
            是否使用居中窗口，语义与 ``pandas.Series.rolling`` 一致。
        by : {'share', 'htype'}, default 'share'
            指定滚动的分组方式：
            - 'share': 每只股票的每个 htype 独立做滚动统计（最常用）；
            - 'htype': 每个 htype 在所有股票上独立做滚动统计。

        Returns
        -------
        HistoryPanelRolling
                滚动窗口统计对象，支持调用 mean(), std(), min(), max() 等

        Examples
        --------
        >>> hp = HistoryPanel(np.array([[[12.3, 12.5, 1020010], [12.6, 13.2, 1020020]],
        ...                                    [[2.3, 2.5, 20010], [2.6, 3.2, 20020]]]),
        ...                          levels=['000300', '000001'],
        ...                          rows=['2020-01-01', '2020-01-02'],
        ...                          columns=['close', 'open', 'vol'])
        >>> hp.rolling(window=2, by='share').mean()
        share 0, label: 000300
                    close  open        vol
        2020-01-01    NaN   NaN        NaN
        2020-01-02   12.45  12.85  1020015.0
        share 1, label: 000001
                    close  open        vol
        2020-01-01    NaN   NaN        NaN
        2020-01-02    2.45   2.85  20015.0
        """
        if self.is_empty:
            return HistoryPanelRolling(self, window, min_periods, center, by)
        if not isinstance(window, int) or window <= 0:
            raise ValueError(f'window must be a positive integer, got {window}')
        if min_periods is None:
            min_periods = window
        if not isinstance(min_periods, int) or min_periods <= 0:
            raise ValueError(f'min_periods must be a positive integer, got {min_periods}')
        if by not in ('share', 'htype'):
            raise ValueError(f'parameter \"by\" must be \"share\" or \"htype\", got {by}')
        return HistoryPanelRolling(self, window, min_periods, center, by)

    def returns(
            self,
            price_htype: str = 'close',
            method: str = 'simple',
            periods: int = 1,
            as_panel: bool = False,
            dropna: bool = False,
    ):
        """基于指定价格序列计算收益率。

        Parameters
        ----------
        price_htype : str, default 'close'
            用于计算收益率的价格类型，必须在 htypes 中存在。
        method : {'simple', 'log'}, default 'simple'
            - simple: r_t = p_t / p_{t-periods} - 1
            - log: r_t = log(p_t) - log(p_{t-periods})
        periods : int, default 1
            收益率间隔的 bar 数。
        as_panel : bool, default False
            False 返回 DataFrame（index=时间，columns=shares）；
            True 返回 HistoryPanel（htypes 仅含 ret_{price_htype}）。
        dropna : bool, default False
            True 时删除全为 NaN 的起始行。

        Returns
        -------
        pandas.DataFrame or HistoryPanel
        """
        if self.is_empty:
            if as_panel:
                return HistoryPanel()
            return pd.DataFrame()
        resolved_price_htype = self._resolve_price_htype(price_htype)
        if method not in ('simple', 'log'):
            raise ValueError(f'method must be "simple" or "log", got {method}')

        ci = self.htypes.index(resolved_price_htype)
        prices = self.values[:, :, ci].astype(float)  # (shares, times)

        n_share, n_time = prices.shape
        ret = np.full((n_share, n_time), np.nan, dtype=float)

        for i in range(n_share):
            p = prices[i, :]
            for t in range(periods, n_time):
                p_prev = p[t - periods]
                p_curr = p[t]
                if np.isnan(p_prev) or np.isnan(p_curr) or p_prev <= 0:
                    ret[i, t] = np.nan
                elif method == 'simple':
                    ret[i, t] = p_curr / p_prev - 1.0
                else:  # log
                    ret[i, t] = np.log(p_curr) - np.log(p_prev)

        if dropna:
            # 删除整行全 NaN 的起始行
            mask = np.any(~np.isnan(ret), axis=0)
            ret = ret[:, mask]
            used_hdates = [d for d, m in zip(self.hdates, mask) if m]
        else:
            used_hdates = list(self.hdates)

        if as_panel:
            new_htype = f'ret_{price_htype}'
            return HistoryPanel(
                values=ret.reshape(n_share, -1, 1),
                levels=self.shares,
                rows=used_hdates,
                columns=[new_htype],
            )
        df = pd.DataFrame(ret.T, index=used_hdates, columns=self.shares)
        return df

    def _broadcast_bool_mask_for_panel(self, mask: Optional[np.ndarray]) -> np.ndarray:
        """将 ``mask`` 广播为与 ``self.values`` 同形的 bool 数组（全 True 表示无掩码）。

        广播规则与 :meth:`where` 中非 callable 条件一致。
        """
        if self.is_empty:
            raise ValueError('internal error: mask broadcast on empty HistoryPanel')
        if mask is None:
            return np.ones(self.shape, dtype=bool)
        try:
            b = np.asarray(mask, dtype=bool)
        except (TypeError, ValueError) as e:
            raise ValueError(
                f'Cannot convert mask to a boolean array: {e}'
            ) from e
        m, l_count, n = self._l_count, self._r_count, self._c_count
        target = (m, l_count, n)
        if b.shape == target:
            return np.array(b, dtype=bool, copy=True)
        if b.ndim == 0:
            broad = np.broadcast_to(b, target)
            return np.array(broad, dtype=bool, copy=True)
        if b.ndim == 2 and b.shape == (m, l_count):
            b = b[:, :, np.newaxis]
        elif b.ndim == 1 and b.shape == (m,):
            b = b.reshape(m, 1, 1)
        elif b.ndim == 2 and b.shape == (m, 1):
            b = b.reshape(m, 1, 1)
        try:
            broad = np.broadcast_to(b, target)
        except ValueError:
            raise ValueError(
                f'Cannot broadcast mask with shape {getattr(b, "shape", ())} '
                f'to panel shape {target}.'
            ) from None
        return np.array(broad, dtype=bool, copy=True)

    @staticmethod
    def _cum_return_1d_along_time(p_eff: np.ndarray, method: str) -> np.ndarray:
        """沿单 share 单列时间序列计算累计收益（已套用 mask 的 ``p_eff``）。"""
        p_eff = np.asarray(p_eff, dtype=float).ravel()
        l_cnt = p_eff.size
        out = np.full(l_cnt, np.nan, dtype=float)
        t0: Optional[int] = None
        for t in range(l_cnt):
            v = p_eff[t]
            if np.isfinite(v) and v > 0:
                t0 = t
                break
        if t0 is None:
            return out
        out[t0] = 0.0
        p0 = p_eff[t0]
        broken = False
        for t in range(t0 + 1, l_cnt):
            v = p_eff[t]
            if broken or not np.isfinite(v) or v <= 0:
                broken = True
                out[t] = np.nan
                continue
            if method == 'simple':
                out[t] = v / p0 - 1.0
            else:
                out[t] = np.log(v) - np.log(p0)
        return out

    @staticmethod
    def _normalize_1d_along_time(
            p_eff: np.ndarray,
            base_index: int,
            mask_1d: np.ndarray,
    ) -> np.ndarray:
        """单 share 单列归一化；``mask_1d`` 与 ``p_eff`` 等长。"""
        p_eff = np.asarray(p_eff, dtype=float).ravel()
        mask_1d = np.asarray(mask_1d, dtype=bool).ravel()
        l_cnt = p_eff.size
        if base_index < 0 or base_index >= l_cnt:
            raise ValueError(f'base_index out of range for time axis: {base_index}')
        if (not mask_1d[base_index]
                or not np.isfinite(p_eff[base_index])
                or p_eff[base_index] == 0.0):
            return np.full(l_cnt, np.nan, dtype=float)
        base = p_eff[base_index]
        return p_eff / base

    def _resolve_cum_norm_column_pairs(
            self,
            htypes: Optional[Union[str, Sequence[str]]],
    ) -> List[Tuple[str, int]]:
        """解析列：返回 (用户标签, 全局列下标) 列表；``htypes is None`` 时等价于 ``close``。"""
        if self.is_empty:
            return []
        if htypes is None:
            labels = ['close']
        elif isinstance(htypes, str):
            labels = [htypes]
        else:
            labels = list(htypes)
        if len(labels) != len(set(labels)):
            raise ValueError('duplicate htype labels in htypes sequence')
        pairs: List[Tuple[str, int]] = []
        for lab in labels:
            resolved = self._resolve_price_htype(lab)
            j = self.htypes.index(resolved)
            pairs.append((lab, j))
        return pairs

    def cum_return(
            self,
            htypes: Optional[Union[str, Sequence[str]]] = None,
            *,
            method: str = 'simple',
            mask: Optional[np.ndarray] = None,
    ) -> 'HistoryPanel':
        """沿时间维逐标的计算累计收益（研究向），返回新面板。

        默认对 ``close`` 列（经 :meth:`_resolve_price_htype` 解析，支持 ``close|b`` 等）计算。
        输出列名为 ``cumret_<用户传入的列名>``，与 :meth:`returns` 使用 ``ret_<price_htype>`` 的策略一致。
        若时间路径上出现 NaN 或非正价格，自该点起后续结果均为 NaN（路径断开）。

        Parameters
        ----------
        htypes : str, sequence of str, optional
            参与计算的列名；``None`` 时仅处理 ``close``（解析后）。
        method : {'simple', 'log'}, default 'simple'
            ``simple``：自首个有效正价 ``t0`` 起 ``p_t/p_{t0}-1``；``log``：``log(p_t)-log(p_{t0})``。
        mask : numpy.ndarray, optional
            与 :meth:`where` 相同广播规则；为 ``False`` 的位置在计算前视为缺失（``NaN``）。

        Returns
        -------
        HistoryPanel
            ``shares`` / ``hdates`` 与原面板一致，仅含累计收益列。

        Raises
        ------
        ValueError
            非法 ``method``、列无法解析、``mask`` 无法广播、或输出列名与现有 ``htypes`` 冲突时抛出（英文）。

        Examples
        --------
        >>> import numpy as np
        >>> import pandas as pd
        >>> from qteasy.history import HistoryPanel
        >>> hp = HistoryPanel(
        ...     np.array([[[10.0], [11.0], [12.0]]]),
        ...     levels=['S'],
        ...     rows=pd.date_range('2023-01-01', periods=3),
        ...     columns=['close'],
        ... )
        >>> cr = hp.cum_return(method='simple')
        >>> cr.htypes
        ['cumret_close']
        >>> float(cr.values[0, -1, 0])
        0.2
        """
        if self.is_empty:
            return HistoryPanel()
        if method not in ('simple', 'log'):
            raise ValueError(f'method must be "simple" or "log", got {method}')
        mask_full = self._broadcast_bool_mask_for_panel(mask)
        pairs = self._resolve_cum_norm_column_pairs(htypes)
        out_names = [f'cumret_{lab}' for lab, _ in pairs]
        for name in out_names:
            if name in self.htypes:
                raise ValueError(
                    f'output htype "{name}" already exists in panel; '
                    'choose different columns or rename existing htypes.'
                )
        m, l_cnt, _ = self.shape
        n_out = len(pairs)
        out_arr = np.full((m, l_cnt, n_out), np.nan, dtype=float)
        values_f = self.values.astype(float)
        for k, (lab, j) in enumerate(pairs):
            for i in range(m):
                p = values_f[i, :, j]
                m_ij = mask_full[i, :, j]
                p_eff = np.where(m_ij, p, np.nan)
                out_arr[i, :, k] = self._cum_return_1d_along_time(p_eff, method)
        return HistoryPanel(
            values=out_arr,
            levels=list(self.shares),
            rows=list(self.hdates),
            columns=out_names,
        )

    def normalize(
            self,
            htypes: Optional[Union[str, Sequence[str]]] = None,
            *,
            base_index: int = 0,
            mask: Optional[np.ndarray] = None,
    ) -> 'HistoryPanel':
        """将指定列按基准时点缩放到相对 1.0（研究向），返回新面板。

        默认以 ``base_index`` 处有效价格为分母；该时点被 ``mask`` 排除、为 ``NaN`` 或为 0 时，
        该 (share, 列) 整条时间序列输出均为 ``NaN``。输出列名为 ``norm_<用户传入的列名>``。

        Parameters
        ----------
        htypes : str, sequence of str, optional
            参与计算的列；``None`` 时仅 ``close``（解析后）。
        base_index : int, default 0
            时间轴上的基准下标（从 0 起）；越界时抛出 ``ValueError``（英文）。
        mask : numpy.ndarray, optional
            与 :meth:`where` 相同广播规则。

        Returns
        -------
        HistoryPanel
            与原面板相同的 ``shares`` / ``hdates``，仅含归一化列。

        Raises
        ------
        ValueError
            列无法解析、``mask`` 无法广播、``base_index`` 越界、或输出列名冲突时抛出（英文）。

        Examples
        --------
        >>> import numpy as np
        >>> import pandas as pd
        >>> from qteasy.history import HistoryPanel
        >>> hp = HistoryPanel(
        ...     np.array([[[10.0], [20.0], [40.0]]]),
        ...     levels=['S'],
        ...     rows=pd.date_range('2023-01-01', periods=3),
        ...     columns=['close'],
        ... )
        >>> nm = hp.normalize(base_index=0)
        >>> float(nm.values[0, -1, 0])
        4.0
        """
        if self.is_empty:
            return HistoryPanel()
        mask_full = self._broadcast_bool_mask_for_panel(mask)
        pairs = self._resolve_cum_norm_column_pairs(htypes)
        out_names = [f'norm_{lab}' for lab, _ in pairs]
        for name in out_names:
            if name in self.htypes:
                raise ValueError(
                    f'output htype "{name}" already exists in panel; '
                    'choose different columns or rename existing htypes.'
                )
        m, l_cnt, _ = self.shape
        n_out = len(pairs)
        out_arr = np.full((m, l_cnt, n_out), np.nan, dtype=float)
        values_f = self.values.astype(float)
        for k, (lab, j) in enumerate(pairs):
            for i in range(m):
                p = values_f[i, :, j]
                m_ij = mask_full[i, :, j]
                p_eff = np.where(m_ij, p, np.nan)
                out_arr[i, :, k] = self._normalize_1d_along_time(
                    p_eff, base_index, m_ij,
                )
        return HistoryPanel(
            values=out_arr,
            levels=list(self.shares),
            rows=list(self.hdates),
            columns=out_names,
        )

    def _resolve_portfolio_htype_pairs(
            self,
            htypes: Union[str, Sequence[str]],
    ) -> List[Tuple[str, int]]:
        """解析 ``portfolio`` 参与聚合的列：``(用户标签, 列下标)``。"""
        if isinstance(htypes, str):
            labels = [htypes]
        else:
            labels = list(htypes)
        pairs: List[Tuple[str, int]] = []
        for lab in labels:
            resolved = self._resolve_price_htype(lab)
            j = self.htypes.index(resolved)
            pairs.append((lab, j))
        return pairs

    @staticmethod
    def _portfolio_aggregate_cell(
            values_f: np.ndarray,
            mask_full: np.ndarray,
            share_indices: Sequence[int],
            t: int,
            j: int,
            *,
            mode: str,
            weights: Optional[np.ndarray],
            normalize_weights: bool,
    ) -> float:
        """单组、单时刻、单列上的组合值（等权或加权）。"""
        xs: List[float] = []
        wi_list: List[float] = []
        for i in share_indices:
            if not mask_full[i, t, j]:
                continue
            v = values_f[i, t, j]
            if not np.isfinite(v):
                continue
            xs.append(float(v))
            if mode == 'weighted':
                if weights is None:
                    raise ValueError('internal: weighted mode without weights')
                if weights.ndim == 1:
                    wi = float(weights[i])
                elif weights.ndim == 2:
                    wi = float(weights[i, t])
                else:
                    raise ValueError('weights must be 1D or 2D')
                wi_list.append(wi)
        if not xs:
            return float('nan')
        if mode == 'equal':
            return float(np.mean(xs))
        w_arr = np.asarray(wi_list, dtype=float)
        x_arr = np.asarray(xs, dtype=float)
        sw = float(np.sum(w_arr))
        if sw == 0.0 or not np.isfinite(sw):
            return float('nan')
        if normalize_weights:
            w_arr = w_arr / sw
            return float(np.sum(w_arr * x_arr))
        return float(np.sum(w_arr * x_arr) / sw)

    def portfolio(
            self,
            htypes: Union[str, Sequence[str]] = 'close',
            *,
            mode: str = 'equal',
            weights: Optional[np.ndarray] = None,
            mask: Optional[np.ndarray] = None,
            groups: Optional[Dict[str, Sequence[str]]] = None,
            benchmark: Optional[str] = None,
            benchmark_output: str = 'none',
            new_share_name: str = 'PORTFOLIO',
            normalize_weights: bool = True,
            allow_ungrouped: str = 'error',
    ) -> 'HistoryPanel':
        """沿 share 维将多标的聚合成组合序列（研究向），返回新面板。

        默认 ``benchmark_output='none'``；若设置 ``benchmark``，可用 ``tag_along`` 附加基准行，
        或用 ``excess_only`` 仅保留 ``excess_<列名> = 组合 - 基准``。

        ``groups`` 为 ``None`` 时，全面板聚成一行，名称为 ``new_share_name``。
        ``groups`` 非空时，键为输出 share 标签（按 **插入序** 排列），值为组内原始 share 列表；
        组间 share 不得重叠。``allow_ungrouped='error'`` 时，每个面板 share 必须恰好属于一组。

        当 ``groups`` 为 ``None`` 且指定了 ``benchmark`` 时，**基准 share 不参与**组合聚合（避免把指数与个股权重混在一起），
        仅用于 ``tag_along`` 或 ``excess_only``；若剔除后无可用 share（例如面板仅含基准）则抛出 ``ValueError``。

        ``mask`` 广播规则与 :meth:`where` 一致；无效格点不参与聚合。

        Parameters
        ----------
        htypes : str or sequence of str, default 'close'
            参与聚合的列名；经 :meth:`_resolve_price_htype` 解析。
        mode : {'equal', 'weighted'}, default 'equal'
            等权平均或与 ``weights`` 联用的加权平均。
        weights : numpy.ndarray, optional
            形状 ``(M,)`` 或 ``(M, L)``，与 ``self.shares`` 顺序对齐；仅 ``mode='weighted'`` 时使用。
        mask : numpy.ndarray, optional
            与 :meth:`where` 相同广播规则。
        groups : dict, optional
            输出组名 → 组内 share 标签列表。
        benchmark : str, optional
            基准 share，须在 ``self.shares`` 中。
        benchmark_output : {'none', 'tag_along', 'excess_only'}, default 'none'
            基准输出形态；无 ``benchmark`` 时仅允许 ``'none'``。
        new_share_name : str, default 'PORTFOLIO'
            无 ``groups`` 时合成行的 share 名。
        normalize_weights : bool, default True
            加权时，在参与聚合的成员上对权重做归一后再加权求和（与 ``sum(w*x)/sum(w)`` 数值一致）。
        allow_ungrouped : {'error', 'exclude'}, default 'error'
            ``groups`` 非空时，是否要求覆盖全部 share。

        Returns
        -------
        HistoryPanel
            新对象；``hdates`` 与时间长度与原面板一致。

        Raises
        ------
        ValueError
            参数非法、share 不在面板、组重叠、mask 无法广播等（英文）。
        """
        if self.is_empty:
            return HistoryPanel()
        if benchmark is None and benchmark_output != 'none':
            raise ValueError(
                'benchmark is None but benchmark_output is not "none"; '
                'set benchmark_output="none" or pass a valid benchmark share.'
            )
        if benchmark_output not in ('none', 'tag_along', 'excess_only'):
            raise ValueError(
                f'benchmark_output must be "none", "tag_along", or "excess_only", '
                f'got {benchmark_output!r}'
            )
        if benchmark is not None and benchmark not in self.shares:
            raise ValueError(f'benchmark "{benchmark}" not found in shares: {self.shares}')
        if mode not in ('equal', 'weighted'):
            raise ValueError(f'mode must be "equal" or "weighted", got {mode!r}')
        if weights is None and mode != 'equal':
            raise ValueError('mode="weighted" requires weights array')
        if weights is not None and mode != 'weighted':
            raise ValueError('weights are only used with mode="weighted"')
        if allow_ungrouped not in ('error', 'exclude'):
            raise ValueError('allow_ungrouped must be "error" or "exclude"')
        m, l_cnt, _ = self.shape
        if weights is not None:
            w_arr = np.asarray(weights, dtype=float)
            if w_arr.ndim == 1:
                if w_arr.shape[0] != m:
                    raise ValueError(
                        f'weights length {w_arr.shape[0]} does not match share count {m}'
                    )
            elif w_arr.ndim == 2:
                if w_arr.shape[0] != m or w_arr.shape[1] != l_cnt:
                    raise ValueError(
                        f'weights shape {w_arr.shape} does not match panel shape {(m, l_cnt)}'
                    )
            else:
                raise ValueError('weights must be 1D or 2D')
            weights_use: Optional[np.ndarray] = w_arr
        else:
            weights_use = None

        mask_full = self._broadcast_bool_mask_for_panel(mask)
        htype_pairs = self._resolve_portfolio_htype_pairs(htypes)
        n_col = len(htype_pairs)
        values_f = self.values.astype(float)

        share_index = {s: i for i, s in enumerate(self.shares)}
        group_specs: List[Tuple[str, List[int]]]
        if groups is None:
            all_idx = list(range(m))
            if benchmark is not None:
                bi = share_index[benchmark]
                all_idx = [i for i in all_idx if i != bi]
                if not all_idx:
                    raise ValueError(
                        'cannot form portfolio: all shares would be excluded '
                        'because benchmark is the only share in the panel'
                    )
            group_specs = [(new_share_name, all_idx)]
        else:
            if len(groups) == 0:
                raise ValueError('groups must be non-empty when provided')
            group_specs = []
            assigned: Dict[str, str] = {}
            for gname, members in groups.items():
                if not members:
                    raise ValueError(f'group "{gname}" has empty member list')
                idxs: List[int] = []
                for s in members:
                    if s not in share_index:
                        raise ValueError(f'share "{s}" in group "{gname}" not in panel shares')
                    if s in assigned:
                        raise ValueError(
                            f'share "{s}" appears in more than one group '
                            f'("{assigned[s]}" and "{gname}")'
                        )
                    assigned[s] = gname
                    idxs.append(share_index[s])
                group_specs.append((gname, idxs))
            if allow_ungrouped == 'error':
                for s in self.shares:
                    if s not in assigned:
                        raise ValueError(
                            f'share "{s}" is not in any group; '
                            'set allow_ungrouped="exclude" to omit unlisted shares'
                        )

        n_grp = len(group_specs)
        port = np.full((n_grp, l_cnt, n_col), np.nan, dtype=float)
        for gi, (_, sidxs) in enumerate(group_specs):
            for t in range(l_cnt):
                for jc, (_, j) in enumerate(htype_pairs):
                    port[gi, t, jc] = self._portfolio_aggregate_cell(
                        values_f,
                        mask_full,
                        sidxs,
                        t,
                        j,
                        mode=mode,
                        weights=weights_use,
                        normalize_weights=normalize_weights,
                    )

        out_shares: List[str] = [name for name, _ in group_specs]
        out_htypes: List[str]
        out_vals: np.ndarray

        if benchmark is not None and benchmark_output == 'excess_only':
            bi = share_index[benchmark]
            bench_block = np.stack(
                [values_f[bi, :, j] for _, j in htype_pairs],
                axis=1,
            )
            excess = port - bench_block[np.newaxis, :, :]
            out_htypes = [f'excess_{lab}' for lab, _ in htype_pairs]
            out_vals = excess
        else:
            out_htypes = [lab for lab, _ in htype_pairs]
            out_vals = port
            if benchmark is not None and benchmark_output == 'tag_along':
                bi = share_index[benchmark]
                bench_block = np.stack(
                    [values_f[bi, :, j] for _, j in htype_pairs],
                    axis=1,
                )
                out_vals = np.concatenate([out_vals, bench_block[np.newaxis, :, :]], axis=0)
                out_shares = out_shares + [benchmark]

        return HistoryPanel(
            values=out_vals,
            levels=out_shares,
            rows=list(self.hdates),
            columns=out_htypes,
        )

    def volatility(
            self,
            window: int = 20,
            price_htype: str = 'close',
            method: str = 'simple',
            annualize: bool = True,
            periods_per_year: Optional[int] = None,
            as_panel: bool = False,
    ):
        """基于收益率序列计算滚动波动率（标准差）。

        Parameters
        ----------
        window : int, default 20
            滚动窗口长度（bar 数）。
        price_htype : str, default 'close'
            用于计算收益率的价格类型。
        method : {'simple', 'log'}, default 'simple'
            收益率计算方式，与 returns() 一致。
        annualize : bool, default True
            是否年化（乘以 sqrt(periods_per_year)）。
        periods_per_year : int, optional
            年化时每年 bar 数；未指定且 annualize=True 时尝试从时间间隔推断，无法推断则报错。
        as_panel : bool, default False
            返回形式同 returns()。

        Returns
        -------
        pandas.DataFrame or HistoryPanel
        """
        if self.is_empty:
            if as_panel:
                return HistoryPanel()
            return pd.DataFrame()
        ret_df = self.returns(price_htype=price_htype, method=method, periods=1, as_panel=False, dropna=False)
        # 滚动标准差：为了在第 window 行即可得到第一个非 NaN 结果，
        # 这里使用 min_periods=1，让 NaN 收益率自然通过跳过逻辑处理。
        vol_df = ret_df.rolling(window=window, min_periods=1).std()

        if annualize:
            if periods_per_year is not None:
                if not isinstance(periods_per_year, (int, float)) or periods_per_year <= 0:
                    raise ValueError(f'periods_per_year must be a positive number, got {periods_per_year}')
                scale = np.sqrt(periods_per_year)
            else:
                # 尝试从 hdates 推断：按平均间隔估算每年 bar 数
                if len(self.hdates) < 2:
                    raise ValueError('cannot infer periods_per_year from fewer than 2 dates; set periods_per_year explicitly')
                try:
                    idx = pd.DatetimeIndex(self.hdates)
                    delta = idx[-1] - idx[0]
                    n_bars = max(1, len(idx) - 1)
                    avg_delta = delta / n_bars
                    days = avg_delta.total_seconds() / 86400.0
                    if days >= 1:
                        scale = np.sqrt(252.0 / days)  # 日频约 252
                    elif days * 5 >= 1:
                        scale = np.sqrt(52.0 / (days * 5))  # 周频约 52
                    else:
                        scale = np.sqrt(252.0 * (1.0 / days))
                except Exception as e:
                    raise ValueError(f'could not infer periods_per_year from hdates: {e}; set periods_per_year explicitly')
            vol_df = vol_df * scale

        if as_panel:
            vol_arr = vol_df.values.T  # (shares, times)
            n_share, n_time = vol_arr.shape
            return HistoryPanel(
                values=vol_arr.reshape(n_share, n_time, 1),
                levels=self.shares,
                rows=list(vol_df.index),
                columns=[f'vol_{window}'],
            )
        return vol_df

    @property
    def kline(self) -> "_HistoryPanelKlineAccessor":
        """K 线技术指标访问器，提供 sma、ema、bbands、macd、kdj 等方法。"""
        return _HistoryPanelKlineAccessor(self)

    def _resolve_price_htype(self, price_htype: str) -> str:
        """解析价格列的实际 htype 名称（支持复权列名自动映射）。

        当面板的价格列使用了复权后缀（例如 ``close|b``），而调用方仍使用默认
        ``price_htype='close'`` 时，本方法会自动选择面板中可用的复权价格列。

        Parameters
        ----------
        price_htype : str
            调用方期望使用的价格类型（例如 ``'close'``、``'high'`` 或带复权后缀的 ``'close|b'``）。

        Returns
        -------
        str
            面板中实际存在的 htype 名称。
        """
        if self.is_empty:
            raise ValueError('HistoryPanel is empty')
        if price_htype in self.htypes:
            return price_htype

        # 仅当用户传入的是无后缀的根价格名时，尝试从复权列中自动映射。
        if '|' not in price_htype:
            root = price_htype
            # 优先顺序：back-adjusted -> forward-adjusted -> 其它同根后缀（稳定选择）
            preferred = [f'{root}|b', f'{root}|f']
            for cand in preferred:
                if cand in self.htypes:
                    return cand

            matching = [h for h in self.htypes if h.startswith(f'{root}|')]
            if matching:
                for cand in preferred:
                    if cand in matching:
                        return cand
                return sorted(matching)[0]

        raise ValueError(f'price_htype "{price_htype}" not found in htypes: {self.htypes}')

    def alpha_beta(
            self,
            benchmark: Union[pd.Series, pd.DataFrame],
            price_htype: str = 'close',
            method: str = 'simple',
            freq: Optional[str] = None,
            annualize: bool = True,
    ) -> pd.DataFrame:
        """计算各股票相对于给定基准收益率序列的 alpha / beta 等指标。

        Parameters
        ----------
        benchmark : Series or DataFrame
            基准价格时间序列，index 应与 HistoryPanel.hdates 对齐或至少有交集。
            DataFrame 时只使用第一列作为基准价格。
        price_htype : str, default 'close'
            用于计算收益率的价格类型。
        method : {'simple', 'log'}, default 'simple'
            收益率计算方式，与 returns() 一致。
        freq : str, optional
            收益率频率字符串，用于 alpha 年化时推断每年 bar 数，如 'D'、'W'、'M'。
        annualize : bool, default True
            是否对 alpha 进行年化。

        Returns
        -------
        pandas.DataFrame
            index 为 shares，列为 ['alpha', 'beta', 'r2', 'n_obs']。
        """
        if self.is_empty:
            return pd.DataFrame(columns=['alpha', 'beta', 'r2', 'n_obs'])

        if not isinstance(benchmark, (pd.Series, pd.DataFrame)):
            raise TypeError('benchmark must be pandas Series or DataFrame')

        if isinstance(benchmark, pd.DataFrame):
            if benchmark.shape[1] == 0:
                raise ValueError('benchmark DataFrame has no columns')
            bench_price = benchmark.iloc[:, 0]
        else:
            bench_price = benchmark

        # 对齐时间索引
        bench_price = bench_price.astype(float)
        stock_ret = self.returns(price_htype=price_htype, method=method, periods=1, as_panel=False, dropna=False)

        # 基准收益率
        bench_ret = bench_price.copy()
        bench_ret.iloc[:] = np.nan
        for i in range(1, len(bench_price)):
            p_prev = bench_price.iloc[i - 1]
            p_curr = bench_price.iloc[i]
            if np.isnan(p_prev) or np.isnan(p_curr) or p_prev <= 0:
                bench_ret.iloc[i] = np.nan
            elif method == 'simple':
                bench_ret.iloc[i] = p_curr / p_prev - 1.0
            else:
                bench_ret.iloc[i] = np.log(p_curr) - np.log(p_prev)

        # 按共同日期对齐
        common_index = stock_ret.index.intersection(bench_ret.index)
        stock_ret = stock_ret.loc[common_index]
        bench_ret = bench_ret.loc[common_index]

        # 每年 bar 数，用于 alpha 年化
        if annualize:
            if freq is not None:
                freq_u = freq.upper()
                if freq_u.startswith('D'):
                    per_year = 252.0
                elif freq_u.startswith('W'):
                    per_year = 52.0
                elif freq_u.startswith('M'):
                    per_year = 12.0
                else:
                    raise ValueError(f'unsupported freq \"{freq}\" for annualization')
            else:
                per_year = 252.0
        else:
            per_year = 1.0

        res = {'alpha': [], 'beta': [], 'r2': [], 'n_obs': []}
        for share in self.shares:
            if share not in stock_ret.columns:
                res['alpha'].append(np.nan)
                res['beta'].append(np.nan)
                res['r2'].append(np.nan)
                res['n_obs'].append(0)
                continue
            y = stock_ret[share]
            x = bench_ret
            mask = (~y.isna()) & (~x.isna())
            xv = x[mask].to_numpy()
            yv = y[mask].to_numpy()
            n = len(xv)
            if n < 2:
                res['alpha'].append(np.nan)
                res['beta'].append(np.nan)
                res['r2'].append(np.nan)
                res['n_obs'].append(n)
                continue

            # 线性回归 y = alpha + beta * x
            beta, alpha = np.polyfit(xv, yv, 1)
            # 拟合优度 R^2
            y_hat = alpha + beta * xv
            ss_res = np.sum((yv - y_hat) ** 2)
            ss_tot = np.sum((yv - np.mean(yv)) ** 2)
            r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan

            res['alpha'].append(alpha * per_year)
            res['beta'].append(beta)
            res['r2'].append(r2)
            res['n_obs'].append(n)

        result = pd.DataFrame(res, index=self.shares)
        return result

    def apply_ta(
            self,
            func_name: str,
            htype: str = 'close',
            shares: Optional[Iterable[str]] = None,
            as_panel: bool = True,
            **kwargs,
    ):
        """调用 qteasy.tafuncs 中的技术指标函数，并在多股票上广播计算。

        Parameters
        ----------
        func_name : str
            qteasy.tafuncs 中的函数名称，如 'sma'、'ema' 等。
        htype : str, default 'close'
            作为输入的一维时间序列的数据类型。
        shares : list of str, optional
            需要计算的股票列表，默认使用全部 shares。
        as_panel : bool, default True
            True 时返回新的 HistoryPanel，在 htypes 末尾追加输出列；
            False 时返回 MultiIndex 列的 DataFrame（时间×[share, output_name]）。
        """
        if self.is_empty:
            return HistoryPanel() if as_panel else pd.DataFrame()
        import qteasy.tafuncs as tafuncs
        if not hasattr(tafuncs, func_name):
            raise ValueError(f'technical indicator function \"{func_name}\" not found in qteasy.tafuncs')
        func = getattr(tafuncs, func_name)

        if htype not in self.htypes:
            raise ValueError(f'htype \"{htype}\" not found in HistoryPanel.htypes: {self.htypes}')

        if shares is None:
            share_list = list(self.shares)
        else:
            if isinstance(shares, str):
                share_list = str_to_list(shares)
            else:
                share_list = list(shares)

        ci = self.htypes.index(htype)
        idx = pd.to_datetime(self.hdates)

        # 收集各 share 的结果
        result_arrays = {}
        out_names = None
        for share in share_list:
            if share not in self.shares:
                raise ValueError(f'share \"{share}\" not found in HistoryPanel.shares')
            li = self.shares.index(share)
            series = pd.Series(self.values[li, :, ci].astype(float), index=idx)
            out = func(series, **kwargs)
            if isinstance(out, (list, tuple)):
                cols = [f'{func_name}_{i}' for i in range(len(out))]
                arrs = [np.asarray(o, dtype=float).ravel() for o in out]
            else:
                cols = [func_name]
                arrs = [np.asarray(out, dtype=float).ravel()]
            if out_names is None:
                out_names = cols
            result_arrays[share] = arrs

        if as_panel:
            # 在原 Panel 后追加新 htypes
            base = self.values.astype(float)
            n_share, n_time, _ = base.shape
            new_cols = list(self.htypes) + list(out_names)
            add_values = np.zeros((n_share, n_time, len(out_names)), dtype=float)
            add_values[:] = np.nan
            for share, arrs in result_arrays.items():
                li = self.shares.index(share)
                for j, arr in enumerate(arrs):
                    L = min(n_time, len(arr))
                    add_values[li, -L:, j] = arr[-L:]
            new_values = np.concatenate([base, add_values], axis=2)
            return HistoryPanel(values=new_values, levels=self.shares, rows=self.hdates, columns=new_cols)

        # 返回 DataFrame：MultiIndex 列 (share, output_name)
        data = {}
        for share, arrs in result_arrays.items():
            for name, arr in zip(out_names, arrs):
                data[(share, name)] = arr
        df = pd.DataFrame(data, index=idx)
        df.columns = pd.MultiIndex.from_tuples(df.columns, names=['share', 'output'])
        return df

    def candle_pattern(
            self,
            name: str,
            price_htypes: tuple[str, str, str, str] = ('open', 'high', 'low', 'close'),
            as_panel: bool = False,
            **kwargs,
    ):
        """基于 ta-lib 形态函数计算蜡烛形态信号。

        Parameters
        ----------
        name : str
            形态函数名称，如 'cdlhammer'。
        price_htypes : tuple of str, default ('open','high','low','close')
            OHLC 对应的 htypes 名称。
        as_panel : bool, default False
            False 返回 DataFrame（时间×股票），True 返回单一 htype 的 HistoryPanel。
        """
        if self.is_empty:
            return HistoryPanel() if as_panel else pd.DataFrame()
        import qteasy.tafuncs as tafuncs
        if not hasattr(tafuncs, name):
            raise ValueError(f'candle pattern function \"{name}\" not found in qteasy.tafuncs')
        func = getattr(tafuncs, name)

        o_name, h_name, l_name, c_name = price_htypes
        for nm in (o_name, h_name, l_name, c_name):
            if nm not in self.htypes:
                raise ValueError(f'price htype \"{nm}\" not found in HistoryPanel.htypes: {self.htypes}')

        oi = self.htypes.index(o_name)
        hi = self.htypes.index(h_name)
        li = self.htypes.index(l_name)
        ci = self.htypes.index(c_name)
        idx = pd.to_datetime(self.hdates)

        signals = np.zeros((self.level_count, self.row_count), dtype=float)
        for s_idx, share in enumerate(self.shares):
            o = pd.Series(self.values[s_idx, :, oi].astype(float), index=idx)
            h = pd.Series(self.values[s_idx, :, hi].astype(float), index=idx)
            l = pd.Series(self.values[s_idx, :, li].astype(float), index=idx)
            c = pd.Series(self.values[s_idx, :, ci].astype(float), index=idx)
            sig = func(o, h, l, c, **kwargs)
            sig_arr = np.asarray(sig, dtype=float).ravel()
            L = min(self.row_count, len(sig_arr))
            signals[s_idx, -L:] = sig_arr[-L:]

        if as_panel:
            return HistoryPanel(values=signals.reshape(self.level_count, self.row_count, 1),
                                levels=self.shares,
                                rows=self.hdates,
                                columns=[name])
        df = pd.DataFrame(signals.T, index=idx, columns=self.shares)
        return df

    def to_df_dict(self, by: str = 'share') -> dict:
        """ 将一个HistoryPanel转化为一个dict，这个dict的keys是HP中的shares，values是每个shares对应的历史数据
            这些数据以DataFrame的格式存储

        Parameters
        ----------
        by: str, {'share', 'shares', 'htype', 'htypes'}, Default: 'share'
            - 'share' 或 'shares': 将HistoryPanel中的数据切成若干片，每一片转化成一个DataFrame，
            它的keys是股票的代码，每个股票代码一个DataFrame
            - 'htype' 或 'htypes': 将HistoryPanel中的数据切成若干片，每一片转化成一个DataFrame，

            它的keys是历史数据类型，每种类型一个DataFrame

        Returns
        -------
        df_dict: dict, {str: pandas.DataFrame}

        Examples
        --------
        >>> hp = HistoryPanel(np.random.randn(2, 3, 4),
        ...                   rows=['2020-01-01', '2020-01-02', '2020-01-03'],
        ...                   levels=['000001', '000002', '000003'],
        ...                   columns=['close', 'open', 'high', 'low'])
        >>> hp
        share 0, label: 000001
                    close,  open,   high,   low
        2020-01-01  0.1,    0.2,    0.3,    0.4
        2020-01-02  0.5,    0.6,    0.7,    0.8
        2020-01-03  0.9,    1.0,    1.1,    1.2
        share 1, label: 000002
                    close,  open,   high,   low
        2020-01-01  1.1,    1.2,    1.3,    1.4
        2020-01-02  1.5,    1.6,    1.7,    1.8
        2020-01-03  1.9,    2.0,    2.1,    2.2
        share 2, label: 000003
                    close,  open,   high,   low
        2020-01-01  2.1,    2.2,    2.3,    2.4
        2020-01-02  2.5,    2.6,    2.7,    2.8
        2020-01-03  2.9,    3.0,    3.1,    3.2

        >>> hp.to_df_dict(by='share')
        {'000001':
                    close,  open,   high,   low
        2020-01-01  0.1,    0.2,    0.3,    0.4
        2020-01-02  0.5,    0.6,    0.7,    0.8
        2020-01-03  0.9,    1.0,    1.1,    1.2
        , '000002':
                    close,  open,   high,   low
        2020-01-01  1.1,    1.2,    1.3,    1.4
        2020-01-02  1.5,    1.6,    1.7,    1.8
        2020-01-03  1.9,    2.0,    2.1,    2.2
        , '000003':
                    close,  open,   high,   low
        2020-01-01  2.1,    2.2,    2.3,    2.4
        2020-01-02  2.5,    2.6,    2.7,    2.8
        2020-01-03  2.9,    3.0,    3.1,    3.2
        }

        >>> hp.to_df_dict(by='htype')
        {'close':
                    000001,  000002,  000003
        2020-01-01  0.1,     1.1,     2.1
        2020-01-02  0.5,     1.5,     2.5
        2020-01-03  0.9,     1.9,     2.9
        , 'open':
                    000001,  000002,  000003
        2020-01-01  0.2,     1.2,     2.2
        2020-01-02  0.6,     1.6,     2.6
        2020-01-03  1.0,     2.0,     3.0
        , 'high':
                    000001,  000002,  000003
        2020-01-01  0.3,     1.3,     2.3
        2020-01-02  0.7,     1.7,     2.7
        2020-01-03  1.1,     2.1,     3.1
        , 'low':
                    000001,  000002,  000003
        2020-01-01  0.4,     1.4,     2.4
        2020-01-02  0.8,     1.8,     2.8
        2020-01-03  1.2,     2.2,     3.2
        }

        """

        if not isinstance(by, str):
            raise TypeError(f'by ({by}) should be a string, and either "shares" or "htypes", got {type(by)}')
        assert by.lower() in ['share', 'shares', 'htype', 'htypes']

        df_dict = {}
        if self.is_empty:
            return df_dict

        if by.lower() in ['share', 'shares']:
            for share in self.shares:
                df_dict[share] = self.slice_to_dataframe(share=share)
            return df_dict

        if by.lower() in ['htype', 'htypes']:
            for htype in self.htypes:
                df_dict[htype] = self.slice_to_dataframe(htype=htype)
            return df_dict

    def unstack(self, by: str = 'share') -> dict:
        """ 等同于方法self.to_df_dict(), 是方法self.to_df_dict()的别称

        Parameters
        ----------
        by: str, {'share', 'htype'}, default 'share'
            指定按照share或者htype来unstack, 默认为share

        Returns
        -------
        dict
            unstack后的结果，是一个字典，key为share或htype，value为对应的DataFrame

        Examples
        --------
        >>> hp = HistoryPanel(np.random.randn(2, 3, 4),
        ...                   rows=['2020-01-01', '2020-01-02', '2020-01-03'],
        ...                   levels=['000001', '000002', '000003'],
        ...                   columns=['close', 'open', 'high', 'low'])
        >>> hp
        share 0, label: 000001
                    close,  open,   high,   low
        2020-01-01  0.1,    0.2,    0.3,    0.4
        2020-01-02  0.5,    0.6,    0.7,    0.8
        2020-01-03  0.9,    1.0,    1.1,    1.2
        share 1, label: 000002
                    close,  open,   high,   low
        2020-01-01  1.1,    1.2,    1.3,    1.4
        2020-01-02  1.5,    1.6,    1.7,    1.8
        2020-01-03  1.9,    2.0,    2.1,    2.2
        share 2, label: 000003
                    close,  open,   high,   low
        2020-01-01  2.1,    2.2,    2.3,    2.4
        2020-01-02  2.5,    2.6,    2.7,    2.8
        2020-01-03  2.9,    3.0,    3.1,    3.2

        >>> hp.unstack(by='share')
        {'000001':
                    close,  open,   high,   low
        2020-01-01  0.1,    0.2,    0.3,    0.4
        2020-01-02  0.5,    0.6,    0.7,    0.8
        2020-01-03  0.9,    1.0,    1.1,    1.2
        , '000002':
                    close,  open,   high,   low
        2020-01-01  1.1,    1.2,    1.3,    1.4
        2020-01-02  1.5,    1.6,    1.7,    1.8
        2020-01-03  1.9,    2.0,    2.1,    2.2
        , '000003':
                    close,  open,   high,   low
        2020-01-01  2.1,    2.2,    2.3,    2.4
        2020-01-02  2.5,    2.6,    2.7,    2.8
        2020-01-03  2.9,    3.0,    3.1,    3.2
        }

        >>> hp.unstack(by='htype')
        {'close':
                    000001,  000002,  000003
        2020-01-01  0.1,     1.1,     2.1
        2020-01-02  0.5,     1.5,     2.5
        2020-01-03  0.9,     1.9,     2.9
        , 'open':
                    000001,  000002,  000003
        2020-01-01  0.2,     1.2,     2.2
        2020-01-02  0.6,     1.6,     2.6
        2020-01-03  1.0,     2.0,     3.0
        , 'high':
                    000001,  000002,  000003
        2020-01-01  0.3,     1.3,     2.3
        2020-01-02  0.7,     1.7,     2.7
        2020-01-03  1.1,     2.1,     3.1
        , 'low':
                    000001,  000002,  000003
        2020-01-01  0.4,     1.4,     2.4
        2020-01-02  0.8,     1.8,     2.8
        2020-01-03  1.2,     2.2,     3.2
        }
        """

        return self.to_df_dict(by=by)

    def flattened_head(self, row_count=5):
        """ 以multi-index DataFrame的形式返回HistoryPanel的最初几行，默认五行

        Parameters
        ----------
        row_count: int, default 5
            打印的行数

        Returns
        -------
        dataframe, multi-indexed by share and htype as columns, with only first row_count rows
        一个dataframe，以share和htype为列的多重索引，只包含前row_count行

        Examples
        --------
        >>> data = np.array([[[12.3, 12.5, 1020010], [12.6, 13.2, 1020020], [12.9, 13.0, 1020030],
        ...                   [12.3, 12.5, 1020040], [12.6, 13.2, 1020050], [12.9, 13.0, 1020060]],
        ...                  [[2.3, 2.5, 20010], [2.6, 2.8, 20020], [2.9, 3.0, 20030],
        ...                   [2.3, 2.5, 20040], [2.6, 2.8, 20050], [2.9, 3.0, 20060]]])
        >>> hp = HistoryPanel(values=data,
        ...                          levels=['000300', '000001'],
        ...                          rows=pd.date_range('2020-01-01', periods=6),
        ...                          columns=['close', 'open', 'vol'])
        >>> hp
        share 0, label: 000300
                    close,  open,   vol
        2020-01-01  12.3,   12.5,   1020010
        2020-01-02  12.6,   13.2,   1020020
        2020-01-03  12.9,   13.0,   1020030
        2020-01-04  12.3,   12.5,   1020040
        2020-01-05  12.6,   13.2,   1020050
        2020-01-06  12.9,   13.0,   1020060
        share 1, label: 000001：
                    close,  open,   vol
        2020-01-01  2.3,    2.5,    20010
        2020-01-02  2.6,    3.2,    20020
        2020-01-03  2.9,    3.0,    20030
        2020-01-04  2.3,    2.5,    20040
        2020-01-05  2.6,    3.2,    20050
        2020-01-06  2.9,    3.0,    20060

        >>> hp.flattened_head(3)
                    000300                  000001
                    close,  open,   vol,    close,  open,   vol
        2020-01-01  12.3,   12.5,   1020010 2.3,    2.5,    20010
        2020-01-02  12.6,   13.2,   1020020 2.6,    3.2,    20020
        2020-01-03  12.9,   13.0,   1020030 2.9,    3.0,    20030
        """
        if row_count <= 0:
            raise ValueError("row_count should be positive")
        if row_count > self.shape[1]:
            row_count = self.shape[1]
        return self.flatten_to_dataframe(along='col').head(row_count)

    def flattened_tail(self, row_count=5):
        """ 以multi-index DataFrame的形式返回HistoryPanel的最后几行，默认五行

        Parameters
        ----------
        row_count: int, default 5
            打印的行数

        Returns
        -------
        dataframe, multi-indexed by share and htype as columns, with only last row_count rows
        一个dataframe，以share和htype为列的多重索引，只包含后row_count行

        Examples
        --------
        >>> data = np.array([[[12.3, 12.5, 1020010], [12.6, 13.2, 1020020], [12.9, 13.0, 1020030],
        ...                   [12.3, 12.5, 1020040], [12.6, 13.2, 1020050], [12.9, 13.0, 1020060]],
        ...                  [[2.3, 2.5, 20010], [2.6, 2.8, 20020], [2.9, 3.0, 20030],
        ...                   [2.3, 2.5, 20040], [2.6, 2.8, 20050], [2.9, 3.0, 20060]]])
        >>> hp = HistoryPanel(values=data,
        ...                          levels=['000300', '000001'],
        ...                          rows=pd.date_range('2020-01-01', periods=6),
        ...                          columns=['close', 'open', 'vol'])
        >>> hp
        share 0, label: 000300
                    close,  open,   vol
        2020-01-01  12.3,   12.5,   1020010
        2020-01-02  12.6,   13.2,   1020020
        2020-01-03  12.9,   13.0,   1020030
        2020-01-04  12.3,   12.5,   1020040
        2020-01-05  12.6,   13.2,   1020050
        2020-01-06  12.9,   13.0,   1020060
        share 1, label: 000001：
                    close,  open,   vol
        2020-01-01  2.3,    2.5,    20010
        2020-01-02  2.6,    3.2,    20020
        2020-01-03  2.9,    3.0,    20030
        2020-01-04  2.3,    2.5,    20040
        2020-01-05  2.6,    3.2,    20050
        2020-01-06  2.9,    3.0,    20060

        >>> hp.flattened_tail(3)
                    000300                  000001
                    close,  open,   vol,    close,  open,   vol
        2020-01-04  12.3,   12.5,   1020040 2.3,    2.5,    20040
        2020-01-05  12.6,   13.2,   1020050 2.6,    3.2,    20050
        2020-01-06  12.9,   13.0,   1020060 2.9,    3.0,    20060
        """
        if row_count <= 0:
            raise ValueError("row_count should be positive")
        if row_count > self.shape[1]:
            row_count = self.shape[1]
        return self.flatten_to_dataframe(along='col').tail(row_count)

    def head(self, row_count=5):
        """返回HistoryPanel的最初几行，默认五行

        Parameters
        ----------
        row_count: int, default 5
            打印的行数

        Returns
        -------
        dataframe, multi-indexed by share and htype as columns, with only first row_count rows
        一个dataframe，以share和htype为列的多重索引，只包含前row_count行

        Examples
        --------
        >>> data = np.array([[[12.3, 12.5, 1020010], [12.6, 13.2, 1020020], [12.9, 13.0, 1020030],
        ...                   [12.3, 12.5, 1020040], [12.6, 13.2, 1020050], [12.9, 13.0, 1020060]],
        ...                  [[2.3, 2.5, 20010], [2.6, 2.8, 20020], [2.9, 3.0, 20030],
        ...                   [2.3, 2.5, 20040], [2.6, 2.8, 20050], [2.9, 3.0, 20060]]])
        >>> hp = HistoryPanel(values=data,
        ...                          levels=['000300', '000001'],
        ...                          rows=pd.date_range('2020-01-01', periods=6),
        ...                          columns=['close', 'open', 'vol'])
        >>> hp
        share 0, label: 000300
                    close,  open,   vol
        2020-01-01  12.3,   12.5,   1020010
        2020-01-02  12.6,   13.2,   1020020
        2020-01-03  12.9,   13.0,   1020030
        2020-01-04  12.3,   12.5,   1020040
        2020-01-05  12.6,   13.2,   1020050
        2020-01-06  12.9,   13.0,   1020060
        share 1, label: 000001：
                    close,  open,   vol
        2020-01-01  2.3,    2.5,    20010
        2020-01-02  2.6,    3.2,    20020
        2020-01-03  2.9,    3.0,    20030
        2020-01-04  2.3,    2.5,    20040
        2020-01-05  2.6,    3.2,    20050
        2020-01-06  2.9,    3.0,    20060

        >>> hp.head(3)
        share 0, label: 000300
                    close,  open,   vol,
        2020-01-01  12.3,   12.5,   1020010
        2020-01-02  12.6,   13.2,   1020020
        2020-01-03  12.9,   13.0,   1020030
        share 1, label: 000001
                    close,  open,   vol
        2020-01-01  2.3,    2.5,    20010
        2020-01-02  2.6,    3.2,    20020
        2020-01-03  2.9,    3.0,    20030
        """
        if row_count <= 0:
            raise ValueError("row_count should be positive")
        if row_count > self.shape[1]:
            row_count = self.shape[1]
        return self.isegment(0, row_count)

    def tail(self, row_count=5):
        """返回HistoryPanel的最末几行，默认五行

        Parameters
        ----------
        row_count: int, default 5
            打印的行数

        Returns
        -------
        dataframe, multi-indexed by share and htype as columns, with only last row_count rows
        一个dataframe，以share和htype为列的多重索引，只包含最后row_count行

        Examples
        --------
        >>> data = np.array([[[12.3, 12.5, 1020010], [12.6, 13.2, 1020020], [12.9, 13.0, 1020030],
        ...                   [12.3, 12.5, 1020040], [12.6, 13.2, 1020050], [12.9, 13.0, 1020060]],
        ...                  [[2.3, 2.5, 20010], [2.6, 2.8, 20020], [2.9, 3.0, 20030],
        ...                   [2.3, 2.5, 20040], [2.6, 2.8, 20050], [2.9, 3.0, 20060]]])
        >>> hp = HistoryPanel(values=data,
        ...                          levels=['000300', '000001'],
        ...                          rows=pd.date_range('2020-01-01', periods=6),
        ...                          columns=['close', 'open', 'vol'])
        >>> hp
        share 0, label: 000300
                    close,  open,   vol
        2020-01-01  12.3,   12.5,   1020010
        2020-01-02  12.6,   13.2,   1020020
        2020-01-03  12.9,   13.0,   1020030
        2020-01-04  12.3,   12.5,   1020040
        2020-01-05  12.6,   13.2,   1020050
        2020-01-06  12.9,   13.0,   1020060
        share 1, label: 000001：
                    close,  open,   vol
        2020-01-01  2.3,    2.5,    20010
        2020-01-02  2.6,    3.2,    20020
        2020-01-03  2.9,    3.0,    20030
        2020-01-04  2.3,    2.5,    20040
        2020-01-05  2.6,    3.2,    20050
        2020-01-06  2.9,    3.0,    20060

        >>> hp.tail(3)
        share 0, label: 000300
                    close,  open,   vol
        2020-01-04  12.3,   12.5,   1020040
        2020-01-05  12.6,   13.2,   1020050
        2020-01-06  12.9,   13.0,   1020060
        share 1, label: 000001：
                    close,  open,   vol
        2020-01-04  2.3,    2.5,    20040
        2020-01-05  2.6,    3.2,    20050
        2020-01-06  2.9,    3.0,    20060
        """
        if row_count <= 0:
            raise ValueError("row_count should be positive")
        if row_count > self.shape[1]:
            row_count = self.shape[1]
        return self.isegment(- row_count, None)

    def research_preset(self, name: str, *, inplace: bool = False) -> 'HistoryPanel':
        """按预设快速生成研究常用列集合，并返回结果面板。

        该方法旨在作为 ``HistoryPanel`` 的“第一入口”：在不引入回测语义的前提下，
        快速拼出 OHLCV + 常用技术指标列（如 MACD、均线）以便直接绘图或继续做研究。

        Parameters
        ----------
        name : str
            预设名称。目前支持：

            - ``'ohlcv_macd_ma'``：要求面板至少包含 ``open/high/low/close/vol``，并生成
              ``macd_12_26_9``、``macd_signal_12_26_9``、``macd_hist_12_26_9`` 与 ``sma_20``。
        inplace : bool, default False
            为 True 时在原面板上原地追加预设列并返回原面板；为 False 时返回新增列后的新面板。

        Returns
        -------
        HistoryPanel
            追加预设列后的 ``HistoryPanel``。当 ``inplace=True`` 时返回原对象。

        Raises
        ------
        ValueError
            当预设名称非法，或缺少预设所需的输入列时抛出（错误信息为英文）。
        """
        presets = {
            'ohlcv_macd_ma': {
                'required': ['open', 'high', 'low', 'close', 'vol'],
                'builder': self._research_preset_ohlcv_macd_ma,
            },
        }
        if not isinstance(name, str) or not name:
            raise ValueError('name must be a non-empty string')
        if name not in presets:
            available = ', '.join(sorted(presets.keys()))
            raise ValueError(f'Unknown research preset "{name}". Available presets: {available}')
        required = presets[name]['required']
        missing = [c for c in required if c not in self.htypes]
        if missing:
            required_str = ', '.join(required)
            missing_str = ', '.join(missing)
            raise ValueError(
                f'Research preset "{name}" requires htypes: {required_str}. '
                f'Missing: {missing_str}. '
                'Please load data with required htypes or add them via bracket assignment.'
            )
        hp = self if inplace else HistoryPanel(
            values=np.array(self.values, copy=True),
            levels=list(self.shares),
            rows=list(self.hdates),
            columns=list(self.htypes),
        )
        return presets[name]['builder'](hp)

    @staticmethod
    def _research_preset_ohlcv_macd_ma(hp: 'HistoryPanel') -> 'HistoryPanel':
        """构建 ``ohlcv_macd_ma`` 预设（内部使用）。"""
        # 只使用公开 API：kline 指标统一走 kline accessor，并使用 inplace=True 扩列
        hp.kline.macd(inplace=True)
        hp.kline.sma(window=20, price_htype='close', inplace=True)
        return hp

    def plot(
        self,
        shares: Optional[Union[str, Iterable[str]]] = None,
        layout: str = 'auto',
        interactive: bool = False,
        highlight: Optional[Any] = None,
        plotly_backend_app: str = 'auto',
        group_titles: Optional[Sequence[str]] = None,
        max_shares_per_figure: int = 5,
        page: int = 1,
        **kwargs,
    ):
        """根据 HistoryPanel 中已有的 htypes 与 shares 自动选择图表类型并绘制图表。

        本方法只消费已有数据不做新增计算，图表类型由内部注册表基于 htypes 决定（如
        OHLC→K 线，vol→成交量，MACD 三列→MACD 图，其余→折线），支持单标的与多标
        的 overlay/stack 布局，以及基于 matplotlib 的静态图和基于 Plotly 的交互式图表。

        Parameters
        ----------
        shares : str or sequence of str, optional
            要参与绘图的标的子集；默认使用 HistoryPanel 的全部 shares。
        layout : {'overlay', 'stack', 'auto'}, default 'auto'
            多标的布局方式；'overlay' 为同组叠加，'stack' 为多组分行展示，'auto' 时
            ``HP_OVERLAY_GROUP_SHARE_COUNT`` 只标的用 overlay，其余用 stack。
        interactive : bool, default False
            为 True 时使用 Plotly 交互后端（需安装 plotly 及 anywidget/ipywidgets）；
            为 False 时使用 matplotlib 静态后端。
        highlight : dict or str, optional
            高亮配置，可为 ``{'condition': 'max'|'min' 或布尔数组, 'style': {...}}``，
            或简写为 'max' / 'min'。
        plotly_backend_app : {'auto', 'FigureWidget', 'html'}, default 'auto'
            仅当 ``interactive=True`` 时有效。在 Notebook 中选择 Plotly 呈现方式：
            ``'auto'`` 优先 ``FigureWidget``，失败则回退 HTML 包装；``'FigureWidget'`` 强制
            Widget，失败抛错；``'html'`` 强制 HTML 包装，失败抛错。非 Notebook 脚本环境下
            ``'auto'`` 仍可能返回原始 ``Figure``。
        max_shares_per_figure : int, default 5
            单张图中最多展示的 share 数量。当请求 shares 数量超过该值时，会按页分割；
            可通过 ``page`` 参数选择要展示的页码。
        page : int, default 1
            要展示的页码（1-based）。当 shares 数量超过 ``max_shares_per_figure`` 时，
            ``page=1`` 为第 1 页，``page=2`` 为第 2 页，以此类推。
        **kwargs
            预留的扩展参数，当前版本中不使用。

        Returns
        -------
        matplotlib.figure.Figure or plotly.graph_objs.FigureWidget or _PlotlyFigureWrapper
            interactive=False 时返回 matplotlib Figure；
            interactive=True 时依 ``plotly_backend_app`` 返回 FigureWidget、HTML 包装器或原始 Figure。

        Notes
        -----
        当注册表产出 **完整 OHLC K 线** 主图时，会显示顶部 OHLC 摘要区：静态图固定为时间轴上
        **最后一根** bar 的摘要；交互图初始与之一致，点击某 bar 后更新为该 bar（面向用户的
        摘要文案为英文）。无 K 线主图（例如仅 close 折线）时不显示该摘要区。

        Examples
        --------
        >>> import qteasy as qt
        >>> hp = qt.get_history_data(htype_names='open, high, low, close, vol',
        ...                          shares='000300.SH', rows=200)
        >>> fig = hp.plot()

        >>> fig_interactive = hp.plot(interactive=True, highlight='max')

        See Also
        --------
        qt.get_kline
            获取 K 线数据并可选 ``as_panel=True`` 得到 HistoryPanel。
        """
        if self.is_empty:
            raise ValueError('Cannot plot an empty HistoryPanel')
        if not interactive and plotly_backend_app != 'auto':
            raise ValueError(
                "plotly_backend_app is only supported when interactive=True."
            )
        from qteasy.hp_visual_spec import (
            get_chart_type_registry,
            build_kline_spec,
            build_volume_spec,
            build_macd_spec,
            build_line_spec,
        )
        from qteasy.hp_visual_render import build_figure_from_specs
        share_list = list(self.shares) if shares is None else (
            [shares] if isinstance(shares, str) else list(shares)
        )
        share_list = [s for s in share_list if s in self.shares]
        if not share_list:
            share_list = list(self.shares)
        if not isinstance(max_shares_per_figure, int) or max_shares_per_figure <= 0:
            raise ValueError('max_shares_per_figure must be a positive int')
        if not isinstance(page, int) or page <= 0:
            raise ValueError('page must be a positive int (1-based)')
        total = len(share_list)
        total_pages = int(np.ceil(total / float(max_shares_per_figure))) if total > 0 else 1
        if page > total_pages:
            raise ValueError(
                f'page {page} is out of range (total_pages={total_pages}, '
                f'max_shares_per_figure={max_shares_per_figure}, total_shares={total})'
            )
        if total > max_shares_per_figure:
            try:
                from qteasy import logger_core
                logger_core.warning(
                    f'HistoryPanel.plot: {total} shares requested, '
                    f'displaying page {page}/{total_pages} with max_shares_per_figure={max_shares_per_figure}.'
                )
            except Exception:
                import warnings
                warnings.warn(
                    f'HistoryPanel.plot: {total} shares requested, '
                    f'displaying page {page}/{total_pages} with max_shares_per_figure={max_shares_per_figure}.',
                    UserWarning,
                    stacklevel=2,
                )
        start = (page - 1) * max_shares_per_figure
        end = start + max_shares_per_figure
        share_list = share_list[start:end]
        registry = get_chart_type_registry()
        types_info = registry.get_applicable_types(self.htypes)
        if not types_info:
            from qteasy.hp_visual_render import _HAS_MPL
            if _HAS_MPL:
                import matplotlib.pyplot as plt
                fig, _ = plt.subplots(1, 1, figsize=(8, 4))
                return fig
            raise RuntimeError('No applicable chart types and matplotlib not available')
        n_share = len(share_list)
        if layout == 'auto':
            layout = 'overlay' if n_share == HP_OVERLAY_GROUP_SHARE_COUNT else 'stack'
        if n_share == 1:
            groups = [share_list]
        elif layout == 'overlay' and n_share == HP_OVERLAY_GROUP_SHARE_COUNT:
            groups = [share_list]
        else:
            groups = [[s] for s in share_list]
        x_dates = list(self.hdates)
        specs_per_group = []

        def _infer_freq_info_from_hdates() -> str:
            """从 hdates 推断频率说明（中文），用于图表标题。"""
            try:
                idx = pd.DatetimeIndex(self.hdates)
                if len(idx) >= 3:
                    f = pd.infer_freq(idx)
                else:
                    f = None
            except Exception:
                f = None
            if not f:
                # 交易日序列在节假日处可能不规则，infer_freq() 常返回 None。
                # 为保证标题稳定，这里用相邻时间间隔的中位数做鲁棒推断。
                try:
                    if len(idx) < 2:
                        return 'K线'
                    deltas = (idx[1:] - idx[:-1]).total_seconds()
                    deltas = np.array([d for d in deltas if d and d > 0], dtype=float)
                    if deltas.size == 0:
                        return 'K线'
                    med_sec = float(np.median(deltas))
                    day = 86400.0
                    if med_sec >= 0.75 * day and med_sec <= 1.5 * day:
                        return '日K'
                    if med_sec >= 6.0 * day and med_sec <= 9.0 * day:
                        return '周K'
                    if med_sec >= 25.0 * day and med_sec <= 35.0 * day:
                        return '月K'
                    if med_sec >= 70.0 * day and med_sec <= 100.0 * day:
                        return '季K'
                    if med_sec >= 300.0 * day:
                        return '年K'
                    # 子日频：小时 / 分钟
                    if med_sec <= 2.0 * 3600.0 and med_sec >= 0.5 * 3600.0:
                        return '小时K'
                    mins = int(round(med_sec / 60.0))
                    if mins > 0:
                        return f'{mins}分钟K'
                except Exception:
                    pass
                return 'K线'
            fu = str(f).upper()
            if fu.startswith('B') or fu.startswith('D'):
                return '日K'
            if fu.startswith('W'):
                return '周K'
            if fu.startswith('M'):
                return '月K'
            if fu.startswith('Q'):
                return '季K'
            if fu.startswith('Y') or fu.startswith('A'):
                return '年K'
            if 'H' == fu or fu.endswith('H'):
                return '小时K'
            if fu.endswith('MIN') or fu.endswith('T'):
                # pandas 可能返回 30T/15T 等
                num = ''.join(ch for ch in fu if ch.isdigit())
                return f'{num}分钟K' if num else '分钟K'
            return 'K线'

        def _infer_adj_info_from_htypes() -> str:
            """从 htypes 推断复权信息（中文）。"""
            hset = set(self.htypes)
            roots = ('open', 'high', 'low', 'close')
            if any(f'{r}|b' in hset for r in roots):
                return '后复权'
            if any(f'{r}|f' in hset for r in roots):
                return '前复权'
            return '未复权'

        freq_info = _infer_freq_info_from_hdates()
        adj_info = _infer_adj_info_from_htypes()

        names_by_symbol: Dict[str, str] = {}
        try:
            from qteasy.trading_util import get_symbol_names
            # get_symbol_names 内部会在 datasource=None 时自动使用 QT_DATA_SOURCE
            names = get_symbol_names(datasource=None, symbols=share_list)
            if isinstance(names, list) and len(names) == len(share_list):
                for s, n in zip(share_list, names):
                    if n and n != 'N/A':
                        names_by_symbol[str(s)] = str(n)
        except Exception:
            names_by_symbol = {}

        def _format_group_title(grp: Sequence[str]) -> str:
            """格式化组标题：CODE [NAME] FREQ - ADJ（NAME 不可用时省略）。"""
            if not grp:
                return ''
            # 与旧逻辑兼容：标题里 share 列表最多展示前三个
            shown = list(grp[:3])
            shown_text = ','.join(shown) if len(grp) > 1 else shown[0]
            shown_names = [names_by_symbol.get(s, '') for s in shown]
            shown_names = [n for n in shown_names if n]
            name_part = f" [{','.join(shown_names)}]" if shown_names else ''
            return f'{shown_text}{name_part} {freq_info} - {adj_info}'.strip()

        # 若调用方显式传入 group_titles，则优先使用；否则按 shares 组装默认标题
        auto_group_titles: List[str] = []
        if group_titles is None:
            for grp in groups:
                auto_group_titles.append(_format_group_title(grp))
        else:
            auto_group_titles = list(group_titles)
        for grp in groups:
            row = []
            for info in types_info:
                tid = info.id
                if tid == 'kline':
                    spec = build_kline_spec(self, shares=grp)
                elif tid == 'volume':
                    spec = build_volume_spec(self, shares=grp)
                elif tid == 'macd':
                    spec = build_macd_spec(self, shares=grp)
                elif tid == 'line':
                    spec = build_line_spec(self, shares=grp)
                else:
                    spec = None
                if spec is not None and highlight is not None:
                    spec = dict(spec)
                    spec['highlight'] = (
                        highlight if isinstance(highlight, dict) else {'condition': highlight}
                    )
                row.append(spec)
            kline_idx = next((i for i, t in enumerate(types_info) if t.id == 'kline'), None)
            vol_idx = next((i for i, t in enumerate(types_info) if t.id == 'volume'), None)
            if (
                kline_idx is not None and vol_idx is not None
                and row[kline_idx] is not None and row[vol_idx] is not None
                and 'open' in row[kline_idx].get('data', {}) and 'close' in row[kline_idx].get('data', {})
            ):
                vol_spec = dict(row[vol_idx])
                vol_spec['data'] = dict(vol_spec.get('data', {}))
                vol_spec['data']['open'] = row[kline_idx]['data']['open']
                vol_spec['data']['close'] = row[kline_idx]['data']['close']
                row[vol_idx] = vol_spec
            specs_per_group.append(row)
        if interactive:
            from qteasy.hp_visual_plotly import (
                _HAS_PLOTLY,
                _normalize_plotly_backend_app,
                build_interactive_figure_from_specs,
                _select_plotly_notebook_output,
            )
            if not _HAS_PLOTLY:
                raise RuntimeError(
                    'interactive=True requires plotly. Install with: pip install plotly'
                )
            _normalize_plotly_backend_app(plotly_backend_app)
            fig = build_interactive_figure_from_specs(
                specs_per_group,
                types_info,
                x_dates=x_dates,
                group_titles=auto_group_titles,
            )
            return _select_plotly_notebook_output(fig, plotly_backend_app)
        fig = build_figure_from_specs(
            specs_per_group,
            types_info,
            x_dates=x_dates,
            group_titles=auto_group_titles,
        )
        return fig

    # 以下 legacy 方法仅保留占位，统一通过 HistoryPanel.plot() 实现可视化
    def candle(self, *args, **kwargs):
        """基于当前 ``HistoryPanel`` 数据绘制蜡烛图（已由 ``plot()`` 统一处理）

        Notes
        -----
        - 新版可视化推荐直接调用 ``HistoryPanel.plot()``，并通过 htypes / layout
          控制是否输出 K 线、成交量等图表类型。
        - 本方法在内部会委托给可视化子模块的统一入口实现，行为与 ``plot()`` 保持
          一致，仅作为语义化别名存在。
        """
        raise NotImplementedError


class _HistoryPanelKlineAccessor:
    """HistoryPanel 的 K 线/技术指标访问器（内部使用）。

    该访问器通过 ``HistoryPanel.kline`` 属性暴露，封装了对 ``HistoryPanel`` 中价格序列
    的常用技术指标计算（如均线、布林带、MACD、KDJ 等）。所有指标计算均遵循以下约定：

    - **输入**：从原始 ``HistoryPanel`` 的某个 ``htype``（如 ``close``）读取价格序列；
    - **输出**：返回一个新的 ``HistoryPanel``，其 values 为原面板 values 与新增指标列
      在第三轴（htypes 轴）上拼接后的结果；
    - **标签保持**：shares 与 hdates 标签保持不变；新增列名由参数或默认规则生成；
    - **不修改原对象**：不会原地修改传入的 ``HistoryPanel``。

    Notes
    -----
    - 本类为内部工具类，主要服务于可视化与策略研究中的快速派生数据生成。
    - 指标函数内部依赖 ``qteasy.tafuncs``（对 TA-Lib 风格函数做了封装/适配）。
    """

    def __init__(self, hp: HistoryPanel):
        """创建一个绑定到指定 ``HistoryPanel`` 的 K 线访问器。

        Parameters
        ----------
        hp : HistoryPanel
            需要进行技术指标派生计算的历史数据容器。

        Returns
        -------
        None
            该方法不返回值，仅在内部保存 ``hp`` 引用。
        """
        self._hp = hp

    def _get_price(self, price_htype: str):
        """从 ``HistoryPanel`` 读取指定 ``htype`` 的二维价格矩阵。

        Parameters
        ----------
        price_htype : str
            价格数据对应的 ``htype`` 名称，典型值为 ``'close'``、``'open'``、``'high'``、
            ``'low'`` 等，必须存在于 ``self._hp.htypes`` 中。

        Returns
        -------
        numpy.ndarray
            二维矩阵，形状为 ``(n_share, n_time)``，dtype 为 float。

        Raises
        ------
        ValueError
            当 ``HistoryPanel`` 为空或 ``price_htype`` 不存在于 ``htypes`` 中时抛出。
        """
        resolved_htype = self._hp._resolve_price_htype(price_htype)
        ci = self._hp.htypes.index(resolved_htype)
        return self._hp.values[:, :, ci].astype(float)

    def _append_htypes(self, new_columns: list, new_arrays: list) -> HistoryPanel:
        """将派生出的指标列追加到原 ``HistoryPanel`` 的 htypes 轴上并返回新面板。

        Parameters
        ----------
        new_columns : list of str
            新增列名列表（对应新增的 htypes）。
        new_arrays : list of numpy.ndarray
            新增列数据列表。列表长度应与 ``new_columns`` 一致；每个数组形状必须为
            ``(n_share, n_time)``。

        Returns
        -------
        HistoryPanel
            追加指标列后的新 ``HistoryPanel``。当原面板为空时返回空面板。

        Notes
        -----
        - 本方法是内部通用拼接工具，不对列名冲突做额外处理（由调用方负责检查）。
        """
        hp = self._hp
        if hp.is_empty:
            return HistoryPanel()
        base = hp.values.astype(float)
        to_add = np.stack(new_arrays, axis=2)  # (L, R, C_new)
        new_values = np.concatenate([base, to_add], axis=2)
        new_htypes = list(hp.htypes) + list(new_columns)
        return HistoryPanel(values=new_values, levels=hp.shares, rows=hp.hdates, columns=new_htypes)

    def _inplace_append_htypes(self, new_columns: list, new_arrays: list) -> HistoryPanel:
        """将派生列原地追加到绑定的 ``HistoryPanel`` 并返回该面板。

        Parameters
        ----------
        new_columns : list of str
            新增列名列表（对应新增的 htypes）。
        new_arrays : list of numpy.ndarray
            新增列数据列表。列表长度应与 ``new_columns`` 一致；每个数组形状必须为
            ``(n_share, n_time)``。

        Returns
        -------
        HistoryPanel
            原地追加后的同一个 ``HistoryPanel`` 对象。

        Raises
        ------
        ValueError
            当绑定面板为空，或新增列名与现有 ``htypes`` 冲突时抛出。

        Notes
        -----
        - 本方法用于实现 ``kline`` 的 ``inplace=True`` 语义：复用 ``HistoryPanel.__setitem__``
          的扩列逻辑，避免维护第二套拼接路径。
        - 原地追加会改变 ``self._hp`` 的 ``values`` 与 ``htypes``，请在文档中明确。
        """
        hp = self._hp
        if hp.is_empty:
            raise ValueError('Cannot apply kline indicator on an empty HistoryPanel')
        for name in new_columns:
            if name in hp.htypes:
                raise ValueError(f'htype "{name}" already exists')
        for name, arr in zip(new_columns, new_arrays):
            hp[name] = arr
        return hp

    def sma(
            self,
            window: int = 20,
            price_htype: str = 'close',
            new_htype: Optional[str] = None,
            *,
            inplace: bool = False,
    ) -> HistoryPanel:
        """计算简单移动平均（SMA）并以新 ``htype`` 追加到面板中。

        Parameters
        ----------
        window : int, default 20
            滚动窗口长度（周期数）。
        price_htype : str, default 'close'
            用于计算均线的价格 ``htype`` 名称。
        new_htype : str, optional
            新增均线列名；为 None 时使用默认列名 ``'sma_{window}'``。

        inplace : bool, default False
            为 True 时在原面板上原地追加均线列并返回原面板；为 False 时返回追加列后的新面板。

        Returns
        -------
        HistoryPanel
            ``inplace=False`` 时返回追加均线列后的新 ``HistoryPanel``；``inplace=True`` 时返回原面板。

        Raises
        ------
        ValueError
            当 ``price_htype`` 不存在，或 ``new_htype`` 已存在于原面板 ``htypes`` 中时抛出。

        Examples
        --------
        >>> hp = qt.get_history_data(htype_names='open,high,low,close', shares='000001.SZ', rows=60, as_data_frame=False)
        >>> hp2 = hp.kline.sma(window=20, price_htype='close')
        >>> hp2
        share 0, label: 000001
                    close,  open,   sma_20
        2020-01-01  10.0,   9.5,    NaN
        2020-01-02  10.5,   10.0,   NaN
        2020-01-03  10.8,   10.5,   NaN
        ...
        2020-02-19  11.2,   10.8,   10.75
        2020-02-20  11.5,   11.2,   10.85
        2020-02-21  11.8,   11.5,   10.95
        """
        from qteasy import tafuncs
        default_name = f'sma_{window}'
        if new_htype is None:
            new_htype = default_name
        if self._hp.is_empty:
            raise ValueError('Cannot apply SMA on an empty HistoryPanel')
        if new_htype in self._hp.htypes:
            raise ValueError(f'new_htype "{new_htype}" already exists in htypes')
        prices = self._get_price(price_htype)
        n_share, n_time = prices.shape
        out = np.full_like(prices, np.nan, dtype=float)
        for i in range(n_share):
            out[i, :] = tafuncs.sma(prices[i, :], timeperiod=window)
        if inplace:
            return self._inplace_append_htypes([new_htype], [out])
        return self._append_htypes([new_htype], [out])

    def ema(
            self,
            span: int = 20,
            price_htype: str = 'close',
            new_htype: Optional[str] = None,
            *,
            inplace: bool = False,
    ) -> HistoryPanel:
        """计算指数移动平均（EMA）并以新 ``htype`` 追加到面板中。

        Parameters
        ----------
        span : int, default 20
            指数平滑跨度（周期数）。
        price_htype : str, default 'close'
            用于计算 EMA 的价格 ``htype`` 名称。
        new_htype : str, optional
            新增 EMA 列名；为 None 时使用默认列名 ``'ema_{span}'``。

        inplace : bool, default False
            为 True 时在原面板上原地追加 EMA 列并返回原面板；为 False 时返回追加列后的新面板。

        Returns
        -------
        HistoryPanel
            ``inplace=False`` 时返回追加 EMA 列后的新 ``HistoryPanel``；``inplace=True`` 时返回原面板。

        Raises
        ------
        ValueError
            当 ``price_htype`` 不存在，或 ``new_htype`` 已存在于原面板 ``htypes`` 中时抛出。
        """
        from qteasy import tafuncs
        default_name = f'ema_{span}'
        if new_htype is None:
            new_htype = default_name
        if self._hp.is_empty:
            raise ValueError('Cannot apply EMA on an empty HistoryPanel')
        if new_htype in self._hp.htypes:
            raise ValueError(f'new_htype "{new_htype}" already exists in htypes')
        prices = self._get_price(price_htype)
        n_share, n_time = prices.shape
        out = np.full_like(prices, np.nan, dtype=float)
        for i in range(n_share):
            res = tafuncs.ema(prices[i, :], span=span)
            arr = np.atleast_1d(np.asarray(res, dtype=float)).ravel()
            out[i, :min(n_time, len(arr))] = arr[:n_time]
        if inplace:
            return self._inplace_append_htypes([new_htype], [out])
        return self._append_htypes([new_htype], [out])

    def bbands(
            self,
            window: int = 20,
            price_htype: str = 'close',
            nbdev_up: float = 2.0,
            nbdev_dn: float = 2.0,
            ma_type: str = 'sma',
            suffix: Optional[str] = None,
            *,
            inplace: bool = False,
    ) -> HistoryPanel:
        """计算布林带（Bollinger Bands）并追加上轨/中轨/下轨三列。

        Parameters
        ----------
        window : int, default 20
            滚动窗口长度。
        price_htype : str, default 'close'
            用于计算布林带的价格 ``htype`` 名称。
        nbdev_up : float, default 2.0
            上轨标准差倍数。
        nbdev_dn : float, default 2.0
            下轨标准差倍数。
        ma_type : {'sma', 'ema'}, default 'sma'
            中轨移动平均类型。当前实现会映射为底层 ``tafuncs`` 的 ``matype`` 参数。
        suffix : str, optional
            列名后缀；为 None 时使用默认规则 ``'{window}_{int(nbdev_up)}_{int(nbdev_dn)}'``。

        inplace : bool, default False
            为 True 时在原面板上原地追加三条布林带曲线并返回原面板；为 False 时返回新面板。

        Returns
        -------
        HistoryPanel
            追加三列后的新 ``HistoryPanel``，新增列名分别为
            ``bbands_upper_{tag}``、``bbands_middle_{tag}``、``bbands_lower_{tag}``。

        Raises
        ------
        ValueError
            当新增列名与现有 ``htypes`` 冲突时抛出。
        """
        from qteasy import tafuncs
        tag = suffix if suffix is not None else f'{window}_{int(nbdev_up)}_{int(nbdev_dn)}'
        upper_name = f'bbands_upper_{tag}'
        middle_name = f'bbands_middle_{tag}'
        lower_name = f'bbands_lower_{tag}'
        for n in (upper_name, middle_name, lower_name):
            if n in self._hp.htypes:
                raise ValueError(f'htype "{n}" already exists')
        prices = self._get_price(price_htype)
        n_share, n_time = prices.shape
        matype = 0 if ma_type == 'sma' else 1  # tafuncs 使用 matype 整数
        u = np.full_like(prices, np.nan, dtype=float)
        m = np.full_like(prices, np.nan, dtype=float)
        l = np.full_like(prices, np.nan, dtype=float)
        for i in range(n_share):
            uu, mm, ll = tafuncs.bbands(
                prices[i, :], timeperiod=window,
                nbdevup=int(nbdev_up), nbdevdn=int(nbdev_dn), matype=matype,
            )
            uu = np.asarray(uu).ravel()
            mm = np.asarray(mm).ravel()
            ll = np.asarray(ll).ravel()
            L = min(n_time, len(uu), len(mm), len(ll))
            u[i, -L:] = uu[-L:]
            m[i, -L:] = mm[-L:]
            l[i, -L:] = ll[-L:]
        if inplace:
            return self._inplace_append_htypes([upper_name, middle_name, lower_name], [u, m, l])
        return self._append_htypes([upper_name, middle_name, lower_name], [u, m, l])

    def macd(
            self,
            price_htype: str = 'close',
            fastperiod: int = 12,
            slowperiod: int = 26,
            signalperiod: int = 9,
            suffix: Optional[str] = None,
            *,
            inplace: bool = False,
    ) -> HistoryPanel:
        """计算 MACD 指标并追加 DIF/DEA/HIST 三列。

        Parameters
        ----------
        price_htype : str, default 'close'
            用于计算 MACD 的价格 ``htype`` 名称。
        fastperiod : int, default 12
            快线周期。
        slowperiod : int, default 26
            慢线周期。
        signalperiod : int, default 9
            信号线周期。
        suffix : str, optional
            列名后缀；为 None 时使用默认规则 ``'{fastperiod}_{slowperiod}_{signalperiod}'``。

        inplace : bool, default False
            为 True 时在原面板上原地追加 MACD 三列并返回原面板；为 False 时返回新面板。

        Returns
        -------
        HistoryPanel
            追加三列后的新 ``HistoryPanel``，新增列名分别为
            ``macd_{tag}``、``macd_signal_{tag}``、``macd_hist_{tag}``。

        Raises
        ------
        ValueError
            当新增列名与现有 ``htypes`` 冲突时抛出。
        """
        from qteasy import tafuncs
        tag = suffix if suffix is not None else f'{fastperiod}_{slowperiod}_{signalperiod}'
        n1, n2, n3 = f'macd_{tag}', f'macd_signal_{tag}', f'macd_hist_{tag}'
        for n in (n1, n2, n3):
            if n in self._hp.htypes:
                raise ValueError(f'htype "{n}" already exists')
        prices = self._get_price(price_htype)
        n_share, n_time = prices.shape
        macd_arr = np.full_like(prices, np.nan, dtype=float)
        sig_arr = np.full_like(prices, np.nan, dtype=float)
        hist_arr = np.full_like(prices, np.nan, dtype=float)
        for i in range(n_share):
            mc, sig, hist = tafuncs.macd(prices[i, :], fastperiod=fastperiod, slowperiod=slowperiod, signalperiod=signalperiod)
            mc, sig, hist = np.asarray(mc).ravel(), np.asarray(sig).ravel(), np.asarray(hist).ravel()
            L = min(n_time, len(mc), len(sig), len(hist))
            macd_arr[i, -L:] = mc[-L:]
            sig_arr[i, -L:] = sig[-L:]
            hist_arr[i, -L:] = hist[-L:]
        if inplace:
            return self._inplace_append_htypes([n1, n2, n3], [macd_arr, sig_arr, hist_arr])
        return self._append_htypes([n1, n2, n3], [macd_arr, sig_arr, hist_arr])

    def kdj(
            self,
            price_htype: str = 'close',
            fastk_period: int = 9,
            slowk_period: int = 3,
            slowd_period: int = 3,
            suffix: Optional[str] = None,
            *,
            inplace: bool = False,
    ) -> HistoryPanel:
        """计算 KDJ 随机指标并追加 K/D/J 三列。

        该指标依赖 ``high``、``low``、``close`` 三个价格序列，因此要求它们存在于
        原面板 ``htypes`` 中。

        Parameters
        ----------
        price_htype : str, default 'close'
            预留参数，保持接口风格一致；KDJ 实际会固定使用 ``high/low/close`` 三列。
        fastk_period : int, default 9
            RSV 计算窗口长度。
        slowk_period : int, default 3
            K 线平滑窗口长度。
        slowd_period : int, default 3
            D 线平滑窗口长度。
        suffix : str, optional
            列名后缀；为 None 时使用默认规则 ``'{fastk_period}_{slowk_period}_{slowd_period}'``。

        inplace : bool, default False
            为 True 时在原面板上原地追加 K/D/J 三列并返回原面板；为 False 时返回新面板。

        Returns
        -------
        HistoryPanel
            追加三列后的新 ``HistoryPanel``，新增列名分别为
            ``kdj_k_{tag}``、``kdj_d_{tag}``、``kdj_j_{tag}``。

        Raises
        ------
        ValueError
            当缺少 ``high`` / ``low`` / ``close`` 任一列，或新增列名冲突时抛出。
        """
        from qteasy import tafuncs
        tag = suffix if suffix is not None else f'{fastk_period}_{slowk_period}_{slowd_period}'
        k_name = f'kdj_k_{tag}'
        d_name = f'kdj_d_{tag}'
        j_name = f'kdj_j_{tag}'
        for n in (k_name, d_name, j_name):
            if n in self._hp.htypes:
                raise ValueError(f'htype "{n}" already exists')
        high = self._get_price('high')
        low = self._get_price('low')
        close = self._get_price('close')
        n_share, n_time = high.shape
        k_arr = np.full_like(close, np.nan, dtype=float)
        d_arr = np.full_like(close, np.nan, dtype=float)
        j_arr = np.full_like(close, np.nan, dtype=float)
        for i in range(n_share):
            kk, dd = tafuncs.stoch(high[i, :], low[i, :], close[i, :],
                                   fastk_period=fastk_period, slowk_period=slowk_period, slowd_period=slowd_period)
            kk = np.asarray(kk).ravel()[:n_time]
            dd = np.asarray(dd).ravel()[:n_time]
            jj = 3 * kk - 2 * dd  # J = 3*K - 2*D
            k_arr[i, :] = kk
            d_arr[i, :] = dd
            j_arr[i, :] = jj
        if inplace:
            return self._inplace_append_htypes([k_name, d_name, j_name], [k_arr, d_arr, j_arr])
        return self._append_htypes([k_name, d_name, j_name], [k_arr, d_arr, j_arr])


    def apply_ta(
            self,
            func_name: str,
            htype: str = 'close',
            shares: Optional[Iterable[str]] = None,
            as_panel: bool = True,
            **kwargs,
    ):
        """在当前面板上应用 ``tafuncs`` 中的技术指标函数（委托给 ``HistoryPanel.apply_ta``）。

        该方法主要用于对齐历史接口/旧计划中的调用方式：将对 ``HistoryPanel`` 的
        技术指标计算入口统一暴露在 ``hp.kline`` 下，但实际实现与参数解析逻辑位于
        :meth:`HistoryPanel.apply_ta`。

        Parameters
        ----------
        func_name : str
            指标函数名（``qteasy.tafuncs`` 中的函数名）。
        htype : str, default 'close'
            输入数据列名（``HistoryPanel`` 的 ``htypes`` 之一）。
        shares : Iterable[str], optional
            限定计算的标的集合；为 None 时对所有 shares 计算。
        as_panel : bool, default True
            返回值类型控制；含义与 :meth:`HistoryPanel.apply_ta` 一致。
        **kwargs :
            透传给指标函数的其他关键字参数。

        Returns
        -------
        Any
            返回值与 :meth:`HistoryPanel.apply_ta` 保持一致。
        """
        return self._hp.apply_ta(func_name=func_name, htype=htype, shares=shares, as_panel=as_panel, **kwargs)


class HistoryPanelRolling:
    """HistoryPanel 的滚动窗口统计对象。

    该对象通常由 :meth:`HistoryPanel.rolling` 创建，对应一个固定的窗口
    参数组合，并提供 ``mean/std/sum/min/max/apply`` 等方法，返回新的
    HistoryPanel。
    """

    def __init__(self,
                 hp: HistoryPanel,
                 window: int,
                 min_periods: int,
                 center: bool,
                 by: str):
        """创建一个绑定到指定 ``HistoryPanel`` 的滚动窗口统计对象。

        Parameters
        ----------
        hp : HistoryPanel
            需要进行滚动统计的历史数据容器。
        window : int
            滚动窗口长度（周期数）。
        min_periods : int
            计算结果不为 NaN 所需的最小样本数，小于该值时结果为 NaN。
        center : bool
            是否将窗口标签居中。含义与 pandas 的 ``Series.rolling(center=...)`` 一致。
        by : {'share', 'htype'}
            滚动维度控制：

            - ``'share'``：每个 share、每个 htype 的时间序列分别滚动计算；
            - ``'htype'``：预留维度，与 ``'share'`` 的行为保持一致，用于兼容不同调用习惯。

        Returns
        -------
        None
            该方法不返回值，仅保存滚动参数以供后续聚合方法调用。
        """
        self._hp = hp
        self._window = window
        self._min_periods = min_periods
        self._center = center
        self._by = by

    def _apply_rolling(self, func_name: str) -> HistoryPanel:
        """对面板数据应用指定的滚动聚合函数并返回新面板（内部方法）。

        Parameters
        ----------
        func_name : str
            pandas ``Rolling`` 对象的方法名，例如 ``'mean'``、``'std'``、``'sum'``、
            ``'min'``、``'max'``。

        Returns
        -------
        HistoryPanel
            滚动聚合后的新 ``HistoryPanel``，shares/hdates/htypes 标签保持不变。
            当原面板为空时返回空面板。
        """
        hp = self._hp
        if hp.is_empty:
            return HistoryPanel()
        values = hp.values.astype(float)
        res = np.full_like(values, np.nan, dtype=float)

        l_cnt, r_cnt, c_cnt = values.shape

        if self._by == 'share':
            # 每只股票、每个 htype 独立做时间滚动
            for li in range(l_cnt):
                for ci in range(c_cnt):
                    series = pd.Series(values[li, :, ci], index=hp.hdates)
                    roller = series.rolling(window=self._window,
                                            min_periods=self._min_periods,
                                            center=self._center)
                    rolled = getattr(roller, func_name)()
                    res[li, :, ci] = rolled.values
        else:  # by == 'htype'
            for ci in range(c_cnt):
                for li in range(l_cnt):
                    series = pd.Series(values[li, :, ci], index=hp.hdates)
                    roller = series.rolling(window=self._window,
                                            min_periods=self._min_periods,
                                            center=self._center)
                    rolled = getattr(roller, func_name)()
                    res[li, :, ci] = rolled.values

        return HistoryPanel(values=res, levels=hp.shares, rows=hp.hdates, columns=hp.htypes)

    def mean(self) -> HistoryPanel:
        """计算滚动窗口均值并返回新面板。

        Returns
        -------
        HistoryPanel
            滚动均值结果面板，标签与原面板一致。
        """
        return self._apply_rolling('mean')

    def std(self) -> HistoryPanel:
        """计算滚动窗口标准差并返回新面板。

        Returns
        -------
        HistoryPanel
            滚动标准差结果面板，标签与原面板一致。
        """
        return self._apply_rolling('std')

    def sum(self) -> HistoryPanel:
        """计算滚动窗口求和并返回新面板。

        Returns
        -------
        HistoryPanel
            滚动求和结果面板，标签与原面板一致。
        """
        return self._apply_rolling('sum')

    def min(self) -> HistoryPanel:
        """计算滚动窗口最小值并返回新面板。

        Returns
        -------
        HistoryPanel
            滚动最小值结果面板，标签与原面板一致。
        """
        return self._apply_rolling('min')

    def max(self) -> HistoryPanel:
        """计算滚动窗口最大值并返回新面板。

        Returns
        -------
        HistoryPanel
            滚动最大值结果面板，标签与原面板一致。
        """
        return self._apply_rolling('max')

    def apply(self,
              func: Callable[[np.ndarray], float],
              raw: bool = False,
              **kwargs) -> HistoryPanel:
        """在滚动窗口上应用自定义函数。

        Parameters
        ----------
        func : callable
            自定义函数，接受一个窗口向量并返回标量。
        raw : bool, default False
            为 ``True`` 时向 func 传入 ``ndarray``，否则传入 ``Series``。
        **kwargs :
            透传给 func 的其他参数。

        Returns
        -------
        HistoryPanel
            应用自定义函数后的滚动结果面板，shares/hdates/htypes 标签保持不变。

        Notes
        -----
        - 与 pandas 一致：当窗口内有效样本数小于 ``min_periods`` 时，结果为 NaN。
        - ``func`` 应返回标量数值；返回数组或非数值类型可能导致 pandas 报错或产生
          不符合预期的结果。

        Examples
        --------
        >>> hp = qt.get_history_data(htype_names='close', shares='000001.SZ', rows=30, as_data_frame=False)
        >>> roller = hp.rolling(window=5, min_periods=5)
        >>> hp_mean = roller.mean()
        >>> hp_mean
        share 0, label: 000001
                    close
        2020-01-01  NaN
        2020-01-02  NaN
        2020-01-03  NaN
        2020-01-04  NaN
        2020-01-05  10.0
        2020-01-06  10.5
        ...
        2020-01-30  11.2

        >>> hp_mad = roller.apply(lambda x: float(np.mean(np.abs(x - np.mean(x)))), raw=True)
        >>> hp_mad
        share 0, label: 000001
                    close
        2020-01-01  NaN
        2020-01-02  NaN
        2020-01-03  NaN
        2020-01-04  NaN
        2020-01-05  0.0
        2020-01-06  0.5
        ...
        2020-01-30  0.4

        """
        hp = self._hp
        if hp.is_empty:
            return HistoryPanel()
        values = hp.values.astype(float)
        res = np.full_like(values, np.nan, dtype=float)
        l_cnt, r_cnt, c_cnt = values.shape

        def _apply_series(s: pd.Series) -> float:
            if raw:
                return func(s.values, **kwargs)
            return func(s, **kwargs)

        if self._by == 'share':
            for li in range(l_cnt):
                for ci in range(c_cnt):
                    series = pd.Series(values[li, :, ci], index=hp.hdates)
                    roller = series.rolling(window=self._window,
                                            min_periods=self._min_periods,
                                            center=self._center)
                    rolled = roller.apply(_apply_series, raw=False)
                    res[li, :, ci] = rolled.values
        else:
            for ci in range(c_cnt):
                for li in range(l_cnt):
                    series = pd.Series(values[li, :, ci], index=hp.hdates)
                    roller = series.rolling(window=self._window,
                                            min_periods=self._min_periods,
                                            center=self._center)
                    rolled = roller.apply(_apply_series, raw=False)
                    res[li, :, ci] = rolled.values

        return HistoryPanel(values=res, levels=hp.shares, rows=hp.hdates, columns=hp.htypes)


def hp_join(*historypanels):
    """ 当元组*historypanels不是None，且内容全都是HistoryPanel对象时，将所有的HistoryPanel对象连接成一个HistoryPanel

    parameters
    ----------
    historypanels: HistoryPanels
        一个或多个HistoryPanel对象，他们将被组合成一个包含他们所有数据的HistoryPanel

    Returns
    -------
    HistoryPanel
        组合后的HistoryPanel
    """
    assert all(isinstance(hp, HistoryPanel) for hp in historypanels), \
        f'Object type Error, all objects passed to this function should be HistoryPanel'
    res_hp = HistoryPanel()
    for hp in historypanels:
        if isinstance(hp, HistoryPanel):
            res_hp.join(other=hp)
    return res_hp


def dataframe_to_hp(
        df: pd.DataFrame,
        hdates=None,
        htypes=None,
        shares=None,
        column_type: str = None
):
    """ 根据DataFrame中的数据创建HistoryPanel对象。

    Parameters
    ----------
    df: pd.DataFrame,
        需要被转化为HistoryPanel的DataFrame。
    hdates: DatetimeIndex or List of DateTime like, Optional
        如果给出hdates，它会被用于转化后HistoryPanel的日期标签
    htypes: str or list of str, Optional
        转化后HistoryPanel的历史数据类型标签
    shares: str or list of str, Optional
        转化后HistoryPanel的股票代码标签
    column_type: str, Default None
        DataFrame的column代表的数据类型，可以为 'shares' or 'htype'
        如果为None，则必须输入htypes和shares参数中的一个

    Returns
    -------
    HistoryPanel对象

    Notes
    -----
    由于DataFrame只有一个二维数组，因此一个DataFrame只能转化为以下两种HistoryPanel之一：
    1，只有一个share，包含一个或多个htype的HistoryPanel，这时HistoryPanel的shape为(1, dates, htypes)
        在这种情况下，htypes可以由一个列表，或逗号分隔字符串给出，也可以由DataFrame对象的column Name来生成，而share则必须给出
    2，只有一个dtype，包含一个或多个shares的HistoryPanel，这时HistoryPanel的shape为(shares, dates, 1)
    具体转化为何种类型的HistoryPanel可以由column_type参数来指定，也可以通过给出hdates、htypes以及shares参数来由程序判断

    Examples
    --------
    >>> dataframe = pd.DataFrame(
    ...     data=np.random.rand(3, 3),
    ...     index=pd.date_range(start='2020-01-01', periods=3),
    ...     columns=['A', 'B', 'C']
    ... )
    >>> dataframe
    Out:
                       A         B         C
    2020-01-01  0.814394  0.284772  0.259304
    2020-01-02  0.237300  0.483317  0.600886
    2020-01-03  0.744638  0.255470  0.953640

    >>> hp = dataframe_to_hp(dataframe, htypes=['open', 'close', 'high'], shares='000001')
    >>> hp
    share 0, label: 000001
                    open     close      high
    2020-01-01  0.814394  0.284772  0.259304
    2020-01-02  0.237300  0.483317  0.600886
    2020-01-03  0.744638  0.255470  0.953640

    >>> hp = dataframe_to_hp(dataframe, htypes='open', shares=['000001', '000002', '000003'])
    >>> hp
    share 0, label: 000001
                    open
    2020-01-01  0.814394
    2020-01-02  0.237300
    2020-01-03  0.744638
    share 1, label: 000002
                    open
    2020-01-01  0.284772
    2020-01-02  0.483317
    2020-01-03  0.255470
    share 2, label: 000003
                    open
    2020-01-01  0.259304
    2020-01-02  0.600886
    2020-01-03  0.953640
    """

    available_column_types = ['shares', 'htypes', None]
    if not isinstance(df, pd.DataFrame):
        msg = f'Input df should be pandas DataFrame! got {type(df)} instead.'
        raise TypeError(msg)
    if hdates is None:
        hdates = df.rename(index=pd.to_datetime).index
    # if not isinstance(hdates, (list, tuple)):
    #     msg = f'TypeError, hdates should be list or tuple, got {type(hdates)} instead.'
    #     raise TypeError(msg)
    index_count = len(hdates)
    if not index_count == len(df.index):
        msg = f'InputError, can not match {index_count} indices with {len(df.hdates)} rows of DataFrame'
        raise ValueError(msg)
    if not column_type in available_column_types:
        msg = f'column_type should be either "shares" or "htypes", got {type(column_type)} instead!'
        raise ValueError(msg)
    # TODO: Temp codes, implement this method when column_type is not given -- the column type should be infered
    #  by the input combination of shares and htypes
    if column_type is None:  # try to infer a proper column type
        if shares is None:
            htype_list = []
            if htypes is None:
                raise KeyError(f'shares and htypes can not both be None if column_type is not given!')
            if isinstance(htypes, str):
                htype_list = str_to_list(htypes)
            try:
                if len(htype_list) == 1:
                    column_type = 'shares'
                else:
                    column_type = 'htypes'
            except:
                raise ValueError(f'htypes should be a list or a string, got {type(htypes)} instead')
        else:
            share_list = []
            if shares is None:
                raise KeyError(f'shares and htypes can not both be None if column_type is not given!')
            if isinstance(shares, str):
                share_list = str_to_list(shares)
            try:
                if len(share_list) == 1:
                    column_type = 'htypes'
                else:
                    column_type = 'shares'
            except:
                raise ValueError(f'shares should be a list or a string, got {type(shares)} instead')

    if column_type == 'shares':
        if shares is None:
            shares = df.columns
        if isinstance(shares, str):
            shares = str_to_list(shares, sep_char=',')
        if not len(shares) == len(df.columns):
            msg = f'Can not match {len(shares)} shares with {len(df.columns)} columns of DataFrame'
            raise ValueError(msg)
        if htypes is None:
            raise KeyError(f', Please provide a valid name for the htype of the History Panel')
        assert isinstance(htypes, str), \
            f'TypeError, data type of dtype should be a string, got {type(htypes)} instead.'
        share_count = len(shares)
        history_panel_value = np.zeros(shape=(share_count, len(hdates), 1))
        for i in range(share_count):
            history_panel_value[i, :, 0] = df.values[:, i]
    else:  # column_type == 'htype'
        if htypes is None:
            htypes = df.columns
        elif isinstance(htypes, str):
            htypes = htypes.split(',')
            assert len(htypes) == len(df.columns), \
                f'InputError, can not match {len(htypes)} shares with {len(df.columns)} columns of DataFrame'
        else:
            assert isinstance(htypes, (list, tuple)), f'TypeError: levels should be list or tuple, ' \
                                                      f'got {type(htypes)} instead.'
            assert len(htypes) == len(df.columns), \
                f'InputError, can not match {len(htypes)} shares with {len(df.columns)} columns of DataFrame'
        assert shares is not None, f'InputError, shares should be given when they can not inferred'
        assert isinstance(shares, str), \
            f'TypeError, data type of share should be a string, got {type(shares)} instead.'
        history_panel_value = df.values.reshape(1, len(hdates), len(htypes))
    return HistoryPanel(values=history_panel_value, levels=shares, rows=hdates, columns=htypes)


def from_single_dataframe(df: pd.DataFrame,
                          hdates=None,
                          htypes=None,
                          shares=None,
                          column_type: str = None) -> HistoryPanel:
    """ 函数dataframe_to_hp()的别称，等同于dataframe_to_hp()"""
    return dataframe_to_hp(df=df,
                           hdates=hdates,
                           htypes=htypes,
                           shares=shares,
                           column_type=column_type)


def from_multi_index_dataframe(df: pd.DataFrame):
    """ 将一个含有multi-index的DataFrame转化为一个HistoryPanel

    Parameters
    ----------
    df: pd.DataFrame
        需要被转化的DataFrame

    Returns
    -------
    HistoryPanel

    """
    raise NotImplementedError


def stack_dataframes(dfs: Union[list, dict],
                     dataframe_as: str = 'shares',
                     shares: Iterable = None,
                     htypes: Iterable = None,
                     fill_value: Any = None):
    """ 将多个dataframe组合成一个HistoryPanel.

    Parameters
    ----------
    dfs: list of DataFrames or dict of DataFrames
        需要被堆叠的dataframe，可以为list或dict，
        dfs可以是一个dict或一个list，如果是一个list，这个list包含需要组合的所有dataframe，如果是dict，这个dict的values包含
        所有需要组合的dataframe，dict的key包含每一个dataframe的标签，这个标签可以被用作HistoryPanel的层（shares）或列
        （htypes）标签。如果dfs是一个list，则组合后的行标签或列标签必须明确给出。
    dataframe_as: str {'shares', 'htypes'}
        每个dataframe代表的数据类型。
        dataframe_as == 'shares'，
            表示每个DataFrame代表一个share的数据，每一列代表一个htype。组合后的HP对象
            层数与DataFrame的数量相同，而列数等于所有DataFrame的列的并集，行标签也为所有DataFrame的行标签的并集
            在这种模式下：
            如果dfs是一个list，shares参数必须给出，且shares的数量必须与DataFrame的数量相同，作为HP的层标签
            如果dfs是一个dict，shares参数不必给出，dfs的keys会被用于层标签，如果shares参数给出且符合要求，
            shares参数将取代dfs的keys参数

        dataframe_as == 'htypes'，
            表示每个DataFrame代表一个htype的数据，每一列代表一个share。组合后的HP对象
            列数与DataFrame的数量相同，而层数等于所有DataFrame的列的并集，行标签也为所有DataFrame的行标签的并集
            在这种模式下，
            如果dfs是一个list，htypes参数必须给出，且htypes的数量必须与DataFrame的数量相同，作为HP的列标签
            如果dfs是一个dict，htypes参数不必给出，dfs的keys会被用于列标签，如果htypes参数给出且符合要求，
            htypes参数将取代dfs的keys参数
    shares: str or list of str
        生成的HistoryPanel的层标签或股票名称标签。
        如果堆叠方式为"shares"，则层标签必须以dict的key的形式给出或者在shares参数中给出
        以下两种参数均有效且等效：
        '000001.SZ, 000002.SZ, 000003.SZ'
        ['000001.SZ', '000002.SZ', '000003.SZ']

        如果堆叠方式为"htypes"，不需要给出shares，默认使用dfs的columns标签的并集作为输出的层标签
        如果给出了shares，则会强制使用shares作为层标签，多出的标签会用fill_values填充，
        多余的DataFrame数据会被丢弃
    htypes: str or list of str
        生成的HistoryPanel的列标签或数据类型标签。
        如果堆叠方式为"htypes"，则层标签必须以dict的key的形式给出或者在shares参数中给出
        以下两种参数均有效且等效：
        '000001.SZ, 000002.SZ, 000003.SZ'
        ['000001.SZ', '000002.SZ', '000003.SZ']
        如果堆叠方式为"shares"，不需要给出htypes，默认使用dfs的columns标签的并集作为列标签
        如果给出了htypes，则会强制用它作为列标签，多出的标签会用fill_values填充，
        多余的DataFrame数据会被丢弃
    fill_value:
        多余的位置用fill_value填充

    Returns
    -------
    HistoryPanel
        一个由多个单index的数据框组成的HistoryPanel对象

    Examples
    --------
    >>> df1 = pd.DataFrame([[1, 2, 3], [4, 5, 6]], index=['20210101', '20210102'], columns=['open', 'close', 'low'])
    >>> df2 = pd.DataFrame([[7, 8, 9], [10, 11, 12]], index=['20210101', '20210102'], columns=['open', 'close', 'low'])
    >>> df3 = pd.DataFrame([[13, 14, 15], [16, 17, 18]], index=['20210101', '20210102'], columns=['open', 'close', 'low'])
    >>> dataframes = [df1, df2, df3]
    >>> hp = stack_dataframes(dataframes, dataframe_as='shares', shares='000001.SZ, 000002.SZ, 000003.SZ')
    >>> hp
    share 0, label: 000001.SZ
             open  close   low
    20210101  1.0    2.0   3.0
    20210102  4.0    5.0   6.0
    share 1, label: 000002.SZ
              open  close   low
    20210101   7.0    8.0   9.0
    20210102  10.0   11.0  12.0
    share 2, label: 000003.SZ
              open  close   low
    20210101  13.0   14.0  15.0
    20210102  16.0   17.0  18.0

    """
    assert isinstance(dfs, (list, dict)), \
        f'TypeError, dfs should be a list of or a dict whose values are pandas DataFrames, got {type(dfs)} instead.'
    assert dataframe_as in ['shares', 'htypes'], \
        f'InputError, valid input for dataframe_as can only be \'shares\' or \'htypes\''
    if fill_value is None:
        fill_value = np.nan
    assert isinstance(fill_value, (int, float)), f'invalid fill value type {type(fill_value)}'
    if shares is not None:
        if isinstance(shares, str):
            shares = str_to_list(shares)
    if htypes is not None:
        if isinstance(htypes, str):
            htypes = str_to_list(htypes)
    combined_index = []
    combined_shares = []
    combined_htypes = []
    # 检查输入参数是否正确
    if dataframe_as == 'shares':
        axis_names = shares
        combined_axis_names = combined_shares
    else:  # dataframe_as == 'htypes':
        axis_names = htypes
        combined_axis_names = combined_htypes
    # 根据叠放方式不同，需要检查的参数也不同
    assert (axis_names is not None) or (isinstance(dfs, dict)), \
        f'htypes should be given if the dataframes are to be stacked along htypes and they are not in a dict'
    assert isinstance(axis_names, (list, str)) or (isinstance(dfs, dict))
    if isinstance(axis_names, str):
        axis_names = str_to_list(axis_names)
    if isinstance(dfs, dict) and axis_names is None:
        axis_names = dfs.keys()
    assert len(axis_names) == len(dfs)
    combined_axis_names.extend(axis_names)

    if isinstance(dfs, dict):
        dfs = dfs.values()
    # 逐个处理所有传入的DataFram，合并index、htypes以及shares
    for df in dfs:
        assert isinstance(df, pd.DataFrame), \
            f'InputError, dfs should be a list of pandas DataFrame, got {type(df)} instead.'
        combined_index.extend(df.rename(index=pd.to_datetime).index)
        if dataframe_as == 'shares':
            combined_htypes.extend(df.columns)
        else:
            combined_shares.extend(df.columns)
    dfs = [df.rename(index=pd.to_datetime) for df in dfs]
    # 合并htypes及shares，
    # 如果没有直接给出shares或htypes，使用他们的并集并排序
    # 如果直接给出了shares或htypes，直接使用并保持原始顺序
    if (dataframe_as == 'shares') and (htypes is None):
        combined_htypes = list(set(combined_htypes))
        combined_htypes.sort()
    elif (dataframe_as == 'shares') and (htypes is not None):
        combined_htypes = htypes
    elif (dataframe_as == 'htypes') and (shares is None):
        combined_shares = list(set(combined_shares))
        combined_shares.sort()
    elif (dataframe_as == 'htypes') and (shares is not None):
        combined_shares = shares
    combined_index = list(set(combined_index))
    htype_count = len(combined_htypes)
    share_count = len(combined_shares)
    index_count = len(combined_index)
    combined_htypes_dict = dict(zip(combined_htypes, range(htype_count)))
    combined_shares_dict = dict(zip(combined_shares, range(share_count)))
    combined_index.sort()
    # 生成并复制数据
    res_values = np.zeros(shape=(share_count, index_count, htype_count))
    res_values.fill(fill_value)
    for df_id in range(len(dfs)):
        extended_df = dfs[df_id].reindex(combined_index)
        for col_name, series in extended_df.items():  # iteritems is deprecated since 1.5 and removed since 2.0
            if dataframe_as == 'shares':
                if col_name not in combined_htypes_dict:
                    continue
                res_values[df_id, :, combined_htypes_dict[col_name]] = series.values
            else:
                if col_name not in combined_shares_dict:
                    continue
                res_values[combined_shares_dict[col_name], :, df_id] = series.values
    return HistoryPanel(res_values,
                        levels=combined_shares,
                        rows=combined_index,
                        columns=combined_htypes)


def from_df_dict(dfs: Union[list, dict], dataframe_as: str = 'shares', shares=None, htypes=None, fill_value=None):
    """ 函数stack_dataframes()的别称，等同于函数stack_dataframes()"""
    return stack_dataframes(dfs=dfs,
                            dataframe_as=dataframe_as,
                            shares=shares,
                            htypes=htypes,
                            fill_value=fill_value)


def _adjust_freq(hist_data: pd.DataFrame,
                 target_freq: str,
                 *,
                 method: str = 'last',
                 b_days_only: bool = True,
                 trade_time_only: bool = True,
                 forced_start: str = None,
                 forced_end: str = None,
                 **kwargs):
    """ 降低获取数据的频率，通过插值的方式将高频数据降频合并为低频数据，使历史数据的时间频率
    符合target_freq

    Parameters
    ----------
    hist_data: pd.DataFrame
        历史数据，是一个index为日期/时间的DataFrame
    target_freq: str
        历史数据的目标频率，包括以下选项：
         - 1/5/15/30min 1/5/15/30分钟频率周期数据(如K线)
         - H/D/W/M 分别代表小时/天/周/月 周期数据(如K线)
         如果下载的数据频率与目标freq不相同，将通过升频或降频使其与目标频率相同
    method: str
        调整数据频率分为数据降频和升频，在两种不同情况下，可用的method不同：
        数据降频就是将多个数据合并为一个，从而减少数据的数量，但保留尽可能多的信息，
        降频可用的methods有：
        - 'last'/'close': 使用合并区间的最后一个值
        - 'first'/'open': 使用合并区间的第一个值
        - 'max'/'high': 使用合并区间的最大值作为合并值
        - 'min'/'low': 使用合并区间的最小值作为合并值
        - 'mean'/'average': 使用合并区间的平均值作为合并值
        - 'sum/total': 使用合并区间的总和作为合并值

        数据升频就是在已有数据中插入新的数据，插入的新数据是缺失数据，需要填充。
        升频可用的methods有：
        - 'ffill': 使用缺失数据之前的最近可用数据填充，如果没有可用数据，填充为NaN
        - 'bfill': 使用缺失数据之后的最近可用数据填充，如果没有可用数据，填充为NaN
        - 'nan': 使用NaN值填充缺失数据
        - 'zero': 使用0值填充缺失数据
    b_days_only: bool 默认True
        是否强制转换自然日频率为工作日，即：
        'D' -> 'B'
        'W' -> 'W-FRI'
        'M' -> 'BM'
    trade_time_only: bool, 默认True
        为True时 仅生成交易时间段内的数据，交易时间段的参数通过**kwargs设定
    forced_start: str, Datetime like, 默认None
        强制开始日期，如果为None，则使用hist_data的第一天为开始日期
    forced_start: str, Datetime like, 默认None
        强制结束日期，如果为None，则使用hist_data的最后一天为结束日期
    **kwargs:
        用于生成trade_time_index的参数，包括：
        include_start:   日期时间序列是否包含开始日期/时间
        include_end:     日期时间序列是否包含结束日期/时间
        start_am:        早晨交易时段的开始时间
        end_am:          早晨交易时段的结束时间
        include_start_am:早晨交易时段是否包括开始时间
        include_end_am:  早晨交易时段是否包括结束时间
        start_pm:        下午交易时段的开始时间
        end_pm:          下午交易时段的结束时间
        include_start_pm 下午交易时段是否包含开始时间
        include_end_pm   下午交易时段是否包含结束时间

    Returns
    -------
    DataFrame:
    一个重新设定index并填充好数据的历史数据DataFrame

    Examples
    --------
    例如，合并下列数据(每一个tuple合并为一个数值，?表示合并后的数值）
        [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(?), (?), (?)]
    数据合并方法:
    - 'last'/'close': 使用合并区间的最后一个值。如：
        [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(3), (5), (7)]
    - 'first'/'open': 使用合并区间的第一个值。如：
        [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(1), (4), (6)]
    - 'max'/'high': 使用合并区间的最大值作为合并值：
        [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(3), (5), (7)]
    - 'min'/'low': 使用合并区间的最小值作为合并值：
        [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(1), (4), (6)]
    - 'avg'/'mean': 使用合并区间的平均值作为合并值：
        [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(2), (4.5), (6.5)]
    - 'sum'/'total': 使用合并区间的平均值作为合并值：
        [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(2), (4.5), (6.5)]

    例如，填充下列数据(?表示插入的数据）
        [1, 2, 3] 填充后变为: [?, 1, ?, 2, ?, 3, ?]
    缺失数据的填充方法如下:
    - 'ffill': 使用缺失数据之前的最近可用数据填充，如果没有可用数据，填充为NaN。如：
        [1, 2, 3] 填充后变为: [NaN, 1, 1, 2, 2, 3, 3]
    - 'bfill': 使用缺失数据之后的最近可用数据填充，如果没有可用数据，填充为NaN。如：
        [1, 2, 3] 填充后变为: [1, 1, 2, 2, 3, 3, NaN]
    - 'nan': 使用NaN值填充缺失数据：
        [1, 2, 3] 填充后变为: [NaN, 1, NaN, 2, NaN, 3, NaN]
    - 'zero': 使用0值填充缺失数据：
        [1, 2, 3] 填充后变为: [0, 1, 0, 2, 0, 3, 0]
    """

    if not isinstance(target_freq, str):
        err = TypeError(f'target freq should be a string, got {target_freq}({type(target_freq)}) instead.')
        raise err
    target_freq = target_freq.upper()
    # 如果hist_data为空，直接返回
    if hist_data.empty:
        return hist_data
    if b_days_only:
        if target_freq in ['W', 'W-SUN']:
            target_freq = 'W-FRI'
        elif target_freq == 'M':
            target_freq = 'BME'
    # 如果hist_data的freq与target_freq一致，也可以直接返回
    # TODO: 这里有bug：强制start/end的情形需要排除
    if hist_data.index.freqstr == target_freq:
        return hist_data
    # 如果hist_data的freq为None，可以infer freq
    if hist_data.index.inferred_freq == target_freq:
        return hist_data

    # 新版本pandas修改了部分freq alias，为了确保向后兼容，确保freq_aliases与pandas版本匹配
    target_freq = pandas_freq_alias_version_conversion(target_freq)

    # 如果target_freq为h，则实际resample频率为30min，因为需要兼顾交易日早上9:30-11:30和下午13:00-15:00两个时段
    # 如果target_freq为30min或15min等，则直接使用该freq
    resampled = hist_data.resample('30min' if target_freq == 'h' else target_freq)
    if method in ['last', 'close']:
        resampled = resampled.last()
    elif method in ['first', 'open']:
        resampled = resampled.first()
    elif method in ['max', 'high']:
        resampled = resampled.max()
    elif method in ['min', 'low']:
        resampled = resampled.min()
    elif method in ['avg', 'mean']:
        resampled = resampled.mean()
    elif method in ['sum', 'total']:
        resampled = resampled.sum()
    elif method == 'ffill':
        resampled = resampled.ffill()
    elif method == 'bfill':
        resampled = resampled.bfill()
    elif method in ['nan', 'none']:
        resampled = resampled.first()
    elif method == 'zero':
        resampled = resampled.first().fillna(0)
    else:
        # for unexpected cases
        err = ValueError(f'resample method {method} can not be recognized.')
        raise err

    # 完成resample频率切换后，根据设置去除非工作日或非交易时段的数据
    # 并填充空数据
    resampled_index = resampled.index
    if forced_start is None:
        start = resampled_index[0]
    else:
        start = pd.to_datetime(forced_start)
    if forced_end is None:
        end = resampled_index[-1]
    else:
        end = pd.to_datetime(forced_end)

    # 如果要求强制转换自然日频率为工作日频率
    # 原来的版本在resample之前就强制转换自然日到工作日，但是测试发现，pd的resample有一个bug：
    # 这个bug会导致method为last时，最后一个工作日的数据取自周日，而不是周五
    # 在实际测试中发现，如果将2020-01-01到2020-01-10之间的Hourly数据汇总到工作日时
    # 2020-01-03是周五，汇总时本来应该将2020-01-03 23:00:00的数据作为当天的数据
    # 但是实际上2020-01-05 23:00:00 的数据被错误地放置到了周五，也就是周日的数据被放到
    # 了周五，这样可能会导致错误的结果
    # 因此解决方案是，仍然按照'D'频率来resample，然后再通过reindex将非交易日的数据去除
    # 不过仅对freq为'D'的频率如此操作
    if b_days_only:
        if target_freq == 'D':
            target_freq = 'B'

    # 如果要求去掉非交易时段的数据
    from qteasy.trading_util import trade_time_index
    if trade_time_only:
        expanded_index = trade_time_index(
                start=start,
                end=end,
                freq=target_freq,
                trade_days_only=b_days_only,
                **kwargs
        )
    else:
        expanded_index = pd.date_range(start=start, end=end, freq=target_freq)
    resampled = resampled.reindex(index=expanded_index)
    # 如果在数据开始或末尾增加了空数据（因为forced start/forced end），需要根据情况填充
    if (expanded_index[-1] > resampled_index[-1]) or (expanded_index[0] < resampled_index[0]):
        if method == 'ffill':
            resampled.ffill(inplace=True)
        elif method == 'bfill':
            resampled.bfill(inplace=True)
        elif method == 'zero':
            resampled.fillna(0, inplace=True)

    return resampled


# ==================
# High level functions that creates HistoryPanel that fits the requirement of trade strategies
# ==================
def get_history_data_packages(
        data_types: list[DataType],
        data_source: DataSource,
        shares,
        start=None,
        end=None,
        rows=None,
) -> dict[str, pd.DataFrame]:
    """ 历史数据获取函数，从本地DataSource（数据库/csv/hdf/fth）获取所需的数据并返回一个
    data_package（包含不同数据类型的区间数据），返回的数据类型为dict，包含每一个data_type
    的历史数据，其columns包括所有的shares。其index为start到end之间的DatatimeIndex，同时
    根据历史数据的类型，数据将被赋予正确的TimeOffset。

    关于TimeOffset：当数据源中的数据频率低于等于日频时，其index标签都仅包含日期，当转换为包含
    时间的index时，时间部分会被置为00:00:00，如20200101会被置为2020-01-01 00:00:00，这与
    事实不符，因为2020-01-01的数据不会在当天0点就可用，因此需要手动设置一个Offset以确定该数据
    的真正可用时间，如收盘价、最高价、最低价在每天的15:00可用，开盘价在每天9:30可用。因此如果读
    取close_E_d的数据，其DatetimeIndex的时间部分应该为 "2020-01-01 15:00:00"，而
    open_E_d的数据的DatetimeIndex应该为"2020-01-01 09:30:00"

    Parameters
    ----------
    data_types: [DataType]
        需要获取的历史数据类型集合，必须是合法的DataType数据类型对象，
    data_source: DataSource
        数据源对象，用于获取数据
    shares: [str, list]
        需要获取历史数据的证券代码集合，可以是以逗号分隔的证券代码字符串或者证券代码字符列表，
        如以下两种输入方式皆合法且等效：
         - str:     '000001.SZ, 000002.SZ, 000004.SZ, 000005.SZ'
         - list:    ['000001.SZ', '000002.SZ', '000004.SZ', '000005.SZ']
    start: str
        YYYYMMDD HH:MM:SS 格式的日期/时间，获取的历史数据的开始日期/时间
    end: str
        YYYYMMDD HH:MM:SS 格式的日期/时间，获取的历史数据的结束日期/时间
    rows: int, optional
        获取的历史数据的行数
        如果rows为正整数，则获取最近的rows行历史数据，如果给出了start或end参数，则忽略rows参数

    Returns
    -------
    dict of DataFrames:
        一个dict，key为data_type.name，value为对应data_type的数据DataFrame

    Examples
    --------
    >>> from qteasy import DataType, DataSource

    """
    if isinstance(data_types, DataType):
        data_types = [data_types]
    if not isinstance(data_types, (list, tuple)):
        raise TypeError(f'data_types should be a list or tuple of DataType, got {type(data_types)} instead.')
    if not all([isinstance(dt, DataType) for dt in data_types]):
        raise TypeError(f'all elements of data_types should be DataType, got {data_types} instead.')

    if shares is None:
        shares = []
    if isinstance(shares, str):
        shares = str_to_list(shares, sep_char=',')

    symbolized_dtypes = [dt for dt in data_types if not dt.unsymbolized]
    unsymbolized_dtypes = [dt for dt in data_types if dt.unsymbolized]

    # 当我们使用unsymbolizer作为是否获取参考数据的依据时，shares就可以为空列表，但是前提是symbolized_dtypes为空
    if len(shares) == 0 and len(symbolized_dtypes) > 0:
        raise ValueError(f'shares can not be an empty list while symbolized data types are given: {symbolized_dtypes}.')

    all_dfs = {}
    # 获取针对shares的symbolized数据
    if len(symbolized_dtypes) > 0:
        all_dfs.update(get_history_data_from_source(
                datasource=data_source,
                htypes=symbolized_dtypes,
                qt_codes=list_to_str_format(shares),
                start=start,
                end=end,
                row_count=rows,
        ))
    # 获取无share的参考数据
    if len(unsymbolized_dtypes) > 0:
        # 获取无share数据
        all_dfs.update(get_reference_data_from_source(
                datasource=data_source,
                htypes=unsymbolized_dtypes,
                start=start,
                end=end,
                row_count=rows,
        ))

    # 根据数据类型设置数据日期时间的Offset值
    for dt in data_types:
        time_availability_offset = dt.get_available_time()
        if time_availability_offset is not None:
            df = all_dfs[dt.dtype_id]
            try:
                df.index = df.index + pd.Timedelta(time_availability_offset)
            except:
                # import pdb
                # pdb.set_trace()
                pass
            all_dfs[dt.dtype_id] = df

    return all_dfs


def get_history_panel(
        data_types: list[DataType],
        data_source: DataSource,
        shares: Optional[Union[str, list[str]]]=None,
        freq=None,
        start=None,
        end=None,
        rows=None,
        drop_nan=True,
        resample_method='ffill',
        b_days_only=True,
        trade_time_only=True,
        return_history_panel=True,
        **kwargs
) -> Union[HistoryPanel, dict[str, pd.DataFrame]]:
    """ 历史数据获取函数，从本地DataSource（数据库/csv/hdf/fth）获取所需的数据并组装为一个
    HistoryPanel数据对象，该HistoryPanel的数据时间频率由参数指定，查找数据时会自动匹配相应
    的数据类型，如果没有完全匹配频率的数据类型，则会找到最近的类型并通过升频或降频的方式调整为
    所需频率输出。

    只要给出数据类型、数据源和证券代码，就可以直接获取所需的历史数据，这个函数存在的意义在于：
    有些数据类型有相同的名字，但是对应不同的频率或资产类型，在读取数据时，这些不同的资产类型
    会被分别处理并存储在不同的数据层中，但我们有时候需要将它们合并起来，例如，股票000001.SZ和
    指数000001.SH都有close类型的数据，但它们是存储在不同的数据表中的不同数据类型。但我们有时候
    希望在close数据层中同时看到股票和指数的close数据，这时就需要将它们合并到同一个数据层中。

    这个函数在读取数据时，会根据数据类型的名字将不同的数据类型合并到一起，例如close_E_d的数据
    会跟close_IDX_d的数据合并，成为同一层的数据并给它一个统一的标签'close'.这样就能在同一层
    中同时看到股票和指数的close数据了。

    同时，这个函数还会根据需要调整数据的频率，将所有不同频率的数据全部都统一为需要的频率输出。
    如果某些数据没有指定频率的数据类型，则会找到频率最接近的类型并通过升频或降频的方式调整为
    需要的频率输出。

    如果选择合并数据类型，则必须确保输入测数据类型不包括多个相同名字不同频率的数据类型，因为
    这种情况会导致错误：例如，输入数据类型包括close_E_d和close_E_h，
    这时在输入处理阶段，程序会检查是否存在多个相同名字的数据类型，如果存在，则只保留频率最接近
    目标频率的那个数据类型，其他相同名字的数据类型会被忽略掉。

    TODO: 将data_types参数改为data_type_names参数，只需要传入数据类型的名称列表即可，
     由函数内部根据名称、频率和shares的资产类型，通过infer_asset_types()函数来自动匹配
     合适的数据类型对象

    Parameters
    ----------
    data_types: [DataType]
        需要获取的历史数据类型的名称，
    data_source: DataSource
        数据源对象，用于获取数据
    shares: [str, list]
        需要获取历史数据的证券代码集合，可以是以逗号分隔的证券代码字符串或者证券代码字符列表，
        如以下两种输入方式皆合法且等效：
         - str:     '000001.SZ, 000002.SZ, 000004.SZ, 000005.SZ'
         - list:    ['000001.SZ', '000002.SZ', '000004.SZ', '000005.SZ']
    freq: str, optional
        如果给出此参数，则强制转换获取的历史数据的频率，此时输出的所有数据全部为同频率：
         - 1/5/15/30min 1/5/15/30分钟频率周期数据(如K线)
         - H/D/W/M 分别代表小时/天/周/月 周期数据(如K线)
        否则输出的历史数据频率与数据类型中规定的频率相同
    start: str datetime like
        YYYYMMDD HH:MM:SS 格式的日期/时间，获取的历史数据的开始日期/时间(如果可用)
    end: str datetime like
        YYYYMMDD HH:MM:SS 格式的日期/时间，获取的历史数据的结束日期/时间(如果可用)
    rows: int
        获取的历史数据的行数，如果rows为None，则获取所有可用的历史数据
        如果rows为正整数，则获取最近的rows行历史数据，如果给出了start或end参数，则忽略rows参数
    drop_nan: bool
        是否保留全NaN的行
    resample_method: str
        如果数据需要升频或降频时，调整频率的方法
        调整数据频率分为数据降频和升频，在两种不同情况下，可用的method不同：
        数据降频就是将多个数据合并为一个，从而减少数据的数量，但保留尽可能多的信息，
        例如，合并下列数据(每一个tuple合并为一个数值，?表示合并后的数值）
            [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(?), (?), (?)]
        数据合并方法:
        - 'last'/'close': 使用合并区间的最后一个值。如：
            [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(3), (5), (7)]
        - 'first'/'open': 使用合并区间的第一个值。如：
            [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(1), (4), (6)]
        - 'max'/'high': 使用合并区间的最大值作为合并值：
            [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(3), (5), (7)]
        - 'min'/'low': 使用合并区间的最小值作为合并值：
            [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(1), (4), (6)]
        - 'avg'/'mean': 使用合并区间的平均值作为合并值：
            [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(2), (4.5), (6.5)]
        - 'sum'/'total': 使用合并区间的平均值作为合并值：
            [(1, 2, 3), (4, 5), (6, 7)] 合并后变为: [(2), (4.5), (6.5)]

        数据升频就是在已有数据中插入新的数据，插入的新数据是缺失数据，需要填充。
        例如，填充下列数据(?表示插入的数据）
            [1, 2, 3] 填充后变为: [?, 1, ?, 2, ?, 3, ?]
        缺失数据的填充方法如下:
        - 'ffill': 使用缺失数据之前的最近可用数据填充，如果没有可用数据，填充为NaN。如：
            [1, 2, 3] 填充后变为: [NaN, 1, 1, 2, 2, 3, 3]
        - 'bfill': 使用缺失数据之后的最近可用数据填充，如果没有可用数据，填充为NaN。如：
            [1, 2, 3] 填充后变为: [1, 1, 2, 2, 3, 3, NaN]
        - 'nan': 使用NaN值填充缺失数据：
            [1, 2, 3] 填充后变为: [NaN, 1, NaN, 2, NaN, 3, NaN]
        - 'zero': 使用0值填充缺失数据：
            [1, 2, 3] 填充后变为: [0, 1, 0, 2, 0, 3, 0]
    b_days_only: bool 默认True
        是否强制转换自然日频率为工作日，即：
        'D' -> 'B'
        'W' -> 'W-FRI'
        'M' -> 'BM'
    trade_time_only: bool, 默认True
        为True时 仅生成交易时间段内的数据，交易时间段的参数通过**kwargs设定
    resample_method: str
        处理数据频率更新时的方法
    return_history_panel: bool, default True
        是否返回HistoryPanel对象，如果为False，则返回一个dict，dict的key为data
    **kwargs:
        用于生成trade_time_index的参数，包括：
        include_start:   日期时间序列是否包含开始日期/时间
        include_end:     日期时间序列是否包含结束日期/时间
        start_am:        早晨交易时段的开始时间
        end_am:          早晨交易时段的结束时间
        include_start_am:早晨交易时段是否包括开始时间
        include_end_am:  早晨交易时段是否包括结束时间
        start_pm:        下午交易时段的开始时间
        end_pm:          下午交易时段的结束时间
        include_start_pm 下午交易时段是否包含开始时间
        include_end_pm   下午交易时段是否包含结束时间

    Returns
    -------
    DataFrame
    """
    if not data_types:
        return HistoryPanel()

    if data_source is None:
        raise TypeError(f'A data source should be given to acquire data from!')

    if freq is not None:
        different_freq_dtypes = [dtype for dtype in data_types if dtype.freq != freq]
        if different_freq_dtypes:
            #     warn(f'Some datatypes ({different_freq_dtypes}) do not match the frequency '
            #          f'you requested to acquire({freq}),\n'
            #          f'They will be re-sampled to match requested frequency!')
            pass

    if shares:
        # 在这里获取有share的数据，但是注意，因为这里选择将相同name但是不同资产类型的数据合并到一起
        # 但如果相同name的数据类型中有多个不同频率，则会在下面的函数中报错，此时应该检查输入的数据类型
        # 并调整其频率，确保每一个name只有一个频率的数据类型
        normal_dfs = get_history_data_from_source(
                datasource=data_source,
                htypes=data_types,
                qt_codes=list_to_str_format(shares),
                start=start,
                end=end,
                freq=freq,
                row_count=rows,
                combine_asset_types=True,
        )
        all_dfs = normal_dfs
    else:
        # 获取无share数据，且数据使用d_type.name为key分组
        reference_dfs = get_reference_data_from_source(
                datasource=data_source,
                htypes=data_types,
                start=start,
                end=end,
                freq=freq,
                row_count=rows,
                group_by_dtype_name=True,
        )
        all_dfs = reference_dfs

    # 处理所有的df，根据设定执行以下几个步骤：
    #  2，检查整行NaN值的情况，根据设定去掉或保留这些行
    #  3，如果df是一个Series，则将其转化为DataFrame
    for htyp, df in all_dfs.items():
        if isinstance(df, pd.Series):
            df = pd.DataFrame(df)
            df.columns = ['none']
        # find freq of the htyp:
        htype_freq = [d_type for d_type in data_types if d_type.name == htyp][0]
        if (not b_days_only) or (not trade_time_only) or (freq != htype_freq.freq):
            new_df = _adjust_freq(
                    df,
                    target_freq=freq,
                    method=resample_method,
                    forced_start=start,
                    forced_end=end,
                    b_days_only=b_days_only,
                    trade_time_only=trade_time_only,
                    **kwargs
            )
            df = new_df
        if rows is not None:
            assert isinstance(rows, int)
            assert rows > 0
            df = df.tail(rows)
        if drop_nan:
            df = df.dropna(how='all')
        all_dfs[htyp] = df
    if return_history_panel:
        result_hp = stack_dataframes(all_dfs, dataframe_as='htypes', htypes=all_dfs.keys(), shares=shares)
        if rows is not None:
            assert isinstance(rows, int)
            assert rows > 0
            result_hp = result_hp.tail(rows)
        return result_hp
    else:
        return all_dfs


# =================================================
# 以下是一些独立的函数, 用于检查和准备历史数据
# =================================================
def check_and_prepare_live_trade_data(op,
                                      trade_date: Union[str, pd.Timestamp],
                                      datasource: DataSource,
                                      shares: Union[str, list[str]],
                                      live_prices: Optional[pd.DataFrame] = None) -> dict[str, pd.DataFrame]:
    """ 在run_mode == 0的情况下准备相应的历史数据

    Parameters
    ----------
    op: Operator
        需要设置数据的Operator对象
    trade_date: str, pd.Timestamp
        交易日期
    datasource: DataSource
        用于下载数据的DataSource对象
    shares: str or list of str
        股票代码清单，逗号分隔字符串或字符串列表
    live_prices: pd.DataFrame, optional
        用于实盘交易的最新价格数据，如果不提供，则从datasource中下载获取

    Returns
    -------
    hist_op: HistoryPanel
        用于回测的历史数据，包含用于计算交易结果的所有历史价格种类
    hist_ref: HistoryPanel
        用于回测的历史参考数据，包含用于计算交易结果的所有历史参考数据
    """

    return check_and_prepare_backtest_data(
            op=op,
            backtest_start=trade_date,
            backtest_end=trade_date,
            shares=shares,
            datasource=datasource,
    )


def check_and_prepare_backtest_data(op,
                                    backtest_start: str,
                                    backtest_end: str,
                                    shares: Union[str, list[str]],
                                    datasource: DataSource) -> dict[str, pd.DataFrame]:
    """ 生成operator对象在回测模式下运行所需要的相关数据包，包括回测所有交易策略所需的历史数据，
    遍历Operator对象中的所有交易策略，获取所有交易策略所需要的所有历史数据。

    这个函数的要点在于解析operator对象中所有策略的数据窗口长度和数据频率，获取的数据必须可以生成足够的
    历史数据窗口以覆盖回测开始日期到回测结束日期之间的所有数据。例如：
    假设回测区间为20200101到20201231，某个策略需要20天的日线数据窗口，那么获取的历史数据起始日期
    应该至少为20191211，以保证在20200101日可以获取到20天的历史数据窗口。

    Parameters
    ----------
    op: qteasy.Operator
        交易员对象，包含投资策略信息
    backtest_start: str
        回测开始日期，格式为 'YYYYMMDD'
    backtest_end: str
        回测结束日期，格式为 'YYYYMMDD'
    shares: list of str
        回测资产池中的股票列表
    datasource: qteasy.DataSource
        数据源对象

    Returns
    -------
    hist_data_package: dict{str, pd.DataFrame}
        包含回测所需的历史数据和资金计划的字典，键为股票代码，值为对应的历史数据DataFrame
    """

    # 根据投资回测区间的开始日期及结束日期，确定需要获取的历史数据的起止日期（因为获取的数据必须覆盖交易策略的最大窗口长度）
    invest_start, invest_end = backtest_start, backtest_end

    # 获取回测所需历史数据的参数
    data_types = op.all_strategy_data_types

    if not data_types:
        return {}

    # 计算数据窗口偏移长度，这个长度需要扣除非交易日，并考虑到低频率数据的影响
    max_window_length = op.max_window_length
    time_offset_multipliers = {
        '1min':     3/240,
        '5min':     3/48,
        '15min':    2/16,
        '30min':    2/8,
        'h':        2/4,
        'd':        1.5,
        'w':        9.,
        'm':        35.,
        'q':        130.,
        'y':        360.,
    }
    max_multiplier = int(np.ceil(max(time_offset_multipliers.get(dt.freq, 1.) for dt in data_types)))
    time_window_delta = pd.Timedelta(max_window_length * max_multiplier * 2, 'D')

    # 通过get_history_data_package函数获取数据类型的原始数据
    hist_data_package = get_history_data_packages(
            data_types=data_types,
            shares=shares,
            start=regulate_date_format(pd.to_datetime(invest_start) - time_window_delta),
            end=invest_end,
            data_source=datasource,
    )

    return hist_data_package


def check_and_prepare_trade_prices(op,
                                   shares: Union[str, list[str]],
                                   price_adj: str,
                                   datasource: DataSource) -> pd.DataFrame:
    """ 基于Operator对象已经生成的group_schedule，获取指定时间区间内的交易价格数据。

    这个函数的要点在于根据operator对象中交易策略的运行时间表，获取每个运行时间点上的历史价格。如果
    operator对象的交易策略有多个运行频率，产生的运行时间表是多个频率的时间点的并集，那么获取的交易价格数据
    也必须覆盖所有这些时间点。此时应该根据运行时间表推测最高频率，获取最高频率交易价格后，再通过search_sorted
    的方式获取所有运行时间点上的交易价格。

    需要注意的是日频以及更低频率的交易价格，必须考虑到这些价格的可用时间，例如收盘价在当天15:00可用，开盘价在当天
    09:30可用。因此在获取日频或更低的交易价格时，需要将价格的时间点调整到对应的可用时间点上。

    Parameters
    ----------
    op: qteasy.Operator
        交易员对象，包含投资策略信息
    shares: list of str
        资产池中的股票列表
    price_adj: str
        价格复权类型，'none' 表示不复权，'back' 表示后复权，'forward' 表示前复权，其余值将引发错误
    datasource: qteasy.DataSource
        数据源对象
    Returns
    -------
    trade_prices: pd.DataFrame
        包含用于回测的交易价格数据
    """
    # 检查Operator对象是否已经创建了交易时间表，如果还没有创建时间表，则报错
    op_group_schedules = op.group_schedules  # 一个dict，每个group为key，一个DataFrame为value
    if not op_group_schedules:
        raise ValueError(f'Operator object has no group schedules, please run op.create_group_schedules() first!')
    if not isinstance(price_adj, str):
        raise TypeError(f'price_adj should be a string, got {type(price_adj)} instead')
    if price_adj.lower() not in ['none', 'n', 'back', 'b', 'forward', 'f', 'accu']:
        raise ValueError(f"invalid price_adj ({price_adj}), which should be anyone of ['none', 'back', 'forward']")
    if isinstance(shares, str):
        shares = str_to_list(shares, sep_char=',')

    all_run_freqs = [group.run_freq for group in op.groups.values()]
    all_run_timings = [group.run_timing for group in op.groups.values()]
    all_schedules = [sched.index for sched in op.group_schedules.values()]
    all_group_ids = [group.name for group in op.groups.values()]
    price_start = min(sched[0] for sched in all_schedules).date() - pd.Timedelta(1, 'd')  # 多取一天以防止时间点在当天的情况
    price_end = max(sched[-1] for sched in all_schedules).date() + pd.Timedelta(1, 'd')  # 多取一天以防止时间点在当天的情况

    trade_prices_per_group = {}

    for freq, timing, sched, group_id in zip(all_run_freqs, all_run_timings, all_schedules, all_group_ids):
        # 生成需要获取的数据的数据类型，以便使用get_history_panel函数获取数据
        data_types = []
        asset_types = 'E, IDX'

        fund_shares = [symbol for symbol in shares if symbol[-2:] in ['OF']]
        dtype_freq = freq

        if (timing == 'open') and freq[0].lower() in ['d', 'w', 'm', 'q', 'y']:  # 日频及更低频率的开盘价使用前一交易日的
            price_data_type_name = 'open'
            dtype_freq = 'd'
        elif (timing == 'close') and freq[0].lower() in ['d', 'w', 'm', 'q', 'y']:  # 日频及更低频率的收盘价使用当日收盘价
            price_data_type_name = 'close'
            dtype_freq = 'd'
        elif (timing not in ['open', 'close']) and freq[0].lower() in ['d', 'w', 'm', 'q']:  # 日频及更低频率的其他时间点使用分钟线价格
            price_data_type_name = 'close'
            dtype_freq = '1min'
        else:  # 其他情况使用当时的价格
            price_data_type_name = 'close'

        if fund_shares:  # 如果有场外基金，使用单位净值或复权作为交易价格
            if price_adj == 'none':
                price_data_type_name += ', unit_nav'
            elif price_adj == 'back':
                price_data_type_name += ', accum_nav'
            else:  # price_adj == 'forward'
                price_data_type_name += ', adj_nav'
            asset_types += ', FD'

        # 获取统一时间频率价格
        data_types.extend(
                infer_data_types(
                        price_data_type_name,
                        freqs=dtype_freq,
                        asset_types=asset_types,
                        adj=price_adj,
                        allow_ignore_freq=True,
                        allow_ignore_adj=True,
                )
        )

        # 生成回测交易价格的数据参数, 交易价格的复权类型根据price_adj参数确定
        trade_prices = get_history_panel(
                data_types=data_types,
                data_source=datasource,
                shares=shares,
                freq=dtype_freq,
                start=price_start,
                end=price_end,
                resample_method='ffill',
                return_history_panel=False,
        )

        # 此时有两种情况，一种是获取的价格数据包含多个数据类型（如开盘价和累计净值），另一种是只包含一个数据类型
        # 需要分别处理，如果包含多个数据类型，则需从多个DataFrame中选择合适的价格进行合并
        if len(trade_prices) == 1:
            price_data_type_name = list(trade_prices.keys())[0]
            trade_prices = trade_prices[price_data_type_name]
        elif len(trade_prices) > 1:  # 此时检查所有的数据列，删除全部为NaN的列，然后将剩下的列进行合并，并补齐缺少的列（这种情况说明有数据未读到，后面应报错）
            for dtype_name, df in trade_prices.items():
                all_nan_cols = df.columns[df.isna().all()].tolist()
                if all_nan_cols:
                    trade_prices[dtype_name] = df.drop(columns=all_nan_cols)
            # 将trade_prices中剩下的DataFrame进行合并
            trade_prices = pd.concat(list(trade_prices.values()), axis=1)
            trade_prices = trade_prices.reindex(columns=shares)
        else:
            raise ValueError(f'Unexpected number of data types ({len(trade_prices)}) in trade prices!')

        # 调整日频及更低频率数据的时间点到对应的可用时间点上
        if dtype_freq.lower() in ['d', 'w', 'm', 'q', 'y']:
            # 从schedules中获取对应的时间可用偏移量
            time_offset = sched[0] - pd.to_datetime(sched[0].date())
            trade_prices.index = trade_prices.index + pd.Timedelta(time_offset)

        trade_prices_per_group[group_id] = trade_prices

    # 当多个交易组存在时，合并各个交易组的交易价格数据，取并集
    all_trade_price_indices = pd.Index([])
    for sched in op_group_schedules.values():
        all_trade_price_indices = all_trade_price_indices.union(sched.index)
    all_trade_price_indices = pd.to_datetime(all_trade_price_indices.sort_values())

    if len(trade_prices_per_group) > 1:

        combined_trade_prices = pd.concat(trade_prices_per_group.values())
        combined_trade_prices = combined_trade_prices.groupby(level=0).first()

    else:
        combined_trade_prices = list(trade_prices_per_group.values())[0]

    # 对combined_trade_prices进行前向填充并确保包含所有交易时间点，但是不需要填充NaN值，当价格为NaN时（例如停牌），就保持为NaN值，表示该时间点价格不可用
    combined_trade_prices = combined_trade_prices.reindex(all_trade_price_indices)
    # combined_trade_prices.ffill(inplace=True)
    # 强制列对齐到完整资产池，避免 backtest_price_adj 等导致列数不足
    combined_trade_prices = combined_trade_prices.reindex(columns=shares)

    return combined_trade_prices


def check_and_prepare_evaluate_price_data(op,
                                          shares: Union[str, list[str]],
                                          datasource: DataSource,
                                          backtest_start,
                                          backtest_end,
                                          backtest_price_adj: str) -> pd.DataFrame:
    """ 基于Operator对象已经生成的group_schedule，获取指定时间区间内的日频收盘价数据，用于回测结果评价。

    本函数通过operator信息获取用于回测结果评价的参考价格数据。与用于回测交易过程的trade_prices不同，
    这里获取的价格数据以日频交易日为时间索引，时间点统一为当日收盘时间15:00:00，主要用于回测结果的
    日度估值和业绩评价，不直接参与回测交易过程。

    Parameters
    ----------
    op: qteasy.Operator
        交易员对象，包含投资策略信息
    shares: list of str
        资产池中的股票列表
    datasource: qteasy.DataSource
        数据源对象
    backtest_start:
        回测开始日期
    backtest_end:
        回测结束日期
    backtest_price_adj: str
        回测价格复权方式，必须与回测过程中使用的价格复权方式保持一致

    Returns
    -------
    evaluate_price_data: pd.DataFrame
        包含用于回测结果评价的日频收盘价数据，索引为交易日15:00:00，列为资产代码
    """

    from qteasy.trading_util import trade_time_index

    if isinstance(shares, str):
        shares = [shares]

    start_date = pd.to_datetime(backtest_start).date()
    end_date = pd.to_datetime(backtest_end).date()

    daily_index = trade_time_index(start=start_date,
                                   end=end_date,
                                   freq='d',
                                   time_offset='15:00')

    # 根据回测配置中的backtest_price_adj确定评价用价格的复权方式，确保与回测价格保持一致
    price_adj = str(backtest_price_adj).lower()
    data_types = infer_data_types(
            'close',
            freqs='d',
            asset_types='E, IDX, FD',
            adj=price_adj,
            allow_ignore_freq=True,
            allow_ignore_adj=True,
    )

    price_panel = get_history_panel(
            data_types=data_types,
            data_source=datasource,
            shares=shares,
            freq='d',
            start=start_date - pd.Timedelta(1, 'd'),
            end=end_date + pd.Timedelta(1, 'd'),
            resample_method='ffill',
            return_history_panel=False,
    )

    if not price_panel:
        raise ValueError(f'No evaluate price data found for shares {shares}!')

    if len(price_panel) == 1:
        dtype_name = list(price_panel.keys())[0]
        evaluate_prices = price_panel[dtype_name]
    else:
        for dtype_name, df in price_panel.items():
            all_nan_cols = df.columns[df.isna().all()].tolist()
            if all_nan_cols:
                price_panel[dtype_name] = df.drop(columns=all_nan_cols)
        evaluate_prices = pd.concat(list(price_panel.values()), axis=1)
        evaluate_prices = evaluate_prices.reindex(columns=shares)

    # 将日频数据时间点调整到收盘时间15:00:00，然后与交易日索引对齐
    evaluate_prices.index = pd.to_datetime(evaluate_prices.index) + pd.Timedelta('15:00:00')
    evaluate_prices = evaluate_prices.reindex(daily_index)
    evaluate_prices.ffill(inplace=True)

    return evaluate_prices


def check_and_prepare_benchmark_data(op,
                                     benchmark_symbol: str,
                                     datasource: DataSource,
                                     backtest_start,
                                     backtest_end) -> pd.DataFrame:
    """ 获取指定时间区间内的回测业绩评价基准数据

    本函数通过operator信息获取业绩评价基准数据。业绩评价基准可以是股票、指数或者基金，但是
    只能包含单一资产的价格数据。业绩评价数据格式与参考数据类型一致，可以是一个DataFrame，索引为时间戳，
    列为资产代码。也可以是一个Series，索引为时间戳，值为资产价格，如果资产类型为E或FD(场内基金），则
    价格为后复权价格。如果资产类型为IDX，则价格为指数点位，如果资产类型为场外基金OF，则价格为基金的复权净值。

    benchmark数据会被作为回测结果的业绩评价基准，在计算中需要与每日的回测结果做比较，因此
    benchmark数据的时间索引统一为回测区间内所有交易日的收盘时间点15:00:00。

    Parameters
    ----------
    op: qteasy.Operator
        交易员对象，包含投资策略信息
    benchmark_symbol: str
        业绩评价基准资产代码
    datasource: qteasy.DataSource
        数据源对象
    backtest_start:
        回测开始日期
    backtest_end:
        回测结束日期

    Returns
    -------
    benchmark_data: pd.DataFrame
        包含用于回测结果评价的基准数据
    """

    from qteasy.trading_util import trade_time_index

    if op.group_timing_table is None or op.group_timing_table.empty:
        raise ValueError(f'Operator object has no group schedules, please run op.create_group_schedules() first!')

    start_date = pd.to_datetime(backtest_start).date()
    end_date = pd.to_datetime(backtest_end).date()

    daily_index = trade_time_index(start=start_date,
                                   end=end_date,
                                   freq='d',
                                   time_offset='15:00')
    # 解析benchmark_symbol，根据资产类型确定数据类型名称
    if benchmark_symbol[-2:] in ['OF']:  # 场外基金
        benchmark_data_type_name = 'adj_nav'
        adj = 'none'
        asset_types = 'FD'
    elif benchmark_symbol[-2:] in ['SZ', 'SH', 'BJ']:  # 覆盖股票、场内基金或指数的情况
        benchmark_data_type_name = 'close'
        adj = 'back'
        asset_types = 'E, IDX, FD'
    else:
        raise ValueError(f'Unsupported benchmark symbol: {benchmark_symbol}, please use stock, index or fund code!')

    data_types = infer_data_types(benchmark_data_type_name,
                                  freqs='d',
                                  asset_types=asset_types,
                                  adj=adj,
                                  allow_ignore_freq=True,
                                  allow_ignore_adj=True)

    benchmark_data = get_history_panel(
            data_types=data_types,
            shares=[benchmark_symbol],
            freq='d',
            start=start_date - pd.Timedelta(1, 'd'),
            end=end_date + pd.Timedelta(1, 'd'),
            data_source=datasource,
            resample_method='ffill',
            return_history_panel=False,
    )

    # benchmark_data中可能存在空DataFrame，逐个检查后将空DataFrame删除，提取非空的DataFrame
    dtype_name_to_drop = [dtype_name for dtype_name, df in benchmark_data.items() if df.empty]
    for dtype_name in dtype_name_to_drop:
        benchmark_data.pop(dtype_name)

    if not benchmark_data:
        raise ValueError(f'No benchmark data found for symbol {benchmark_symbol}!')

    benchmark_data = benchmark_data[list(benchmark_data.keys())[0]]  # 提取DataFrame

    # 将日频数据时间点调整到收盘时间15:00:00，然后与交易日索引对齐
    benchmark_data.index = pd.to_datetime(benchmark_data.index) + pd.Timedelta('15:00:00')
    benchmark_data = benchmark_data.reindex(daily_index)
    benchmark_data.ffill(inplace=True)

    return benchmark_data
