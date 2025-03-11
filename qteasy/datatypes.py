# coding=utf-8
# ======================================
# File:     datatypes.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2024-09-20
# Desc:
#   Definition of DataType class,
# representing historical data types
# that can be used by qteasy, and the
# collection of all built-in data types.
# ======================================


import pandas as pd
from functools import lru_cache
from warnings import warn
from math import ceil

from .utilfuncs import (
    AVAILABLE_ASSET_TYPES,
    str_to_list,
    _lev_ratio,
    _partial_lev_ratio,
    _wildcard_match,
)


def define(name, freq, asset_type, description, acquisition_type, **kwargs):
    """
    Define a new data type and add it to the USER_DATA_TYPE_MAP.

    Parameters
    ----------
    name: str
    freq: str
    asset_type: str
    description: str
    acquisition_type: str
    kwargs: dict
    """
    global DATA_TYPE_MAP
    global DATA_TYPE_MAP_COLUMNS
    global DATA_TYPE_MAP_INDEX_NAMES

    key = (name, freq, asset_type)
    if key in DATA_TYPE_MAP:
        raise ValueError(f'DataType {key} already exists in DATA_TYPE_MAP.')
    DATA_TYPE_MAP[key] = [description, acquisition_type, kwargs]
    DATA_TYPE_MAP_INDEX_NAMES = list(set(DATA_TYPE_MAP_INDEX_NAMES) | set(key))
    _get_built_in_data_type_map()


def get_dtype_map(include_user_defined=False, refresh_cache=False) -> pd.DataFrame:
    """ 获取所有内置以及用户定义数据类型的清单

    Parameters
    ----------
    include_user_defined: bool, default False
        是否包含用户定义的数据类型, 如果为True, 则返回所有数据类型，包括内置和用户定义的
    refresh_cache: bool, default False
        是否刷新用户定义的数据类型缓存，如果为True，清除缓存并重新获取用户定义的数据类型

    Returns
    -------
    dtype_map: pd.DataFrame

    """
    if refresh_cache:
        _get_user_data_type_map.cache_clear()
    built_in_map = _get_built_in_data_type_map()
    if include_user_defined:
        user_map = _get_user_data_type_map()
        return pd.concat([built_in_map, user_map])

    return built_in_map


def infer_data_types(names, freqs, asset_types, adj=None,
                     force_match_freq=False,
                     force_match_asset_type=False) -> list:
    """ 根据输入的名称、频率和资产类型推断数据类型，如果某个name找不到匹配的freq或asset_type，则根据
    force_match_freq / force_match_asset_type的值确定如何操作：

    如果force_match_freq为True，则强制性为无法匹配的names匹配一个存在的DataType
    否则忽略找不到freq的name
    如果force_match_asset_type为True，则强制性为无法匹配的names匹配一个存在的
    DataType，否则忽略无法匹配asset_type的name

    Parameters
    ----------
    names: str or [str]
        一个包含所有需要的数据类型名称的列表，也可以以逗号分隔字符串形式给出
    freqs: str or [str]
        一个包含可能的freq的列表，也可以以逗号分隔字符串形式给出
    asset_types: str or [str]
        一个包含可能的资产类型的列表，也可以以逗号分隔字符串形式给出
    adj: str, optinal, deprecated
        价格调整因子，如果给出，强制性调整价格类型
    force_match_freq: bool, optional, default False
        是否强制匹配freq，如果为True，则为某些无法找到匹配freq的数据类型强制匹配一个合法的freq
    force_match_asset_type: bool, optional, default False
        是否强制匹配资产类型，如果为True，则为某些无法找到匹配的资产类型的数据类型强制匹配一个合法的资产类型

    Return
    ------
    data_types: list of DataTypes
    """

    if isinstance(names, str):
        names = str_to_list(names)
    if not isinstance(names, list):
        err = TypeError(f'names should be a string of list of strings, but got {type(names)}')
        raise err

    if isinstance(freqs, str):
        freqs = str_to_list(freqs)
    if not isinstance(freqs, list):
        err = TypeError(f'freqs should be a string or a list of strings, but got {type(freqs)}')
        raise err

    if isinstance(asset_types, str):
        asset_types = str_to_list(asset_types)
    if not isinstance(asset_types, list):
        err = TypeError(f'asset_types should be a string or a list of strings, but got {type(asset_types)}')
        raise err
    if 'any' in asset_types:
        asset_types = AVAILABLE_ASSET_TYPES

    if adj is not None:
        if not isinstance(adj, str):
            err = TypeError(f'adj should be a string, but got {type(adj)}')
            raise err
        adj = adj.lower()
        price_types = ['close', 'open', 'high', 'low']
        if adj in ['b', 'back']:
            names = [f'{n}|b' if n in price_types else n for n in names]
            msg = f'Using parameter "adj" for price adjustment is deprecated, please use data types like ' \
                  f'"close|b" instead of "adj=\'b\'" in the future.'
            warn(msg, DeprecationWarning)
        if adj in ['f', 'fw', 'forward']:
            names = [f'{n}|f' if n in price_types else n for n in names]
            msg = f'Using parameter "adj" for price adjustment is deprecated, please use data types like ' \
                  f'"close|f" instead of "adj=\'f\'" in the future.'
            warn(msg, DeprecationWarning)

    # TODO: 需要优化：将force_match_freq / force_match_asset_type作为DataType的__init__()参数，那么这里就可以
    #  使用itertools.product以及列表推导式来简化代码了。
    data_types = []
    for n in names:
        for f in freqs:
            for at in asset_types:
                try:
                    data_types.append(DataType(name=n, freq=f, asset_type=at))
                except ValueError:
                    if force_match_freq and force_match_asset_type:
                        try:
                            data_types.append(DataType(name=n))
                        except ValueError:
                            pass
                    elif force_match_freq:
                        try:
                            data_types.append(DataType(name=n, asset_type=at))
                        except ValueError:
                            pass
                    elif force_match_asset_type:
                        try:
                            data_types.append(DataType(name=n, freq=f))
                        except ValueError:
                            pass
                    else:
                        pass
    # remove all duplicated data types:
    data_types = list(set(data_types))

    return data_types


@lru_cache(maxsize=1)
def _get_built_in_data_type_map() -> pd.DataFrame:
    """ 获取所有内置数据类型的清单

    Returns
    -------
    dtype_map: pd.DataFrame
    """
    type_map = pd.DataFrame(DATA_TYPE_MAP).T
    type_map.columns = DATA_TYPE_MAP_COLUMNS
    type_map.index.names = DATA_TYPE_MAP_INDEX_NAMES

    return type_map


@lru_cache(maxsize=1)
def _get_user_data_type_map() -> pd.DataFrame:
    """get a DataFrame of USER_DATA_TYPE_MAP for checking."""

    if not USER_DATA_TYPE_MAP:
        return pd.DataFrame()

    type_map = pd.DataFrame(USER_DATA_TYPE_MAP).T
    type_map.columns = DATA_TYPE_MAP_COLUMNS
    type_map.index.names = DATA_TYPE_MAP_INDEX_NAMES

    return type_map


def _parse_name_and_params(name: str) -> tuple:
    """parse the name string into name, parameters, unsymbolizer in a form:

    name:params-unsymbolizer

    Parameters
    ----------
    name: str
        the name string

    Returns
    -------
    tuple
        search_name: str
            the search_name of the data type, replacing the parameters with '%' if there are any
        params: str
            the parameters of the data type
        unsymbolizer: str
            the column name used to unsymbolize historical data (convert hist data to reference data)
    """
    if '-' in name:
        name, unsymbolizer = name.split('-')
    else:
        unsymbolizer = None

    if '|' in name:
        search_name, params = name.split('|')
        search_name = search_name + '|%'
        return search_name, params, unsymbolizer
    else:
        return name, None, unsymbolizer


def _parse_built_in_type_id(name: str) -> tuple:
    """ 根据客户输入的名称在内置数据类型中查找匹配的数据类型
    如果正确匹配，返回数据类型以及可用的内置频率和资产类型，如果匹配不到，返回空tuple

    Parameters
    ----------
    name: str
        数据类型的名称

    Returns
    -------
    tuple
        built_in_freqs: tuple
            数据的频率
        built_in_asset_types: tuple
            数据的资产类型
    """
    data_map = _get_built_in_data_type_map()

    matched_types = data_map.loc[(name, slice(None), slice(None))]

    if matched_types.empty:
        return tuple(), tuple()
    else:
        return matched_types.index.get_level_values('freq').unique(), \
            matched_types.index.get_level_values('asset_type').unique()


def _parse_user_defined_type_id(name: str) -> tuple:
    """ 根据客户输入的名称在用户自定义数据类型中查找匹配的数据类型
    如果正确匹配，返回数据类型以及可用的内置频率和资产类型，如果匹配不到，返回空tuple

    Parameters
    ----------
    name: str
        数据类型的名称

    Returns
    -------
    tuple
        user_defined_freqs: tuple
            数据的频率
        user_defined_asset_types: tuple
            数据的资产类型
    """
    type_map = _get_user_data_type_map()

    if type_map.empty:
        return tuple(), tuple()

    matched_types = type_map.loc[(name, slice(None), slice(None))]

    if matched_types.empty:
        return tuple(), tuple()
    else:
        return matched_types.index.get_level_values('freq').unique(), \
            matched_types.index.get_level_values('asset_type').unique()


def _parse_aquisition_parameters(search_name, name_par, freq, asset_type, built_in_tables=True) -> tuple:
    """ 根据正确的search_name， name_par， freq和asset_type查找数据类型的获取参数
    如果存在name_par，将name_par解析为参数的一部分，放入获取参数中

    Parameters
    ----------
    search_name: str
        数据类型的名称
    name_par: str
        数据类型的参数
    freq: str
        数据的频率
    asset_type: str
        数据的资产类型
    built_in_tables: bool, default True
        是否查找内置数据类型表，如果为False，查找用户自定义数据类型表

    Returns
    -------
    tuple
        description: str
            数据类型的描述
        acquisition_type: str
            数据获取方式
        kwargs: dict
            获取数据的参数
    """
    if built_in_tables:
        data_map = DATA_TYPE_MAP
    else:
        data_map = USER_DATA_TYPE_MAP

    key = (search_name, freq, asset_type)
    if key not in data_map:
        raise ValueError(f'DataType {search_name}({asset_type})@{freq} not found in DATA_TYPE_MAP.')

    description, acquisition_type, kwargs = data_map[key]

    kwargs=kwargs.copy()  # 因为dict是immutable变量，如果直接引用，会导致同样的dtype引用同一个kwargs对象

    # 如果name_par不为空，解析name_par并加入description或者kwargs中
    if name_par is not None:
        # 解析description中的参数
        if '%' in description:
            description = description.replace('%', name_par)
        # 解析kwargs中的参数
        for k, v in kwargs.items():
            if '%' in v and isinstance(v, str):
                kwargs[k] = v.replace('%', name_par)
            if '%' in v and isinstance(v, list):
                kwargs[k] = [i.replace('%', name_par) for i in v]

    return description, acquisition_type, kwargs


class DataType:
    """
    DataType class, 代表qteasy可以使用的历史数据类型。

    qteasy的每一个历史数据类型由三组参数定义：
    - name: 数据类型的名称
    - freq: 数据的频率
    - asset_type: 数据的资产类型
    以上三组参数唯一地定义了一个数据类型。qteasy定义了大量常用的数据类型，用户可以直接使用这些数据类型，也可以根据自己的需求定义新的数据类型。
    如果用户自定义新的数据类型，三组参数不能与已有的数据类型重复。

    用户在自定义数据类型时，需要指定数据类型的描述、数据获取方式、以及获取数据的参数。详情参见qteasy文档。

    一旦定义了数据类型，该数据类型就可以被qteasy用于历史数据的下载、处理、分析，也可以直接被用于交易策略的开发。

    需要获取数据时，通过DataType.get_data_from_source()方法获取。

    """

    aquisition_types = [
        'basics',
        # 直接获取数据表中与资产有关的一个数据字段，该数据与日期无关，输出index为qt_code的Series
        # {'table_name': table, 'column': column}
        'reference',
        # 直接获取日期表中与资产无关的数据字段，该数据与资产无关，输出index为date的Series
        # {'table_name': table, 'column': column}
        'selection',
        # 数据筛选型。从basics表中筛选出数据并输出，如股票代码、行业分类等。输出index为qt_code的Series
        # {'table_name': table, 'column': output_col, 'sel_by': sel_column, 'keys': keys}
        'direct',
        # 获取时间数据表中部分资产有关一个确定时间段的数据字段，并筛选位于开始/结束日期之间的数据，
        # 输出index为datetime，column为qt_code的DataFrame
        # {'table_name': table, 'column': column}
        'adjustment',
        # 数据修正型。从一张表中直读数据A，另一张表直读数据B，并用B修正后输出，如复权价格
        # {'table_name': table, 'column': column, 'adj_table': table, 'adj_column': column, 'adj_type': type}
        'relations',
        # 数据关联型。从两张表中读取数据A与B，并输出它们之间的某种关系，如eq/ne/gt/or/nor等等
        'operation',  # 数据计算型。从两张表中读取数据A与B，并输出他们之间的计算结果，如+/-/*//
        'event_status',
        # 事件状态型。从时间数据表中查询事件的发生日期并在事件影响区间内填充不同状态的，如停牌，改名等
        # 要求数据表的PK类型为code-date型（T4型）
        # 输出index为datetime，column为qt_code的DataFrame
        # {'table_name': table, 'column': column}
        'event_multi_stat',
        # 多事件状态型。从表中查询多个事件的发生日期并在事件影响区间内填充多个不同的状态，如管理层名单等
        # 数据表的PK类型必须为date-code-other类型（T5类型），其中other列被用于筛选同一时间内的不同状态
        # 此处一般表示不同的人员姓名
        # {'table_name': table, 'column': column, 'id_index': id, 'start_col': start, 'end_col': end}
        'event_signal',
        # 事件信号型。从表中查询事件的发生日期并在事件发生时产生信号的，如涨跌停，上板上榜等
        # 要求数据表的PK类型为code-date型（T4型）
        # 输出index为datetime，column为qt_code的DataFrame
        # {'table_name': table, 'column': output_col}
        'selected_events',
        # 筛选事件型数据，本质上与事件信号型数据类似，同样筛选日期数据表中的事件是否发生。
        # 但是要求数据表的PK类型为code-date-other型（T5型），要求额外给出信息用于筛选不同other字段的值
        # 输出index为datetime，column为qt_code的DataFrame
        # {'table_name': table, 'column': output_col, 'sel_by': column, 'key': key}
        'composition',
        # 成份数据。从成份表中筛选出来数据并行列转换，该成分表与时间相关，如指数成分股
        # {'table_name': 'index_weight', 'column': 'weight', 'comp_column': 'index_code', 'index': '%'}],
        'category',  # 成分分类数据，输出某个股票属于哪一个成分，该成分是静态的与时间无关，如行业分类、地域分类等
        # 以下为一些特殊类型，由特殊的过程实现
        'complex',  # 单时刻复合类型。查找一个时间点上可用的多种数据并组合输出，如个股某时刻的财务报表
    ]

    def __init__(self, *, name, freq=None, asset_type=None):
        """
        根据用户输入的名称或完整参数实例化一个DataType对象。

        如果用户输入完整的三合一参数，将检查该类型是否已经存在，如果存在，则生成该类型的实例，否则抛出异常。
        如果用户仅输入名称，将尝试从DATA_TYPE_MAP中匹配相应的参数，如果找到唯一匹配，则生成该类型的实例，如果找到多组匹配，
        则使用第一个匹配的类型生成DataType对象，如果找不到匹配，则报错。

        用户自定义的数据类型也在上述查找匹配范围内。而用户需要通过datatypes.define()方法将自定义的数据类型添加到DATA_TYPE_MAP中。

        Parameters
        ----------
        name: str
            数据类型的名称
        freq: str, optional
            数据的频率: d(日), w(周), m(月), q(季), y(年), 1/5/15/30min, h
            如果给出此参数，必须匹配某一个内置数据类型的频率
            如果不给出此参数，将使用内置数据类型中的第一个频率
        asset_type: str
            数据的资产类型: E(股票), IDX(指数), FD(基金), FT(期货), OPT(期权)
            如果给出此参数，必须匹配某一个内置数据类型的资产类型
            如果不给出此参数，将使用内置数据类型中的第一个资产类型

        Raises
        ------
        ValueError
            如果用户输入的参数不在DATA_TYPE_MAP中
            ValueError: DataType {name}({asset_type})@{freq} not found in DATA_TYPE_MAP.
        ValueError NotImplemented!
            如果用户输入的参数不完整，在DATA_TYPE_MAP中无法匹配到唯一的数据类型
            ValueError: Input matches multiple data types in DATA_TYPE_MAP, specify your input: {types}?.
        """
        if not isinstance(name, str):
            raise TypeError(f'name must be a string, got {type(name)}')

        search_name, name_pars, unsymbolizer = _parse_name_and_params(name)

        # 根据用户输入的name查找所有匹配的频率和资产类型
        built_in_freqs, built_in_asset_types = _parse_built_in_type_id(search_name)
        user_defined_freqs, user_defined_asset_types = _parse_user_defined_type_id(search_name)

        # 如果用户同时输入了freq和asset_type，确认用户输入是否在匹配的范围内
        # 如果用户输入不在匹配范围内，抛出异常，如果在匹配范围内，使用用户输入作为default值
        if (freq is None) and len(built_in_freqs) > 0:
            default_freq = built_in_freqs[0]
        elif (freq is None) and len(user_defined_freqs) > 0:
            default_freq = user_defined_freqs[0]
        elif (freq in built_in_freqs) or (freq in user_defined_freqs):
            default_freq = freq
        else:
            raise ValueError(f'DataType {name}({asset_type})@{freq} not found in DATA_TYPE_MAP.')

        if (asset_type is None) and len(built_in_asset_types) > 0:
            default_asset_type = built_in_asset_types[0]
        elif (asset_type is None) and len(user_defined_asset_types) > 0:
            default_asset_type = user_defined_asset_types[0]
        elif (asset_type in built_in_asset_types) or (asset_type in user_defined_asset_types):
            default_asset_type = asset_type
        else:
            raise ValueError(f'DataType {name}({asset_type})@{freq} not found in DATA_TYPE_MAP.')

        # 已经确认了name，freq和asset_type的合法性，现在可以生成DataType实例
        # 根据search_name，freq和asset_type查找description以及acquisition_type等信息
        description, acquisition_type, kwargs = _parse_aquisition_parameters(
                search_name=search_name,
                name_par=name_pars,
                freq=default_freq,
                asset_type=default_asset_type,
                built_in_tables=built_in_freqs is not None,
        )

        # if default_asset_type.lower() == 'none':
        #     default_asset_type = None
        #
        # if default_freq.lower() == 'none':
        #     default_freq = None

        self._name = name
        self._name_pars = None
        self._default_freq = default_freq
        self._default_asset_type = default_asset_type
        self._all_built_in_freqs = None  # TODO: are these properties still needed?
        self._all_built_in_asset_types = None
        self._all_user_defined_freqs = None
        self._all_user_defined_asset_types = None
        self._description = description
        self._acquisition_type = acquisition_type
        self._unsymbolizer = unsymbolizer

        self._kwargs = kwargs

    @property
    def name(self):
        return self._name

    @property
    def id(self):
        return f'{self._name}({self._default_asset_type})'

    @property
    def freq(self):
        return self._default_freq

    @property
    def asset_type(self):
        return self._default_asset_type

    @property
    def unsymbolizer(self):
        return self._unsymbolizer

    @property
    def available_freqs(self):
        return self._all_built_in_asset_types.extend(self._all_user_defined_freqs)

    @property
    def available_asset_types(self):
        return self._all_built_in_asset_types.extend(self._all_user_defined_asset_types)

    @property
    def description(self):
        return self._description

    @property
    def acquisition_type(self):
        return self._acquisition_type

    @property
    def kwargs(self):
        return self._kwargs

    def __repr__(self):
        return f'DataType(\'{self.name}\', \'{self.freq}\', \'{self.asset_type}\')'

    def __str__(self):
        return f'{self.name}({self.asset_type})@{self.freq}'

    def __eq__(self, other):
        """ two data types are considered equal if their names, freqs and asset types are the same """
        if not isinstance(other, DataType):
            return False
        return self.name == other.name and self.freq == other.freq and self.asset_type == other.asset_type

    def __hash__(self):
        """ hash of data type is equal to hash of datatype.__str__()"""
        return hash(str(self))

    # 真正的顶层数据获取API接口函数
    def get_data_from_source(
            self, datasource, *,
            symbols: str = None,
            starts: str = None,
            ends: str = None,
    ):
        """ Datatype类从DataSource类获取数据的方法，根据数据类型的获取方式，调用相应的方法获取数据并输出

        如果symbols为None，则输出为un-symbolised数据，否则输出为symbolised数据

        Parameters
        ----------
        datasource: DataSource
            数据类型对象
        symbols: str
            股票代码列表，一个逗号分隔的字符串，如'000001.SZ,000002.SZ'
        starts: str
            开始日期, YYYYMMDD格式
        ends: str
            结束日期, YYYYMMDD格式

        """

        acquisition_type = self.acquisition_type

        if acquisition_type == 'basics':
            acquired_data = self._get_basics(datasource, symbols=symbols)
        elif acquisition_type == 'reference':
            acquired_data = self._get_reference(datasource, symbols=None, starts=starts, ends=ends)
        elif acquisition_type == 'selection':
            acquired_data = self._get_selection(datasource, symbols=symbols, starts=starts, ends=ends)
        elif acquisition_type == 'direct':
            acquired_data = self._get_direct(datasource, symbols=symbols, starts=starts, ends=ends)
        elif acquisition_type == 'adjustment':
            acquired_data = self._get_adjustment(datasource, symbols=symbols, starts=starts, ends=ends)
        elif acquisition_type == 'operation':
            acquired_data = self._get_operation(datasource, symbols=symbols, starts=starts, ends=ends)
        elif acquisition_type == 'relations':
            acquired_data = self._get_relations(datasource, symbols=symbols, starts=starts, ends=ends)
        elif acquisition_type == 'event_multi_stat':
            acquired_data = self._get_event_multi_stat(datasource, symbols=symbols, starts=starts, ends=ends)
        elif acquisition_type == 'event_status':
            acquired_data = self._get_event_status(datasource, symbols=symbols, starts=starts, ends=ends)
        elif acquisition_type == 'event_signal':
            acquired_data = self._get_event_signal(datasource, symbols=symbols, starts=starts, ends=ends)
        elif acquisition_type == 'selected_events':
            acquired_data = self._get_selected_events(datasource, symbols=symbols, starts=starts, ends=ends)
        elif acquisition_type == 'composition':
            acquired_data = self._get_composition(datasource, symbols=symbols, starts=starts, ends=ends)
        elif acquisition_type == 'category':
            acquired_data = self._get_category(datasource, symbols=symbols)
        elif acquisition_type == 'complex':
            acquired_data = self._get_complex(datasource, symbols=symbols, date=starts)
        else:
            raise ValueError(f'Unknown acquisition type: {acquisition_type}')
        # basic data will be returned directly
        if acquisition_type == 'basics':
            return acquired_data

        if acquired_data.empty:
            return acquired_data

        if self.unsymbolizer is not None:
            return self._unsymbolised(acquired_data, self.unsymbolizer)

        return self._symbolised(acquired_data)

    def _get_basics(self, datasource, *, symbols=None, starts=None, ends=None) -> pd.Series:
        """基本数据的获取方法：
        从table_name表中选出column列的数据并输出。
        如果给出symbols则筛选出symbols的数据，否则输出全部数据。
        start和end无效，只是为了保持接口一致性。

        Parameters
        ----------
        datasource: DataSource
            数据源对象
        symbols: str
            股票代码列表，一个逗号分隔的字符串，如'000001.SZ,000002.SZ'

        Returns
        -------
        pd.Series
        """

        # try to get arguments from kwargs
        table_name = self.kwargs.get('table_name')
        column = self.kwargs.get('column')

        if table_name is None or column is None:
            raise ValueError('table_name and column must be provided for basics data type')

        acquired_data = datasource.read_cached_table_data(table_name, shares=symbols, start=starts, end=ends)

        if acquired_data.empty:
            return pd.Series()

        if column not in acquired_data.columns:
            raise KeyError(f'column {column} not in table data: {acquired_data.columns}')

        return acquired_data[column]

    def _get_reference(self, datasource, *, symbols=None, starts=None, ends=None) -> pd.Series:
        """

        :param datasource:
        :param symbols:
        :param starts:
        :param ends:
        :return:
        """
        table_name = self.kwargs.get('table_name')

        acquired_data = self._get_basics(datasource, symbols=symbols, starts=starts, ends=ends)

        if acquired_data.empty:
            return acquired_data

        # if data index type is Month/Quater (table names is some special names), then they
        # should be converted to datetime:
        if (table_name in ['cn_gdp']) and isinstance(acquired_data.index[0], str):  # converting quarter to date
            from .data_channels import _convert_quarter_str_to_absolute_quarter
            from .data_channels import _convert_absolute_quarter_to_quarter_str
            new_index = [_convert_quarter_str_to_absolute_quarter(idx) + 1 for idx in acquired_data.index]
            new_index = [_convert_absolute_quarter_to_quarter_str(idx) for idx in new_index]
            new_index = pd.Index((pd.to_datetime(idx) for idx in new_index)) - pd.Timedelta(1, 'd')
            acquired_data.index = new_index

        elif (table_name in ['cn_cpi', 'cn_ppi', 'cn_money', 'cn_sf', 'cn_pmi']) and \
                isinstance(acquired_data.index[0], str):
            from .data_channels import _convert_month_str_to_absolute_month
            from .data_channels import _convert_absolute_month_to_month_str
            new_index = [_convert_month_str_to_absolute_month(idx) + 1 for idx in acquired_data.index]
            new_index = [_convert_absolute_month_to_month_str(idx) + '01' for idx in new_index]
            new_index = pd.Index((pd.to_datetime(idx) for idx in new_index)) - pd.Timedelta(1, 'd')
            acquired_data.index = new_index

        return acquired_data

    def _get_selection(self, datasource, *, symbols=None, starts=None, ends=None) -> pd.Series:
        """筛选型的数据获取方法，可以用于筛选基础类型数据，也可以筛选历史数据和参考数据：
        从table_name表中筛选出sel_by=keys的数据并输出column列数据

        如果筛选基础类型数据：
        可以通过给出symbols筛选出symbols的数据，否则输出全部数据。
        如果筛选历史数据或参考数据：
        可以通过给出starts/ends筛选出一个历史区间的数据

        Parameters
        ----------
        datasource: DataSource
            数据源对象
        symbols: str
            股票代码列表，一个逗号分隔的字符串，如'000001.SZ,000002.SZ'
        starts: str
            开始日期，YYYYMMDD格式
        ends: str
            结束日期，YYYYMMDD格式

        Returns
        -------
        pd.Series
        """

        # try to get arguments from kwargs
        table_name = self.kwargs.get('table_name')
        column = self.kwargs.get('column')
        sel_by = self.kwargs.get('sel_by')
        keys = self.kwargs.get('keys')

        if table_name is None or column is None or sel_by is None or keys is None:
            raise ValueError('table_name, column, sel_by and keys must be provided for selection data type')

        acquired_data = datasource.read_cached_table_data(table_name, shares=symbols, start=starts, end=ends)

        if acquired_data.empty:
            return pd.Series()

        if sel_by in acquired_data.columns:
            selected_data = acquired_data[acquired_data[sel_by].isin(keys)]
        elif sel_by in acquired_data.index.names:
            index_name_count = len(acquired_data.index.names)
            index_pos = acquired_data.index.names.index(sel_by)
            slicers = [slice(None)] * index_name_count
            slicers[index_pos] = keys
            slicers = tuple(slicers)
            selected_data = acquired_data.loc[slicers, :]
            selected_data.index = selected_data.index.droplevel(sel_by)

        else:
            # raise error if sel_by is not in table data
            raise KeyError(f'sel_by {sel_by} not in table data: {acquired_data.columns}')

        return selected_data[column]

    def _get_direct(self, datasource, *, symbols, starts, ends) -> pd.DataFrame:
        """直读从时间序列数据表中读取数据
        从table_name表中选出column列的数据并输出。
        必须给出symbols数据，以输出index为datetime，column为symbols的DataFrame
        必须给出start和end以筛选出在start和end之间的数据
        """
        if starts is None or ends is None:
            raise ValueError('start and end must be provided for direct data type')

        data_series = self._get_basics(datasource, symbols=symbols, starts=starts, ends=ends)

        if data_series.empty:
            return pd.DataFrame()

        unstacked_df = data_series.unstack(level=0)

        return unstacked_df

    def _get_adjustment(self, datasource, *, symbols, starts, ends) -> pd.DataFrame:
        """修正型的数据获取方法
        从table_name表中选出column列的数据，并从adj_table表中选出adj_column列数据，根据adj_type调整后输出
        必须给出symbols数据，以输出index为datetime，column为symbols的DataFrame
        必须给出start和end以筛选出在start和end之间的数据
        """
        table_name = self.kwargs.get('table_name')
        column = self.kwargs.get('column')
        adj_table = self.kwargs.get('adj_table')
        adj_column = self.kwargs.get('adj_column')
        adj_type = self.kwargs.get('adj_type')

        if table_name is None or column is None or adj_table is None or adj_column is None:
            raise ValueError(
                    'table_name_A, column_A, table_name_B and column_B must be provided for adjustment data type')

        acquired_data = datasource.read_cached_table_data(table_name, shares=symbols, start=starts, end=ends)

        if acquired_data.empty:
            return pd.DataFrame()
        acquired_data = acquired_data[column].unstack(level='ts_code')

        adj_factors = datasource.read_cached_table_data(adj_table, shares=symbols, start=starts, end=ends)

        if adj_factors.empty:
            return pd.DataFrame()
        adj_factors = adj_factors[adj_column].unstack(level='ts_code')

        adj_factors = adj_factors.reindex(acquired_data.index, method='ffill')

        back_adj_data = acquired_data * adj_factors

        if adj_type in ['backward', 'b', 'bk']:
            return back_adj_data.round(2)

        fwd_adj_data = back_adj_data / adj_factors.iloc[-1]
        return fwd_adj_data.round(2)

    def _get_operation(self, datasource, *, symbols=None, starts=None, ends=None) -> pd.DataFrame:
        """数据操作型的数据获取方法"""
        raise NotImplementedError

    def _get_relations(self, datasource, *, symbols=None, starts=None, ends=None) -> pd.DataFrame:
        """数据关联型的数据获取方法"""
        raise NotImplementedError

    def _get_event_multi_stat(self, datasource, *, symbols=None, starts=None, ends=None) -> pd.DataFrame:
        """事件多状态型的数据获取方法

        Parameters
        ----------
        symbols: str
            股票代码列表，一个逗号分隔的字符串，如'000001.SZ,000002.SZ'
        starts: str
            开始日期，YYYYMMDD格式
        ends: str
            结束日期，YYYYMMDD格式

        Returns
        -------
        DataFrame
        """

        from .database import (
            get_built_in_table_schema,
        )

        if symbols is None:
            raise ValueError('symbols must be provided for event status data type')
        if starts is None or ends is None:
            raise ValueError('start and end must be provided for event status data type')

        table_name = self.kwargs.get('table_name')
        column = self.kwargs.get('column')
        id_index = self.kwargs.get('id_index')
        start_col = self.kwargs.get('start_col')
        end_col = self.kwargs.get('end_col')

        if table_name is None or column is None:
            raise ValueError('table_name and column must be provided for basics data type')

        acquired_data = datasource.read_cached_table_data(
                table_name,
                shares=symbols,
                start=starts,
                end=ends,
                primary_key_in_index=False,
        )

        columns, dtypes, primary_keys, pk_dtypes = get_built_in_table_schema(table_name, with_primary_keys=True)

        if id_index != column:
            # 此时需要将id_index和column合并为一个新的index
            cols_to_keep = [start_col, end_col, column]
            cols_to_keep.extend(primary_keys)
            acquired_data = acquired_data[cols_to_keep]
            # create id_index and column pairs
            combined_data = acquired_data[id_index] + '-' + acquired_data[column].astype(str)
            acquired_data.loc[:, column] = combined_data
        else:
            # 此时id_index就是column，直接使用，不需要合并
            cols_to_keep = [start_col, end_col]
            cols_to_keep.extend(primary_keys)
            acquired_data = acquired_data[cols_to_keep]

        if acquired_data.empty:
            return pd.DataFrame()

        # make group and combine events on the same date for the same symbol
        grouped = acquired_data.groupby(['ts_code', start_col])
        events = grouped[column].apply(lambda x: list(x))
        events = events.unstack(level='ts_code')

        # expand the index to include starts and ends dates
        events = _expand_df_index(events, starts, ends).ffill()

        # filter out events that are not in the date range
        date_mask = (events.index >= starts) & (events.index <= ends)
        events = events.loc[date_mask]

        return events

    def _get_event_status(self, datasource, *, symbols=None, starts=None, ends=None) -> pd.DataFrame:
        """事件状态型的数据获取方法

        Parameters
        ----------
        symbols: str
            股票代码列表，一个逗号分隔的字符串，如'000001.SZ,000002.SZ'
        starts: str
            开始日期，YYYYMMDD格式
        ends: str
            结束日期，YYYYMMDD格式

        Returns
        -------
        DataFrame
        """

        if symbols is None:
            raise ValueError('symbols must be provided for event status data type')
        if starts is None or ends is None:
            raise ValueError('start and end must be provided for event status data type')

        # acquire data without time thus status can be ffilled from previous dates
        data_series = self._get_basics(datasource, symbols=symbols, starts=starts, ends=ends)

        if data_series.empty:
            return pd.DataFrame()

        data_df = data_series.unstack(level='ts_code')

        try:
            # expand the index to include starts and ends dates
            status = _expand_df_index(data_df, starts, ends).ffill()
        except:
            pass

        # filter out events that are not in the date range
        date_mask = (status.index >= starts) & (status.index <= ends)
        status = status.loc[date_mask]

        return status

    def _get_event_signal(self, datasource, *, symbols=None, starts=None, ends=None) -> pd.DataFrame:
        """事件信号型的数据获取方法

        Parameters
        ----------
        symbols: str
            股票代码列表，一个逗号分隔的字符串，如'000001.SZ,000002.SZ'
        starts: str
            开始日期，YYYYMMDD格式
        ends: str
            结束日期，YYYYMMDD格式

        Returns
        -------
        DataFrame
        """

        if symbols is None:
            raise ValueError('symbols must be provided for event status data type')
        if starts is None or ends is None:
            raise ValueError('start and end must be provided for event status data type')

        data_series = self._get_basics(datasource, symbols=symbols, starts=starts, ends=ends)

        if data_series.empty:
            return pd.DataFrame()

        signals = data_series.unstack(level='ts_code')

        # if index is a MultiIndex with multiple datetime levels, use the last level as the date index
        if isinstance(signals.index, pd.MultiIndex):
            signals.index = signals.index.get_level_values(-1)

        return signals

    def _get_selected_events(self, datasource, *, symbols=None, starts=None, ends=None) -> pd.DataFrame:
        """

        Parameters
        ----------

        Returns
        -------
        pd.DataFrame
        """

        sel_by = self.kwargs.get('sel_by')
        key = self.kwargs.get('key')

        if symbols is None:
            raise ValueError('symbols must be provided for event status data type')
        if starts is None or ends is None:
            raise ValueError('start and end must be provided for event status data type')

        data_series = self._get_basics(datasource, symbols=symbols, starts=starts, ends=ends)

        if data_series.empty:
            return pd.DataFrame()

        signals = data_series.unstack(level='ts_code')

        if sel_by not in signals.index.names:
            raise KeyError(f'the sel_by column ({sel_by}) not in index: {signals.index.names}')

        try:
            signals = signals.loc[(slice(None), key),]
            signals.index = signals.index.get_level_values(0)
        except:
            return pd.DataFrame()

        return signals

    def _get_composition(self, datasource, *, symbols=None, starts=None, ends=None) -> pd.DataFrame:
        """成份查询型的数据获取方法

        Parameters
        ----------
        symbols: str
            股票代码列表, 一个逗号分隔的字符串，如'000001.SZ,000002.SZ'
        starts: str
            开始日期，YYYYMMDD格式
        ends: str
            结束日期，YYYYMMDD格式

        Returns
        -------
        DataFrame
        """

        table_name = self.kwargs.get('table_name')
        column = self.kwargs.get('column')
        comp_column = self.kwargs.get('comp_column')
        index = self.kwargs.get('index')

        weight_data = datasource.read_cached_table_data(table_name, shares=index, start=starts, end=ends)
        if not weight_data.empty:
            weight_data = weight_data.unstack()
        else:
            # return empty data
            return weight_data

        weight_data.columns = weight_data.columns.get_level_values(1)
        weight_data.index = weight_data.index.get_level_values(1)

        if symbols is not None:
            symbols = str_to_list(symbols)
            weight_data = weight_data.reindex(columns=symbols)

        return weight_data

    def _get_category(self, datasource, *, symbols=None) -> pd.Series:
        """成份查询型的数据获取方法

        Parameters
        ----------
        symbols: str
            股票代码列表，一个逗号分隔的字符串，如'000001.SZ,000002.SZ'

        Returns
        -------
        DataFrame
        """

        table_name = self.kwargs.get('table_name')
        column = self.kwargs.get('column')
        comp_column = self.kwargs.get('comp_column')

        category_data = datasource.read_cached_table_data(table_name)
        category = category_data.index.to_frame()
        category.index = category[column]

        category = category.loc[str_to_list(symbols)]

        grouped = category.groupby(category.index)
        result = grouped[comp_column].apply(lambda x: list(x))

        return result

    def _get_complex(self, datasource, *, symbols=None, date=None) -> pd.DataFrame:
        """复合型的数据获取方法"""
        raise NotImplementedError

    # TODO: consider moving this function to utility functions, separated in multiple simpler functions and been used
    #  in other functions in other modules

    def _symbolised(self, acquired_data) -> pd.DataFrame:
        """将数据转换为symbolised格式"""
        return acquired_data

    def _unsymbolised(self, acquired_data, column_name) -> pd.Series:
        """将数据转换为un-symbolised格式。

        symbolized数据为index为日期、column为qt_code的DataFrame，unsymbolize
        以后输出数据为index为日期、没有column的Series

        Parameters
        ----------
        acquired_data: pd.DataFrame
            symbolised格式的数据, index为datetime，columns为qt_code
        column_name: str
            需要筛选的column的名称，column_name必须在columns中
        """
        if (self.freq == 'None') or (self.asset_type == 'None'):
            err = TypeError(f'Only history data')

        if column_name not in acquired_data.columns:
            err = KeyError(f'columu name {column_name} not in columns of acquired_data: \n{acquired_data.columns}')
            raise err
        return acquired_data[column_name]


DATA_TYPE_MAP_COLUMNS = ['description', 'acquisition_type', 'kwargs']
DATA_TYPE_MAP_INDEX_NAMES = ('dtype', 'freq', 'asset_type')
DATA_TYPE_MAP = {
    ('trade_cal', 'd', 'None'):                       ['交易日历', 'direct',
                                                       {'table_name': 'trade_calendar', 'column': 'is_open'}],
    ('pre_trade_day|%', 'd', 'None'):                 ['上一交易日', 'selection',
                                                       {'table_name': 'trade_calendar', 'column': 'pretrade_date',
                                                        'sel_by':     'exchange', 'keys': '%'}],
    ('is_trade_day|%', 'd', 'None'):                  ['是否交易日-市场代码：%', 'selection',
                                                       {'table_name': 'trade_calendar', 'column': 'is_open',
                                                        'sel_by':     'exchange', 'keys': '%'}],
    ('stock_symbol', 'None', 'E'):                    ['股票基本信息 - 股票代码', 'basics',
                                                       {'table_name': 'stock_basic', 'column': 'symbol'}],
    ('stock_name', 'None', 'E'):                      ['股票基本信息 - 股票名称', 'basics',
                                                       {'table_name': 'stock_basic', 'column': 'name'}],
    ('area', 'None', 'E'):                            ['股票基本信息 - 地域', 'basics',
                                                       {'table_name': 'stock_basic', 'column': 'area'}],
    ('industry', 'None', 'E'):                        ['股票基本信息 - 所属行业', 'basics',
                                                       {'table_name': 'stock_basic', 'column': 'industry'}],
    ('fullname', 'None', 'E'):                        ['股票基本信息 - 股票全称', 'basics',
                                                       {'table_name': 'stock_basic', 'column': 'fullname'}],
    ('enname', 'None', 'E'):                          ['股票基本信息 - 英文全称', 'basics',
                                                       {'table_name': 'stock_basic', 'column': 'enname'}],
    ('cnspell', 'None', 'E'):                         ['股票基本信息 - 拼音缩写', 'basics',
                                                       {'table_name': 'stock_basic', 'column': 'cnspell'}],
    ('market', 'None', 'E'):                          ['股票基本信息 - 市场类型', 'basics',
                                                       {'table_name': 'stock_basic', 'column': 'market'}],
    ('exchange', 'None', 'E'):                        ['股票基本信息 - 交易所代码', 'basics',
                                                       {'table_name': 'stock_basic', 'column': 'exchange'}],
    ('curr_type', 'None', 'E'):                       ['股票基本信息 - 交易货币', 'basics',
                                                       {'table_name': 'stock_basic', 'column': 'curr_type'}],
    ('list_status', 'None', 'E'):                     ['股票基本信息 - 上市状态 L上市 D退市 P暂停上市', 'basics',
                                                       {'table_name': 'stock_basic', 'column': 'list_status'}],
    ('list_date', 'None', 'E'):                       ['股票基本信息 - 上市日期', 'basics',
                                                       {'table_name': 'stock_basic', 'column': 'list_date'}],
    ('delist_date', 'None', 'E'):                     ['股票基本信息 - 退市日期', 'basics',
                                                       {'table_name': 'stock_basic', 'column': 'delist_date'}],
    ('is_hs', 'None', 'E'):                           ['股票基本信息 - 是否沪深港通标的', 'basics',
                                                       {'table_name': 'stock_basic', 'column': 'is_hs'}],
    ('wt_idx|%', 'd', 'E'):                           ['股票在指数中所占权重 - %', 'composition',
                                                       {'table_name':  'index_weight', 'column': 'weight',
                                                        'comp_column': 'index_code', 'index': '%'}],
    # 按照'ths_category',一个股票可能会同时被分到多个类别中，这样导致无法选择出唯一的分类，临时解决措施是使用类似event_multi_stat
    # 的方式处理
    ('ths_category', 'None', 'E'):                    ['股票同花顺行业分类', 'category',
                                                       {'table_name':  'ths_index_weight', 'column': 'con_code',
                                                        'comp_column': 'ts_code'}],
    # ('sw_l1_code','None','E'):	['股票行业分类 - 申万L1','category',{'table_name': 'sw_industry_detail', 'column': 'L1-code'}],
    ('market', 'None', 'IDX'):                        ['指数基本信息 - 市场', 'basics',
                                                       {'table_name': 'index_basic', 'column': 'market'}],
    ('publisher', 'None', 'IDX'):                     ['指数基本信息 - 发布方', 'basics',
                                                       {'table_name': 'index_basic', 'column': 'publisher'}],
    ('index_type', 'None', 'IDX'):                    ['指数基本信息 - 指数风格', 'basics',
                                                       {'table_name': 'index_basic', 'column': 'index_type'}],
    ('category', 'None', 'IDX'):                      ['指数基本信息 - 指数类别', 'basics',
                                                       {'table_name': 'index_basic', 'column': 'category'}],
    ('base_date', 'None', 'IDX'):                     ['指数基本信息 - 基期', 'basics',
                                                       {'table_name': 'index_basic', 'column': 'base_date'}],
    ('base_point', 'None', 'IDX'):                    ['指数基本信息 - 基点', 'basics',
                                                       {'table_name': 'index_basic', 'column': 'base_point'}],
    ('list_date', 'None', 'IDX'):                     ['指数基本信息 - 发布日期', 'basics',
                                                       {'table_name': 'index_basic', 'column': 'list_date'}],
    ('weight_rule', 'None', 'IDX'):                   ['指数基本信息 - 加权方式', 'basics',
                                                       {'table_name': 'index_basic', 'column': 'weight_rule'}],
    ('desc', 'None', 'IDX'):                          ['指数基本信息 - 描述', 'basics',
                                                       {'table_name': 'index_basic', 'column': 'desc'}],
    ('exp_date', 'None', 'IDX'):                      ['指数基本信息 - 终止日期', 'basics',
                                                       {'table_name': 'index_basic', 'column': 'exp_date'}],
    ('sw_industry_name', 'None', 'IDX'):              ['申万行业分类 - 名称', 'basics',
                                                       {'table_name': 'sw_industry_basic', 'column': 'industry_name'}],
    ('sw_parent_code', 'None', 'IDX'):                ['申万行业分类 - 上级行业代码', 'basics',
                                                       {'table_name': 'sw_industry_basic', 'column': 'parent_code'}],
    ('sw_level', 'None', 'IDX'):                      ['申万行业分类 - 级别', 'basics',
                                                       {'table_name': 'sw_industry_basic', 'column': 'level'}],
    ('sw_industry_code', 'None', 'IDX'):              ['申万行业分类 - 行业代码', 'basics',
                                                       {'table_name': 'sw_industry_basic', 'column': 'industry_code'}],
    ('sw_published', 'None', 'IDX'):                  ['申万行业分类 - 是否发布', 'basics',
                                                       {'table_name': 'sw_industry_basic', 'column': 'is_pub'}],
    ('sw_source', 'None', 'IDX'):                     ['申万行业分类 - 分类版本', 'basics',
                                                       {'table_name': 'sw_industry_basic', 'column': 'src'}],
    ('sw_level|%', 'None', 'IDX'):                    ['申万行业分类筛选 - %', 'selection',
                                                       {'table_name': 'sw_industry_basic', 'column': 'level',
                                                        'sel_by':     'level', 'keys': ['%']}],
    ('sw|%', 'None', 'IDX'):                          ['申万行业分类筛选 - %', 'selection',
                                                       {'table_name': 'sw_industry_basic', 'column': 'src',
                                                        'sel_by':     'src', 'keys': ['%']}],
    ('ths_industry_name', 'None', 'IDX'):             ['同花顺行业分类基本信息 - 行业名称', 'basics',
                                                       {'table_name': 'ths_index_basic', 'column': 'name'}],
    ('ths_industry_count', 'None', 'IDX'):            ['同花顺行业分类基本信息 - 股票数量', 'basics',
                                                       {'table_name': 'ths_index_basic', 'column': 'count'}],
    ('ths_industry_exchange', 'None', 'IDX'):         ['同花顺行业分类基本信息 - 交易所', 'basics',
                                                       {'table_name': 'ths_index_basic', 'column': 'exchange'}],
    ('ths_industry_date', 'None', 'IDX'):             ['同花顺行业分类基本信息 - 发布日期', 'basics',
                                                       {'table_name': 'ths_index_basic', 'column': 'list_date'}],
    ('fund_name', 'None', 'FD'):                      ['基金基本信息 - 简称', 'basics',
                                                       {'table_name': 'fund_basic', 'column': 'name'}],
    ('management', 'None', 'FD'):                     ['基金基本信息 - 管理人', 'basics',
                                                       {'table_name': 'fund_basic', 'column': 'management'}],
    ('custodian', 'None', 'FD'):                      ['基金基本信息 - 托管人', 'basics',
                                                       {'table_name': 'fund_basic', 'column': 'custodian'}],
    ('fund_type', 'None', 'FD'):                      ['基金基本信息 - 投资类型', 'basics',
                                                       {'table_name': 'fund_basic', 'column': 'fund_type'}],
    ('found_date', 'None', 'FD'):                     ['基金基本信息 - 成立日期', 'basics',
                                                       {'table_name': 'fund_basic', 'column': 'found_date'}],
    ('due_date', 'None', 'FD'):                       ['基金基本信息 - 到期日期', 'basics',
                                                       {'table_name': 'fund_basic', 'column': 'due_date'}],
    ('list_date', 'None', 'FD'):                      ['基金基本信息 - 上市时间', 'basics',
                                                       {'table_name': 'fund_basic', 'column': 'list_date'}],
    ('issue_date', 'None', 'FD'):                     ['基金基本信息 - 发行日期', 'basics',
                                                       {'table_name': 'fund_basic', 'column': 'issue_date'}],
    ('delist_date', 'None', 'FD'):                    ['基金基本信息 - 退市日期', 'basics',
                                                       {'table_name': 'fund_basic', 'column': 'delist_date'}],
    ('issue_amount', 'None', 'FD'):                   ['基金基本信息 - 发行份额(亿)', 'basics',
                                                       {'table_name': 'fund_basic', 'column': 'issue_amount'}],
    ('m_fee', 'None', 'FD'):                          ['基金基本信息 - 管理费', 'basics',
                                                       {'table_name': 'fund_basic', 'column': 'm_fee'}],
    ('c_fee', 'None', 'FD'):                          ['基金基本信息 - 托管费', 'basics',
                                                       {'table_name': 'fund_basic', 'column': 'c_fee'}],
    ('duration_year', 'None', 'FD'):                  ['基金基本信息 - 存续期', 'basics',
                                                       {'table_name': 'fund_basic', 'column': 'duration_year'}],
    ('p_value', 'None', 'FD'):                        ['基金基本信息 - 面值', 'basics',
                                                       {'table_name': 'fund_basic', 'column': 'p_value'}],
    ('min_amount', 'None', 'FD'):                     ['基金基本信息 - 起点金额(万元)', 'basics',
                                                       {'table_name': 'fund_basic', 'column': 'min_amount'}],
    ('exp_return', 'None', 'FD'):                     ['基金基本信息 - 预期收益率', 'basics',
                                                       {'table_name': 'fund_basic', 'column': 'exp_return'}],
    ('benchmark', 'None', 'FD'):                      ['基金基本信息 - 业绩比较基准', 'basics',
                                                       {'table_name': 'fund_basic', 'column': 'benchmark'}],
    ('status', 'None', 'FD'):                         ['基金基本信息 - 存续状态D摘牌 I发行 L已上市', 'basics',
                                                       {'table_name': 'fund_basic', 'column': 'status'}],
    ('invest_type', 'None', 'FD'):                    ['基金基本信息 - 投资风格', 'basics',
                                                       {'table_name': 'fund_basic', 'column': 'invest_type'}],
    ('type', 'None', 'FD'):                           ['基金基本信息 - 基金类型', 'basics',
                                                       {'table_name': 'fund_basic', 'column': 'type'}],
    ('trustee', 'None', 'FD'):                        ['基金基本信息 - 受托人', 'basics',
                                                       {'table_name': 'fund_basic', 'column': 'trustee'}],
    ('purc_startdate', 'None', 'FD'):                 ['基金基本信息 - 日常申购起始日', 'basics',
                                                       {'table_name': 'fund_basic', 'column': 'purc_startdate'}],
    ('redm_startdate', 'None', 'FD'):                 ['基金基本信息 - 日常赎回起始日', 'basics',
                                                       {'table_name': 'fund_basic', 'column': 'redm_startdate'}],
    ('market', 'None', 'FD'):                         ['基金基本信息 - E场内O场外', 'basics',
                                                       {'table_name': 'fund_basic', 'column': 'market'}],
    ('symbol', 'None', 'FT'):                         ['期货基本信息 - 交易标识', 'basics',
                                                       {'table_name': 'future_basic', 'column': 'symbol'}],
    ('exchange', 'None', 'FT'):                       ['期货基本信息 - 交易市场', 'basics',
                                                       {'table_name': 'future_basic', 'column': 'exchange'}],
    ('name', 'None', 'FT'):                           ['期货基本信息 - 中文简称', 'basics',
                                                       {'table_name': 'future_basic', 'column': 'name'}],
    ('fut_code', 'None', 'FT'):                       ['期货基本信息 - 合约产品代码', 'basics',
                                                       {'table_name': 'future_basic', 'column': 'fut_code'}],
    ('multiplier', 'None', 'FT'):                     ['期货基本信息 - 合约乘数(只适用于国债期货、指数期货)', 'basics',
                                                       {'table_name': 'future_basic', 'column': 'multiplier'}],
    ('trade_unit', 'None', 'FT'):                     ['期货基本信息 - 交易计量单位', 'basics',
                                                       {'table_name': 'future_basic', 'column': 'trade_unit'}],
    ('per_unit', 'None', 'FT'):                       ['期货基本信息 - 交易单位(每手)', 'basics',
                                                       {'table_name': 'future_basic', 'column': 'per_unit'}],
    ('quote_unit', 'None', 'FT'):                     ['期货基本信息 - 报价单位', 'basics',
                                                       {'table_name': 'future_basic', 'column': 'quote_unit'}],
    ('quote_unit_desc', 'None', 'FT'):                ['期货基本信息 - 最小报价单位说明', 'basics',
                                                       {'table_name': 'future_basic', 'column': 'quote_unit_desc'}],
    ('d_mode_desc', 'None', 'FT'):                    ['期货基本信息 - 交割方式说明', 'basics',
                                                       {'table_name': 'future_basic', 'column': 'd_mode_desc'}],
    ('list_date', 'None', 'FT'):                      ['期货基本信息 - 上市日期', 'basics',
                                                       {'table_name': 'future_basic', 'column': 'list_date'}],
    ('delist_date', 'None', 'FT'):                    ['期货基本信息 - 最后交易日期', 'basics',
                                                       {'table_name': 'future_basic', 'column': 'delist_date'}],
    ('d_month', 'None', 'FT'):                        ['期货基本信息 - 交割月份', 'basics',
                                                       {'table_name': 'future_basic', 'column': 'd_month'}],
    ('last_ddate', 'None', 'FT'):                     ['期货基本信息 - 最后交割日', 'basics',
                                                       {'table_name': 'future_basic', 'column': 'last_ddate'}],
    ('trade_time_desc', 'None', 'FT'):                ['期货基本信息 - 交易时间说明', 'basics',
                                                       {'table_name': 'future_basic', 'column': 'trade_time_desc'}],
    ('exchange', 'None', 'OPT'):                      ['期权基本信息 - 交易市场', 'basics',
                                                       {'table_name': 'opt_basic', 'column': 'exchange'}],
    ('name', 'None', 'OPT'):                          ['期权基本信息 - 合约名称', 'basics',
                                                       {'table_name': 'opt_basic', 'column': 'name'}],
    ('per_unit', 'None', 'OPT'):                      ['期权基本信息 - 合约单位', 'basics',
                                                       {'table_name': 'opt_basic', 'column': 'per_unit'}],
    ('opt_code', 'None', 'OPT'):                      ['期权基本信息 - 标的合约代码', 'basics',
                                                       {'table_name': 'opt_basic', 'column': 'opt_code'}],
    ('opt_type', 'None', 'OPT'):                      ['期权基本信息 - 合约类型', 'basics',
                                                       {'table_name': 'opt_basic', 'column': 'opt_type'}],
    ('call_put', 'None', 'OPT'):                      ['期权基本信息 - 期权类型', 'basics',
                                                       {'table_name': 'opt_basic', 'column': 'call_put'}],
    ('exercise_type', 'None', 'OPT'):                 ['期权基本信息 - 行权方式', 'basics',
                                                       {'table_name': 'opt_basic', 'column': 'exercise_type'}],
    ('exercise_price', 'None', 'OPT'):                ['期权基本信息 - 行权价格', 'basics',
                                                       {'table_name': 'opt_basic', 'column': 'exercise_price'}],
    ('s_month', 'None', 'OPT'):                       ['期权基本信息 - 结算月', 'basics',
                                                       {'table_name': 'opt_basic', 'column': 's_month'}],
    ('maturity_date', 'None', 'OPT'):                 ['期权基本信息 - 到期日', 'basics',
                                                       {'table_name': 'opt_basic', 'column': 'maturity_date'}],
    ('list_price', 'None', 'OPT'):                    ['期权基本信息 - 挂牌基准价', 'basics',
                                                       {'table_name': 'opt_basic', 'column': 'list_price'}],
    ('list_date', 'None', 'OPT'):                     ['期权基本信息 - 开始交易日期', 'basics',
                                                       {'table_name': 'opt_basic', 'column': 'list_date'}],
    ('delist_date', 'None', 'OPT'):                   ['期权基本信息 - 最后交易日期', 'basics',
                                                       {'table_name': 'opt_basic', 'column': 'delist_date'}],
    ('last_edate', 'None', 'OPT'):                    ['期权基本信息 - 最后行权日期', 'basics',
                                                       {'table_name': 'opt_basic', 'column': 'last_edate'}],
    ('last_ddate', 'None', 'OPT'):                    ['期权基本信息 - 最后交割日期', 'basics',
                                                       {'table_name': 'opt_basic', 'column': 'last_ddate'}],
    ('quote_unit', 'None', 'OPT'):                    ['期权基本信息 - 报价单位', 'basics',
                                                       {'table_name': 'opt_basic', 'column': 'quote_unit'}],
    ('min_price_chg', 'None', 'OPT'):                 ['期权基本信息 - 最小价格波幅', 'basics',
                                                       {'table_name': 'opt_basic', 'column': 'min_price_chg'}],
    ('chairman', 'd', 'E'):                           ['公司信息 - 法人代表', 'basics',
                                                       {'table_name': 'stock_company', 'column': 'chairman'}],
    ('manager', 'd', 'E'):                            ['公司信息 - 总经理', 'basics',
                                                       {'table_name': 'stock_company', 'column': 'manager'}],
    ('secretary', 'd', 'E'):                          ['公司信息 - 董秘', 'basics',
                                                       {'table_name': 'stock_company', 'column': 'secretary'}],
    ('reg_capital', 'd', 'E'):                        ['公司信息 - 注册资本', 'basics',
                                                       {'table_name': 'stock_company', 'column': 'reg_capital'}],
    ('setup_date', 'd', 'E'):                         ['公司信息 - 注册日期', 'basics',
                                                       {'table_name': 'stock_company', 'column': 'setup_date'}],
    ('province', 'd', 'E'):                           ['公司信息 - 所在省份', 'basics',
                                                       {'table_name': 'stock_company', 'column': 'province'}],
    ('city', 'd', 'E'):                               ['公司信息 - 所在城市', 'basics',
                                                       {'table_name': 'stock_company', 'column': 'city'}],
    ('introduction', 'd', 'E'):                       ['公司信息 - 公司介绍', 'basics',
                                                       {'table_name': 'stock_company', 'column': 'introduction'}],
    ('website', 'd', 'E'):                            ['公司信息 - 公司主页', 'basics',
                                                       {'table_name': 'stock_company', 'column': 'website'}],
    ('email', 'd', 'E'):                              ['公司信息 - 电子邮件', 'basics',
                                                       {'table_name': 'stock_company', 'column': 'email'}],
    ('office', 'd', 'E'):                             ['公司信息 - 办公室', 'basics',
                                                       {'table_name': 'stock_company', 'column': 'office'}],
    ('employees', 'd', 'E'):                          ['公司信息 - 员工人数', 'basics',
                                                       {'table_name': 'stock_company', 'column': 'employees'}],
    ('main_business', 'd', 'E'):                      ['公司信息 - 主要业务及产品', 'basics',
                                                       {'table_name': 'stock_company', 'column': 'main_business'}],
    ('business_scope', 'd', 'E'):                     ['公司信息 - 经营范围', 'basics',
                                                       {'table_name': 'stock_company', 'column': 'business_scope'}],
    ('managers_name', 'd', 'E'):                      ['公司高管信息 - 高管姓名', 'event_multi_stat',
                                                       {'table_name': 'stk_managers',
                                                        'column':     'name',
                                                        'id_index':   'name',
                                                        'start_col':  'begin_date',
                                                        'end_col':    'end_date'}],
    ('managers_gender', 'd', 'E'):                    ['公司高管信息 - 性别', 'event_multi_stat',
                                                       {'table_name': 'stk_managers',
                                                        'column':     'gender',
                                                        'id_index':   'name',
                                                        'start_col':  'begin_date',
                                                        'end_col':    'end_date'}],
    ('managers_lev', 'd', 'E'):                       ['公司高管信息 - 岗位类别', 'event_multi_stat',
                                                       {'table_name': 'stk_managers', 'column': 'lev',
                                                        'id_index':   'name', 'start_col': 'begin_date',
                                                        'end_col':    'end_date'}],
    ('manager_title', 'd', 'E'):                      ['公司高管信息 - 岗位', 'event_multi_stat',
                                                       {'table_name': 'stk_managers', 'column': 'title',
                                                        'id_index':   'name', 'start_col': 'begin_date',
                                                        'end_col':    'end_date'}],
    ('managers_edu', 'd', 'E'):                       ['公司高管信息 - 学历', 'event_multi_stat',
                                                       {'table_name': 'stk_managers', 'column': 'edu',
                                                        'id_index':   'name', 'start_col': 'begin_date',
                                                        'end_col':    'end_date'}],
    ('managers_national', 'd', 'E'):                  ['公司高管信息 - 国籍', 'event_multi_stat',
                                                       {'table_name': 'stk_managers', 'column': 'national',
                                                        'id_index':   'name', 'start_col': 'begin_date',
                                                        'end_col':    'end_date'}],
    ('managers_birthday', 'd', 'E'):                  ['公司高管信息 - 出生年月', 'event_multi_stat',
                                                       {'table_name': 'stk_managers', 'column': 'birthday',
                                                        'id_index':   'name', 'start_col': 'begin_date',
                                                        'end_col':    'end_date'}],
    ('managers_resume', 'd', 'E'):                    ['公司高管信息 - 个人简历', 'event_multi_stat',
                                                       {'table_name': 'stk_managers', 'column': 'resume',
                                                        'id_index':   'name', 'start_col': 'begin_date',
                                                        'end_col':    'end_date'}],
    # ('manager_salary_name','d','E'):	['管理层薪酬 - 姓名','direct',{'table_name': 'stk_rewards', 'column': 'name'}],
    # ('manager_salary_title','d','E'):	['管理层薪酬 - 职务','direct',{'table_name': 'stk_rewards', 'column': 'title'}],
    # ('reward','d','E'):	['管理层薪酬 - 报酬','direct',{'table_name': 'stk_rewards', 'column': 'reward'}],
    # ('hold_vol','d','E'):	['管理层薪酬 - 持股数','direct',{'table_name': 'stk_rewards', 'column': 'hold_vol'}],
    ('ipo_date', 'd', 'E'):                           ['新股上市信息 - 上网发行日期', 'basics',
                                                       {'table_name': 'new_share', 'column': 'ipo_date'}],
    ('issue_date', 'd', 'E'):                         ['新股上市信息 - 上市日期', 'basics',
                                                       {'table_name': 'new_share', 'column': 'issue_date'}],
    ('IPO_amount', 'd', 'E'):                         ['新股上市信息 - 发行总量（万股）', 'basics',
                                                       {'table_name': 'new_share', 'column': 'amount'}],
    ('market_amount', 'd', 'E'):                      ['新股上市信息 - 上网发行总量（万股）', 'basics',
                                                       {'table_name': 'new_share', 'column': 'market_amount'}],
    ('initial_price', 'd', 'E'):                      ['新股上市信息 - 发行价格', 'basics',
                                                       {'table_name': 'new_share', 'column': 'price'}],
    ('initial_pe', 'd', 'E'):                         ['新股上市信息 - 发行市盈率', 'basics',
                                                       {'table_name': 'new_share', 'column': 'pe'}],
    ('limit_amount', 'd', 'E'):                       ['新股上市信息 - 个人申购上限（万股）', 'basics',
                                                       {'table_name': 'new_share', 'column': 'limit_amount'}],
    ('funds', 'd', 'E'):                              ['新股上市信息 - 募集资金（亿元）', 'basics',
                                                       {'table_name': 'new_share', 'column': 'funds'}],
    ('ballot', 'd', 'E'):                             ['新股上市信息 - 中签率', 'basics',
                                                       {'table_name': 'new_share', 'column': 'ballot'}],
    ('hk_top10_close', 'd', 'E'):                     [' 港股通十大成交 - 收盘价', 'direct',
                                                       {'table_name': 'hk_top10_stock', 'column': 'close'}],
    ('hk_top10_p_change', 'd', 'E'):                  [' 港股通十大成交 - 涨跌幅', 'direct',
                                                       {'table_name': 'hk_top10_stock', 'column': 'p_change'}],
    ('hk_top10_rank', 'd', 'E'):                      [' 港股通十大成交 - 排名', 'direct',
                                                       {'table_name': 'hk_top10_stock', 'column': 'rank'}],
    ('hk_top10_amount', 'd', 'E'):                    [' 港股通十大成交 - 累计成交额（元）', 'direct',
                                                       {'table_name': 'hk_top10_stock', 'column': 'amount'}],
    ('hk_top10_net_amount', 'd', 'E'):                [' 港股通十大成交 - 净买入金额（元）', 'direct',
                                                       {'table_name': 'hk_top10_stock', 'column': 'net_amount'}],
    ('hk_top10_sh_amount', 'd', 'E'):                 [' 港股通十大成交 - 沪市成交额（元）', 'direct',
                                                       {'table_name': 'hk_top10_stock', 'column': 'sh_amount'}],
    ('hk_top10_sh_net_amount', 'd', 'E'):             [' 港股通十大成交 - 沪市净买入额（元）', 'direct',
                                                       {'table_name': 'hk_top10_stock', 'column': 'sh_net_amount'}],
    ('hk_top10_sh_buy', 'd', 'E'):                    [' 港股通十大成交 - 沪市买入金额（元）', 'direct',
                                                       {'table_name': 'hk_top10_stock', 'column': 'sh_buy'}],
    ('hk_top10_sh_sell', 'd', 'E'):                   [' 港股通十大成交 - 沪市卖出金额（元）', 'direct',
                                                       {'table_name': 'hk_top10_stock', 'column': 'sh_sell'}],
    ('hk_top10_sz_amount', 'd', 'E'):                 [' 港股通十大成交 - 深市成交金额（元）', 'direct',
                                                       {'table_name': 'hk_top10_stock', 'column': 'sz_amount'}],
    ('hk_top10_sz_net_amount', 'd', 'E'):             [' 港股通十大成交 - 深市净买入额（元）', 'direct',
                                                       {'table_name': 'hk_top10_stock', 'column': 'sz_net_amount'}],
    ('hk_top10_sh_buy', 'd', 'E'):                    [' 港股通十大成交 - 深市净买入金额（元）', 'direct',
                                                       {'table_name': 'hk_top10_stock', 'column': 'sz_buy'}],
    ('hk_top10_sh_sell', 'd', 'E'):                   [' 港股通十大成交 - 深市净买入金额（元）', 'direct',
                                                       {'table_name': 'hk_top10_stock', 'column': 'sz_sell'}],
    ('open|%', 'd', 'E'):                             ['股票日K线 - 复权开盘价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'stock_daily', 'column': 'open',
                                                        'adj_table':  'stock_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('high|%', 'd', 'E'):                             ['股票日K线 - 复权最高价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'stock_daily', 'column': 'high',
                                                        'adj_table':  'stock_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('low|%', 'd', 'E'):                              ['股票日K线 - 复权最低价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'stock_daily', 'column': 'low',
                                                        'adj_table':  'stock_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('close|%', 'd', 'E'):                            ['股票日K线 - 复权收盘价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'stock_daily', 'column': 'close',
                                                        'adj_table':  'stock_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('open', 'd', 'E'):                               ['股票日K线 - 开盘价', 'direct',
                                                       {'table_name': 'stock_daily', 'column': 'open'}],
    ('high', 'd', 'E'):                               ['股票日K线 - 最高价', 'direct',
                                                       {'table_name': 'stock_daily', 'column': 'high'}],
    ('low', 'd', 'E'):                                ['股票日K线 - 最低价', 'direct',
                                                       {'table_name': 'stock_daily', 'column': 'low'}],
    ('close', 'd', 'E'):                              ['股票日K线 - 收盘价', 'direct',
                                                       {'table_name': 'stock_daily', 'column': 'close'}],
    ('volume', 'd', 'E'):                             ['股票日K线 - 成交量 （手）', 'direct',
                                                       {'table_name': 'stock_daily', 'column': 'vol'}],
    ('amount', 'd', 'E'):                             ['股票日K线 - 成交额 （千元）', 'direct',
                                                       {'table_name': 'stock_daily', 'column': 'amount'}],
    ('open|%', 'w', 'E'):                             ['股票周K线 - 复权开盘价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'stock_weekly', 'column': 'open',
                                                        'adj_table':  'stock_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('high|%', 'w', 'E'):                             ['股票周K线 - 复权最高价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'stock_weekly', 'column': 'high',
                                                        'adj_table':  'stock_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('low|%', 'w', 'E'):                              ['股票周K线 - 复权最低价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'stock_weekly', 'column': 'low',
                                                        'adj_table':  'stock_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('close|%', 'w', 'E'):                            ['股票周K线 - 复权收盘价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'stock_weekly', 'column': 'close',
                                                        'adj_table':  'stock_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('open', 'w', 'E'):                               ['股票周K线 - 开盘价', 'direct',
                                                       {'table_name': 'stock_weekly', 'column': 'open'}],
    ('high', 'w', 'E'):                               ['股票周K线 - 最高价', 'direct',
                                                       {'table_name': 'stock_weekly', 'column': 'high'}],
    ('low', 'w', 'E'):                                ['股票周K线 - 最低价', 'direct',
                                                       {'table_name': 'stock_weekly', 'column': 'low'}],
    ('close', 'w', 'E'):                              ['股票周K线 - 收盘价', 'direct',
                                                       {'table_name': 'stock_weekly', 'column': 'close'}],
    ('volume', 'w', 'E'):                             ['股票周K线 - 成交量 （手）', 'direct',
                                                       {'table_name': 'stock_weekly', 'column': 'vol'}],
    ('amount', 'w', 'E'):                             ['股票周K线 - 成交额 （千元）', 'direct',
                                                       {'table_name': 'stock_weekly', 'column': 'amount'}],
    ('open|%', 'm', 'E'):                             ['股票月K线 - 复权开盘价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'stock_monthly', 'column': 'open',
                                                        'adj_table':  'stock_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('high|%', 'm', 'E'):                             ['股票月K线 - 复权最高价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'stock_monthly', 'column': 'high',
                                                        'adj_table':  'stock_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('low|%', 'm', 'E'):                              ['股票月K线 - 复权最低价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'stock_monthly', 'column': 'low',
                                                        'adj_table':  'stock_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('close|%', 'm', 'E'):                            ['股票月K线 - 复权收盘价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'stock_monthly', 'column': 'close',
                                                        'adj_table':  'stock_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('open', 'm', 'E'):                               ['股票月K线 - 开盘价', 'direct',
                                                       {'table_name': 'stock_monthly', 'column': 'open'}],
    ('high', 'm', 'E'):                               ['股票月K线 - 最高价', 'direct',
                                                       {'table_name': 'stock_monthly', 'column': 'high'}],
    ('low', 'm', 'E'):                                ['股票月K线 - 最低价', 'direct',
                                                       {'table_name': 'stock_monthly', 'column': 'low'}],
    ('close', 'm', 'E'):                              ['股票月K线 - 收盘价', 'direct',
                                                       {'table_name': 'stock_monthly', 'column': 'close'}],
    ('volume', 'm', 'E'):                             ['股票月K线 - 成交量 （手）', 'direct',
                                                       {'table_name': 'stock_monthly', 'column': 'vol'}],
    ('amount', 'm', 'E'):                             ['股票月K线 - 成交额 （千元）', 'direct',
                                                       {'table_name': 'stock_monthly', 'column': 'amount'}],
    ('open|%', '1min', 'E'):                          ['股票60秒K线 - 复权开盘价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'stock_1min', 'column': 'open',
                                                        'adj_table':  'stock_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('high|%', '1min', 'E'):                          ['股票60秒K线 - 复权最高价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'stock_1min', 'column': 'high',
                                                        'adj_table':  'stock_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('low|%', '1min', 'E'):                           ['股票60秒K线 - 复权最低价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'stock_1min', 'column': 'low',
                                                        'adj_table':  'stock_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('close|%', '1min', 'E'):                         ['股票60秒K线 - 复权收盘价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'stock_1min', 'column': 'close',
                                                        'adj_table':  'stock_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('open', '1min', 'E'):                            ['股票60秒K线 - 开盘价', 'direct',
                                                       {'table_name': 'stock_1min', 'column': 'open'}],
    ('high', '1min', 'E'):                            ['股票60秒K线 - 最高价', 'direct',
                                                       {'table_name': 'stock_1min', 'column': 'high'}],
    ('low', '1min', 'E'):                             ['股票60秒K线 - 最低价', 'direct',
                                                       {'table_name': 'stock_1min', 'column': 'low'}],
    ('close', '1min', 'E'):                           ['股票60秒K线 - 收盘价', 'direct',
                                                       {'table_name': 'stock_1min', 'column': 'close'}],
    ('volume', '1min', 'E'):                          ['股票60秒K线 - 成交量 （手）', 'direct',
                                                       {'table_name': 'stock_1min', 'column': 'vol'}],
    ('amount', '1min', 'E'):                          ['股票60秒K线 - 成交额 （千元）', 'direct',
                                                       {'table_name': 'stock_1min', 'column': 'amount'}],
    ('open|%', '5min', 'E'):                          ['股票5分钟K线 - 复权开盘价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'stock_5min', 'column': 'open',
                                                        'adj_table':  'stock_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('high|%', '5min', 'E'):                          ['股票5分钟K线 - 复权最高价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'stock_5min', 'column': 'high',
                                                        'adj_table':  'stock_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('low|%', '5min', 'E'):                           ['股票5分钟K线 - 复权最低价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'stock_5min', 'column': 'low',
                                                        'adj_table':  'stock_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('close|%', '5min', 'E'):                         ['股票5分钟K线 - 复权收盘价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'stock_5min', 'column': 'close',
                                                        'adj_table':  'stock_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('open', '5min', 'E'):                            ['股票5分钟K线 - 开盘价', 'direct',
                                                       {'table_name': 'stock_5min', 'column': 'open'}],
    ('high', '5min', 'E'):                            ['股票5分钟K线 - 最高价', 'direct',
                                                       {'table_name': 'stock_5min', 'column': 'high'}],
    ('low', '5min', 'E'):                             ['股票5分钟K线 - 最低价', 'direct',
                                                       {'table_name': 'stock_5min', 'column': 'low'}],
    ('close', '5min', 'E'):                           ['股票5分钟K线 - 收盘价', 'direct',
                                                       {'table_name': 'stock_5min', 'column': 'close'}],
    ('volume', '5min', 'E'):                          ['股票5分钟K线 - 成交量 （手）', 'direct',
                                                       {'table_name': 'stock_5min', 'column': 'vol'}],
    ('amount', '5min', 'E'):                          ['股票5分钟K线 - 成交额 （千元）', 'direct',
                                                       {'table_name': 'stock_5min', 'column': 'amount'}],
    ('open|%', '15min', 'E'):                         ['股票15分钟K线 - 复权开盘价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'stock_15min', 'column': 'open',
                                                        'adj_table':  'stock_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('high|%', '15min', 'E'):                         ['股票15分钟K线 - 复权最高价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'stock_15min', 'column': 'high',
                                                        'adj_table':  'stock_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('low|%', '15min', 'E'):                          ['股票15分钟K线 - 复权最低价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'stock_15min', 'column': 'low',
                                                        'adj_table':  'stock_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('close|%', '15min', 'E'):                        ['股票15分钟K线 - 复权收盘价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'stock_15min', 'column': 'close',
                                                        'adj_table':  'stock_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('open', '15min', 'E'):                           ['股票15分钟K线 - 开盘价', 'direct',
                                                       {'table_name': 'stock_15min', 'column': 'open'}],
    ('high', '15min', 'E'):                           ['股票15分钟K线 - 最高价', 'direct',
                                                       {'table_name': 'stock_15min', 'column': 'high'}],
    ('low', '15min', 'E'):                            ['股票15分钟K线 - 最低价', 'direct',
                                                       {'table_name': 'stock_15min', 'column': 'low'}],
    ('close', '15min', 'E'):                          ['股票15分钟K线 - 收盘价', 'direct',
                                                       {'table_name': 'stock_15min', 'column': 'close'}],
    ('volume', '15min', 'E'):                         ['股票15分钟K线 - 成交量 （手）', 'direct',
                                                       {'table_name': 'stock_15min', 'column': 'vol'}],
    ('amount', '15min', 'E'):                         ['股票15分钟K线 - 成交额 （千元）', 'direct',
                                                       {'table_name': 'stock_15min', 'column': 'amount'}],
    ('open|%', '30min', 'E'):                         ['股票30分钟K线 - 复权开盘价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'stock_30min', 'column': 'open',
                                                        'adj_table':  'stock_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('high|%', '30min', 'E'):                         ['股票30分钟K线 - 复权最高价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'stock_30min', 'column': 'high',
                                                        'adj_table':  'stock_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('low|%', '30min', 'E'):                          ['股票30分钟K线 - 复权最低价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'stock_30min', 'column': 'low',
                                                        'adj_table':  'stock_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('close|%', '30min', 'E'):                        ['股票30分钟K线 - 复权收盘价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'stock_30min', 'column': 'close',
                                                        'adj_table':  'stock_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('open', '30min', 'E'):                           ['股票30分钟K线 - 开盘价', 'direct',
                                                       {'table_name': 'stock_30min', 'column': 'open'}],
    ('high', '30min', 'E'):                           ['股票30分钟K线 - 最高价', 'direct',
                                                       {'table_name': 'stock_30min', 'column': 'high'}],
    ('low', '30min', 'E'):                            ['股票30分钟K线 - 最低价', 'direct',
                                                       {'table_name': 'stock_30min', 'column': 'low'}],
    ('close', '30min', 'E'):                          ['股票30分钟K线 - 收盘价', 'direct',
                                                       {'table_name': 'stock_30min', 'column': 'close'}],
    ('volume', '30min', 'E'):                         ['股票30分钟K线 - 成交量 （手）', 'direct',
                                                       {'table_name': 'stock_30min', 'column': 'vol'}],
    ('amount', '30min', 'E'):                         ['股票30分钟K线 - 成交额 （千元）', 'direct',
                                                       {'table_name': 'stock_30min', 'column': 'amount'}],
    ('open|%', 'h', 'E'):                             ['股票小时K线 - 复权开盘价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'stock_hourly', 'column': 'open',
                                                        'adj_table':  'stock_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('high|%', 'h', 'E'):                             ['股票小时K线 - 复权最高价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'stock_hourly', 'column': 'high',
                                                        'adj_table':  'stock_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('low|%', 'h', 'E'):                              ['股票小时K线 - 复权最低价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'stock_hourly', 'column': 'low',
                                                        'adj_table':  'stock_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('close|%', 'h', 'E'):                            ['股票小时K线 - 复权收盘价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'stock_hourly', 'column': 'close',
                                                        'adj_table':  'stock_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('open', 'h', 'E'):                               ['股票小时K线 - 开盘价', 'direct',
                                                       {'table_name': 'stock_hourly', 'column': 'open'}],
    ('high', 'h', 'E'):                               ['股票小时K线 - 最高价', 'direct',
                                                       {'table_name': 'stock_hourly', 'column': 'high'}],
    ('low', 'h', 'E'):                                ['股票小时K线 - 最低价', 'direct',
                                                       {'table_name': 'stock_hourly', 'column': 'low'}],
    ('close', 'h', 'E'):                              ['股票小时K线 - 收盘价', 'direct',
                                                       {'table_name': 'stock_hourly', 'column': 'close'}],
    ('volume', 'h', 'E'):                             ['股票小时K线 - 成交量 （手）', 'direct',
                                                       {'table_name': 'stock_hourly', 'column': 'vol'}],
    ('amount', 'h', 'E'):                             ['股票小时K线 - 成交额 （千元）', 'direct',
                                                       {'table_name': 'stock_hourly', 'column': 'amount'}],
    ('ths_open', 'd', 'IDX'):                         ['同花顺指数日K线 - 开盘价', 'direct',
                                                       {'table_name': 'ths_index_daily', 'column': 'open'}],
    ('ths_high', 'd', 'IDX'):                         ['同花顺指数日K线 - 最高价', 'direct',
                                                       {'table_name': 'ths_index_daily', 'column': 'high'}],
    ('ths_low', 'd', 'IDX'):                          ['同花顺指数日K线 - 最低价', 'direct',
                                                       {'table_name': 'ths_index_daily', 'column': 'low'}],
    ('ths_close', 'd', 'IDX'):                        ['同花顺指数日K线 - 收盘价', 'direct',
                                                       {'table_name': 'ths_index_daily', 'column': 'close'}],
    ('ths_change', 'd', 'IDX'):                       ['同花顺指数日K线 - 最低价', 'direct',
                                                       {'table_name': 'ths_index_daily', 'column': 'change'}],
    ('ths_avg_price', 'd', 'IDX'):                    ['同花顺指数日K线 - 平均价', 'direct',
                                                       {'table_name': 'ths_index_daily', 'column': 'avg_price'}],
    ('ths_pct_change', 'd', 'IDX'):                   ['同花顺指数日K线 - 涨跌幅', 'direct',
                                                       {'table_name': 'ths_index_daily', 'column': 'pct_change'}],
    ('ths_vol', 'd', 'IDX'):                          ['同花顺指数日K线 - 成交量 （万股）', 'direct',
                                                       {'table_name': 'ths_index_daily', 'column': 'vol'}],
    ('ths_turnover', 'd', 'IDX'):                     ['同花顺指数日K线 - 换手率', 'direct',
                                                       {'table_name': 'ths_index_daily', 'column': 'turnover_rate'}],
    ('ths_float_mv', 'd', 'IDX'):                     ['同花顺指数日K线 - 流通市值 （万元）', 'direct',
                                                       {'table_name': 'ths_index_daily', 'column': 'float_mv'}],
    ('ths_total_mv', 'd', 'IDX'):                     ['同花顺指数日K线 - 总市值 （万元）', 'direct',
                                                       {'table_name': 'ths_index_daily', 'column': 'total_mv'}],
    ('ci_open', 'd', 'IDX'):                          ['中信指数日K线 - 开盘价', 'direct',
                                                       {'table_name': 'ci_index_daily', 'column': 'open'}],
    ('ci_high', 'd', 'IDX'):                          ['中信指数日K线 - 最高价', 'direct',
                                                       {'table_name': 'ci_index_daily', 'column': 'high'}],
    ('ci_low', 'd', 'IDX'):                           ['中信指数日K线 - 最低价', 'direct',
                                                       {'table_name': 'ci_index_daily', 'column': 'low'}],
    ('ci_close', 'd', 'IDX'):                         ['中信指数日K线 - 收盘价', 'direct',
                                                       {'table_name': 'ci_index_daily', 'column': 'close'}],
    ('ci_change', 'd', 'IDX'):                        ['中信指数日K线 - 涨跌额', 'direct',
                                                       {'table_name': 'ci_index_daily', 'column': 'change'}],
    ('ci_pct_change', 'd', 'IDX'):                    ['中信指数日K线 - 涨跌幅', 'direct',
                                                       {'table_name': 'ci_index_daily', 'column': 'pct_change'}],
    ('ci_vol', 'd', 'IDX'):                           ['中信指数日K线 - 成交量 （万股）', 'direct',
                                                       {'table_name': 'ci_index_daily', 'column': 'vol'}],
    ('ci_amount', 'd', 'IDX'):                        ['中信指数日K线 - 成交额 （万元）', 'direct',
                                                       {'table_name': 'ci_index_daily', 'column': 'amount'}],
    ('ci_pre_close', 'd', 'IDX'):                     ['中信指数日K线 - 昨日收盘点位', 'direct',
                                                       {'table_name': 'ci_index_daily', 'column': 'pre_close'}],
    ('sw_open', 'd', 'IDX'):                          ['申万指数日K线 - 开盘价', 'direct',
                                                       {'table_name': 'sw_index_daily', 'column': 'open'}],
    ('sw_high', 'd', 'IDX'):                          ['申万指数日K线 - 最高价', 'direct',
                                                       {'table_name': 'sw_index_daily', 'column': 'high'}],
    ('sw_low', 'd', 'IDX'):                           ['申万指数日K线 - 最低价', 'direct',
                                                       {'table_name': 'sw_index_daily', 'column': 'low'}],
    ('sw_close', 'd', 'IDX'):                         ['申万指数日K线 - 收盘价', 'direct',
                                                       {'table_name': 'sw_index_daily', 'column': 'close'}],
    ('sw_change', 'd', 'IDX'):                        ['申万指数日K线 - 涨跌额', 'direct',
                                                       {'table_name': 'sw_index_daily', 'column': 'change'}],
    ('sw_pct_change', 'd', 'IDX'):                    ['申万指数日K线 - 涨跌幅', 'direct',
                                                       {'table_name': 'sw_index_daily', 'column': 'pct_change'}],
    ('sw_vol', 'd', 'IDX'):                           ['申万指数日K线 - 成交量 （万股）', 'direct',
                                                       {'table_name': 'sw_index_daily', 'column': 'vol'}],
    ('sw_amount', 'd', 'IDX'):                        ['申万指数日K线 - 成交额 （万元）', 'direct',
                                                       {'table_name': 'sw_index_daily', 'column': 'amount'}],
    ('sw_pe', 'd', 'IDX'):                            ['申万指数日K线 - 市盈率', 'direct',
                                                       {'table_name': 'sw_index_daily', 'column': 'pe'}],
    ('sw_pb', 'd', 'IDX'):                            ['申万指数日K线 - 市净率', 'direct',
                                                       {'table_name': 'sw_index_daily', 'column': 'pb'}],
    ('sw_float_mv', 'd', 'IDX'):                      ['申万指数日K线 - 流通市值 （万元）', 'direct',
                                                       {'table_name': 'sw_index_daily', 'column': 'float_mv'}],
    ('sw_total_mv', 'd', 'IDX'):                      ['申万指数日K线 - 总市值 （万元）', 'direct',
                                                       {'table_name': 'sw_index_daily', 'column': 'total_mv'}],
    ('g_index_open', 'd', 'IDX'):                     ['全球指数日K线行情 - 开盘价', 'direct',
                                                       {'table_name': 'global_index_daily', 'column': 'open'}],
    ('g_index_high', 'd', 'IDX'):                     ['全球指数日K线行情 - 最高价', 'direct',
                                                       {'table_name': 'global_index_daily', 'column': 'high'}],
    ('g_index_low', 'd', 'IDX'):                      ['全球指数日K线行情 - 最低价', 'direct',
                                                       {'table_name': 'global_index_daily', 'column': 'low'}],
    ('g_index_close', 'd', 'IDX'):                    [' 全球指数日K线行情 - 收盘价', 'direct',
                                                       {'table_name': 'global_index_daily', 'column': 'close'}],
    ('g_index_change', 'd', 'IDX'):                   ['全球指数日K线行情 - 最低价', 'direct',
                                                       {'table_name': 'global_index_daily', 'column': 'change'}],
    ('g_index_pct_change', 'd', 'IDX'):               ['全球指数日K线行情 - 收盘价', 'direct',
                                                       {'table_name': 'global_index_daily', 'column': 'pct_chg'}],
    ('g_index_vol', 'd', 'IDX'):                      ['全球指数日K线行情 - 成交量', 'direct',
                                                       {'table_name': 'global_index_daily', 'column': 'vol'}],
    ('g_index_amount', 'd', 'IDX'):                   ['全球指数日K线行情 - 成交额', 'direct',
                                                       {'table_name': 'global_index_daily', 'column': 'amount'}],
    ('g_index_pre_close', 'd', 'IDX'):                ['全球指数日K线行情 - 昨日收盘价', 'direct',
                                                       {'table_name': 'global_index_daily', 'column': 'pre_close'}],
    ('g_index_swing', 'd', 'IDX'):                    ['全球指数日K线行情 - 振幅', 'direct',
                                                       {'table_name': 'global_index_daily', 'column': 'swing'}],
    ('open', 'd', 'IDX'):                             ['指数日K线 - 开盘价', 'direct',
                                                       {'table_name': 'index_daily', 'column': 'open'}],
    ('high', 'd', 'IDX'):                             ['指数日K线 - 最高价', 'direct',
                                                       {'table_name': 'index_daily', 'column': 'high'}],
    ('low', 'd', 'IDX'):                              ['指数日K线 - 最低价', 'direct',
                                                       {'table_name': 'index_daily', 'column': 'low'}],
    ('close', 'd', 'IDX'):                            ['指数日K线 - 收盘价', 'direct',
                                                       {'table_name': 'index_daily', 'column': 'close'}],
    ('volume', 'd', 'IDX'):                           ['指数日K线 - 成交量 （手）', 'direct',
                                                       {'table_name': 'index_daily', 'column': 'vol'}],
    ('amount', 'd', 'IDX'):                           ['指数日K线 - 成交额 （千元）', 'direct',
                                                       {'table_name': 'index_daily', 'column': 'amount'}],
    ('open', 'w', 'IDX'):                             ['指数周K线 - 开盘价', 'direct',
                                                       {'table_name': 'index_weekly', 'column': 'open'}],
    ('high', 'w', 'IDX'):                             ['指数周K线 - 最高价', 'direct',
                                                       {'table_name': 'index_weekly', 'column': 'high'}],
    ('low', 'w', 'IDX'):                              ['指数周K线 - 最低价', 'direct',
                                                       {'table_name': 'index_weekly', 'column': 'low'}],
    ('close', 'w', 'IDX'):                            ['指数周K线 - 收盘价', 'direct',
                                                       {'table_name': 'index_weekly', 'column': 'close'}],
    ('volume', 'w', 'IDX'):                           ['指数周K线 - 成交量 （手）', 'direct',
                                                       {'table_name': 'index_weekly', 'column': 'vol'}],
    ('amount', 'w', 'IDX'):                           ['指数周K线 - 成交额 （千元）', 'direct',
                                                       {'table_name': 'index_weekly', 'column': 'amount'}],
    ('open', 'm', 'IDX'):                             ['指数月K线 - 开盘价', 'direct',
                                                       {'table_name': 'index_monthly', 'column': 'open'}],
    ('high', 'm', 'IDX'):                             ['指数月K线 - 最高价', 'direct',
                                                       {'table_name': 'index_monthly', 'column': 'high'}],
    ('low', 'm', 'IDX'):                              ['指数月K线 - 最低价', 'direct',
                                                       {'table_name': 'index_monthly', 'column': 'low'}],
    ('close', 'm', 'IDX'):                            ['指数月K线 - 收盘价', 'direct',
                                                       {'table_name': 'index_monthly', 'column': 'close'}],
    ('volume', 'm', 'IDX'):                           ['指数月K线 - 成交量 （手）', 'direct',
                                                       {'table_name': 'index_monthly', 'column': 'vol'}],
    ('amount', 'm', 'IDX'):                           ['指数月K线 - 成交额 （千元）', 'direct',
                                                       {'table_name': 'index_monthly', 'column': 'amount'}],
    ('open', '1min', 'IDX'):                          ['指数60秒K线 - 开盘价', 'direct',
                                                       {'table_name': 'index_1min', 'column': 'open'}],
    ('high', '1min', 'IDX'):                          ['指数60秒K线 - 最高价', 'direct',
                                                       {'table_name': 'index_1min', 'column': 'high'}],
    ('low', '1min', 'IDX'):                           ['指数60秒K线 - 最低价', 'direct',
                                                       {'table_name': 'index_1min', 'column': 'low'}],
    ('close', '1min', 'IDX'):                         ['指数60秒K线 - 收盘价', 'direct',
                                                       {'table_name': 'index_1min', 'column': 'close'}],
    ('volume', '1min', 'IDX'):                        ['指数60秒K线 - 成交量 （手）', 'direct',
                                                       {'table_name': 'index_1min', 'column': 'vol'}],
    ('amount', '1min', 'IDX'):                        ['指数60秒K线 - 成交额 （千元）', 'direct',
                                                       {'table_name': 'index_1min', 'column': 'amount'}],
    ('open', '5min', 'IDX'):                          ['指数5分钟K线 - 开盘价', 'direct',
                                                       {'table_name': 'index_5min', 'column': 'open'}],
    ('high', '5min', 'IDX'):                          ['指数5分钟K线 - 最高价', 'direct',
                                                       {'table_name': 'index_5min', 'column': 'high'}],
    ('low', '5min', 'IDX'):                           ['指数5分钟K线 - 最低价', 'direct',
                                                       {'table_name': 'index_5min', 'column': 'low'}],
    ('close', '5min', 'IDX'):                         ['指数5分钟K线 - 收盘价', 'direct',
                                                       {'table_name': 'index_5min', 'column': 'close'}],
    ('volume', '5min', 'IDX'):                        ['指数5分钟K线 - 成交量 （手）', 'direct',
                                                       {'table_name': 'index_5min', 'column': 'vol'}],
    ('amount', '5min', 'IDX'):                        ['指数5分钟K线 - 成交额 （千元）', 'direct',
                                                       {'table_name': 'index_5min', 'column': 'amount'}],
    ('open', '15min', 'IDX'):                         ['指数15分钟K线 - 开盘价', 'direct',
                                                       {'table_name': 'index_15min', 'column': 'open'}],
    ('high', '15min', 'IDX'):                         ['指数15分钟K线 - 最高价', 'direct',
                                                       {'table_name': 'index_15min', 'column': 'high'}],
    ('low', '15min', 'IDX'):                          ['指数15分钟K线 - 最低价', 'direct',
                                                       {'table_name': 'index_15min', 'column': 'low'}],
    ('close', '15min', 'IDX'):                        ['指数15分钟K线 - 收盘价', 'direct',
                                                       {'table_name': 'index_15min', 'column': 'close'}],
    ('volume', '15min', 'IDX'):                       ['指数15分钟K线 - 成交量 （手）', 'direct',
                                                       {'table_name': 'index_15min', 'column': 'vol'}],
    ('amount', '15min', 'IDX'):                       ['指数15分钟K线 - 成交额 （千元）', 'direct',
                                                       {'table_name': 'index_15min', 'column': 'amount'}],
    ('open', '30min', 'IDX'):                         ['指数30分钟K线 - 开盘价', 'direct',
                                                       {'table_name': 'index_30min', 'column': 'open'}],
    ('high', '30min', 'IDX'):                         ['指数30分钟K线 - 最高价', 'direct',
                                                       {'table_name': 'index_30min', 'column': 'high'}],
    ('low', '30min', 'IDX'):                          ['指数30分钟K线 - 最低价', 'direct',
                                                       {'table_name': 'index_30min', 'column': 'low'}],
    ('close', '30min', 'IDX'):                        ['指数30分钟K线 - 收盘价', 'direct',
                                                       {'table_name': 'index_30min', 'column': 'close'}],
    ('volume', '30min', 'IDX'):                       ['指数30分钟K线 - 成交量 （手）', 'direct',
                                                       {'table_name': 'index_30min', 'column': 'vol'}],
    ('amount', '30min', 'IDX'):                       ['指数30分钟K线 - 成交额 （千元）', 'direct',
                                                       {'table_name': 'index_30min', 'column': 'amount'}],
    ('open', 'h', 'IDX'):                             ['指数小时K线 - 开盘价', 'direct',
                                                       {'table_name': 'index_hourly', 'column': 'open'}],
    ('high', 'h', 'IDX'):                             ['指数小时K线 - 最高价', 'direct',
                                                       {'table_name': 'index_hourly', 'column': 'high'}],
    ('low', 'h', 'IDX'):                              ['指数小时K线 - 最低价', 'direct',
                                                       {'table_name': 'index_hourly', 'column': 'low'}],
    ('close', 'h', 'IDX'):                            ['指数小时K线 - 收盘价', 'direct',
                                                       {'table_name': 'index_hourly', 'column': 'close'}],
    ('volume', 'h', 'IDX'):                           ['指数小时K线 - 成交量 （手）', 'direct',
                                                       {'table_name': 'index_hourly', 'column': 'vol'}],
    ('amount', 'h', 'IDX'):                           ['指数小时K线 - 成交额 （千元）', 'direct',
                                                       {'table_name': 'index_hourly', 'column': 'amount'}],
    ('open', 'd', 'FT'):                              ['期货日K线 - 开盘价', 'direct',
                                                       {'table_name': 'future_daily', 'column': 'open'}],
    ('high', 'd', 'FT'):                              ['期货日K线 - 最高价', 'direct',
                                                       {'table_name': 'future_daily', 'column': 'high'}],
    ('low', 'd', 'FT'):                               ['期货日K线 - 最低价', 'direct',
                                                       {'table_name': 'future_daily', 'column': 'low'}],
    ('close', 'd', 'FT'):                             ['期货日K线 - 收盘价', 'direct',
                                                       {'table_name': 'future_daily', 'column': 'close'}],
    ('volume', 'd', 'FT'):                            ['期货日K线 - 成交量 （手）', 'direct',
                                                       {'table_name': 'future_daily', 'column': 'vol'}],
    ('amount', 'd', 'FT'):                            ['期货日K线 - 成交额 （千元）', 'direct',
                                                       {'table_name': 'future_daily', 'column': 'amount'}],
    ('settle', 'd', 'FT'):                            ['期货日K线 - 结算价', 'direct',
                                                       {'table_name': 'future_daily', 'column': 'settle'}],
    ('close_chg', 'd', 'FT'):                         ['期货日K线 - 收盘价涨跌', 'direct',
                                                       {'table_name': 'future_daily', 'column': 'change1'}],
    ('settle_chg', 'd', 'FT'):                        ['期货日K线 - 结算价涨跌', 'direct',
                                                       {'table_name': 'future_daily', 'column': 'change2'}],
    ('oi', 'd', 'FT'):                                ['期货日K线 - 持仓量（手）', 'direct',
                                                       {'table_name': 'future_daily', 'column': 'oi'}],
    ('oi_chg', 'd', 'FT'):                            ['期货日K线 - 持仓量变化', 'direct',
                                                       {'table_name': 'future_daily', 'column': 'oi_chg'}],
    ('delf_settle', 'd', 'FT'):                       ['期货日K线 - 交割结算价', 'direct',
                                                       {'table_name': 'future_daily', 'column': 'delv_settle'}],
    ('open', 'w', 'FT'):                              ['期货周K线 - 开盘价', 'direct',
                                                       {'table_name': 'future_weekly', 'column': 'open'}],
    ('high', 'w', 'FT'):                              ['期货周K线 - 最高价', 'direct',
                                                       {'table_name': 'future_weekly', 'column': 'high'}],
    ('low', 'w', 'FT'):                               ['期货周K线 - 最低价', 'direct',
                                                       {'table_name': 'future_weekly', 'column': 'low'}],
    ('close', 'w', 'FT'):                             ['期货周K线 - 收盘价', 'direct',
                                                       {'table_name': 'future_weekly', 'column': 'close'}],
    ('volume', 'w', 'FT'):                            ['期货周K线 - 成交量（手）', 'direct',
                                                       {'table_name': 'future_weekly', 'column': 'vol'}],
    ('amount', 'w', 'FT'):                            ['期货周K线 - 成交额 （千元）', 'direct',
                                                       {'table_name': 'future_weekly', 'column': 'amount'}],
    ('settle', 'w', 'FT'):                            ['期货周K线 - 结算价', 'direct',
                                                       {'table_name': 'future_weekly', 'column': 'settle'}],
    ('close_chg', 'w', 'FT'):                         ['期货周K线 - 收盘价涨跌', 'direct',
                                                       {'table_name': 'future_weekly', 'column': 'change1'}],
    ('settle_chg', 'w', 'FT'):                        ['期货周K线 - 结算价涨跌', 'direct',
                                                       {'table_name': 'future_weekly', 'column': 'change2'}],
    ('oi', 'w', 'FT'):                                ['期货周K线 - 持仓量（手）', 'direct',
                                                       {'table_name': 'future_weekly', 'column': 'oi'}],
    ('oi_chg', 'w', 'FT'):                            ['期货周K线 - 持仓量变化', 'direct',
                                                       {'table_name': 'future_weekly', 'column': 'oi_chg'}],
    ('delf_settle', 'w', 'FT'):                       ['期货周K线 - 交割结算价', 'direct',
                                                       {'table_name': 'future_weekly', 'column': 'delv_settle'}],
    ('open', 'm', 'FT'):                              ['期货月K线 - 开盘价', 'direct',
                                                       {'table_name': 'future_monthly', 'column': 'open'}],
    ('high', 'm', 'FT'):                              ['期货月K线 - 最高价', 'direct',
                                                       {'table_name': 'future_monthly', 'column': 'high'}],
    ('low', 'm', 'FT'):                               ['期货月K线 - 最低价', 'direct',
                                                       {'table_name': 'future_monthly', 'column': 'low'}],
    ('close', 'm', 'FT'):                             ['期货月K线 - 收盘价', 'direct',
                                                       {'table_name': 'future_monthly', 'column': 'close'}],
    ('volume', 'm', 'FT'):                            ['期货月K线 - 成交量（手）', 'direct',
                                                       {'table_name': 'future_monthly', 'column': 'vol'}],
    ('amount', 'm', 'FT'):                            ['期货月K线 - 成交额 （千元）', 'direct',
                                                       {'table_name': 'future_monthly', 'column': 'amount'}],
    ('settle', 'm', 'FT'):                            ['期货月K线 - 结算价', 'direct',
                                                       {'table_name': 'future_monthly', 'column': 'settle'}],
    ('close_chg', 'm', 'FT'):                         ['期货月K线 - 收盘价涨跌', 'direct',
                                                       {'table_name': 'future_monthly', 'column': 'change1'}],
    ('settle_chg', 'm', 'FT'):                        ['期货月K线 - 结算价涨跌', 'direct',
                                                       {'table_name': 'future_monthly', 'column': 'change2'}],
    ('oi', 'm', 'FT'):                                ['期货月K线 - 持仓量（手）', 'direct',
                                                       {'table_name': 'future_monthly', 'column': 'oi'}],
    ('oi_chg', 'm', 'FT'):                            ['期货月K线 - 持仓量变化', 'direct',
                                                       {'table_name': 'future_monthly', 'column': 'oi_chg'}],
    ('delf_settle', 'm', 'FT'):                       ['期货月K线 - 交割结算价', 'direct',
                                                       {'table_name': 'future_monthly', 'column': 'delv_settle'}],
    ('open', '1min', 'FT'):                           ['期货60秒K线 - 开盘价', 'direct',
                                                       {'table_name': 'future_1min', 'column': 'open'}],
    ('high', '1min', 'FT'):                           ['期货60秒K线 - 最高价', 'direct',
                                                       {'table_name': 'future_1min', 'column': 'high'}],
    ('low', '1min', 'FT'):                            ['期货60秒K线 - 最低价', 'direct',
                                                       {'table_name': 'future_1min', 'column': 'low'}],
    ('close', '1min', 'FT'):                          ['期货60秒K线 - 收盘价', 'direct',
                                                       {'table_name': 'future_1min', 'column': 'close'}],
    ('volume', '1min', 'FT'):                         ['期货60秒K线 - 成交量 （手）', 'direct',
                                                       {'table_name': 'future_1min', 'column': 'vol'}],
    ('amount', '1min', 'FT'):                         ['期货60秒K线 - 成交额 （千元）', 'direct',
                                                       {'table_name': 'future_1min', 'column': 'amount'}],
    ('open', '5min', 'FT'):                           ['期货5分钟K线 - 开盘价', 'direct',
                                                       {'table_name': 'future_5min', 'column': 'open'}],
    ('high', '5min', 'FT'):                           ['期货5分钟K线 - 最高价', 'direct',
                                                       {'table_name': 'future_5min', 'column': 'high'}],
    ('low', '5min', 'FT'):                            ['期货5分钟K线 - 最低价', 'direct',
                                                       {'table_name': 'future_5min', 'column': 'low'}],
    ('close', '5min', 'FT'):                          ['期货5分钟K线 - 收盘价', 'direct',
                                                       {'table_name': 'future_5min', 'column': 'close'}],
    ('volume', '5min', 'FT'):                         ['期货5分钟K线 - 成交量 （手）', 'direct',
                                                       {'table_name': 'future_5min', 'column': 'vol'}],
    ('amount', '5min', 'FT'):                         ['期货5分钟K线 - 成交额 （千元）', 'direct',
                                                       {'table_name': 'future_5min', 'column': 'amount'}],
    ('open', '15min', 'FT'):                          ['期货15分钟K线 - 开盘价', 'direct',
                                                       {'table_name': 'future_15min', 'column': 'open'}],
    ('high', '15min', 'FT'):                          ['期货15分钟K线 - 最高价', 'direct',
                                                       {'table_name': 'future_15min', 'column': 'high'}],
    ('low', '15min', 'FT'):                           ['期货15分钟K线 - 最低价', 'direct',
                                                       {'table_name': 'future_15min', 'column': 'low'}],
    ('close', '15min', 'FT'):                         ['期货15分钟K线 - 收盘价', 'direct',
                                                       {'table_name': 'future_15min', 'column': 'close'}],
    ('volume', '15min', 'FT'):                        ['期货15分钟K线 - 成交量 （手）', 'direct',
                                                       {'table_name': 'future_15min', 'column': 'vol'}],
    ('amount', '15min', 'FT'):                        ['期货15分钟K线 - 成交额 （千元）', 'direct',
                                                       {'table_name': 'future_15min', 'column': 'amount'}],
    ('open', '30min', 'FT'):                          ['期货30分钟K线 - 开盘价', 'direct',
                                                       {'table_name': 'future_30min', 'column': 'open'}],
    ('high', '30min', 'FT'):                          ['期货30分钟K线 - 最高价', 'direct',
                                                       {'table_name': 'future_30min', 'column': 'high'}],
    ('low', '30min', 'FT'):                           ['期货30分钟K线 - 最低价', 'direct',
                                                       {'table_name': 'future_30min', 'column': 'low'}],
    ('close', '30min', 'FT'):                         ['期货30分钟K线 - 收盘价', 'direct',
                                                       {'table_name': 'future_30min', 'column': 'close'}],
    ('volume', '30min', 'FT'):                        ['期货30分钟K线 - 成交量 （手）', 'direct',
                                                       {'table_name': 'future_30min', 'column': 'vol'}],
    ('amount', '30min', 'FT'):                        ['期货30分钟K线 - 成交额 （千元）', 'direct',
                                                       {'table_name': 'future_30min', 'column': 'amount'}],
    ('open', 'h', 'FT'):                              ['期货小时K线 - 开盘价', 'direct',
                                                       {'table_name': 'future_hourly', 'column': 'open'}],
    ('high', 'h', 'FT'):                              ['期货小时K线 - 最高价', 'direct',
                                                       {'table_name': 'future_hourly', 'column': 'high'}],
    ('low', 'h', 'FT'):                               ['期货小时K线 - 最低价', 'direct',
                                                       {'table_name': 'future_hourly', 'column': 'low'}],
    ('close', 'h', 'FT'):                             ['期货小时K线 - 收盘价', 'direct',
                                                       {'table_name': 'future_hourly', 'column': 'close'}],
    ('volume', 'h', 'FT'):                            ['期货小时K线 - 成交量 （手）', 'direct',
                                                       {'table_name': 'future_hourly', 'column': 'vol'}],
    ('amount', 'h', 'FT'):                            ['期货小时K线 - 成交额 （千元）', 'direct',
                                                       {'table_name': 'future_hourly', 'column': 'amount'}],
    ('open', 'd', 'OPT'):                             ['期权日K线 - 开盘价', 'direct',
                                                       {'table_name': 'options_daily', 'column': 'open'}],
    ('high', 'd', 'OPT'):                             ['期权日K线 - 最高价', 'direct',
                                                       {'table_name': 'options_daily', 'column': 'high'}],
    ('low', 'd', 'OPT'):                              ['期权日K线 - 最低价', 'direct',
                                                       {'table_name': 'options_daily', 'column': 'low'}],
    ('close', 'd', 'OPT'):                            ['期权日K线 - 收盘价', 'direct',
                                                       {'table_name': 'options_daily', 'column': 'close'}],
    ('volume', 'd', 'OPT'):                           ['期权日K线 - 成交量 （手）', 'direct',
                                                       {'table_name': 'options_daily', 'column': 'vol'}],
    ('amount', 'd', 'OPT'):                           ['期权日K线 - 成交额 （千元）', 'direct',
                                                       {'table_name': 'options_daily', 'column': 'amount'}],
    ('open', '1min', 'OPT'):                          ['期权60秒K线 - 开盘价', 'direct',
                                                       {'table_name': 'options_1min', 'column': 'open'}],
    ('high', '1min', 'OPT'):                          ['期权60秒K线 - 最高价', 'direct',
                                                       {'table_name': 'options_1min', 'column': 'high'}],
    ('low', '1min', 'OPT'):                           ['期权60秒K线 - 最低价', 'direct',
                                                       {'table_name': 'options_1min', 'column': 'low'}],
    ('close', '1min', 'OPT'):                         ['期权60秒K线 - 收盘价', 'direct',
                                                       {'table_name': 'options_1min', 'column': 'close'}],
    ('volume', '1min', 'OPT'):                        ['期权60秒K线 - 成交量 （手）', 'direct',
                                                       {'table_name': 'options_1min', 'column': 'vol'}],
    ('amount', '1min', 'OPT'):                        ['期权60秒K线 - 成交额 （千元）', 'direct',
                                                       {'table_name': 'options_1min', 'column': 'amount'}],
    ('open', '5min', 'OPT'):                          ['期权5分钟K线 - 开盘价', 'direct',
                                                       {'table_name': 'options_5min', 'column': 'open'}],
    ('high', '5min', 'OPT'):                          ['期权5分钟K线 - 最高价', 'direct',
                                                       {'table_name': 'options_5min', 'column': 'high'}],
    ('low', '5min', 'OPT'):                           ['期权5分钟K线 - 最低价', 'direct',
                                                       {'table_name': 'options_5min', 'column': 'low'}],
    ('close', '5min', 'OPT'):                         ['期权5分钟K线 - 收盘价', 'direct',
                                                       {'table_name': 'options_5min', 'column': 'close'}],
    ('volume', '5min', 'OPT'):                        ['期权5分钟K线 - 成交量 （手）', 'direct',
                                                       {'table_name': 'options_5min', 'column': 'vol'}],
    ('amount', '5min', 'OPT'):                        ['期权5分钟K线 - 成交额 （千元）', 'direct',
                                                       {'table_name': 'options_5min', 'column': 'amount'}],
    ('open', '15min', 'OPT'):                         ['期权15分钟K线 - 开盘价', 'direct',
                                                       {'table_name': 'options_15min', 'column': 'open'}],
    ('high', '15min', 'OPT'):                         ['期权15分钟K线 - 最高价', 'direct',
                                                       {'table_name': 'options_15min', 'column': 'high'}],
    ('low', '15min', 'OPT'):                          ['期权15分钟K线 - 最低价', 'direct',
                                                       {'table_name': 'options_15min', 'column': 'low'}],
    ('close', '15min', 'OPT'):                        ['期权15分钟K线 - 收盘价', 'direct',
                                                       {'table_name': 'options_15min', 'column': 'close'}],
    ('volume', '15min', 'OPT'):                       ['期权15分钟K线 - 成交量 （手）', 'direct',
                                                       {'table_name': 'options_15min', 'column': 'vol'}],
    ('amount', '15min', 'OPT'):                       ['期权15分钟K线 - 成交额 （千元）', 'direct',
                                                       {'table_name': 'options_15min', 'column': 'amount'}],
    ('open', '30min', 'OPT'):                         ['期权30分钟K线 - 开盘价', 'direct',
                                                       {'table_name': 'options_30min', 'column': 'open'}],
    ('high', '30min', 'OPT'):                         ['期权30分钟K线 - 最高价', 'direct',
                                                       {'table_name': 'options_30min', 'column': 'high'}],
    ('low', '30min', 'OPT'):                          ['期权30分钟K线 - 最低价', 'direct',
                                                       {'table_name': 'options_30min', 'column': 'low'}],
    ('close', '30min', 'OPT'):                        ['期权30分钟K线 - 收盘价', 'direct',
                                                       {'table_name': 'options_30min', 'column': 'close'}],
    ('volume', '30min', 'OPT'):                       ['期权30分钟K线 - 成交量 （手）', 'direct',
                                                       {'table_name': 'options_30min', 'column': 'vol'}],
    ('amount', '30min', 'OPT'):                       ['期权30分钟K线 - 成交额 （千元）', 'direct',
                                                       {'table_name': 'options_30min', 'column': 'amount'}],
    ('open', 'h', 'OPT'):                             ['期权小时K线 - 开盘价', 'direct',
                                                       {'table_name': 'options_hourly', 'column': 'open'}],
    ('high', 'h', 'OPT'):                             ['期权小时K线 - 最高价', 'direct',
                                                       {'table_name': 'options_hourly', 'column': 'high'}],
    ('low', 'h', 'OPT'):                              ['期权小时K线 - 最低价', 'direct',
                                                       {'table_name': 'options_hourly', 'column': 'low'}],
    ('close', 'h', 'OPT'):                            ['期权小时K线 - 收盘价', 'direct',
                                                       {'table_name': 'options_hourly', 'column': 'close'}],
    ('volume', 'h', 'OPT'):                           ['期权小时K线 - 成交量 （手）', 'direct',
                                                       {'table_name': 'options_hourly', 'column': 'vol'}],
    ('amount', 'h', 'OPT'):                           ['期权小时K线 - 成交额 （千元）', 'direct',
                                                       {'table_name': 'options_hourly', 'column': 'amount'}],
    ('open|%', 'd', 'FD'):                            ['基金日K线 - 复权开盘价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'fund_daily', 'column': 'open',
                                                        'adj_table':  'fund_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('high|%', 'd', 'FD'):                            ['基金日K线 - 复权最高价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'fund_daily', 'column': 'high',
                                                        'adj_table':  'fund_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('low|%', 'd', 'FD'):                             ['基金日K线 - 复权最低价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'fund_daily', 'column': 'low',
                                                        'adj_table':  'fund_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('close|%', 'd', 'FD'):                           ['基金日K线 - 复权收盘价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'fund_daily', 'column': 'close',
                                                        'adj_table':  'fund_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('open', 'd', 'FD'):                              ['基金日K线 - 开盘价', 'direct',
                                                       {'table_name': 'fund_daily', 'column': 'open'}],
    ('high', 'd', 'FD'):                              ['基金日K线 - 最高价', 'direct',
                                                       {'table_name': 'fund_daily', 'column': 'high'}],
    ('low', 'd', 'FD'):                               ['基金日K线 - 最低价', 'direct',
                                                       {'table_name': 'fund_daily', 'column': 'low'}],
    ('close', 'd', 'FD'):                             ['基金日K线 - 收盘价', 'direct',
                                                       {'table_name': 'fund_daily', 'column': 'close'}],
    ('volume', 'd', 'FD'):                            ['基金日K线 - 成交量 （手）', 'direct',
                                                       {'table_name': 'fund_daily', 'column': 'vol'}],
    ('amount', 'd', 'FD'):                            ['基金日K线 - 成交额 （千元）', 'direct',
                                                       {'table_name': 'fund_daily', 'column': 'amount'}],
    ('open|%', 'w', 'FD'):                            ['基金周K线 - 复权开盘价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'fund_weekly', 'column': 'open',
                                                        'adj_table':  'fund_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('high|%', 'w', 'FD'):                            ['基金周K线 - 复权最高价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'fund_weekly', 'column': 'high',
                                                        'adj_table':  'fund_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('low|%', 'w', 'FD'):                             ['基金周K线 - 复权最低价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'fund_weekly', 'column': 'low',
                                                        'adj_table':  'fund_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('close|%', 'w', 'FD'):                           ['基金周K线 - 复权收盘价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'fund_weekly', 'column': 'close',
                                                        'adj_table':  'fund_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('open', 'w', 'FD'):                              ['基金周K线 - 开盘价', 'direct',
                                                       {'table_name': 'fund_weekly', 'column': 'open'}],
    ('high', 'w', 'FD'):                              ['基金周K线 - 最高价', 'direct',
                                                       {'table_name': 'fund_weekly', 'column': 'high'}],
    ('low', 'w', 'FD'):                               ['基金周K线 - 最低价', 'direct',
                                                       {'table_name': 'fund_weekly', 'column': 'low'}],
    ('close', 'w', 'FD'):                             ['基金周K线 - 收盘价', 'direct',
                                                       {'table_name': 'fund_weekly', 'column': 'close'}],
    ('volume', 'w', 'FD'):                            ['基金周K线 - 成交量 （手）', 'direct',
                                                       {'table_name': 'fund_weekly', 'column': 'vol'}],
    ('amount', 'w', 'FD'):                            ['基金周K线 - 成交额 （千元）', 'direct',
                                                       {'table_name': 'fund_weekly', 'column': 'amount'}],
    ('open|%', 'm', 'FD'):                            ['基金月K线 - 复权开盘价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'fund_monthly', 'column': 'open',
                                                        'adj_table':  'fund_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('high|%', 'm', 'FD'):                            ['基金月K线 - 复权最高价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'fund_monthly', 'column': 'high',
                                                        'adj_table':  'fund_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('low|%', 'm', 'FD'):                             ['基金月K线 - 复权最低价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'fund_monthly', 'column': 'low',
                                                        'adj_table':  'fund_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('close|%', 'm', 'FD'):                           ['基金月K线 - 复权收盘价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'fund_monthly', 'column': 'close',
                                                        'adj_table':  'fund_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('open', 'm', 'FD'):                              ['基金月K线 - 开盘价', 'direct',
                                                       {'table_name': 'fund_monthly', 'column': 'open'}],
    ('high', 'm', 'FD'):                              ['基金月K线 - 最高价', 'direct',
                                                       {'table_name': 'fund_monthly', 'column': 'high'}],
    ('low', 'm', 'FD'):                               ['基金月K线 - 最低价', 'direct',
                                                       {'table_name': 'fund_monthly', 'column': 'low'}],
    ('close', 'm', 'FD'):                             ['基金月K线 - 收盘价', 'direct',
                                                       {'table_name': 'fund_monthly', 'column': 'close'}],
    ('volume', 'm', 'FD'):                            ['基金月K线 - 成交量 （手）', 'direct',
                                                       {'table_name': 'fund_monthly', 'column': 'vol'}],
    ('amount', 'm', 'FD'):                            ['基金月K线 - 成交额 （千元）', 'direct',
                                                       {'table_name': 'fund_monthly', 'column': 'amount'}],
    ('open|%', '1min', 'FD'):                         ['基金60秒K线 - 复权开盘价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'fund_1min', 'column': 'open',
                                                        'adj_table':  'fund_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('high|%', '1min', 'FD'):                         ['基金60秒K线 - 复权最高价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'fund_1min', 'column': 'high',
                                                        'adj_table':  'fund_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('low|%', '1min', 'FD'):                          ['基金60秒K线 - 复权最低价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'fund_1min', 'column': 'low',
                                                        'adj_table':  'fund_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('close|%', '1min', 'FD'):                        ['基金60秒K线 - 复权收盘价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'fund_1min', 'column': 'close',
                                                        'adj_table':  'fund_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('open', '1min', 'FD'):                           ['基金60秒K线 - 开盘价', 'direct',
                                                       {'table_name': 'fund_1min', 'column': 'open'}],
    ('high', '1min', 'FD'):                           ['基金60秒K线 - 最高价', 'direct',
                                                       {'table_name': 'fund_1min', 'column': 'high'}],
    ('low', '1min', 'FD'):                            ['基金60秒K线 - 最低价', 'direct',
                                                       {'table_name': 'fund_1min', 'column': 'low'}],
    ('close', '1min', 'FD'):                          ['基金60秒K线 - 收盘价', 'direct',
                                                       {'table_name': 'fund_1min', 'column': 'close'}],
    ('volume', '1min', 'FD'):                         ['基金60秒K线 - 成交量 （手）', 'direct',
                                                       {'table_name': 'fund_1min', 'column': 'vol'}],
    ('amount', '1min', 'FD'):                         ['基金60秒K线 - 成交额 （千元）', 'direct',
                                                       {'table_name': 'fund_1min', 'column': 'amount'}],
    ('open|%', '5min', 'FD'):                         ['基金5分钟K线 - 复权开盘价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'fund_5min', 'column': 'open',
                                                        'adj_table':  'fund_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('high|%', '5min', 'FD'):                         ['基金5分钟K线 - 复权最高价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'fund_5min', 'column': 'high',
                                                        'adj_table':  'fund_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('low|%', '5min', 'FD'):                          ['基金5分钟K线 - 复权最低价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'fund_5min', 'column': 'low',
                                                        'adj_table':  'fund_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('close|%', '5min', 'FD'):                        ['基金5分钟K线 - 复权收盘价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'fund_5min', 'column': 'close',
                                                        'adj_table':  'fund_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('open', '5min', 'FD'):                           ['基金5分钟K线 - 开盘价', 'direct',
                                                       {'table_name': 'fund_5min', 'column': 'open'}],
    ('high', '5min', 'FD'):                           ['基金5分钟K线 - 最高价', 'direct',
                                                       {'table_name': 'fund_5min', 'column': 'high'}],
    ('low', '5min', 'FD'):                            ['基金5分钟K线 - 最低价', 'direct',
                                                       {'table_name': 'fund_5min', 'column': 'low'}],
    ('close', '5min', 'FD'):                          ['基金5分钟K线 - 收盘价', 'direct',
                                                       {'table_name': 'fund_5min', 'column': 'close'}],
    ('volume', '5min', 'FD'):                         ['基金5分钟K线 - 成交量 （手）', 'direct',
                                                       {'table_name': 'fund_5min', 'column': 'vol'}],
    ('amount', '5min', 'FD'):                         ['基金5分钟K线 - 成交额 （千元）', 'direct',
                                                       {'table_name': 'fund_5min', 'column': 'amount'}],
    ('open|%', '15min', 'FD'):                        ['基金15分钟K线 - 复权开盘价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'fund_15min', 'column': 'open',
                                                        'adj_table':  'fund_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('high|%', '15min', 'FD'):                        ['基金15分钟K线 - 复权最高价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'fund_15min', 'column': 'high',
                                                        'adj_table':  'fund_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('low|%', '15min', 'FD'):                         ['基金15分钟K线 - 复权最低价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'fund_15min', 'column': 'low',
                                                        'adj_table':  'fund_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('close|%', '15min', 'FD'):                       ['基金15分钟K线 - 复权收盘价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'fund_15min', 'column': 'close',
                                                        'adj_table':  'fund_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('open', '15min', 'FD'):                          ['基金15分钟K线 - 开盘价', 'direct',
                                                       {'table_name': 'fund_15min', 'column': 'open'}],
    ('high', '15min', 'FD'):                          ['基金15分钟K线 - 最高价', 'direct',
                                                       {'table_name': 'fund_15min', 'column': 'high'}],
    ('low', '15min', 'FD'):                           ['基金15分钟K线 - 最低价', 'direct',
                                                       {'table_name': 'fund_15min', 'column': 'low'}],
    ('close', '15min', 'FD'):                         ['基金15分钟K线 - 收盘价', 'direct',
                                                       {'table_name': 'fund_15min', 'column': 'close'}],
    ('volume', '15min', 'FD'):                        ['基金15分钟K线 - 成交量 （手）', 'direct',
                                                       {'table_name': 'fund_15min', 'column': 'vol'}],
    ('amount', '15min', 'FD'):                        ['基金15分钟K线 - 成交额 （千元）', 'direct',
                                                       {'table_name': 'fund_15min', 'column': 'amount'}],
    ('open|%', '30min', 'FD'):                        ['基金30分钟K线 - 复权开盘价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'fund_30min', 'column': 'open',
                                                        'adj_table':  'fund_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('high|%', '30min', 'FD'):                        ['基金30分钟K线 - 复权最高价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'fund_30min', 'column': 'high',
                                                        'adj_table':  'fund_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('low|%', '30min', 'FD'):                         ['基金30分钟K线 - 复权最低价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'fund_30min', 'column': 'low',
                                                        'adj_table':  'fund_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('close|%', '30min', 'FD'):                       ['基金30分钟K线 - 复权收盘价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'fund_30min', 'column': 'close',
                                                        'adj_table':  'fund_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('open', '30min', 'FD'):                          ['基金30分钟K线 - 开盘价', 'direct',
                                                       {'table_name': 'fund_30min', 'column': 'open'}],
    ('high', '30min', 'FD'):                          ['基金30分钟K线 - 最高价', 'direct',
                                                       {'table_name': 'fund_30min', 'column': 'high'}],
    ('low', '30min', 'FD'):                           ['基金30分钟K线 - 最低价', 'direct',
                                                       {'table_name': 'fund_30min', 'column': 'low'}],
    ('close', '30min', 'FD'):                         ['基金30分钟K线 - 收盘价', 'direct',
                                                       {'table_name': 'fund_30min', 'column': 'close'}],
    ('volume', '30min', 'FD'):                        ['基金30分钟K线 - 成交量 （手）', 'direct',
                                                       {'table_name': 'fund_30min', 'column': 'vol'}],
    ('amount', '30min', 'FD'):                        ['基金30分钟K线 - 成交额 （千元）', 'direct',
                                                       {'table_name': 'fund_30min', 'column': 'amount'}],
    ('open|%', 'h', 'FD'):                            ['基金小时K线 - 复权开盘价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'fund_hourly', 'column': 'open',
                                                        'adj_table':  'fund_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('high|%', 'h', 'FD'):                            ['基金小时K线 - 复权最高价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'fund_hourly', 'column': 'high',
                                                        'adj_table':  'fund_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('low|%', 'h', 'FD'):                             ['基金小时K线 - 复权最低价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'fund_hourly', 'column': 'low',
                                                        'adj_table':  'fund_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('close|%', 'h', 'FD'):                           ['基金小时K线 - 复权收盘价-b:后复权f:前复权', 'adjustment',
                                                       {'table_name': 'fund_hourly', 'column': 'close',
                                                        'adj_table':  'fund_adj_factor', 'adj_column': 'adj_factor',
                                                        'adj_type':   '%'}],
    ('open', 'h', 'FD'):                              ['基金小时K线 - 开盘价', 'direct',
                                                       {'table_name': 'fund_hourly', 'column': 'open'}],
    ('high', 'h', 'FD'):                              ['基金小时K线 - 最高价', 'direct',
                                                       {'table_name': 'fund_hourly', 'column': 'high'}],
    ('low', 'h', 'FD'):                               ['基金小时K线 - 最低价', 'direct',
                                                       {'table_name': 'fund_hourly', 'column': 'low'}],
    ('close', 'h', 'FD'):                             ['基金小时K线 - 收盘价', 'direct',
                                                       {'table_name': 'fund_hourly', 'column': 'close'}],
    ('volume', 'h', 'FD'):                            ['基金小时K线 - 成交量 （手）', 'direct',
                                                       {'table_name': 'fund_hourly', 'column': 'vol'}],
    ('amount', 'h', 'FD'):                            ['基金小时K线 - 成交额 （千元）', 'direct',
                                                       {'table_name': 'fund_hourly', 'column': 'amount'}],
    ('unit_nav', 'd', 'FD'):                          ['基金净值 - 单位净值', 'direct',
                                                       {'table_name': 'fund_nav', 'column': 'unit_nav'}],
    ('accum_nav', 'd', 'FD'):                         ['基金净值 - 累计净值', 'direct',
                                                       {'table_name': 'fund_nav', 'column': 'accum_nav'}],
    ('accum_div', 'd', 'FD'):                         ['基金净值 - 累计分红', 'direct',
                                                       {'table_name': 'fund_nav', 'column': 'accum_div'}],
    ('net_asset', 'd', 'FD'):                         ['基金净值 - 资产净值', 'direct',
                                                       {'table_name': 'fund_nav', 'column': 'net_asset'}],
    ('total_netasset', 'd', 'FD'):                    ['基金净值 - 累计资产净值', 'direct',
                                                       {'table_name': 'fund_nav', 'column': 'total_netasset'}],
    ('adj_nav', 'd', 'FD'):                           ['基金净值 - 复权净值', 'direct',
                                                       {'table_name': 'fund_nav', 'column': 'adj_nav'}],
    ('buy_sm_vol', 'd', 'E'):                         ['个股资金流向 - 小单买入量（手）', 'direct',
                                                       {'table_name': 'money_flow', 'column': 'buy_sm_vol'}],
    ('buy_sm_amount', 'd', 'E'):                      ['个股资金流向 - 小单买入金额（万元）', 'direct',
                                                       {'table_name': 'money_flow', 'column': 'buy_sm_amount'}],
    ('sell_sm_vol', 'd', 'E'):                        ['个股资金流向 - 小单卖出量（手）', 'direct',
                                                       {'table_name': 'money_flow', 'column': 'sell_sm_vol'}],
    ('sell_sm_amount', 'd', 'E'):                     ['个股资金流向 - 小单卖出金额（万元）', 'direct',
                                                       {'table_name': 'money_flow', 'column': 'sell_sm_amount'}],
    ('buy_md_vol', 'd', 'E'):                         ['个股资金流向 - 中单买入量（手）', 'direct',
                                                       {'table_name': 'money_flow', 'column': 'buy_md_vol'}],
    ('buy_md_amount', 'd', 'E'):                      ['个股资金流向 - 中单买入金额（万元）', 'direct',
                                                       {'table_name': 'money_flow', 'column': 'buy_md_amount'}],
    ('sell_md_vol', 'd', 'E'):                        ['个股资金流向 - 中单卖出量（手）', 'direct',
                                                       {'table_name': 'money_flow', 'column': 'sell_md_vol'}],
    ('sell_md_amount', 'd', 'E'):                     ['个股资金流向 - 中单卖出金额（万元）', 'direct',
                                                       {'table_name': 'money_flow', 'column': 'sell_md_amount'}],
    ('buy_lg_vol', 'd', 'E'):                         ['个股资金流向 - 大单买入量（手）', 'direct',
                                                       {'table_name': 'money_flow', 'column': 'buy_lg_vol'}],
    ('buy_lg_amount', 'd', 'E'):                      ['个股资金流向 - 大单买入金额（万元）', 'direct',
                                                       {'table_name': 'money_flow', 'column': 'buy_lg_amount'}],
    ('sell_lg_vol', 'd', 'E'):                        ['个股资金流向 - 大单卖出量（手）', 'direct',
                                                       {'table_name': 'money_flow', 'column': 'sell_lg_vol'}],
    ('sell_lg_amount', 'd', 'E'):                     ['个股资金流向 - 大单卖出金额（万元）', 'direct',
                                                       {'table_name': 'money_flow', 'column': 'sell_lg_amount'}],
    ('buy_elg_vol', 'd', 'E'):                        ['个股资金流向 - 特大单买入量（手）', 'direct',
                                                       {'table_name': 'money_flow', 'column': 'buy_elg_vol'}],
    ('buy_elg_amount', 'd', 'E'):                     ['个股资金流向 - 特大单买入金额（万元）', 'direct',
                                                       {'table_name': 'money_flow', 'column': 'buy_elg_amount'}],
    ('sell_elg_vol', 'd', 'E'):                       ['个股资金流向 - 特大单卖出量（手）', 'direct',
                                                       {'table_name': 'money_flow', 'column': 'sell_elg_vol'}],
    ('sell_elg_amount', 'd', 'E'):                    ['个股资金流向 - 特大单卖出金额（万元）', 'direct',
                                                       {'table_name': 'money_flow', 'column': 'sell_elg_amount'}],
    ('net_mf_vol', 'd', 'E'):                         ['个股资金流向 - 净流入量（手）', 'direct',
                                                       {'table_name': 'money_flow', 'column': 'net_mf_vol'}],
    ('net_mf_amount', 'd', 'E'):                      ['个股资金流向 - 净流入额（万元）', 'direct',
                                                       {'table_name': 'money_flow', 'column': 'net_mf_amount'}],
    ('up_limit', 'd', 'E'):                           ['涨停板 - 涨停价', 'direct',
                                                       {'table_name': 'stock_limit', 'column': 'up_limit'}],
    ('down_limit', 'd', 'E'):                         ['跌停板 - 跌停价', 'direct',
                                                       {'table_name': 'stock_limit', 'column': 'down_limit'}],
    ('ggt_ss', 'd', 'Any'):                           ['沪深港通资金流向 - 港股通（上海）', 'reference',
                                                       {'table_name': 'hs_money_flow', 'column': 'ggt_ss'}],
    ('ggt_sz', 'd', 'Any'):                           ['沪深港通资金流向 - 港股通（深圳）', 'reference',
                                                       {'table_name': 'hs_money_flow', 'column': 'ggt_sz'}],
    ('hgt', 'd', 'Any'):                              ['沪深港通资金流向 - 沪股通（百万元）', 'reference',
                                                       {'table_name': 'hs_money_flow', 'column': 'hgt'}],
    ('sgt', 'd', 'Any'):                              ['沪深港通资金流向 - 深股通（百万元）', 'reference',
                                                       {'table_name': 'hs_money_flow', 'column': 'sgt'}],
    ('north_money', 'd', 'Any'):                      ['沪深港通资金流向 - 北向资金（百万元）', 'reference',
                                                       {'table_name': 'hs_money_flow', 'column': 'north_money'}],
    ('south_money', 'd', 'Any'):                      ['沪深港通资金流向 - 南向资金（百万元）', 'reference',
                                                       {'table_name': 'hs_money_flow', 'column': 'south_money'}],
    ('basic_eps', 'q', 'E'):                          ['上市公司利润表 - 基本每股收益', 'direct',
                                                       {'table_name': 'income', 'column': 'basic_eps'}],
    ('diluted_eps', 'q', 'E'):                        ['上市公司利润表 - 稀释每股收益', 'direct',
                                                       {'table_name': 'income', 'column': 'diluted_eps'}],
    ('total_revenue', 'q', 'E'):                      ['上市公司利润表 - 营业总收入', 'direct',
                                                       {'table_name': 'income', 'column': 'total_revenue'}],
    ('revenue', 'q', 'E'):                            ['上市公司利润表 - 营业收入', 'direct',
                                                       {'table_name': 'income', 'column': 'revenue'}],
    ('int_income', 'q', 'E'):                         ['上市公司利润表 - 利息收入', 'direct',
                                                       {'table_name': 'income', 'column': 'int_income'}],
    ('prem_earned', 'q', 'E'):                        ['上市公司利润表 - 已赚保费', 'direct',
                                                       {'table_name': 'income', 'column': 'prem_earned'}],
    ('comm_income', 'q', 'E'):                        ['上市公司利润表 - 手续费及佣金收入', 'direct',
                                                       {'table_name': 'income', 'column': 'comm_income'}],
    ('n_commis_income', 'q', 'E'):                    ['上市公司利润表 - 手续费及佣金净收入', 'direct',
                                                       {'table_name': 'income', 'column': 'n_commis_income'}],
    ('n_oth_income', 'q', 'E'):                       ['上市公司利润表 - 其他经营净收益', 'direct',
                                                       {'table_name': 'income', 'column': 'n_oth_income'}],
    ('n_oth_b_income', 'q', 'E'):                     ['上市公司利润表 - 加:其他业务净收益', 'direct',
                                                       {'table_name': 'income', 'column': 'n_oth_b_income'}],
    ('prem_income', 'q', 'E'):                        ['上市公司利润表 - 保险业务收入', 'direct',
                                                       {'table_name': 'income', 'column': 'prem_income'}],
    ('out_prem', 'q', 'E'):                           ['上市公司利润表 - 减:分出保费', 'direct',
                                                       {'table_name': 'income', 'column': 'out_prem'}],
    ('une_prem_reser', 'q', 'E'):                     ['上市公司利润表 - 提取未到期责任准备金', 'direct',
                                                       {'table_name': 'income', 'column': 'une_prem_reser'}],
    ('reins_income', 'q', 'E'):                       ['上市公司利润表 - 其中:分保费收入', 'direct',
                                                       {'table_name': 'income', 'column': 'reins_income'}],
    ('n_sec_tb_income', 'q', 'E'):                    ['上市公司利润表 - 代理买卖证券业务净收入', 'direct',
                                                       {'table_name': 'income', 'column': 'n_sec_tb_income'}],
    ('n_sec_uw_income', 'q', 'E'):                    ['上市公司利润表 - 证券承销业务净收入', 'direct',
                                                       {'table_name': 'income', 'column': 'n_sec_uw_income'}],
    ('n_asset_mg_income', 'q', 'E'):                  ['上市公司利润表 - 受托客户资产管理业务净收入', 'direct',
                                                       {'table_name': 'income', 'column': 'n_asset_mg_income'}],
    ('oth_b_income', 'q', 'E'):                       ['上市公司利润表 - 其他业务收入', 'direct',
                                                       {'table_name': 'income', 'column': 'oth_b_income'}],
    ('fv_value_chg_gain', 'q', 'E'):                  ['上市公司利润表 - 加:公允价值变动净收益', 'direct',
                                                       {'table_name': 'income', 'column': 'fv_value_chg_gain'}],
    ('invest_income', 'q', 'E'):                      ['上市公司利润表 - 加:投资净收益', 'direct',
                                                       {'table_name': 'income', 'column': 'invest_income'}],
    ('ass_invest_income', 'q', 'E'):                  ['上市公司利润表 - 其中:对联营企业和合营企业的投资收益', 'direct',
                                                       {'table_name': 'income', 'column': 'ass_invest_income'}],
    ('forex_gain', 'q', 'E'):                         ['上市公司利润表 - 加:汇兑净收益', 'direct',
                                                       {'table_name': 'income', 'column': 'forex_gain'}],
    ('total_cogs', 'q', 'E'):                         ['上市公司利润表 - 营业总成本', 'direct',
                                                       {'table_name': 'income', 'column': 'total_cogs'}],
    ('oper_cost', 'q', 'E'):                          ['上市公司利润表 - 减:营业成本', 'direct',
                                                       {'table_name': 'income', 'column': 'oper_cost'}],
    ('int_exp', 'q', 'E'):                            ['上市公司利润表 - 减:利息支出', 'direct',
                                                       {'table_name': 'income', 'column': 'int_exp'}],
    ('comm_exp', 'q', 'E'):                           ['上市公司利润表 - 减:手续费及佣金支出', 'direct',
                                                       {'table_name': 'income', 'column': 'comm_exp'}],
    ('biz_tax_surchg', 'q', 'E'):                     ['上市公司利润表 - 减:营业税金及附加', 'direct',
                                                       {'table_name': 'income', 'column': 'biz_tax_surchg'}],
    ('sell_exp', 'q', 'E'):                           ['上市公司利润表 - 减:销售费用', 'direct',
                                                       {'table_name': 'income', 'column': 'sell_exp'}],
    ('admin_exp', 'q', 'E'):                          ['上市公司利润表 - 减:管理费用', 'direct',
                                                       {'table_name': 'income', 'column': 'admin_exp'}],
    ('fin_exp', 'q', 'E'):                            ['上市公司利润表 - 减:财务费用', 'direct',
                                                       {'table_name': 'income', 'column': 'fin_exp'}],
    ('assets_impair_loss', 'q', 'E'):                 ['上市公司利润表 - 减:资产减值损失', 'direct',
                                                       {'table_name': 'income', 'column': 'assets_impair_loss'}],
    ('prem_refund', 'q', 'E'):                        ['上市公司利润表 - 退保金', 'direct',
                                                       {'table_name': 'income', 'column': 'prem_refund'}],
    ('compens_payout', 'q', 'E'):                     ['上市公司利润表 - 赔付总支出', 'direct',
                                                       {'table_name': 'income', 'column': 'compens_payout'}],
    ('reser_insur_liab', 'q', 'E'):                   ['上市公司利润表 - 提取保险责任准备金', 'direct',
                                                       {'table_name': 'income', 'column': 'reser_insur_liab'}],
    ('div_payt', 'q', 'E'):                           ['上市公司利润表 - 保户红利支出', 'direct',
                                                       {'table_name': 'income', 'column': 'div_payt'}],
    ('reins_exp', 'q', 'E'):                          ['上市公司利润表 - 分保费用', 'direct',
                                                       {'table_name': 'income', 'column': 'reins_exp'}],
    ('oper_exp', 'q', 'E'):                           ['上市公司利润表 - 营业支出', 'direct',
                                                       {'table_name': 'income', 'column': 'oper_exp'}],
    ('compens_payout_refu', 'q', 'E'):                ['上市公司利润表 - 减:摊回赔付支出', 'direct',
                                                       {'table_name': 'income', 'column': 'compens_payout_refu'}],
    ('insur_reser_refu', 'q', 'E'):                   ['上市公司利润表 - 减:摊回保险责任准备金', 'direct',
                                                       {'table_name': 'income', 'column': 'insur_reser_refu'}],
    ('reins_cost_refund', 'q', 'E'):                  ['上市公司利润表 - 减:摊回分保费用', 'direct',
                                                       {'table_name': 'income', 'column': 'reins_cost_refund'}],
    ('other_bus_cost', 'q', 'E'):                     ['上市公司利润表 - 其他业务成本', 'direct',
                                                       {'table_name': 'income', 'column': 'other_bus_cost'}],
    ('operate_profit', 'q', 'E'):                     ['上市公司利润表 - 营业利润', 'direct',
                                                       {'table_name': 'income', 'column': 'operate_profit'}],
    ('non_oper_income', 'q', 'E'):                    ['上市公司利润表 - 加:营业外收入', 'direct',
                                                       {'table_name': 'income', 'column': 'non_oper_income'}],
    ('non_oper_exp', 'q', 'E'):                       ['上市公司利润表 - 减:营业外支出', 'direct',
                                                       {'table_name': 'income', 'column': 'non_oper_exp'}],
    ('nca_disploss', 'q', 'E'):                       ['上市公司利润表 - 其中:减:非流动资产处置净损失', 'direct',
                                                       {'table_name': 'income', 'column': 'nca_disploss'}],
    ('total_profit', 'q', 'E'):                       ['上市公司利润表 - 利润总额', 'direct',
                                                       {'table_name': 'income', 'column': 'total_profit'}],
    ('income_tax', 'q', 'E'):                         ['上市公司利润表 - 所得税费用', 'direct',
                                                       {'table_name': 'income', 'column': 'income_tax'}],
    ('net_income', 'q', 'E'):                         ['上市公司利润表 - 净利润(含少数股东损益)', 'direct',
                                                       {'table_name': 'income', 'column': 'n_income'}],
    ('n_income_attr_p', 'q', 'E'):                    ['上市公司利润表 - 净利润(不含少数股东损益)', 'direct',
                                                       {'table_name': 'income', 'column': 'n_income_attr_p'}],
    ('minority_gain', 'q', 'E'):                      ['上市公司利润表 - 少数股东损益', 'direct',
                                                       {'table_name': 'income', 'column': 'minority_gain'}],
    ('oth_compr_income', 'q', 'E'):                   ['上市公司利润表 - 其他综合收益', 'direct',
                                                       {'table_name': 'income', 'column': 'oth_compr_income'}],
    ('t_compr_income', 'q', 'E'):                     ['上市公司利润表 - 综合收益总额', 'direct',
                                                       {'table_name': 'income', 'column': 't_compr_income'}],
    ('compr_inc_attr_p', 'q', 'E'):                   ['上市公司利润表 - 归属于母公司(或股东)的综合收益总额', 'direct',
                                                       {'table_name': 'income', 'column': 'compr_inc_attr_p'}],
    ('compr_inc_attr_m_s', 'q', 'E'):                 ['上市公司利润表 - 归属于少数股东的综合收益总额', 'direct',
                                                       {'table_name': 'income', 'column': 'compr_inc_attr_m_s'}],
    ('income_ebit', 'q', 'E'):                        ['上市公司利润表 - 息税前利润', 'direct',
                                                       {'table_name': 'income', 'column': 'ebit'}],
    ('income_ebitda', 'q', 'E'):                      ['上市公司利润表 - 息税折旧摊销前利润', 'direct',
                                                       {'table_name': 'income', 'column': 'ebitda'}],
    ('insurance_exp', 'q', 'E'):                      ['上市公司利润表 - 保险业务支出', 'direct',
                                                       {'table_name': 'income', 'column': 'insurance_exp'}],
    ('undist_profit', 'q', 'E'):                      ['上市公司利润表 - 年初未分配利润', 'direct',
                                                       {'table_name': 'income', 'column': 'undist_profit'}],
    ('distable_profit', 'q', 'E'):                    ['上市公司利润表 - 可分配利润', 'direct',
                                                       {'table_name': 'income', 'column': 'distable_profit'}],
    ('income_rd_exp', 'q', 'E'):                      ['上市公司利润表 - 研发费用', 'direct',
                                                       {'table_name': 'income', 'column': 'rd_exp'}],
    ('fin_exp_int_exp', 'q', 'E'):                    ['上市公司利润表 - 财务费用:利息费用', 'direct',
                                                       {'table_name': 'income', 'column': 'fin_exp_int_exp'}],
    ('fin_exp_int_inc', 'q', 'E'):                    ['上市公司利润表 - 财务费用:利息收入', 'direct',
                                                       {'table_name': 'income', 'column': 'fin_exp_int_inc'}],
    ('transfer_surplus_rese', 'q', 'E'):              ['上市公司利润表 - 盈余公积转入', 'direct',
                                                       {'table_name': 'income', 'column': 'transfer_surplus_rese'}],
    ('transfer_housing_imprest', 'q', 'E'):           ['上市公司利润表 - 住房周转金转入', 'direct',
                                                       {'table_name': 'income', 'column': 'transfer_housing_imprest'}],
    ('transfer_oth', 'q', 'E'):                       ['上市公司利润表 - 其他转入', 'direct',
                                                       {'table_name': 'income', 'column': 'transfer_oth'}],
    ('adj_lossgain', 'q', 'E'):                       ['上市公司利润表 - 调整以前年度损益', 'direct',
                                                       {'table_name': 'income', 'column': 'adj_lossgain'}],
    ('withdra_legal_surplus', 'q', 'E'):              ['上市公司利润表 - 提取法定盈余公积', 'direct',
                                                       {'table_name': 'income', 'column': 'withdra_legal_surplus'}],
    ('withdra_legal_pubfund', 'q', 'E'):              ['上市公司利润表 - 提取法定公益金', 'direct',
                                                       {'table_name': 'income', 'column': 'withdra_legal_pubfund'}],
    ('withdra_biz_devfund', 'q', 'E'):                ['上市公司利润表 - 提取企业发展基金', 'direct',
                                                       {'table_name': 'income', 'column': 'withdra_biz_devfund'}],
    ('withdra_rese_fund', 'q', 'E'):                  ['上市公司利润表 - 提取储备基金', 'direct',
                                                       {'table_name': 'income', 'column': 'withdra_rese_fund'}],
    ('withdra_oth_ersu', 'q', 'E'):                   ['上市公司利润表 - 提取任意盈余公积金', 'direct',
                                                       {'table_name': 'income', 'column': 'withdra_oth_ersu'}],
    ('workers_welfare', 'q', 'E'):                    ['上市公司利润表 - 职工奖金福利', 'direct',
                                                       {'table_name': 'income', 'column': 'workers_welfare'}],
    ('distr_profit_shrhder', 'q', 'E'):               ['上市公司利润表 - 可供股东分配的利润', 'direct',
                                                       {'table_name': 'income', 'column': 'distr_profit_shrhder'}],
    ('prfshare_payable_dvd', 'q', 'E'):               ['上市公司利润表 - 应付优先股股利', 'direct',
                                                       {'table_name': 'income', 'column': 'prfshare_payable_dvd'}],
    ('comshare_payable_dvd', 'q', 'E'):               ['上市公司利润表 - 应付普通股股利', 'direct',
                                                       {'table_name': 'income', 'column': 'comshare_payable_dvd'}],
    ('capit_comstock_div', 'q', 'E'):                 ['上市公司利润表 - 转作股本的普通股股利', 'direct',
                                                       {'table_name': 'income', 'column': 'capit_comstock_div'}],
    ('net_after_nr_lp_correct', 'q', 'E'):            ['上市公司利润表 - 扣除非经常性损益后的净利润（更正前）', 'direct',
                                                       {'table_name': 'income', 'column': 'net_after_nr_lp_correct'}],
    ('income_credit_impa_loss', 'q', 'E'):            ['上市公司利润表 - 信用减值损失', 'direct',
                                                       {'table_name': 'income', 'column': 'credit_impa_loss'}],
    ('net_expo_hedging_benefits', 'q', 'E'):          ['上市公司利润表 - 净敞口套期收益', 'direct',
                                                       {'table_name': 'income', 'column': 'net_expo_hedging_benefits'}],
    ('oth_impair_loss_assets', 'q', 'E'):             ['上市公司利润表 - 其他资产减值损失', 'direct',
                                                       {'table_name': 'income', 'column': 'oth_impair_loss_assets'}],
    ('total_opcost', 'q', 'E'):                       ['上市公司利润表 - 营业总成本（二）', 'direct',
                                                       {'table_name': 'income', 'column': 'total_opcost'}],
    ('amodcost_fin_assets', 'q', 'E'):                ['上市公司利润表 - 以摊余成本计量的金融资产终止确认收益',
                                                       'direct',
                                                       {'table_name': 'income', 'column': 'amodcost_fin_assets'}],
    ('oth_income', 'q', 'E'):                         ['上市公司利润表 - 其他收益', 'direct',
                                                       {'table_name': 'income', 'column': 'oth_income'}],
    ('asset_disp_income', 'q', 'E'):                  ['上市公司利润表 - 资产处置收益', 'direct',
                                                       {'table_name': 'income', 'column': 'asset_disp_income'}],
    ('continued_net_profit', 'q', 'E'):               ['上市公司利润表 - 持续经营净利润', 'direct',
                                                       {'table_name': 'income', 'column': 'continued_net_profit'}],
    ('end_net_profit', 'q', 'E'):                     ['上市公司利润表 - 终止经营净利润', 'direct',
                                                       {'table_name': 'income', 'column': 'end_net_profit'}],
    ('total_share', 'q', 'E'):                        ['上市公司资产负债表 - 期末总股本', 'direct',
                                                       {'table_name': 'balance', 'column': 'total_share'}],
    ('cap_rese', 'q', 'E'):                           ['上市公司资产负债表 - 资本公积金', 'direct',
                                                       {'table_name': 'balance', 'column': 'cap_rese'}],
    ('undistr_porfit', 'q', 'E'):                     ['上市公司资产负债表 - 未分配利润', 'direct',
                                                       {'table_name': 'balance', 'column': 'undistr_porfit'}],
    ('surplus_rese', 'q', 'E'):                       ['上市公司资产负债表 - 盈余公积金', 'direct',
                                                       {'table_name': 'balance', 'column': 'surplus_rese'}],
    ('special_rese', 'q', 'E'):                       ['上市公司资产负债表 - 专项储备', 'direct',
                                                       {'table_name': 'balance', 'column': 'special_rese'}],
    ('money_cap', 'q', 'E'):                          ['上市公司资产负债表 - 货币资金', 'direct',
                                                       {'table_name': 'balance', 'column': 'money_cap'}],
    ('trad_asset', 'q', 'E'):                         ['上市公司资产负债表 - 交易性金融资产', 'direct',
                                                       {'table_name': 'balance', 'column': 'trad_asset'}],
    ('notes_receiv', 'q', 'E'):                       ['上市公司资产负债表 - 应收票据', 'direct',
                                                       {'table_name': 'balance', 'column': 'notes_receiv'}],
    ('accounts_receiv', 'q', 'E'):                    ['上市公司资产负债表 - 应收账款', 'direct',
                                                       {'table_name': 'balance', 'column': 'accounts_receiv'}],
    ('oth_receiv', 'q', 'E'):                         ['上市公司资产负债表 - 其他应收款', 'direct',
                                                       {'table_name': 'balance', 'column': 'oth_receiv'}],
    ('prepayment', 'q', 'E'):                         ['上市公司资产负债表 - 预付款项', 'direct',
                                                       {'table_name': 'balance', 'column': 'prepayment'}],
    ('div_receiv', 'q', 'E'):                         ['上市公司资产负债表 - 应收股利', 'direct',
                                                       {'table_name': 'balance', 'column': 'div_receiv'}],
    ('int_receiv', 'q', 'E'):                         ['上市公司资产负债表 - 应收利息', 'direct',
                                                       {'table_name': 'balance', 'column': 'int_receiv'}],
    ('inventories', 'q', 'E'):                        ['上市公司资产负债表 - 存货', 'direct',
                                                       {'table_name': 'balance', 'column': 'inventories'}],
    ('amor_exp', 'q', 'E'):                           ['上市公司资产负债表 - 长期待摊费用', 'direct',
                                                       {'table_name': 'balance', 'column': 'amor_exp'}],
    ('nca_within_1y', 'q', 'E'):                      ['上市公司资产负债表 - 一年内到期的非流动资产', 'direct',
                                                       {'table_name': 'balance', 'column': 'nca_within_1y'}],
    ('sett_rsrv', 'q', 'E'):                          ['上市公司资产负债表 - 结算备付金', 'direct',
                                                       {'table_name': 'balance', 'column': 'sett_rsrv'}],
    ('loanto_oth_bank_fi', 'q', 'E'):                 ['上市公司资产负债表 - 拆出资金', 'direct',
                                                       {'table_name': 'balance', 'column': 'loanto_oth_bank_fi'}],
    ('premium_receiv', 'q', 'E'):                     ['上市公司资产负债表 - 应收保费', 'direct',
                                                       {'table_name': 'balance', 'column': 'premium_receiv'}],
    ('reinsur_receiv', 'q', 'E'):                     ['上市公司资产负债表 - 应收分保账款', 'direct',
                                                       {'table_name': 'balance', 'column': 'reinsur_receiv'}],
    ('reinsur_res_receiv', 'q', 'E'):                 ['上市公司资产负债表 - 应收分保合同准备金', 'direct',
                                                       {'table_name': 'balance', 'column': 'reinsur_res_receiv'}],
    ('pur_resale_fa', 'q', 'E'):                      ['上市公司资产负债表 - 买入返售金融资产', 'direct',
                                                       {'table_name': 'balance', 'column': 'pur_resale_fa'}],
    ('oth_cur_assets', 'q', 'E'):                     ['上市公司资产负债表 - 其他流动资产', 'direct',
                                                       {'table_name': 'balance', 'column': 'oth_cur_assets'}],
    ('total_cur_assets', 'q', 'E'):                   ['上市公司资产负债表 - 流动资产合计', 'direct',
                                                       {'table_name': 'balance', 'column': 'total_cur_assets'}],
    ('fa_avail_for_sale', 'q', 'E'):                  ['上市公司资产负债表 - 可供出售金融资产', 'direct',
                                                       {'table_name': 'balance', 'column': 'fa_avail_for_sale'}],
    ('htm_invest', 'q', 'E'):                         ['上市公司资产负债表 - 持有至到期投资', 'direct',
                                                       {'table_name': 'balance', 'column': 'htm_invest'}],
    ('lt_eqt_invest', 'q', 'E'):                      ['上市公司资产负债表 - 长期股权投资', 'direct',
                                                       {'table_name': 'balance', 'column': 'lt_eqt_invest'}],
    ('invest_real_estate', 'q', 'E'):                 ['上市公司资产负债表 - 投资性房地产', 'direct',
                                                       {'table_name': 'balance', 'column': 'invest_real_estate'}],
    ('time_deposits', 'q', 'E'):                      ['上市公司资产负债表 - 定期存款', 'direct',
                                                       {'table_name': 'balance', 'column': 'time_deposits'}],
    ('oth_assets', 'q', 'E'):                         ['上市公司资产负债表 - 其他资产', 'direct',
                                                       {'table_name': 'balance', 'column': 'oth_assets'}],
    ('lt_rec', 'q', 'E'):                             ['上市公司资产负债表 - 长期应收款', 'direct',
                                                       {'table_name': 'balance', 'column': 'lt_rec'}],
    ('fix_assets', 'q', 'E'):                         ['上市公司资产负债表 - 固定资产', 'direct',
                                                       {'table_name': 'balance', 'column': 'fix_assets'}],
    ('cip', 'q', 'E'):                                ['上市公司资产负债表 - 在建工程', 'direct',
                                                       {'table_name': 'balance', 'column': 'cip'}],
    ('const_materials', 'q', 'E'):                    ['上市公司资产负债表 - 工程物资', 'direct',
                                                       {'table_name': 'balance', 'column': 'const_materials'}],
    ('fixed_assets_disp', 'q', 'E'):                  ['上市公司资产负债表 - 固定资产清理', 'direct',
                                                       {'table_name': 'balance', 'column': 'fixed_assets_disp'}],
    ('produc_bio_assets', 'q', 'E'):                  ['上市公司资产负债表 - 生产性生物资产', 'direct',
                                                       {'table_name': 'balance', 'column': 'produc_bio_assets'}],
    ('oil_and_gas_assets', 'q', 'E'):                 ['上市公司资产负债表 - 油气资产', 'direct',
                                                       {'table_name': 'balance', 'column': 'oil_and_gas_assets'}],
    ('intan_assets', 'q', 'E'):                       ['上市公司资产负债表 - 无形资产', 'direct',
                                                       {'table_name': 'balance', 'column': 'intan_assets'}],
    ('r_and_d', 'q', 'E'):                            ['上市公司资产负债表 - 研发支出', 'direct',
                                                       {'table_name': 'balance', 'column': 'r_and_d'}],
    ('goodwill', 'q', 'E'):                           ['上市公司资产负债表 - 商誉', 'direct',
                                                       {'table_name': 'balance', 'column': 'goodwill'}],
    ('lt_amor_exp', 'q', 'E'):                        ['上市公司资产负债表 - 长期待摊费用', 'direct',
                                                       {'table_name': 'balance', 'column': 'lt_amor_exp'}],
    ('defer_tax_assets', 'q', 'E'):                   ['上市公司资产负债表 - 递延所得税资产', 'direct',
                                                       {'table_name': 'balance', 'column': 'defer_tax_assets'}],
    ('decr_in_disbur', 'q', 'E'):                     ['上市公司资产负债表 - 发放贷款及垫款', 'direct',
                                                       {'table_name': 'balance', 'column': 'decr_in_disbur'}],
    ('oth_nca', 'q', 'E'):                            ['上市公司资产负债表 - 其他非流动资产', 'direct',
                                                       {'table_name': 'balance', 'column': 'oth_nca'}],
    ('total_nca', 'q', 'E'):                          ['上市公司资产负债表 - 非流动资产合计', 'direct',
                                                       {'table_name': 'balance', 'column': 'total_nca'}],
    ('cash_reser_cb', 'q', 'E'):                      ['上市公司资产负债表 - 现金及存放中央银行款项', 'direct',
                                                       {'table_name': 'balance', 'column': 'cash_reser_cb'}],
    ('depos_in_oth_bfi', 'q', 'E'):                   ['上市公司资产负债表 - 存放同业和其它金融机构款项', 'direct',
                                                       {'table_name': 'balance', 'column': 'depos_in_oth_bfi'}],
    ('prec_metals', 'q', 'E'):                        ['上市公司资产负债表 - 贵金属', 'direct',
                                                       {'table_name': 'balance', 'column': 'prec_metals'}],
    ('deriv_assets', 'q', 'E'):                       ['上市公司资产负债表 - 衍生金融资产', 'direct',
                                                       {'table_name': 'balance', 'column': 'deriv_assets'}],
    ('rr_reins_une_prem', 'q', 'E'):                  ['上市公司资产负债表 - 应收分保未到期责任准备金', 'direct',
                                                       {'table_name': 'balance', 'column': 'rr_reins_une_prem'}],
    ('rr_reins_outstd_cla', 'q', 'E'):                ['上市公司资产负债表 - 应收分保未决赔款准备金', 'direct',
                                                       {'table_name': 'balance', 'column': 'rr_reins_outstd_cla'}],
    ('rr_reins_lins_liab', 'q', 'E'):                 ['上市公司资产负债表 - 应收分保寿险责任准备金', 'direct',
                                                       {'table_name': 'balance', 'column': 'rr_reins_lins_liab'}],
    ('rr_reins_lthins_liab', 'q', 'E'):               ['上市公司资产负债表 - 应收分保长期健康险责任准备金', 'direct',
                                                       {'table_name': 'balance', 'column': 'rr_reins_lthins_liab'}],
    ('refund_depos', 'q', 'E'):                       ['上市公司资产负债表 - 存出保证金', 'direct',
                                                       {'table_name': 'balance', 'column': 'refund_depos'}],
    ('ph_pledge_loans', 'q', 'E'):                    ['上市公司资产负债表 - 保户质押贷款', 'direct',
                                                       {'table_name': 'balance', 'column': 'ph_pledge_loans'}],
    ('refund_cap_depos', 'q', 'E'):                   ['上市公司资产负债表 - 存出资本保证金', 'direct',
                                                       {'table_name': 'balance', 'column': 'refund_cap_depos'}],
    ('indep_acct_assets', 'q', 'E'):                  ['上市公司资产负债表 - 独立账户资产', 'direct',
                                                       {'table_name': 'balance', 'column': 'indep_acct_assets'}],
    ('client_depos', 'q', 'E'):                       ['上市公司资产负债表 - 其中：客户资金存款', 'direct',
                                                       {'table_name': 'balance', 'column': 'client_depos'}],
    ('client_prov', 'q', 'E'):                        ['上市公司资产负债表 - 其中：客户备付金', 'direct',
                                                       {'table_name': 'balance', 'column': 'client_prov'}],
    ('transac_seat_fee', 'q', 'E'):                   ['上市公司资产负债表 - 其中:交易席位费', 'direct',
                                                       {'table_name': 'balance', 'column': 'transac_seat_fee'}],
    ('invest_as_receiv', 'q', 'E'):                   ['上市公司资产负债表 - 应收款项类投资', 'direct',
                                                       {'table_name': 'balance', 'column': 'invest_as_receiv'}],
    ('total_assets', 'q', 'E'):                       ['上市公司资产负债表 - 资产总计', 'direct',
                                                       {'table_name': 'balance', 'column': 'total_assets'}],
    ('lt_borr', 'q', 'E'):                            ['上市公司资产负债表 - 长期借款', 'direct',
                                                       {'table_name': 'balance', 'column': 'lt_borr'}],
    ('st_borr', 'q', 'E'):                            ['上市公司资产负债表 - 短期借款', 'direct',
                                                       {'table_name': 'balance', 'column': 'st_borr'}],
    ('cb_borr', 'q', 'E'):                            ['上市公司资产负债表 - 向中央银行借款', 'direct',
                                                       {'table_name': 'balance', 'column': 'cb_borr'}],
    ('depos_ib_deposits', 'q', 'E'):                  ['上市公司资产负债表 - 吸收存款及同业存放', 'direct',
                                                       {'table_name': 'balance', 'column': 'depos_ib_deposits'}],
    ('loan_oth_bank', 'q', 'E'):                      ['上市公司资产负债表 - 拆入资金', 'direct',
                                                       {'table_name': 'balance', 'column': 'loan_oth_bank'}],
    ('trading_fl', 'q', 'E'):                         ['上市公司资产负债表 - 交易性金融负债', 'direct',
                                                       {'table_name': 'balance', 'column': 'trading_fl'}],
    ('notes_payable', 'q', 'E'):                      ['上市公司资产负债表 - 应付票据', 'direct',
                                                       {'table_name': 'balance', 'column': 'notes_payable'}],
    ('acct_payable', 'q', 'E'):                       ['上市公司资产负债表 - 应付账款', 'direct',
                                                       {'table_name': 'balance', 'column': 'acct_payable'}],
    ('adv_receipts', 'q', 'E'):                       ['上市公司资产负债表 - 预收款项', 'direct',
                                                       {'table_name': 'balance', 'column': 'adv_receipts'}],
    ('sold_for_repur_fa', 'q', 'E'):                  ['上市公司资产负债表 - 卖出回购金融资产款', 'direct',
                                                       {'table_name': 'balance', 'column': 'sold_for_repur_fa'}],
    ('comm_payable', 'q', 'E'):                       ['上市公司资产负债表 - 应付手续费及佣金', 'direct',
                                                       {'table_name': 'balance', 'column': 'comm_payable'}],
    ('payroll_payable', 'q', 'E'):                    ['上市公司资产负债表 - 应付职工薪酬', 'direct',
                                                       {'table_name': 'balance', 'column': 'payroll_payable'}],
    ('taxes_payable', 'q', 'E'):                      ['上市公司资产负债表 - 应交税费', 'direct',
                                                       {'table_name': 'balance', 'column': 'taxes_payable'}],
    ('int_payable', 'q', 'E'):                        ['上市公司资产负债表 - 应付利息', 'direct',
                                                       {'table_name': 'balance', 'column': 'int_payable'}],
    ('div_payable', 'q', 'E'):                        ['上市公司资产负债表 - 应付股利', 'direct',
                                                       {'table_name': 'balance', 'column': 'div_payable'}],
    ('oth_payable', 'q', 'E'):                        ['上市公司资产负债表 - 其他应付款', 'direct',
                                                       {'table_name': 'balance', 'column': 'oth_payable'}],
    ('acc_exp', 'q', 'E'):                            ['上市公司资产负债表 - 预提费用', 'direct',
                                                       {'table_name': 'balance', 'column': 'acc_exp'}],
    ('deferred_inc', 'q', 'E'):                       ['上市公司资产负债表 - 递延收益', 'direct',
                                                       {'table_name': 'balance', 'column': 'deferred_inc'}],
    ('st_bonds_payable', 'q', 'E'):                   ['上市公司资产负债表 - 应付短期债券', 'direct',
                                                       {'table_name': 'balance', 'column': 'st_bonds_payable'}],
    ('payable_to_reinsurer', 'q', 'E'):               ['上市公司资产负债表 - 应付分保账款', 'direct',
                                                       {'table_name': 'balance', 'column': 'payable_to_reinsurer'}],
    ('rsrv_insur_cont', 'q', 'E'):                    ['上市公司资产负债表 - 保险合同准备金', 'direct',
                                                       {'table_name': 'balance', 'column': 'rsrv_insur_cont'}],
    ('acting_trading_sec', 'q', 'E'):                 ['上市公司资产负债表 - 代理买卖证券款', 'direct',
                                                       {'table_name': 'balance', 'column': 'acting_trading_sec'}],
    ('acting_uw_sec', 'q', 'E'):                      ['上市公司资产负债表 - 代理承销证券款', 'direct',
                                                       {'table_name': 'balance', 'column': 'acting_uw_sec'}],
    ('non_cur_liab_due_1y', 'q', 'E'):                ['上市公司资产负债表 - 一年内到期的非流动负债', 'direct',
                                                       {'table_name': 'balance', 'column': 'non_cur_liab_due_1y'}],
    ('oth_cur_liab', 'q', 'E'):                       ['上市公司资产负债表 - 其他流动负债', 'direct',
                                                       {'table_name': 'balance', 'column': 'oth_cur_liab'}],
    ('total_cur_liab', 'q', 'E'):                     ['上市公司资产负债表 - 流动负债合计', 'direct',
                                                       {'table_name': 'balance', 'column': 'total_cur_liab'}],
    ('bond_payable', 'q', 'E'):                       ['上市公司资产负债表 - 应付债券', 'direct',
                                                       {'table_name': 'balance', 'column': 'bond_payable'}],
    ('lt_payable', 'q', 'E'):                         ['上市公司资产负债表 - 长期应付款', 'direct',
                                                       {'table_name': 'balance', 'column': 'lt_payable'}],
    ('specific_payables', 'q', 'E'):                  ['上市公司资产负债表 - 专项应付款', 'direct',
                                                       {'table_name': 'balance', 'column': 'specific_payables'}],
    ('estimated_liab', 'q', 'E'):                     ['上市公司资产负债表 - 预计负债', 'direct',
                                                       {'table_name': 'balance', 'column': 'estimated_liab'}],
    ('defer_tax_liab', 'q', 'E'):                     ['上市公司资产负债表 - 递延所得税负债', 'direct',
                                                       {'table_name': 'balance', 'column': 'defer_tax_liab'}],
    ('defer_inc_non_cur_liab', 'q', 'E'):             ['上市公司资产负债表 - 递延收益-非流动负债', 'direct',
                                                       {'table_name': 'balance', 'column': 'defer_inc_non_cur_liab'}],
    ('oth_ncl', 'q', 'E'):                            ['上市公司资产负债表 - 其他非流动负债', 'direct',
                                                       {'table_name': 'balance', 'column': 'oth_ncl'}],
    ('total_ncl', 'q', 'E'):                          ['上市公司资产负债表 - 非流动负债合计', 'direct',
                                                       {'table_name': 'balance', 'column': 'total_ncl'}],
    ('depos_oth_bfi', 'q', 'E'):                      ['上市公司资产负债表 - 同业和其它金融机构存放款项', 'direct',
                                                       {'table_name': 'balance', 'column': 'depos_oth_bfi'}],
    ('deriv_liab', 'q', 'E'):                         ['上市公司资产负债表 - 衍生金融负债', 'direct',
                                                       {'table_name': 'balance', 'column': 'deriv_liab'}],
    ('depos', 'q', 'E'):                              ['上市公司资产负债表 - 吸收存款', 'direct',
                                                       {'table_name': 'balance', 'column': 'depos'}],
    ('agency_bus_liab', 'q', 'E'):                    ['上市公司资产负债表 - 代理业务负债', 'direct',
                                                       {'table_name': 'balance', 'column': 'agency_bus_liab'}],
    ('oth_liab', 'q', 'E'):                           ['上市公司资产负债表 - 其他负债', 'direct',
                                                       {'table_name': 'balance', 'column': 'oth_liab'}],
    ('prem_receiv_adva', 'q', 'E'):                   ['上市公司资产负债表 - 预收保费', 'direct',
                                                       {'table_name': 'balance', 'column': 'prem_receiv_adva'}],
    ('depos_received', 'q', 'E'):                     ['上市公司资产负债表 - 存入保证金', 'direct',
                                                       {'table_name': 'balance', 'column': 'depos_received'}],
    ('ph_invest', 'q', 'E'):                          ['上市公司资产负债表 - 保户储金及投资款', 'direct',
                                                       {'table_name': 'balance', 'column': 'ph_invest'}],
    ('reser_une_prem', 'q', 'E'):                     ['上市公司资产负债表 - 未到期责任准备金', 'direct',
                                                       {'table_name': 'balance', 'column': 'reser_une_prem'}],
    ('reser_outstd_claims', 'q', 'E'):                ['上市公司资产负债表 - 未决赔款准备金', 'direct',
                                                       {'table_name': 'balance', 'column': 'reser_outstd_claims'}],
    ('reser_lins_liab', 'q', 'E'):                    ['上市公司资产负债表 - 寿险责任准备金', 'direct',
                                                       {'table_name': 'balance', 'column': 'reser_lins_liab'}],
    ('reser_lthins_liab', 'q', 'E'):                  ['上市公司资产负债表 - 长期健康险责任准备金', 'direct',
                                                       {'table_name': 'balance', 'column': 'reser_lthins_liab'}],
    ('indept_acc_liab', 'q', 'E'):                    ['上市公司资产负债表 - 独立账户负债', 'direct',
                                                       {'table_name': 'balance', 'column': 'indept_acc_liab'}],
    ('pledge_borr', 'q', 'E'):                        ['上市公司资产负债表 - 其中:质押借款', 'direct',
                                                       {'table_name': 'balance', 'column': 'pledge_borr'}],
    ('indem_payable', 'q', 'E'):                      ['上市公司资产负债表 - 应付赔付款', 'direct',
                                                       {'table_name': 'balance', 'column': 'indem_payable'}],
    ('policy_div_payable', 'q', 'E'):                 ['上市公司资产负债表 - 应付保单红利', 'direct',
                                                       {'table_name': 'balance', 'column': 'policy_div_payable'}],
    ('total_liab', 'q', 'E'):                         ['上市公司资产负债表 - 负债合计', 'direct',
                                                       {'table_name': 'balance', 'column': 'total_liab'}],
    ('treasury_share', 'q', 'E'):                     ['上市公司资产负债表 - 减:库存股', 'direct',
                                                       {'table_name': 'balance', 'column': 'treasury_share'}],
    ('ordin_risk_reser', 'q', 'E'):                   ['上市公司资产负债表 - 一般风险准备', 'direct',
                                                       {'table_name': 'balance', 'column': 'ordin_risk_reser'}],
    ('forex_differ', 'q', 'E'):                       ['上市公司资产负债表 - 外币报表折算差额', 'direct',
                                                       {'table_name': 'balance', 'column': 'forex_differ'}],
    ('invest_loss_unconf', 'q', 'E'):                 ['上市公司资产负债表 - 未确认的投资损失', 'direct',
                                                       {'table_name': 'balance', 'column': 'invest_loss_unconf'}],
    ('minority_int', 'q', 'E'):                       ['上市公司资产负债表 - 少数股东权益', 'direct',
                                                       {'table_name': 'balance', 'column': 'minority_int'}],
    ('total_hldr_eqy_exc_min_int', 'q', 'E'):         ['上市公司资产负债表 - 股东权益合计(不含少数股东权益)', 'direct',
                                                       {'table_name': 'balance',
                                                        'column':     'total_hldr_eqy_exc_min_int'}],
    ('total_hldr_eqy_inc_min_int', 'q', 'E'):         ['上市公司资产负债表 - 股东权益合计(含少数股东权益)', 'direct',
                                                       {'table_name': 'balance',
                                                        'column':     'total_hldr_eqy_inc_min_int'}],
    ('total_liab_hldr_eqy', 'q', 'E'):                ['上市公司资产负债表 - 负债及股东权益总计', 'direct',
                                                       {'table_name': 'balance', 'column': 'total_liab_hldr_eqy'}],
    ('lt_payroll_payable', 'q', 'E'):                 ['上市公司资产负债表 - 长期应付职工薪酬', 'direct',
                                                       {'table_name': 'balance', 'column': 'lt_payroll_payable'}],
    ('oth_comp_income', 'q', 'E'):                    ['上市公司资产负债表 - 其他综合收益', 'direct',
                                                       {'table_name': 'balance', 'column': 'oth_comp_income'}],
    ('oth_eqt_tools', 'q', 'E'):                      ['上市公司资产负债表 - 其他权益工具', 'direct',
                                                       {'table_name': 'balance', 'column': 'oth_eqt_tools'}],
    ('oth_eqt_tools_p_shr', 'q', 'E'):                ['上市公司资产负债表 - 其他权益工具(优先股)', 'direct',
                                                       {'table_name': 'balance', 'column': 'oth_eqt_tools_p_shr'}],
    ('lending_funds', 'q', 'E'):                      ['上市公司资产负债表 - 融出资金', 'direct',
                                                       {'table_name': 'balance', 'column': 'lending_funds'}],
    ('acc_receivable', 'q', 'E'):                     ['上市公司资产负债表 - 应收款项', 'direct',
                                                       {'table_name': 'balance', 'column': 'acc_receivable'}],
    ('st_fin_payable', 'q', 'E'):                     ['上市公司资产负债表 - 应付短期融资款', 'direct',
                                                       {'table_name': 'balance', 'column': 'st_fin_payable'}],
    ('payables', 'q', 'E'):                           ['上市公司资产负债表 - 应付款项', 'direct',
                                                       {'table_name': 'balance', 'column': 'payables'}],
    ('hfs_assets', 'q', 'E'):                         ['上市公司资产负债表 - 持有待售的资产', 'direct',
                                                       {'table_name': 'balance', 'column': 'hfs_assets'}],
    ('hfs_sales', 'q', 'E'):                          ['上市公司资产负债表 - 持有待售的负债', 'direct',
                                                       {'table_name': 'balance', 'column': 'hfs_sales'}],
    ('cost_fin_assets', 'q', 'E'):                    ['上市公司资产负债表 - 以摊余成本计量的金融资产', 'direct',
                                                       {'table_name': 'balance', 'column': 'cost_fin_assets'}],
    ('fair_value_fin_assets', 'q', 'E'):              [
        '上市公司资产负债表 - 以公允价值计量且其变动计入其他综合收益的金融资产', 'direct',
        {'table_name': 'balance', 'column': 'fair_value_fin_assets'}],
    ('cip_total', 'q', 'E'):                          ['上市公司资产负债表 - 在建工程(合计)(元)', 'direct',
                                                       {'table_name': 'balance', 'column': 'cip_total'}],
    ('oth_pay_total', 'q', 'E'):                      ['上市公司资产负债表 - 其他应付款(合计)(元)', 'direct',
                                                       {'table_name': 'balance', 'column': 'oth_pay_total'}],
    ('long_pay_total', 'q', 'E'):                     ['上市公司资产负债表 - 长期应付款(合计)(元)', 'direct',
                                                       {'table_name': 'balance', 'column': 'long_pay_total'}],
    ('debt_invest', 'q', 'E'):                        ['上市公司资产负债表 - 债权投资(元)', 'direct',
                                                       {'table_name': 'balance', 'column': 'debt_invest'}],
    ('oth_debt_invest', 'q', 'E'):                    ['上市公司资产负债表 - 其他债权投资(元)', 'direct',
                                                       {'table_name': 'balance', 'column': 'oth_debt_invest'}],
    ('oth_eq_invest', 'q', 'E'):                      ['上市公司资产负债表 - 其他权益工具投资(元)', 'direct',
                                                       {'table_name': 'balance', 'column': 'oth_eq_invest'}],
    ('oth_illiq_fin_assets', 'q', 'E'):               ['上市公司资产负债表 - 其他非流动金融资产(元)', 'direct',
                                                       {'table_name': 'balance', 'column': 'oth_illiq_fin_assets'}],
    ('oth_eq_ppbond', 'q', 'E'):                      ['上市公司资产负债表 - 其他权益工具:永续债(元)', 'direct',
                                                       {'table_name': 'balance', 'column': 'oth_eq_ppbond'}],
    ('receiv_financing', 'q', 'E'):                   ['上市公司资产负债表 - 应收款项融资', 'direct',
                                                       {'table_name': 'balance', 'column': 'receiv_financing'}],
    ('use_right_assets', 'q', 'E'):                   ['上市公司资产负债表 - 使用权资产', 'direct',
                                                       {'table_name': 'balance', 'column': 'use_right_assets'}],
    ('lease_liab', 'q', 'E'):                         ['上市公司资产负债表 - 租赁负债', 'direct',
                                                       {'table_name': 'balance', 'column': 'lease_liab'}],
    ('contract_assets', 'q', 'E'):                    ['上市公司资产负债表 - 合同资产', 'direct',
                                                       {'table_name': 'balance', 'column': 'contract_assets'}],
    ('contract_liab', 'q', 'E'):                      ['上市公司资产负债表 - 合同负债', 'direct',
                                                       {'table_name': 'balance', 'column': 'contract_liab'}],
    ('accounts_receiv_bill', 'q', 'E'):               ['上市公司资产负债表 - 应收票据及应收账款', 'direct',
                                                       {'table_name': 'balance', 'column': 'accounts_receiv_bill'}],
    ('accounts_pay', 'q', 'E'):                       ['上市公司资产负债表 - 应付票据及应付账款', 'direct',
                                                       {'table_name': 'balance', 'column': 'accounts_pay'}],
    ('oth_rcv_total', 'q', 'E'):                      ['上市公司资产负债表 - 其他应收款(合计)（元）', 'direct',
                                                       {'table_name': 'balance', 'column': 'oth_rcv_total'}],
    ('fix_assets_total', 'q', 'E'):                   ['上市公司资产负债表 - 固定资产(合计)(元)', 'direct',
                                                       {'table_name': 'balance', 'column': 'fix_assets_total'}],
    ('net_profit', 'q', 'E'):                         ['上市公司现金流量表 - 净利润', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'net_profit'}],
    ('finan_exp', 'q', 'E'):                          ['上市公司现金流量表 - 财务费用', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'finan_exp'}],
    ('c_fr_sale_sg', 'q', 'E'):                       ['上市公司现金流量表 - 销售商品、提供劳务收到的现金', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'c_fr_sale_sg'}],
    ('recp_tax_rends', 'q', 'E'):                     ['上市公司现金流量表 - 收到的税费返还', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'recp_tax_rends'}],
    ('n_depos_incr_fi', 'q', 'E'):                    ['上市公司现金流量表 - 客户存款和同业存放款项净增加额', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'n_depos_incr_fi'}],
    ('n_incr_loans_cb', 'q', 'E'):                    ['上市公司现金流量表 - 向中央银行借款净增加额', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'n_incr_loans_cb'}],
    ('n_inc_borr_oth_fi', 'q', 'E'):                  ['上市公司现金流量表 - 向其他金融机构拆入资金净增加额', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'n_inc_borr_oth_fi'}],
    ('prem_fr_orig_contr', 'q', 'E'):                 ['上市公司现金流量表 - 收到原保险合同保费取得的现金', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'prem_fr_orig_contr'}],
    ('n_incr_insured_dep', 'q', 'E'):                 ['上市公司现金流量表 - 保户储金净增加额', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'n_incr_insured_dep'}],
    ('n_reinsur_prem', 'q', 'E'):                     ['上市公司现金流量表 - 收到再保业务现金净额', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'n_reinsur_prem'}],
    ('n_incr_disp_tfa', 'q', 'E'):                    ['上市公司现金流量表 - 处置交易性金融资产净增加额', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'n_incr_disp_tfa'}],
    ('ifc_cash_incr', 'q', 'E'):                      ['上市公司现金流量表 - 收取利息和手续费净增加额', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'ifc_cash_incr'}],
    ('n_incr_disp_faas', 'q', 'E'):                   ['上市公司现金流量表 - 处置可供出售金融资产净增加额', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'n_incr_disp_faas'}],
    ('n_incr_loans_oth_bank', 'q', 'E'):              ['上市公司现金流量表 - 拆入资金净增加额', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'n_incr_loans_oth_bank'}],
    ('n_cap_incr_repur', 'q', 'E'):                   ['上市公司现金流量表 - 回购业务资金净增加额', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'n_cap_incr_repur'}],
    ('c_fr_oth_operate_a', 'q', 'E'):                 ['上市公司现金流量表 - 收到其他与经营活动有关的现金', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'c_fr_oth_operate_a'}],
    ('c_inf_fr_operate_a', 'q', 'E'):                 ['上市公司现金流量表 - 经营活动现金流入小计', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'c_inf_fr_operate_a'}],
    ('c_paid_goods_s', 'q', 'E'):                     ['上市公司现金流量表 - 购买商品、接受劳务支付的现金', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'c_paid_goods_s'}],
    ('c_paid_to_for_empl', 'q', 'E'):                 ['上市公司现金流量表 - 支付给职工以及为职工支付的现金', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'c_paid_to_for_empl'}],
    ('c_paid_for_taxes', 'q', 'E'):                   ['上市公司现金流量表 - 支付的各项税费', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'c_paid_for_taxes'}],
    ('n_incr_clt_loan_adv', 'q', 'E'):                ['上市公司现金流量表 - 客户贷款及垫款净增加额', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'n_incr_clt_loan_adv'}],
    ('n_incr_dep_cbob', 'q', 'E'):                    ['上市公司现金流量表 - 存放央行和同业款项净增加额', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'n_incr_dep_cbob'}],
    ('c_pay_claims_orig_inco', 'q', 'E'):             ['上市公司现金流量表 - 支付原保险合同赔付款项的现金', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'c_pay_claims_orig_inco'}],
    ('pay_handling_chrg', 'q', 'E'):                  ['上市公司现金流量表 - 支付手续费的现金', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'pay_handling_chrg'}],
    ('pay_comm_insur_plcy', 'q', 'E'):                ['上市公司现金流量表 - 支付保单红利的现金', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'pay_comm_insur_plcy'}],
    ('oth_cash_pay_oper_act', 'q', 'E'):              ['上市公司现金流量表 - 支付其他与经营活动有关的现金', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'oth_cash_pay_oper_act'}],
    ('st_cash_out_act', 'q', 'E'):                    ['上市公司现金流量表 - 经营活动现金流出小计', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'st_cash_out_act'}],
    ('n_cashflow_act', 'q', 'E'):                     ['上市公司现金流量表 - 经营活动产生的现金流量净额', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'n_cashflow_act'}],
    ('oth_recp_ral_inv_act', 'q', 'E'):               ['上市公司现金流量表 - 收到其他与投资活动有关的现金', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'oth_recp_ral_inv_act'}],
    ('c_disp_withdrwl_invest', 'q', 'E'):             ['上市公司现金流量表 - 收回投资收到的现金', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'c_disp_withdrwl_invest'}],
    ('c_recp_return_invest', 'q', 'E'):               ['上市公司现金流量表 - 取得投资收益收到的现金', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'c_recp_return_invest'}],
    ('n_recp_disp_fiolta', 'q', 'E'):                 [
        '上市公司现金流量表 - 处置固定资产、无形资产和其他长期资产收回的现金净额', 'direct',
        {'table_name': 'cashflow', 'column': 'n_recp_disp_fiolta'}],
    ('n_recp_disp_sobu', 'q', 'E'):                   ['上市公司现金流量表 - 处置子公司及其他营业单位收到的现金净额',
                                                       'direct',
                                                       {'table_name': 'cashflow', 'column': 'n_recp_disp_sobu'}],
    ('stot_inflows_inv_act', 'q', 'E'):               ['上市公司现金流量表 - 投资活动现金流入小计', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'stot_inflows_inv_act'}],
    ('c_pay_acq_const_fiolta', 'q', 'E'):             [
        '上市公司现金流量表 - 购建固定资产、无形资产和其他长期资产支付的现金', 'direct',
        {'table_name': 'cashflow', 'column': 'c_pay_acq_const_fiolta'}],
    ('c_paid_invest', 'q', 'E'):                      ['上市公司现金流量表 - 投资支付的现金', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'c_paid_invest'}],
    ('n_disp_subs_oth_biz', 'q', 'E'):                ['上市公司现金流量表 - 取得子公司及其他营业单位支付的现金净额',
                                                       'direct',
                                                       {'table_name': 'cashflow', 'column': 'n_disp_subs_oth_biz'}],
    ('oth_pay_ral_inv_act', 'q', 'E'):                ['上市公司现金流量表 - 支付其他与投资活动有关的现金', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'oth_pay_ral_inv_act'}],
    ('n_incr_pledge_loan', 'q', 'E'):                 ['上市公司现金流量表 - 质押贷款净增加额', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'n_incr_pledge_loan'}],
    ('stot_out_inv_act', 'q', 'E'):                   ['上市公司现金流量表 - 投资活动现金流出小计', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'stot_out_inv_act'}],
    ('n_cashflow_inv_act', 'q', 'E'):                 ['上市公司现金流量表 - 投资活动产生的现金流量净额', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'n_cashflow_inv_act'}],
    ('c_recp_borrow', 'q', 'E'):                      ['上市公司现金流量表 - 取得借款收到的现金', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'c_recp_borrow'}],
    ('proc_issue_bonds', 'q', 'E'):                   ['上市公司现金流量表 - 发行债券收到的现金', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'proc_issue_bonds'}],
    ('oth_cash_recp_ral_fnc_act', 'q', 'E'):          ['上市公司现金流量表 - 收到其他与筹资活动有关的现金', 'direct',
                                                       {'table_name': 'cashflow',
                                                        'column':     'oth_cash_recp_ral_fnc_act'}],
    ('stot_cash_in_fnc_act', 'q', 'E'):               ['上市公司现金流量表 - 筹资活动现金流入小计', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'stot_cash_in_fnc_act'}],
    ('free_cashflow', 'q', 'E'):                      ['上市公司现金流量表 - 企业自由现金流量', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'free_cashflow'}],
    ('c_prepay_amt_borr', 'q', 'E'):                  ['上市公司现金流量表 - 偿还债务支付的现金', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'c_prepay_amt_borr'}],
    ('c_pay_dist_dpcp_int_exp', 'q', 'E'):            ['上市公司现金流量表 - 分配股利、利润或偿付利息支付的现金',
                                                       'direct',
                                                       {'table_name': 'cashflow', 'column': 'c_pay_dist_dpcp_int_exp'}],
    ('incl_dvd_profit_paid_sc_ms', 'q', 'E'):         ['上市公司现金流量表 - 其中:子公司支付给少数股东的股利、利润',
                                                       'direct', {'table_name': 'cashflow',
                                                                  'column':     'incl_dvd_profit_paid_sc_ms'}],
    ('oth_cashpay_ral_fnc_act', 'q', 'E'):            ['上市公司现金流量表 - 支付其他与筹资活动有关的现金', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'oth_cashpay_ral_fnc_act'}],
    ('stot_cashout_fnc_act', 'q', 'E'):               ['上市公司现金流量表 - 筹资活动现金流出小计', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'stot_cashout_fnc_act'}],
    ('n_cash_flows_fnc_act', 'q', 'E'):               ['上市公司现金流量表 - 筹资活动产生的现金流量净额', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'n_cash_flows_fnc_act'}],
    ('eff_fx_flu_cash', 'q', 'E'):                    ['上市公司现金流量表 - 汇率变动对现金的影响', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'eff_fx_flu_cash'}],
    ('n_incr_cash_cash_equ', 'q', 'E'):               ['上市公司现金流量表 - 现金及现金等价物净增加额', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'n_incr_cash_cash_equ'}],
    ('c_cash_equ_beg_period', 'q', 'E'):              ['上市公司现金流量表 - 期初现金及现金等价物余额', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'c_cash_equ_beg_period'}],
    ('c_cash_equ_end_period', 'q', 'E'):              ['上市公司现金流量表 - 期末现金及现金等价物余额', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'c_cash_equ_end_period'}],
    ('c_recp_cap_contrib', 'q', 'E'):                 ['上市公司现金流量表 - 吸收投资收到的现金', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'c_recp_cap_contrib'}],
    ('incl_cash_rec_saims', 'q', 'E'):                ['上市公司现金流量表 - 其中:子公司吸收少数股东投资收到的现金',
                                                       'direct',
                                                       {'table_name': 'cashflow', 'column': 'incl_cash_rec_saims'}],
    ('uncon_invest_loss', 'q', 'E'):                  ['上市公司现金流量表 - 未确认投资损失', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'uncon_invest_loss'}],
    ('prov_depr_assets', 'q', 'E'):                   ['上市公司现金流量表 - 加:资产减值准备', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'prov_depr_assets'}],
    ('depr_fa_coga_dpba', 'q', 'E'):                  [
        '上市公司现金流量表 - 固定资产折旧、油气资产折耗、生产性生物资产折旧', 'direct',
        {'table_name': 'cashflow', 'column': 'depr_fa_coga_dpba'}],
    ('amort_intang_assets', 'q', 'E'):                ['上市公司现金流量表 - 无形资产摊销', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'amort_intang_assets'}],
    ('lt_amort_deferred_exp', 'q', 'E'):              ['上市公司现金流量表 - 长期待摊费用摊销', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'lt_amort_deferred_exp'}],
    ('decr_deferred_exp', 'q', 'E'):                  ['上市公司现金流量表 - 待摊费用减少', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'decr_deferred_exp'}],
    ('incr_acc_exp', 'q', 'E'):                       ['上市公司现金流量表 - 预提费用增加', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'incr_acc_exp'}],
    ('loss_disp_fiolta', 'q', 'E'):                   ['上市公司现金流量表 - 处置固定、无形资产和其他长期资产的损失',
                                                       'direct',
                                                       {'table_name': 'cashflow', 'column': 'loss_disp_fiolta'}],
    ('loss_scr_fa', 'q', 'E'):                        ['上市公司现金流量表 - 固定资产报废损失', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'loss_scr_fa'}],
    ('loss_fv_chg', 'q', 'E'):                        ['上市公司现金流量表 - 公允价值变动损失', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'loss_fv_chg'}],
    ('invest_loss', 'q', 'E'):                        ['上市公司现金流量表 - 投资损失', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'invest_loss'}],
    ('decr_def_inc_tax_assets', 'q', 'E'):            ['上市公司现金流量表 - 递延所得税资产减少', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'decr_def_inc_tax_assets'}],
    ('incr_def_inc_tax_liab', 'q', 'E'):              ['上市公司现金流量表 - 递延所得税负债增加', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'incr_def_inc_tax_liab'}],
    ('decr_inventories', 'q', 'E'):                   ['上市公司现金流量表 - 存货的减少', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'decr_inventories'}],
    ('decr_oper_payable', 'q', 'E'):                  ['上市公司现金流量表 - 经营性应收项目的减少', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'decr_oper_payable'}],
    ('incr_oper_payable', 'q', 'E'):                  ['上市公司现金流量表 - 经营性应付项目的增加', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'incr_oper_payable'}],
    ('others', 'q', 'E'):                             ['上市公司现金流量表 - 其他', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'others'}],
    ('im_net_cashflow_oper_act', 'q', 'E'):           ['上市公司现金流量表 - 经营活动产生的现金流量净额(间接法)',
                                                       'direct', {'table_name': 'cashflow',
                                                                  'column':     'im_net_cashflow_oper_act'}],
    ('conv_debt_into_cap', 'q', 'E'):                 ['上市公司现金流量表 - 债务转为资本', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'conv_debt_into_cap'}],
    ('conv_copbonds_due_within_1y', 'q', 'E'):        ['上市公司现金流量表 - 一年内到期的可转换公司债券', 'direct',
                                                       {'table_name': 'cashflow',
                                                        'column':     'conv_copbonds_due_within_1y'}],
    ('fa_fnc_leases', 'q', 'E'):                      ['上市公司现金流量表 - 融资租入固定资产', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'fa_fnc_leases'}],
    ('im_n_incr_cash_equ', 'q', 'E'):                 ['上市公司现金流量表 - 现金及现金等价物净增加额(间接法)',
                                                       'direct',
                                                       {'table_name': 'cashflow', 'column': 'im_n_incr_cash_equ'}],
    ('net_dism_capital_add', 'q', 'E'):               ['上市公司现金流量表 - 拆出资金净增加额', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'net_dism_capital_add'}],
    ('net_cash_rece_sec', 'q', 'E'):                  ['上市公司现金流量表 - 代理买卖证券收到的现金净额(元)', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'net_cash_rece_sec'}],
    ('cashflow_credit_impa_loss', 'q', 'E'):          ['上市公司现金流量表 - 信用减值损失', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'credit_impa_loss'}],
    ('use_right_asset_dep', 'q', 'E'):                ['上市公司现金流量表 - 使用权资产折旧', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'use_right_asset_dep'}],
    ('oth_loss_asset', 'q', 'E'):                     ['上市公司现金流量表 - 其他资产减值损失', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'oth_loss_asset'}],
    ('end_bal_cash', 'q', 'E'):                       ['上市公司现金流量表 - 现金的期末余额', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'end_bal_cash'}],
    ('beg_bal_cash', 'q', 'E'):                       ['上市公司现金流量表 - 减:现金的期初余额', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'beg_bal_cash'}],
    ('end_bal_cash_equ', 'q', 'E'):                   ['上市公司现金流量表 - 加:现金等价物的期末余额', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'end_bal_cash_equ'}],
    ('beg_bal_cash_equ', 'q', 'E'):                   ['上市公司现金流量表 - 减:现金等价物的期初余额', 'direct',
                                                       {'table_name': 'cashflow', 'column': 'beg_bal_cash_equ'}],
    ('express_revenue', 'q', 'E'):                    ['上市公司业绩快报 - 营业收入(元)', 'direct',
                                                       {'table_name': 'express', 'column': 'revenue'}],
    ('express_operate_profit', 'q', 'E'):             ['上市公司业绩快报 - 营业利润(元)', 'direct',
                                                       {'table_name': 'express', 'column': 'operate_profit'}],
    ('express_total_profit', 'q', 'E'):               ['上市公司业绩快报 - 利润总额(元)', 'direct',
                                                       {'table_name': 'express', 'column': 'total_profit'}],
    ('express_n_income', 'q', 'E'):                   ['上市公司业绩快报 - 净利润(元)', 'direct',
                                                       {'table_name': 'express', 'column': 'n_income'}],
    ('express_total_assets', 'q', 'E'):               ['上市公司业绩快报 - 总资产(元)', 'direct',
                                                       {'table_name': 'express', 'column': 'total_assets'}],
    ('express_total_hldr_eqy_exc_min_int', 'q', 'E'): ['上市公司业绩快报 - 股东权益合计(不含少数股东权益)(元)',
                                                       'direct', {'table_name': 'express',
                                                                  'column':     'total_hldr_eqy_exc_min_int'}],
    ('express_diluted_eps', 'q', 'E'):                ['上市公司业绩快报 - 每股收益(摊薄)(元)', 'direct',
                                                       {'table_name': 'express', 'column': 'diluted_eps'}],
    ('diluted_roe', 'q', 'E'):                        ['上市公司业绩快报 - 净资产收益率(摊薄)(%)', 'direct',
                                                       {'table_name': 'express', 'column': 'diluted_roe'}],
    ('yoy_net_profit', 'q', 'E'):                     ['上市公司业绩快报 - 去年同期修正后净利润', 'direct',
                                                       {'table_name': 'express', 'column': 'yoy_net_profit'}],
    ('bps', 'q', 'E'):                                ['上市公司业绩快报 - 每股净资产', 'direct',
                                                       {'table_name': 'express', 'column': 'bps'}],
    ('yoy_sales', 'q', 'E'):                          ['上市公司业绩快报 - 同比增长率:营业收入', 'direct',
                                                       {'table_name': 'express', 'column': 'yoy_sales'}],
    ('yoy_op', 'q', 'E'):                             ['上市公司业绩快报 - 同比增长率:营业利润', 'direct',
                                                       {'table_name': 'express', 'column': 'yoy_op'}],
    ('yoy_tp', 'q', 'E'):                             ['上市公司业绩快报 - 同比增长率:利润总额', 'direct',
                                                       {'table_name': 'express', 'column': 'yoy_tp'}],
    ('yoy_dedu_np', 'q', 'E'):                        ['上市公司业绩快报 - 同比增长率:归属母公司股东的净利润', 'direct',
                                                       {'table_name': 'express', 'column': 'yoy_dedu_np'}],
    ('yoy_eps', 'q', 'E'):                            ['上市公司业绩快报 - 同比增长率:基本每股收益', 'direct',
                                                       {'table_name': 'express', 'column': 'yoy_eps'}],
    ('yoy_roe', 'q', 'E'):                            ['上市公司业绩快报 - 同比增减:加权平均净资产收益率', 'direct',
                                                       {'table_name': 'express', 'column': 'yoy_roe'}],
    ('growth_assets', 'q', 'E'):                      ['上市公司业绩快报 - 比年初增长率:总资产', 'direct',
                                                       {'table_name': 'express', 'column': 'growth_assets'}],
    ('yoy_equity', 'q', 'E'):                         ['上市公司业绩快报 - 比年初增长率:归属母公司的股东权益', 'direct',
                                                       {'table_name': 'express', 'column': 'yoy_equity'}],
    ('growth_bps', 'q', 'E'):                         ['上市公司业绩快报 - 比年初增长率:归属于母公司股东的每股净资产',
                                                       'direct', {'table_name': 'express', 'column': 'growth_bps'}],
    ('or_last_year', 'q', 'E'):                       ['上市公司业绩快报 - 去年同期营业收入', 'direct',
                                                       {'table_name': 'express', 'column': 'or_last_year'}],
    ('op_last_year', 'q', 'E'):                       ['上市公司业绩快报 - 去年同期营业利润', 'direct',
                                                       {'table_name': 'express', 'column': 'op_last_year'}],
    ('tp_last_year', 'q', 'E'):                       ['上市公司业绩快报 - 去年同期利润总额', 'direct',
                                                       {'table_name': 'express', 'column': 'tp_last_year'}],
    ('np_last_year', 'q', 'E'):                       ['上市公司业绩快报 - 去年同期净利润', 'direct',
                                                       {'table_name': 'express', 'column': 'np_last_year'}],
    ('eps_last_year', 'q', 'E'):                      ['上市公司业绩快报 - 去年同期每股收益', 'direct',
                                                       {'table_name': 'express', 'column': 'eps_last_year'}],
    ('open_net_assets', 'q', 'E'):                    ['上市公司业绩快报 - 期初净资产', 'direct',
                                                       {'table_name': 'express', 'column': 'open_net_assets'}],
    ('open_bps', 'q', 'E'):                           ['上市公司业绩快报 - 期初每股净资产', 'direct',
                                                       {'table_name': 'express', 'column': 'open_bps'}],
    ('perf_summary', 'q', 'E'):                       ['上市公司业绩快报 - 业绩简要说明', 'direct',
                                                       {'table_name': 'express', 'column': 'perf_summary'}],
    ('eps', 'q', 'E'):                                ['上市公司财务指标 - 基本每股收益', 'direct',
                                                       {'table_name': 'financial', 'column': 'eps'}],
    ('dt_eps', 'q', 'E'):                             ['上市公司财务指标 - 稀释每股收益', 'direct',
                                                       {'table_name': 'financial', 'column': 'dt_eps'}],
    ('total_revenue_ps', 'q', 'E'):                   ['上市公司财务指标 - 每股营业总收入', 'direct',
                                                       {'table_name': 'financial', 'column': 'total_revenue_ps'}],
    ('revenue_ps', 'q', 'E'):                         ['上市公司财务指标 - 每股营业收入', 'direct',
                                                       {'table_name': 'financial', 'column': 'revenue_ps'}],
    ('capital_rese_ps', 'q', 'E'):                    ['上市公司财务指标 - 每股资本公积', 'direct',
                                                       {'table_name': 'financial', 'column': 'capital_rese_ps'}],
    ('surplus_rese_ps', 'q', 'E'):                    ['上市公司财务指标 - 每股盈余公积', 'direct',
                                                       {'table_name': 'financial', 'column': 'surplus_rese_ps'}],
    ('undist_profit_ps', 'q', 'E'):                   ['上市公司财务指标 - 每股未分配利润', 'direct',
                                                       {'table_name': 'financial', 'column': 'undist_profit_ps'}],
    ('extra_item', 'q', 'E'):                         ['上市公司财务指标 - 非经常性损益', 'direct',
                                                       {'table_name': 'financial', 'column': 'extra_item'}],
    ('profit_dedt', 'q', 'E'):                        ['上市公司财务指标 - 扣除非经常性损益后的净利润（扣非净利润）',
                                                       'direct', {'table_name': 'financial', 'column': 'profit_dedt'}],
    ('gross_margin', 'q', 'E'):                       ['上市公司财务指标 - 毛利', 'direct',
                                                       {'table_name': 'financial', 'column': 'gross_margin'}],
    ('current_ratio', 'q', 'E'):                      ['上市公司财务指标 - 流动比率', 'direct',
                                                       {'table_name': 'financial', 'column': 'current_ratio'}],
    ('quick_ratio', 'q', 'E'):                        ['上市公司财务指标 - 速动比率', 'direct',
                                                       {'table_name': 'financial', 'column': 'quick_ratio'}],
    ('cash_ratio', 'q', 'E'):                         ['上市公司财务指标 - 保守速动比率', 'direct',
                                                       {'table_name': 'financial', 'column': 'cash_ratio'}],
    ('invturn_days', 'q', 'E'):                       ['上市公司财务指标 - 存货周转天数', 'direct',
                                                       {'table_name': 'financial', 'column': 'invturn_days'}],
    ('arturn_days', 'q', 'E'):                        ['上市公司财务指标 - 应收账款周转天数', 'direct',
                                                       {'table_name': 'financial', 'column': 'arturn_days'}],
    ('inv_turn', 'q', 'E'):                           ['上市公司财务指标 - 存货周转率', 'direct',
                                                       {'table_name': 'financial', 'column': 'inv_turn'}],
    ('ar_turn', 'q', 'E'):                            ['上市公司财务指标 - 应收账款周转率', 'direct',
                                                       {'table_name': 'financial', 'column': 'ar_turn'}],
    ('ca_turn', 'q', 'E'):                            ['上市公司财务指标 - 流动资产周转率', 'direct',
                                                       {'table_name': 'financial', 'column': 'ca_turn'}],
    ('fa_turn', 'q', 'E'):                            ['上市公司财务指标 - 固定资产周转率', 'direct',
                                                       {'table_name': 'financial', 'column': 'fa_turn'}],
    ('assets_turn', 'q', 'E'):                        ['上市公司财务指标 - 总资产周转率', 'direct',
                                                       {'table_name': 'financial', 'column': 'assets_turn'}],
    ('op_income', 'q', 'E'):                          ['上市公司财务指标 - 经营活动净收益', 'direct',
                                                       {'table_name': 'financial', 'column': 'op_income'}],
    ('valuechange_income', 'q', 'E'):                 ['上市公司财务指标 - 价值变动净收益', 'direct',
                                                       {'table_name': 'financial', 'column': 'valuechange_income'}],
    ('interst_income', 'q', 'E'):                     ['上市公司财务指标 - 利息费用', 'direct',
                                                       {'table_name': 'financial', 'column': 'interst_income'}],
    ('daa', 'q', 'E'):                                ['上市公司财务指标 - 折旧与摊销', 'direct',
                                                       {'table_name': 'financial', 'column': 'daa'}],
    ('ebit', 'q', 'E'):                               ['上市公司财务指标 - 息税前利润', 'direct',
                                                       {'table_name': 'financial', 'column': 'ebit'}],
    ('ebitda', 'q', 'E'):                             ['上市公司财务指标 - 息税折旧摊销前利润', 'direct',
                                                       {'table_name': 'financial', 'column': 'ebitda'}],
    ('fcff', 'q', 'E'):                               ['上市公司财务指标 - 企业自由现金流量', 'direct',
                                                       {'table_name': 'financial', 'column': 'fcff'}],
    ('fcfe', 'q', 'E'):                               ['上市公司财务指标 - 股权自由现金流量', 'direct',
                                                       {'table_name': 'financial', 'column': 'fcfe'}],
    ('current_exint', 'q', 'E'):                      ['上市公司财务指标 - 无息流动负债', 'direct',
                                                       {'table_name': 'financial', 'column': 'current_exint'}],
    ('noncurrent_exint', 'q', 'E'):                   ['上市公司财务指标 - 无息非流动负债', 'direct',
                                                       {'table_name': 'financial', 'column': 'noncurrent_exint'}],
    ('interestdebt', 'q', 'E'):                       ['上市公司财务指标 - 带息债务', 'direct',
                                                       {'table_name': 'financial', 'column': 'interestdebt'}],
    ('netdebt', 'q', 'E'):                            ['上市公司财务指标 - 净债务', 'direct',
                                                       {'table_name': 'financial', 'column': 'netdebt'}],
    ('tangible_asset', 'q', 'E'):                     ['上市公司财务指标 - 有形资产', 'direct',
                                                       {'table_name': 'financial', 'column': 'tangible_asset'}],
    ('working_capital', 'q', 'E'):                    ['上市公司财务指标 - 营运资金', 'direct',
                                                       {'table_name': 'financial', 'column': 'working_capital'}],
    ('networking_capital', 'q', 'E'):                 ['上市公司财务指标 - 营运流动资本', 'direct',
                                                       {'table_name': 'financial', 'column': 'networking_capital'}],
    ('invest_capital', 'q', 'E'):                     ['上市公司财务指标 - 全部投入资本', 'direct',
                                                       {'table_name': 'financial', 'column': 'invest_capital'}],
    ('retained_earnings', 'q', 'E'):                  ['上市公司财务指标 - 留存收益', 'direct',
                                                       {'table_name': 'financial', 'column': 'retained_earnings'}],
    ('diluted2_eps', 'q', 'E'):                       ['上市公司财务指标 - 期末摊薄每股收益', 'direct',
                                                       {'table_name': 'financial', 'column': 'diluted2_eps'}],
    ('express_bps', 'q', 'E'):                        ['上市公司财务指标 - 每股净资产', 'direct',
                                                       {'table_name': 'financial', 'column': 'bps'}],
    ('ocfps', 'q', 'E'):                              ['上市公司财务指标 - 每股经营活动产生的现金流量净额', 'direct',
                                                       {'table_name': 'financial', 'column': 'ocfps'}],
    ('retainedps', 'q', 'E'):                         ['上市公司财务指标 - 每股留存收益', 'direct',
                                                       {'table_name': 'financial', 'column': 'retainedps'}],
    ('cfps', 'q', 'E'):                               ['上市公司财务指标 - 每股现金流量净额', 'direct',
                                                       {'table_name': 'financial', 'column': 'cfps'}],
    ('ebit_ps', 'q', 'E'):                            ['上市公司财务指标 - 每股息税前利润', 'direct',
                                                       {'table_name': 'financial', 'column': 'ebit_ps'}],
    ('fcff_ps', 'q', 'E'):                            ['上市公司财务指标 - 每股企业自由现金流量', 'direct',
                                                       {'table_name': 'financial', 'column': 'fcff_ps'}],
    ('fcfe_ps', 'q', 'E'):                            ['上市公司财务指标 - 每股股东自由现金流量', 'direct',
                                                       {'table_name': 'financial', 'column': 'fcfe_ps'}],
    ('netprofit_margin', 'q', 'E'):                   ['上市公司财务指标 - 销售净利率', 'direct',
                                                       {'table_name': 'financial', 'column': 'netprofit_margin'}],
    ('grossprofit_margin', 'q', 'E'):                 ['上市公司财务指标 - 销售毛利率', 'direct',
                                                       {'table_name': 'financial', 'column': 'grossprofit_margin'}],
    ('cogs_of_sales', 'q', 'E'):                      ['上市公司财务指标 - 销售成本率', 'direct',
                                                       {'table_name': 'financial', 'column': 'cogs_of_sales'}],
    ('expense_of_sales', 'q', 'E'):                   ['上市公司财务指标 - 销售期间费用率', 'direct',
                                                       {'table_name': 'financial', 'column': 'expense_of_sales'}],
    ('profit_to_gr', 'q', 'E'):                       ['上市公司财务指标 - 净利润/营业总收入', 'direct',
                                                       {'table_name': 'financial', 'column': 'profit_to_gr'}],
    ('saleexp_to_gr', 'q', 'E'):                      ['上市公司财务指标 - 销售费用/营业总收入', 'direct',
                                                       {'table_name': 'financial', 'column': 'saleexp_to_gr'}],
    ('adminexp_of_gr', 'q', 'E'):                     ['上市公司财务指标 - 管理费用/营业总收入', 'direct',
                                                       {'table_name': 'financial', 'column': 'adminexp_of_gr'}],
    ('finaexp_of_gr', 'q', 'E'):                      ['上市公司财务指标 - 财务费用/营业总收入', 'direct',
                                                       {'table_name': 'financial', 'column': 'finaexp_of_gr'}],
    ('impai_ttm', 'q', 'E'):                          ['上市公司财务指标 - 资产减值损失/营业总收入', 'direct',
                                                       {'table_name': 'financial', 'column': 'impai_ttm'}],
    ('gc_of_gr', 'q', 'E'):                           ['上市公司财务指标 - 营业总成本/营业总收入', 'direct',
                                                       {'table_name': 'financial', 'column': 'gc_of_gr'}],
    ('op_of_gr', 'q', 'E'):                           ['上市公司财务指标 - 营业利润/营业总收入', 'direct',
                                                       {'table_name': 'financial', 'column': 'op_of_gr'}],
    ('ebit_of_gr', 'q', 'E'):                         ['上市公司财务指标 - 息税前利润/营业总收入', 'direct',
                                                       {'table_name': 'financial', 'column': 'ebit_of_gr'}],
    ('roe', 'q', 'E'):                                ['上市公司财务指标 - 净资产收益率', 'direct',
                                                       {'table_name': 'financial', 'column': 'roe'}],
    ('roe_waa', 'q', 'E'):                            ['上市公司财务指标 - 加权平均净资产收益率', 'direct',
                                                       {'table_name': 'financial', 'column': 'roe_waa'}],
    ('roe_dt', 'q', 'E'):                             ['上市公司财务指标 - 净资产收益率(扣除非经常损益)', 'direct',
                                                       {'table_name': 'financial', 'column': 'roe_dt'}],
    ('roa', 'q', 'E'):                                ['上市公司财务指标 - 总资产报酬率', 'direct',
                                                       {'table_name': 'financial', 'column': 'roa'}],
    ('npta', 'q', 'E'):                               ['上市公司财务指标 - 总资产净利润', 'direct',
                                                       {'table_name': 'financial', 'column': 'npta'}],
    ('roic', 'q', 'E'):                               ['上市公司财务指标 - 投入资本回报率', 'direct',
                                                       {'table_name': 'financial', 'column': 'roic'}],
    ('roe_yearly', 'q', 'E'):                         ['上市公司财务指标 - 年化净资产收益率', 'direct',
                                                       {'table_name': 'financial', 'column': 'roe_yearly'}],
    ('roa2_yearly', 'q', 'E'):                        ['上市公司财务指标 - 年化总资产报酬率', 'direct',
                                                       {'table_name': 'financial', 'column': 'roa2_yearly'}],
    ('roe_avg', 'q', 'E'):                            ['上市公司财务指标 - 平均净资产收益率(增发条件)', 'direct',
                                                       {'table_name': 'financial', 'column': 'roe_avg'}],
    ('opincome_of_ebt', 'q', 'E'):                    ['上市公司财务指标 - 经营活动净收益/利润总额', 'direct',
                                                       {'table_name': 'financial', 'column': 'opincome_of_ebt'}],
    ('investincome_of_ebt', 'q', 'E'):                ['上市公司财务指标 - 价值变动净收益/利润总额', 'direct',
                                                       {'table_name': 'financial', 'column': 'investincome_of_ebt'}],
    ('n_op_profit_of_ebt', 'q', 'E'):                 ['上市公司财务指标 - 营业外收支净额/利润总额', 'direct',
                                                       {'table_name': 'financial', 'column': 'n_op_profit_of_ebt'}],
    ('tax_to_ebt', 'q', 'E'):                         ['上市公司财务指标 - 所得税/利润总额', 'direct',
                                                       {'table_name': 'financial', 'column': 'tax_to_ebt'}],
    ('dtprofit_to_profit', 'q', 'E'):                 ['上市公司财务指标 - 扣除非经常损益后的净利润/净利润', 'direct',
                                                       {'table_name': 'financial', 'column': 'dtprofit_to_profit'}],
    ('salescash_to_or', 'q', 'E'):                    ['上市公司财务指标 - 销售商品提供劳务收到的现金/营业收入',
                                                       'direct',
                                                       {'table_name': 'financial', 'column': 'salescash_to_or'}],
    ('ocf_to_or', 'q', 'E'):                          ['上市公司财务指标 - 经营活动产生的现金流量净额/营业收入',
                                                       'direct', {'table_name': 'financial', 'column': 'ocf_to_or'}],
    ('ocf_to_opincome', 'q', 'E'):                    ['上市公司财务指标 - 经营活动产生的现金流量净额/经营活动净收益',
                                                       'direct',
                                                       {'table_name': 'financial', 'column': 'ocf_to_opincome'}],
    ('capitalized_to_da', 'q', 'E'):                  ['上市公司财务指标 - 资本支出/折旧和摊销', 'direct',
                                                       {'table_name': 'financial', 'column': 'capitalized_to_da'}],
    ('debt_to_assets', 'q', 'E'):                     ['上市公司财务指标 - 资产负债率', 'direct',
                                                       {'table_name': 'financial', 'column': 'debt_to_assets'}],
    ('assets_to_eqt', 'q', 'E'):                      ['上市公司财务指标 - 权益乘数', 'direct',
                                                       {'table_name': 'financial', 'column': 'assets_to_eqt'}],
    ('dp_assets_to_eqt', 'q', 'E'):                   ['上市公司财务指标 - 权益乘数(杜邦分析)', 'direct',
                                                       {'table_name': 'financial', 'column': 'dp_assets_to_eqt'}],
    ('ca_to_assets', 'q', 'E'):                       ['上市公司财务指标 - 流动资产/总资产', 'direct',
                                                       {'table_name': 'financial', 'column': 'ca_to_assets'}],
    ('nca_to_assets', 'q', 'E'):                      ['上市公司财务指标 - 非流动资产/总资产', 'direct',
                                                       {'table_name': 'financial', 'column': 'nca_to_assets'}],
    ('tbassets_to_totalassets', 'q', 'E'):            ['上市公司财务指标 - 有形资产/总资产', 'direct',
                                                       {'table_name': 'financial',
                                                        'column':     'tbassets_to_totalassets'}],
    ('int_to_talcap', 'q', 'E'):                      ['上市公司财务指标 - 带息债务/全部投入资本', 'direct',
                                                       {'table_name': 'financial', 'column': 'int_to_talcap'}],
    ('eqt_to_talcapital', 'q', 'E'):                  ['上市公司财务指标 - 归属于母公司的股东权益/全部投入资本',
                                                       'direct',
                                                       {'table_name': 'financial', 'column': 'eqt_to_talcapital'}],
    ('currentdebt_to_debt', 'q', 'E'):                ['上市公司财务指标 - 流动负债/负债合计', 'direct',
                                                       {'table_name': 'financial', 'column': 'currentdebt_to_debt'}],
    ('longdeb_to_debt', 'q', 'E'):                    ['上市公司财务指标 - 非流动负债/负债合计', 'direct',
                                                       {'table_name': 'financial', 'column': 'longdeb_to_debt'}],
    ('ocf_to_shortdebt', 'q', 'E'):                   ['上市公司财务指标 - 经营活动产生的现金流量净额/流动负债',
                                                       'direct',
                                                       {'table_name': 'financial', 'column': 'ocf_to_shortdebt'}],
    ('debt_to_eqt', 'q', 'E'):                        ['上市公司财务指标 - 产权比率', 'direct',
                                                       {'table_name': 'financial', 'column': 'debt_to_eqt'}],
    ('eqt_to_debt', 'q', 'E'):                        ['上市公司财务指标 - 归属于母公司的股东权益/负债合计', 'direct',
                                                       {'table_name': 'financial', 'column': 'eqt_to_debt'}],
    ('eqt_to_interestdebt', 'q', 'E'):                ['上市公司财务指标 - 归属于母公司的股东权益/带息债务', 'direct',
                                                       {'table_name': 'financial', 'column': 'eqt_to_interestdebt'}],
    ('tangibleasset_to_debt', 'q', 'E'):              ['上市公司财务指标 - 有形资产/负债合计', 'direct',
                                                       {'table_name': 'financial', 'column': 'tangibleasset_to_debt'}],
    ('tangasset_to_intdebt', 'q', 'E'):               ['上市公司财务指标 - 有形资产/带息债务', 'direct',
                                                       {'table_name': 'financial', 'column': 'tangasset_to_intdebt'}],
    ('tangibleasset_to_netdebt', 'q', 'E'):           ['上市公司财务指标 - 有形资产/净债务', 'direct',
                                                       {'table_name': 'financial',
                                                        'column':     'tangibleasset_to_netdebt'}],
    ('ocf_to_debt', 'q', 'E'):                        ['上市公司财务指标 - 经营活动产生的现金流量净额/负债合计',
                                                       'direct', {'table_name': 'financial', 'column': 'ocf_to_debt'}],
    ('ocf_to_interestdebt', 'q', 'E'):                ['上市公司财务指标 - 经营活动产生的现金流量净额/带息债务',
                                                       'direct',
                                                       {'table_name': 'financial', 'column': 'ocf_to_interestdebt'}],
    ('ocf_to_netdebt', 'q', 'E'):                     ['上市公司财务指标 - 经营活动产生的现金流量净额/净债务', 'direct',
                                                       {'table_name': 'financial', 'column': 'ocf_to_netdebt'}],
    ('ebit_to_interest', 'q', 'E'):                   ['上市公司财务指标 - 已获利息倍数(EBIT/利息费用)', 'direct',
                                                       {'table_name': 'financial', 'column': 'ebit_to_interest'}],
    ('longdebt_to_workingcapital', 'q', 'E'):         ['上市公司财务指标 - 长期债务与营运资金比率', 'direct',
                                                       {'table_name': 'financial',
                                                        'column':     'longdebt_to_workingcapital'}],
    ('ebitda_to_debt', 'q', 'E'):                     ['上市公司财务指标 - 息税折旧摊销前利润/负债合计', 'direct',
                                                       {'table_name': 'financial', 'column': 'ebitda_to_debt'}],
    ('turn_days', 'q', 'E'):                          ['上市公司财务指标 - 营业周期', 'direct',
                                                       {'table_name': 'financial', 'column': 'turn_days'}],
    ('roa_yearly', 'q', 'E'):                         ['上市公司财务指标 - 年化总资产净利率', 'direct',
                                                       {'table_name': 'financial', 'column': 'roa_yearly'}],
    ('roa_dp', 'q', 'E'):                             ['上市公司财务指标 - 总资产净利率(杜邦分析)', 'direct',
                                                       {'table_name': 'financial', 'column': 'roa_dp'}],
    ('fixed_assets', 'q', 'E'):                       ['上市公司财务指标 - 固定资产合计', 'direct',
                                                       {'table_name': 'financial', 'column': 'fixed_assets'}],
    ('profit_prefin_exp', 'q', 'E'):                  ['上市公司财务指标 - 扣除财务费用前营业利润', 'direct',
                                                       {'table_name': 'financial', 'column': 'profit_prefin_exp'}],
    ('non_op_profit', 'q', 'E'):                      ['上市公司财务指标 - 非营业利润', 'direct',
                                                       {'table_name': 'financial', 'column': 'non_op_profit'}],
    ('op_to_ebt', 'q', 'E'):                          ['上市公司财务指标 - 营业利润／利润总额', 'direct',
                                                       {'table_name': 'financial', 'column': 'op_to_ebt'}],
    ('nop_to_ebt', 'q', 'E'):                         ['上市公司财务指标 - 非营业利润／利润总额', 'direct',
                                                       {'table_name': 'financial', 'column': 'nop_to_ebt'}],
    ('ocf_to_profit', 'q', 'E'):                      ['上市公司财务指标 - 经营活动产生的现金流量净额／营业利润',
                                                       'direct',
                                                       {'table_name': 'financial', 'column': 'ocf_to_profit'}],
    ('cash_to_liqdebt', 'q', 'E'):                    ['上市公司财务指标 - 货币资金／流动负债', 'direct',
                                                       {'table_name': 'financial', 'column': 'cash_to_liqdebt'}],
    ('cash_to_liqdebt_withinterest', 'q', 'E'):       ['上市公司财务指标 - 货币资金／带息流动负债', 'direct',
                                                       {'table_name': 'financial',
                                                        'column':     'cash_to_liqdebt_withinterest'}],
    ('op_to_liqdebt', 'q', 'E'):                      ['上市公司财务指标 - 营业利润／流动负债', 'direct',
                                                       {'table_name': 'financial', 'column': 'op_to_liqdebt'}],
    ('op_to_debt', 'q', 'E'):                         ['上市公司财务指标 - 营业利润／负债合计', 'direct',
                                                       {'table_name': 'financial', 'column': 'op_to_debt'}],
    ('roic_yearly', 'q', 'E'):                        ['上市公司财务指标 - 年化投入资本回报率', 'direct',
                                                       {'table_name': 'financial', 'column': 'roic_yearly'}],
    ('total_fa_trun', 'q', 'E'):                      ['上市公司财务指标 - 固定资产合计周转率', 'direct',
                                                       {'table_name': 'financial', 'column': 'total_fa_trun'}],
    ('profit_to_op', 'q', 'E'):                       ['上市公司财务指标 - 利润总额／营业收入', 'direct',
                                                       {'table_name': 'financial', 'column': 'profit_to_op'}],
    ('q_opincome', 'q', 'E'):                         ['上市公司财务指标 - 经营活动单季度净收益', 'direct',
                                                       {'table_name': 'financial', 'column': 'q_opincome'}],
    ('q_investincome', 'q', 'E'):                     ['上市公司财务指标 - 价值变动单季度净收益', 'direct',
                                                       {'table_name': 'financial', 'column': 'q_investincome'}],
    ('q_dtprofit', 'q', 'E'):                         ['上市公司财务指标 - 扣除非经常损益后的单季度净利润', 'direct',
                                                       {'table_name': 'financial', 'column': 'q_dtprofit'}],
    ('q_eps', 'q', 'E'):                              ['上市公司财务指标 - 每股收益(单季度)', 'direct',
                                                       {'table_name': 'financial', 'column': 'q_eps'}],
    ('q_netprofit_margin', 'q', 'E'):                 ['上市公司财务指标 - 销售净利率(单季度)', 'direct',
                                                       {'table_name': 'financial', 'column': 'q_netprofit_margin'}],
    ('q_gsprofit_margin', 'q', 'E'):                  ['上市公司财务指标 - 销售毛利率(单季度)', 'direct',
                                                       {'table_name': 'financial', 'column': 'q_gsprofit_margin'}],
    ('q_exp_to_sales', 'q', 'E'):                     ['上市公司财务指标 - 销售期间费用率(单季度)', 'direct',
                                                       {'table_name': 'financial', 'column': 'q_exp_to_sales'}],
    ('q_profit_to_gr', 'q', 'E'):                     ['上市公司财务指标 - 净利润／营业总收入(单季度)', 'direct',
                                                       {'table_name': 'financial', 'column': 'q_profit_to_gr'}],
    ('q_saleexp_to_gr', 'q', 'E'):                    ['上市公司财务指标 - 销售费用／营业总收入 (单季度)', 'direct',
                                                       {'table_name': 'financial', 'column': 'q_saleexp_to_gr'}],
    ('q_adminexp_to_gr', 'q', 'E'):                   ['上市公司财务指标 - 管理费用／营业总收入 (单季度)', 'direct',
                                                       {'table_name': 'financial', 'column': 'q_adminexp_to_gr'}],
    ('q_finaexp_to_gr', 'q', 'E'):                    ['上市公司财务指标 - 财务费用／营业总收入 (单季度)', 'direct',
                                                       {'table_name': 'financial', 'column': 'q_finaexp_to_gr'}],
    ('q_impair_to_gr_ttm', 'q', 'E'):                 ['上市公司财务指标 - 资产减值损失／营业总收入(单季度)', 'direct',
                                                       {'table_name': 'financial', 'column': 'q_impair_to_gr_ttm'}],
    ('q_gc_to_gr', 'q', 'E'):                         ['上市公司财务指标 - 营业总成本／营业总收入 (单季度)', 'direct',
                                                       {'table_name': 'financial', 'column': 'q_gc_to_gr'}],
    ('q_op_to_gr', 'q', 'E'):                         ['上市公司财务指标 - 营业利润／营业总收入(单季度)', 'direct',
                                                       {'table_name': 'financial', 'column': 'q_op_to_gr'}],
    ('q_roe', 'q', 'E'):                              ['上市公司财务指标 - 净资产收益率(单季度)', 'direct',
                                                       {'table_name': 'financial', 'column': 'q_roe'}],
    ('q_dt_roe', 'q', 'E'):                           ['上市公司财务指标 - 净资产单季度收益率(扣除非经常损益)',
                                                       'direct', {'table_name': 'financial', 'column': 'q_dt_roe'}],
    ('q_npta', 'q', 'E'):                             ['上市公司财务指标 - 总资产净利润(单季度)', 'direct',
                                                       {'table_name': 'financial', 'column': 'q_npta'}],
    ('q_opincome_to_ebt', 'q', 'E'):                  ['上市公司财务指标 - 经营活动净收益／利润总额(单季度)', 'direct',
                                                       {'table_name': 'financial', 'column': 'q_opincome_to_ebt'}],
    ('q_investincome_to_ebt', 'q', 'E'):              ['上市公司财务指标 - 价值变动净收益／利润总额(单季度)', 'direct',
                                                       {'table_name': 'financial', 'column': 'q_investincome_to_ebt'}],
    ('q_dtprofit_to_profit', 'q', 'E'):               ['上市公司财务指标 - 扣除非经常损益后的净利润／净利润(单季度)',
                                                       'direct',
                                                       {'table_name': 'financial', 'column': 'q_dtprofit_to_profit'}],
    ('q_salescash_to_or', 'q', 'E'):                  ['上市公司财务指标 - 销售商品提供劳务收到的现金／营业收入(单季度)',
                                                       'direct',
                                                       {'table_name': 'financial', 'column': 'q_salescash_to_or'}],
    ('q_ocf_to_sales', 'q', 'E'):                     ['上市公司财务指标 - 经营活动产生的现金流量净额／营业收入(单季度)',
                                                       'direct',
                                                       {'table_name': 'financial', 'column': 'q_ocf_to_sales'}],
    ('q_ocf_to_or', 'q', 'E'):                        [
        '上市公司财务指标 - 经营活动产生的现金流量净额／经营活动净收益(单季度)', 'direct',
        {'table_name': 'financial', 'column': 'q_ocf_to_or'}],
    ('basic_eps_yoy', 'q', 'E'):                      ['上市公司财务指标 - 基本每股收益同比增长率(%)', 'direct',
                                                       {'table_name': 'financial', 'column': 'basic_eps_yoy'}],
    ('dt_eps_yoy', 'q', 'E'):                         ['上市公司财务指标 - 稀释每股收益同比增长率(%)', 'direct',
                                                       {'table_name': 'financial', 'column': 'dt_eps_yoy'}],
    ('cfps_yoy', 'q', 'E'):                           ['上市公司财务指标 - 每股经营活动产生的现金流量净额同比增长率(%)',
                                                       'direct', {'table_name': 'financial', 'column': 'cfps_yoy'}],
    ('op_yoy', 'q', 'E'):                             ['上市公司财务指标 - 营业利润同比增长率(%)', 'direct',
                                                       {'table_name': 'financial', 'column': 'op_yoy'}],
    ('ebt_yoy', 'q', 'E'):                            ['上市公司财务指标 - 利润总额同比增长率(%)', 'direct',
                                                       {'table_name': 'financial', 'column': 'ebt_yoy'}],
    ('netprofit_yoy', 'q', 'E'):                      ['上市公司财务指标 - 归属母公司股东的净利润同比增长率(%)',
                                                       'direct',
                                                       {'table_name': 'financial', 'column': 'netprofit_yoy'}],
    ('dt_netprofit_yoy', 'q', 'E'):                   [
        '上市公司财务指标 - 归属母公司股东的净利润-扣除非经常损益同比增长率(%)', 'direct',
        {'table_name': 'financial', 'column': 'dt_netprofit_yoy'}],
    ('ocf_yoy', 'q', 'E'):                            ['上市公司财务指标 - 经营活动产生的现金流量净额同比增长率(%)',
                                                       'direct', {'table_name': 'financial', 'column': 'ocf_yoy'}],
    ('roe_yoy', 'q', 'E'):                            ['上市公司财务指标 - 净资产收益率(摊薄)同比增长率(%)', 'direct',
                                                       {'table_name': 'financial', 'column': 'roe_yoy'}],
    ('bps_yoy', 'q', 'E'):                            ['上市公司财务指标 - 每股净资产相对年初增长率(%)', 'direct',
                                                       {'table_name': 'financial', 'column': 'bps_yoy'}],
    ('assets_yoy', 'q', 'E'):                         ['上市公司财务指标 - 资产总计相对年初增长率(%)', 'direct',
                                                       {'table_name': 'financial', 'column': 'assets_yoy'}],
    ('eqt_yoy', 'q', 'E'):                            ['上市公司财务指标 - 归属母公司的股东权益相对年初增长率(%)',
                                                       'direct', {'table_name': 'financial', 'column': 'eqt_yoy'}],
    ('tr_yoy', 'q', 'E'):                             ['上市公司财务指标 - 营业总收入同比增长率(%)', 'direct',
                                                       {'table_name': 'financial', 'column': 'tr_yoy'}],
    ('or_yoy', 'q', 'E'):                             ['上市公司财务指标 - 营业收入同比增长率(%)', 'direct',
                                                       {'table_name': 'financial', 'column': 'or_yoy'}],
    ('q_gr_yoy', 'q', 'E'):                           ['上市公司财务指标 - 营业总收入同比增长率(%)(单季度)', 'direct',
                                                       {'table_name': 'financial', 'column': 'q_gr_yoy'}],
    ('q_gr_qoq', 'q', 'E'):                           ['上市公司财务指标 - 营业总收入环比增长率(%)(单季度)', 'direct',
                                                       {'table_name': 'financial', 'column': 'q_gr_qoq'}],
    ('q_sales_yoy', 'q', 'E'):                        ['上市公司财务指标 - 营业收入同比增长率(%)(单季度)', 'direct',
                                                       {'table_name': 'financial', 'column': 'q_sales_yoy'}],
    ('q_sales_qoq', 'q', 'E'):                        ['上市公司财务指标 - 营业收入环比增长率(%)(单季度)', 'direct',
                                                       {'table_name': 'financial', 'column': 'q_sales_qoq'}],
    ('q_op_yoy', 'q', 'E'):                           ['上市公司财务指标 - 营业利润同比增长率(%)(单季度)', 'direct',
                                                       {'table_name': 'financial', 'column': 'q_op_yoy'}],
    ('q_op_qoq', 'q', 'E'):                           ['上市公司财务指标 - 营业利润环比增长率(%)(单季度)', 'direct',
                                                       {'table_name': 'financial', 'column': 'q_op_qoq'}],
    ('q_profit_yoy', 'q', 'E'):                       ['上市公司财务指标 - 净利润同比增长率(%)(单季度)', 'direct',
                                                       {'table_name': 'financial', 'column': 'q_profit_yoy'}],
    ('q_profit_qoq', 'q', 'E'):                       ['上市公司财务指标 - 净利润环比增长率(%)(单季度)', 'direct',
                                                       {'table_name': 'financial', 'column': 'q_profit_qoq'}],
    ('q_netprofit_yoy', 'q', 'E'):                    ['上市公司财务指标 - 归属母公司股东的净利润同比增长率(%)(单季度)',
                                                       'direct',
                                                       {'table_name': 'financial', 'column': 'q_netprofit_yoy'}],
    ('q_netprofit_qoq', 'q', 'E'):                    ['上市公司财务指标 - 归属母公司股东的净利润环比增长率(%)(单季度)',
                                                       'direct',
                                                       {'table_name': 'financial', 'column': 'q_netprofit_qoq'}],
    ('equity_yoy', 'q', 'E'):                         ['上市公司财务指标 - 净资产同比增长率', 'direct',
                                                       {'table_name': 'financial', 'column': 'equity_yoy'}],
    ('rd_exp', 'q', 'E'):                             ['上市公司财务指标 - 研发费用', 'direct',
                                                       {'table_name': 'financial', 'column': 'rd_exp'}],
    ('rzye|%', 'd', 'None'):                          ['融资融券交易汇总 - 融资余额(元)', 'selection',
                                                       {'table_name': 'margin', 'column': 'rzye',
                                                        'sel_by':     'exchange_id', 'keys': '%'}],
    ('rzmre|%', 'd', 'None'):                         ['融资融券交易汇总 - 融资买入额(元)', 'selection',
                                                       {'table_name': 'margin', 'column': 'rzmre',
                                                        'sel_by':     'exchange_id', 'keys': '%'}],
    ('rzche|%', 'd', 'None'):                         ['融资融券交易汇总 - 融资偿还额(元)', 'selection',
                                                       {'table_name': 'margin', 'column': 'rzche',
                                                        'sel_by':     'exchange_id', 'keys': '%'}],
    ('rqye|%', 'd', 'None'):                          ['融资融券交易汇总 - 融券余额(元)', 'selection',
                                                       {'table_name': 'margin', 'column': 'rqye',
                                                        'sel_by':     'exchange_id', 'keys': '%'}],
    ('rqmcl|%', 'd', 'None'):                         ['融资融券交易汇总 - 融券卖出量(股,份,手)', 'selection',
                                                       {'table_name': 'margin', 'column': 'rqmcl',
                                                        'sel_by':     'exchange_id', 'keys': '%'}],
    ('rzrqye|%', 'd', 'None'):                        ['融资融券交易汇总 - 融资融券余额(元)', 'selection',
                                                       {'table_name': 'margin', 'column': 'rzrqye',
                                                        'sel_by':     'exchange_id', 'keys': '%'}],
    ('rqyl|%', 'd', 'None'):                          ['融资融券交易汇总 - 融券余量(股,份,手)', 'selection',
                                                       {'table_name': 'margin', 'column': 'rqyl',
                                                        'sel_by':     'exchange_id', 'keys': '%'}],
    ('top_list_close', 'd', 'E'):                     ['龙虎榜交易明细 - 收盘价', 'event_signal',
                                                       {'table_name': 'top_list', 'column': 'close'}],
    ('top_list_pct_change', 'd', 'E'):                ['龙虎榜交易明细 - 涨跌幅', 'event_signal',
                                                       {'table_name': 'top_list', 'column': 'pct_change'}],
    ('top_list_turnover_rate', 'd', 'E'):             ['龙虎榜交易明细 - 换手率', 'event_signal',
                                                       {'table_name': 'top_list', 'column': 'turnover_rate'}],
    ('top_list_amount', 'd', 'E'):                    ['龙虎榜交易明细 - 总成交额', 'event_signal',
                                                       {'table_name': 'top_list', 'column': 'amount'}],
    ('top_list_l_sell', 'd', 'E'):                    ['龙虎榜交易明细 - 龙虎榜卖出额', 'event_signal',
                                                       {'table_name': 'top_list', 'column': 'l_sell'}],
    ('top_list_l_buy', 'd', 'E'):                     ['龙虎榜交易明细 - 龙虎榜买入额', 'event_signal',
                                                       {'table_name': 'top_list', 'column': 'l_buy'}],
    ('top_list_l_amount', 'd', 'E'):                  ['龙虎榜交易明细- 龙虎榜成交额', 'event_signal',
                                                       {'table_name': 'top_list', 'column': 'l_amount'}],
    ('top_list_net_amount', 'd', 'E'):                ['龙虎榜交易明细 - 龙虎榜净买入额', 'event_signal',
                                                       {'table_name': 'top_list', 'column': 'net_amount'}],
    ('top_list_net_rate', 'd', 'E'):                  ['龙虎榜交易明细 - 龙虎榜净买额占比', 'event_signal',
                                                       {'table_name': 'top_list', 'column': 'net_rate'}],
    ('top_list_amount_rate', 'd', 'E'):               ['龙虎榜交易明细 - 龙虎榜成交额占比', 'event_signal',
                                                       {'table_name': 'top_list', 'column': 'amount_rate'}],
    ('top_list_float_values', 'd', 'E'):              ['龙虎榜交易明细 - 当日流通市值', 'event_signal',
                                                       {'table_name': 'top_list', 'column': 'float_values'}],
    ('top_list_reason', 'd', 'E'):                    ['龙虎榜交易明细 - 上榜理由', 'event_signal',
                                                       {'table_name': 'top_list', 'column': 'reason'}],
    ('total_mv', 'd', 'IDX'):                         ['指数技术指标 - 当日总市值（元）', 'direct',
                                                       {'table_name': 'index_indicator', 'column': 'total_mv'}],
    ('float_mv', 'd', 'IDX'):                         ['指数技术指标 - 当日流通市值（元）', 'direct',
                                                       {'table_name': 'index_indicator', 'column': 'float_mv'}],
    ('total_share     float', 'd', 'IDX'):            ['指数技术指标 - 当日总股本（股）', 'direct',
                                                       {'table_name': 'index_indicator', 'column': 'total_share'}],
    ('float_share', 'd', 'IDX'):                      ['指数技术指标 - 当日流通股本（股）', 'direct',
                                                       {'table_name': 'index_indicator', 'column': 'float_share'}],
    ('free_share', 'd', 'IDX'):                       ['指数技术指标 - 当日自由流通股本（股）', 'direct',
                                                       {'table_name': 'index_indicator', 'column': 'free_share'}],
    ('turnover_rate', 'd', 'IDX'):                    ['指数技术指标 - 换手率', 'direct',
                                                       {'table_name': 'index_indicator', 'column': 'turnover_rate'}],
    ('turnover_rate_f', 'd', 'IDX'):                  ['指数技术指标 - 换手率(基于自由流通股本)', 'direct',
                                                       {'table_name': 'index_indicator', 'column': 'turnover_rate_f'}],
    ('pe', 'd', 'IDX'):                               ['指数技术指标 - 市盈率', 'direct',
                                                       {'table_name': 'index_indicator', 'column': 'pe'}],
    ('pe_ttm', 'd', 'IDX'):                           ['指数技术指标 - 市盈率TTM', 'direct',
                                                       {'table_name': 'index_indicator', 'column': 'pe_ttm'}],
    ('pb', 'd', 'IDX'):                               ['指数技术指标 - 市净率', 'direct',
                                                       {'table_name': 'index_indicator', 'column': 'pb'}],
    ('turnover_rate', 'd', 'E'):                      ['股票技术指标 - 换手率（%）', 'direct',
                                                       {'table_name': 'stock_indicator', 'column': 'turnover_rate'}],
    ('turnover_rate_f', 'd', 'E'):                    ['股票技术指标 - 换手率（自由流通股）', 'direct',
                                                       {'table_name': 'stock_indicator', 'column': 'turnover_rate_f'}],
    ('volume_ratio', 'd', 'E'):                       ['股票技术指标 - 量比', 'direct',
                                                       {'table_name': 'stock_indicator', 'column': 'volume_ratio'}],
    ('pe', 'd', 'E'):                                 ['股票技术指标 - 市盈率（总市值/净利润， 亏损的PE为空）', 'direct',
                                                       {'table_name': 'stock_indicator', 'column': 'pe'}],
    ('pe_ttm', 'd', 'E'):                             ['股票技术指标 - 市盈率（TTM，亏损的PE为空）', 'direct',
                                                       {'table_name': 'stock_indicator', 'column': 'pe_ttm'}],
    ('pb', 'd', 'E'):                                 ['股票技术指标 - 市净率（总市值/净资产）', 'direct',
                                                       {'table_name': 'stock_indicator', 'column': 'pb'}],
    ('ps', 'd', 'E'):                                 ['股票技术指标 - 市销率', 'direct',
                                                       {'table_name': 'stock_indicator', 'column': 'ps'}],
    ('ps_ttm', 'd', 'E'):                             ['股票技术指标 - 市销率（TTM）', 'direct',
                                                       {'table_name': 'stock_indicator', 'column': 'ps_ttm'}],
    ('dv_ratio', 'd', 'E'):                           ['股票技术指标 - 股息率 （%）', 'direct',
                                                       {'table_name': 'stock_indicator', 'column': 'dv_ratio'}],
    ('dv_ttm', 'd', 'E'):                             ['股票技术指标 - 股息率（TTM）（%）', 'direct',
                                                       {'table_name': 'stock_indicator', 'column': 'dv_ttm'}],
    ('total_share', 'd', 'E'):                        ['股票技术指标 - 总股本 （万股）', 'direct',
                                                       {'table_name': 'stock_indicator', 'column': 'total_share'}],
    ('float_share', 'd', 'E'):                        ['股票技术指标 - 流通股本 （万股）', 'direct',
                                                       {'table_name': 'stock_indicator', 'column': 'float_share'}],
    ('free_share', 'd', 'E'):                         ['股票技术指标 - 自由流通股本 （万）', 'direct',
                                                       {'table_name': 'stock_indicator', 'column': 'free_share'}],
    ('total_mv', 'd', 'E'):                           ['股票技术指标 - 总市值 （万元）', 'direct',
                                                       {'table_name': 'stock_indicator', 'column': 'total_mv'}],
    ('circ_mv', 'd', 'E'):                            ['股票技术指标 - 流通市值（万元）', 'direct',
                                                       {'table_name': 'stock_indicator', 'column': 'circ_mv'}],
    ('vol_ratio', 'd', 'E'):                          ['股票技术指标 - 量比', 'direct',
                                                       {'table_name': 'stock_indicator2', 'column': 'vol_ratio'}],
    ('turn_over', 'd', 'E'):                          ['股票技术指标 - 换手率', 'direct',
                                                       {'table_name': 'stock_indicator2', 'column': 'turn_over'}],
    ('swing', 'd', 'E'):                              ['股票技术指标 - 振幅', 'direct',
                                                       {'table_name': 'stock_indicator2', 'column': 'swing'}],
    ('selling', 'd', 'E'):                            ['股票技术指标 - 内盘（主动卖，手）', 'direct',
                                                       {'table_name': 'stock_indicator2', 'column': 'selling'}],
    ('buying', 'd', 'E'):                             ['股票技术指标 - 外盘（主动买， 手）', 'direct',
                                                       {'table_name': 'stock_indicator2', 'column': 'buying'}],
    ('total_share_b', 'd', 'E'):                      ['股票技术指标 - 总股本(亿)', 'direct',
                                                       {'table_name': 'stock_indicator2', 'column': 'total_share'}],
    ('float_share_b', 'd', 'E'):                      ['股票技术指标 - 流通股本(亿)', 'direct',
                                                       {'table_name': 'stock_indicator2', 'column': 'float_share'}],
    ('pe_2', 'd', 'E'):                               ['股票技术指标 - 动态市盈率', 'direct',
                                                       {'table_name': 'stock_indicator2', 'column': 'pe'}],
    ('float_mv_2', 'd', 'E'):                         ['股票技术指标 - 流通市值', 'direct',
                                                       {'table_name': 'stock_indicator2', 'column': 'float_mv'}],
    ('total_mv_2', 'd', 'E'):                         ['股票技术指标 - 总市值', 'direct',
                                                       {'table_name': 'stock_indicator2', 'column': 'total_mv'}],
    ('avg_price', 'd', 'E'):                          ['股票技术指标 - 平均价', 'direct',
                                                       {'table_name': 'stock_indicator2', 'column': 'avg_price'}],
    ('strength', 'd', 'E'):                           ['股票技术指标 - 强弱度(%)', 'direct',
                                                       {'table_name': 'stock_indicator2', 'column': 'strength'}],
    ('activity', 'd', 'E'):                           ['股票技术指标 - 活跃度(%)', 'direct',
                                                       {'table_name': 'stock_indicator2', 'column': 'activity'}],
    ('avg_turnover', 'd', 'E'):                       ['股票技术指标 - 笔换手', 'direct',
                                                       {'table_name': 'stock_indicator2', 'column': 'avg_turnover'}],
    ('attack', 'd', 'E'):                             ['股票技术指标 - 攻击波(%)', 'direct',
                                                       {'table_name': 'stock_indicator2', 'column': 'attack'}],
    ('interval_3', 'd', 'E'):                         ['股票技术指标 - 近3月涨幅', 'direct',
                                                       {'table_name': 'stock_indicator2', 'column': 'interval_3'}],
    ('interval_6', 'd', 'E'):                         ['股票技术指标 - 近6月涨幅', 'direct',
                                                       {'table_name': 'stock_indicator2', 'column': 'interval_6'}],
    ('cur_name', 'd', 'E'):                           ['股票 - 当前最新证券名称', 'event_status',
                                                       {'table_name': 'stock_names', 'column': 'name'}],
    ('change_reason', 'd', 'E'):                      ['股票更名 - 变更原因', 'event_signal',
                                                       {'table_name': 'stock_names', 'column': 'change_reason'}],
    ('suspend_timing', 'd', 'E'):                     ['日内停牌时间段', 'event_signal',
                                                       {'table_name': 'stock_suspend', 'column': 'suspend_timing'}],
    ('is_suspended', 'd', 'E'):                       ['停复牌类型：S-停牌，R-复牌', 'event_signal',
                                                       {'table_name': 'stock_suspend', 'column': 'suspend_type'}],
    ('is_HS_top10', 'd', 'E'):                        ['沪深港通十大成交股上榜', 'event_signal',
                                                       {'table_name': 'hs_top10_stock', 'column': 'name'}],
    ('top10_close', 'd', 'E'):                        ['沪深港通十大成交股上榜 - 收盘价', 'event_signal',
                                                       {'table_name': 'hs_top10_stock', 'column': 'close'}],
    ('top10_change', 'd', 'E'):                       ['沪深港通十大成交股上榜 - 涨跌额', 'event_signal',
                                                       {'table_name': 'hs_top10_stock', 'column': 'change'}],
    ('top10_rank', 'd', 'E'):                         ['沪深港通十大成交股上榜 - 资金排名', 'event_signal',
                                                       {'table_name': 'hs_top10_stock', 'column': 'rank'}],
    ('top10_amount', 'd', 'E'):                       ['沪深港通十大成交股上榜 - 成交金额（元）', 'event_signal',
                                                       {'table_name': 'hs_top10_stock', 'column': 'amount'}],
    ('top10_net_amount', 'd', 'E'):                   ['沪深港通十大成交股上榜 - 净成交金额（元）', 'event_signal',
                                                       {'table_name': 'hs_top10_stock', 'column': 'net_amount'}],
    ('top10_buy', 'd', 'E'):                          ['沪深港通十大成交股上榜 - 买入金额（元）', 'event_signal',
                                                       {'table_name': 'hs_top10_stock', 'column': 'buy'}],
    ('top10_sell', 'd', 'E'):                         ['沪深港通十大成交股上榜 - 卖出金额（元）', 'event_signal',
                                                       {'table_name': 'hs_top10_stock', 'column': 'sell'}],
    ('fd_share', 'd', 'FD'):                          ['基金份额（万）', 'direct',
                                                       {'table_name': 'fund_share', 'column': 'fd_share'}],
    ('managers_name', 'd', 'FD'):                     ['基金经理姓名', 'event_multi_stat',
                                                       {'table_name': 'fund_manager', 'column': 'name',
                                                        'id_index':   'name', 'start_col': 'begin_date',
                                                        'end_col':    'end_date'}],
    ('managers_gender', 'd', 'FD'):                   ['基金经理 - 性别', 'event_multi_stat',
                                                       {'table_name': 'fund_manager', 'column': 'gender',
                                                        'id_index':   'name', 'start_col': 'begin_date',
                                                        'end_col':    'end_date'}],
    ('managers_birth_year', 'd', 'FD'):               ['基金经理 - 出生年份', 'event_multi_stat',
                                                       {'table_name': 'fund_manager', 'column': 'birth_year',
                                                        'id_index':   'name', 'start_col': 'begin_date',
                                                        'end_col':    'end_date'}],
    ('managers_edu', 'd', 'FD'):                      ['基金经理 - 学历', 'event_multi_stat',
                                                       {'table_name': 'fund_manager', 'column': 'edu',
                                                        'id_index':   'name', 'start_col': 'begin_date',
                                                        'end_col':    'end_date'}],
    ('nationality', 'd', 'FD'):                       ['基金经理 - 国籍', 'event_multi_stat',
                                                       {'table_name': 'fund_manager', 'column': 'nationality',
                                                        'id_index':   'name', 'start_col': 'begin_date',
                                                        'end_col':    'end_date'}],
    ('managers_resume', 'd', 'FD'):                   ['基金经理 - 简历', 'event_multi_stat',
                                                       {'table_name': 'fund_manager', 'column': 'resume',
                                                        'id_index':   'name', 'start_col': 'begin_date',
                                                        'end_col':    'end_date'}],
    ('stk_div_planned', 'd', 'E'):                    ['预案-每股送转', 'selected_events',
                                                       {'table_name': 'dividend', 'column': 'stk_div',
                                                        'sel_by':     'div_proc', 'key': '预案'}],
    ('stk_bo_rate_planned', 'd', 'E'):                ['预案-每股送股比例', 'selected_events',
                                                       {'table_name': 'dividend', 'column': 'stk_bo_rate',
                                                        'sel_by':     'div_proc', 'key': '预案'}],
    ('stk_co_rate_planned', 'd', 'E'):                ['预案-每股转增比例', 'selected_events',
                                                       {'table_name': 'dividend', 'column': 'stk_co_rate',
                                                        'sel_by':     'div_proc', 'key': '预案'}],
    ('cash_div_planned', 'd', 'E'):                   ['预案-每股分红（税后）', 'selected_events',
                                                       {'table_name': 'dividend', 'column': 'cash_div',
                                                        'sel_by':     'div_proc', 'key': '预案'}],
    ('cash_div_tax_planned', 'd', 'E'):               ['预案-每股分红（税前）', 'selected_events',
                                                       {'table_name': 'dividend', 'column': 'cash_div_tax',
                                                        'sel_by':     'div_proc', 'key': '预案'}],
    ('stk_div_approved', 'd', 'E'):                   ['股东大会批准-每股送转', 'selected_events',
                                                       {'table_name': 'dividend', 'column': 'stk_div',
                                                        'sel_by':     'div_proc', 'key': '股东大会通过'}],
    ('stk_bo_rate_approved', 'd', 'E'):               ['股东大会批准-每股送股比例', 'selected_events',
                                                       {'table_name': 'dividend', 'column': 'stk_bo_rate',
                                                        'sel_by':     'div_proc', 'key': '股东大会通过'}],
    ('stk_co_rate_approved', 'd', 'E'):               ['股东大会批准-每股转增比例', 'selected_events',
                                                       {'table_name': 'dividend', 'column': 'stk_co_rate',
                                                        'sel_by':     'div_proc', 'key': '股东大会通过'}],
    ('cash_div_approved', 'd', 'E'):                  ['股东大会批准-每股分红（税后）', 'selected_events',
                                                       {'table_name': 'dividend', 'column': 'cash_div',
                                                        'sel_by':     'div_proc', 'key': '股东大会通过'}],
    ('cash_div_tax_approved', 'd', 'E'):              ['股东大会批准-每股分红（税前）', 'selected_events',
                                                       {'table_name': 'dividend', 'column': 'cash_div_tax',
                                                        'sel_by':     'div_proc', 'key': '股东大会通过'}],
    ('stk_div', 'd', 'E'):                            ['实施-每股送转', 'selected_events',
                                                       {'table_name': 'dividend', 'column': 'stk_div',
                                                        'sel_by':     'div_proc', 'key': '实施'}],
    ('stk_bo_rate', 'd', 'E'):                        ['实施-每股送股比例', 'selected_events',
                                                       {'table_name': 'dividend', 'column': 'stk_bo_rate',
                                                        'sel_by':     'div_proc', 'key': '实施'}],
    ('stk_co_rate', 'd', 'E'):                        ['实施-每股转增比例', 'selected_events',
                                                       {'table_name': 'dividend', 'column': 'stk_co_rate',
                                                        'sel_by':     'div_proc', 'key': '实施'}],
    ('cash_div', 'd', 'E'):                           ['实施-每股分红（税后）', 'selected_events',
                                                       {'table_name': 'dividend', 'column': 'cash_div',
                                                        'sel_by':     'div_proc', 'key': '实施'}],
    ('cash_div_tax', 'd', 'E'):                       ['实施-每股分红（税前）', 'selected_events',
                                                       {'table_name': 'dividend', 'column': 'cash_div_tax',
                                                        'sel_by':     'div_proc', 'key': '实施'}],
    ('record_date', 'd', 'E'):                        ['实施-股权登记日', 'selected_events',
                                                       {'table_name': 'dividend', 'column': 'record_date',
                                                        'sel_by':     'div_proc', 'key': '实施'}],
    ('ex_date', 'd', 'E'):                            ['实施-除权除息日', 'selected_events',
                                                       {'table_name': 'dividend', 'column': 'ex_date',
                                                        'sel_by':     'div_proc', 'key': '实施'}],
    ('pay_date', 'd', 'E'):                           ['实施-派息日', 'selected_events',
                                                       {'table_name': 'dividend', 'column': 'pay_date',
                                                        'sel_by':     'div_proc', 'key': '实施'}],
    ('imp_ann_date', 'd', 'E'):                       ['实施-实施公告日', 'selected_events',
                                                       {'table_name': 'dividend', 'column': 'imp_ann_date',
                                                        'sel_by':     'div_proc', 'key': '实施'}],
    ('base_date', 'd', 'E'):                          ['实施-基准日', 'selected_events',
                                                       {'table_name': 'dividend', 'column': 'base_date',
                                                        'sel_by':     'div_proc', 'key': '实施'}],
    ('base_share', 'd', 'E'):                         ['实施-基准股本（万）', 'selected_events',
                                                       {'table_name': 'dividend', 'column': 'base_share',
                                                        'sel_by':     'div_proc', 'key': '实施'}],
    ('exalter', 'd', 'E'):                            ['龙虎榜机构明细 - 营业部名称', 'event_signal',
                                                       {'table_name': 'top_inst', 'column': 'exalter'}],
    ('side', 'd', 'E'):                               [
        '龙虎榜机构明细 - 买卖类型0：买入金额最大的前5名， 1：卖出金额最大的前5名', 'event_signal',
        {'table_name': 'top_inst', 'column': 'side'}],
    ('buy', 'd', 'E'):                                ['龙虎榜机构明细 - 买入额（元）', 'event_signal',
                                                       {'table_name': 'top_inst', 'column': 'buy'}],
    ('buy_rate', 'd', 'E'):                           ['龙虎榜机构明细 - 买入占总成交比例', 'event_signal',
                                                       {'table_name': 'top_inst', 'column': 'buy_rate'}],
    ('sell', 'd', 'E'):                               ['龙虎榜机构明细 - 卖出额（元）', 'event_signal',
                                                       {'table_name': 'top_inst', 'column': 'sell'}],
    ('sell_rate', 'd', 'E'):                          ['龙虎榜机构明细 - 卖出占总成交比例', 'event_signal',
                                                       {'table_name': 'top_inst', 'column': 'sell_rate'}],
    ('net_buy', 'd', 'E'):                            ['龙虎榜机构明细 - 净成交额（元）', 'event_signal',
                                                       {'table_name': 'top_inst', 'column': 'net_buy'}],
    ('reason', 'd', 'E'):                             ['龙虎榜机构明细 - 上榜理由', 'event_signal',
                                                       {'table_name': 'top_inst', 'column': 'reason'}],
    ('shibor|%', 'd', 'None'):                        ['上海银行间行业拆放利率(SHIBOR) - %', 'reference',
                                                       {'table_name': 'shibor', 'column': '%'}],
    ('libor_usd|%', 'd', 'None'):                     ['伦敦银行间行业拆放利率(LIBOR) USD - %', 'selection',
                                                       {'table_name': 'libor', 'column': '%', 'sel_by': 'curr_type',
                                                        'keys':       ['USD']}],
    ('libor_eur|%', 'd', 'None'):                     ['伦敦银行间行业拆放利率(LIBOR) EUR - %', 'selection',
                                                       {'table_name': 'libor', 'column': '%', 'sel_by': 'curr_type',
                                                        'keys':       ['EUR']}],
    ('libor_gbp|%', 'd', 'None'):                     ['伦敦银行间行业拆放利率(LIBOR) GBP - %', 'selection',
                                                       {'table_name': 'libor', 'column': '%', 'sel_by': 'curr_type',
                                                        'keys':       ['GBP']}],
    ('hibor|%', 'd', 'None'):                         ['香港银行间行业拆放利率(HIBOR) - %', 'reference',
                                                       {'table_name': 'hibor', 'column': '%'}],
    ('wz_comp', 'd', 'None'):                         ['温州民间融资综合利率指数', 'reference',
                                                       {'table_name': 'wz_index', 'column': 'comp_rate'}],
    ('wz_center', 'd', 'None'):                       ['民间借贷服务中心利率', 'reference',
                                                       {'table_name': 'wz_index', 'column': 'center_rate'}],
    ('wz_micro', 'd', 'None'):                        ['小额贷款公司放款利率', 'reference',
                                                       {'table_name': 'wz_index', 'column': 'micro_rate'}],
    ('wz_cm', 'd', 'None'):                           ['民间资本管理公司融资价格', 'reference',
                                                       {'table_name': 'wz_index', 'column': 'cm_rate'}],
    ('wz_sdb', 'd', 'None'):                          ['社会直接借贷利率', 'reference',
                                                       {'table_name': 'wz_index', 'column': 'sdb_rate'}],
    ('wz_om', 'd', 'None'):                           ['其他市场主体利率', 'reference',
                                                       {'table_name': 'wz_index', 'column': 'om_rate'}],
    ('wz_aa', 'd', 'None'):                           ['农村互助会互助金费率', 'reference',
                                                       {'table_name': 'wz_index', 'column': 'aa_rate'}],
    ('wz_m1', 'd', 'None'):                           ['温州地区民间借贷分期限利率（一月期）', 'reference',
                                                       {'table_name': 'wz_index', 'column': 'm1_rate'}],
    ('wz_m3', 'd', 'None'):                           ['温州地区民间借贷分期限利率（三月期）', 'reference',
                                                       {'table_name': 'wz_index', 'column': 'm3_rate'}],
    ('wz_m6', 'd', 'None'):                           ['温州地区民间借贷分期限利率（六月期）', 'reference',
                                                       {'table_name': 'wz_index', 'column': 'm6_rate'}],
    ('wz_m12', 'd', 'None'):                          ['温州地区民间借贷分期限利率（一年期）', 'reference',
                                                       {'table_name': 'wz_index', 'column': 'm12_rate'}],
    ('wz_long', 'd', 'None'):                         ['温州地区民间借贷分期限利率（长期）', 'reference',
                                                       {'table_name': 'wz_index', 'column': 'long_rate'}],
    ('gz_d10', 'd', 'None'):                          ['小额贷市场平均利率（十天）', 'reference',
                                                       {'table_name': 'gz_index', 'column': 'd10_rate'}],
    ('gz_m1', 'd', 'None'):                           ['小额贷市场平均利率（一月期）', 'reference',
                                                       {'table_name': 'gz_index', 'column': 'm1_rate'}],
    ('gz_m3', 'd', 'None'):                           ['小额贷市场平均利率（三月期）', 'reference',
                                                       {'table_name': 'gz_index', 'column': 'm3_rate'}],
    ('gz_m6', 'd', 'None'):                           ['小额贷市场平均利率（六月期）', 'reference',
                                                       {'table_name': 'gz_index', 'column': 'm6_rate'}],
    ('gz_m12', 'd', 'None'):                          ['小额贷市场平均利率（一年期）', 'reference',
                                                       {'table_name': 'gz_index', 'column': 'm12_rate'}],
    ('gz_long', 'd', 'None'):                         ['小额贷市场平均利率（长期）', 'reference',
                                                       {'table_name': 'gz_index', 'column': 'long_rate'}],
    ('cn_gdp', 'q', 'None'):                          ['GDP累计值（亿元）', 'reference',
                                                       {'table_name': 'cn_gdp', 'column': 'gdp'}],
    ('cn_gdp_yoy', 'q', 'None'):                      ['当季同比增速（%）', 'reference',
                                                       {'table_name': 'cn_gdp', 'column': 'gdp_yoy'}],
    ('cn_gdp_pi', 'q', 'None'):                       ['第一产业累计值（亿元）', 'reference',
                                                       {'table_name': 'cn_gdp', 'column': 'pi'}],
    ('cn_gdp_pi_yoy', 'q', 'None'):                   ['第一产业同比增速（%）', 'reference',
                                                       {'table_name': 'cn_gdp', 'column': 'pi_yoy'}],
    ('cn_gdp_si', 'q', 'None'):                       ['第二产业累计值（亿元）', 'reference',
                                                       {'table_name': 'cn_gdp', 'column': 'si'}],
    ('cn_gdp_si_yoy', 'q', 'None'):                   ['第二产业同比增速（%）', 'reference',
                                                       {'table_name': 'cn_gdp', 'column': 'si_yoy'}],
    ('cn_gdp_ti', 'q', 'None'):                       ['第三产业累计值（亿元）', 'reference',
                                                       {'table_name': 'cn_gdp', 'column': 'ti'}],
    ('cn_gdp_ti_yoy', 'q', 'None'):                   ['第三产业同比增速（%）', 'reference',
                                                       {'table_name': 'cn_gdp', 'column': 'ti_yoy'}],
    ('nt_val', 'm', 'None'):                          ['全国当月值', 'reference',
                                                       {'table_name': 'cn_cpi', 'column': 'nt_val'}],
    ('nt_yoy', 'm', 'None'):                          ['全国同比（%）', 'reference',
                                                       {'table_name': 'cn_cpi', 'column': 'nt_yoy'}],
    ('nt_mom', 'm', 'None'):                          ['全国环比（%）', 'reference',
                                                       {'table_name': 'cn_cpi', 'column': 'nt_mom'}],
    ('nt_accu', 'm', 'None'):                         ['全国累计值', 'reference',
                                                       {'table_name': 'cn_cpi', 'column': 'nt_accu'}],
    ('town_val', 'm', 'None'):                        ['城市当月值', 'reference',
                                                       {'table_name': 'cn_cpi', 'column': 'town_val'}],
    ('town_yoy', 'm', 'None'):                        ['城市同比（%）', 'reference',
                                                       {'table_name': 'cn_cpi', 'column': 'town_yoy'}],
    ('town_mom', 'm', 'None'):                        ['城市环比（%）', 'reference',
                                                       {'table_name': 'cn_cpi', 'column': 'town_mom'}],
    ('town_accu', 'm', 'None'):                       ['城市累计值', 'reference',
                                                       {'table_name': 'cn_cpi', 'column': 'town_accu'}],
    ('cnt_val', 'm', 'None'):                         ['农村当月值', 'reference',
                                                       {'table_name': 'cn_cpi', 'column': 'cnt_val'}],
    ('cnt_yoy', 'm', 'None'):                         ['农村同比（%）', 'reference',
                                                       {'table_name': 'cn_cpi', 'column': 'cnt_yoy'}],
    ('cnt_mom', 'm', 'None'):                         ['农村环比（%）', 'reference',
                                                       {'table_name': 'cn_cpi', 'column': 'cnt_mom'}],
    ('cnt_accu', 'm', 'None'):                        ['农村累计值', 'reference',
                                                       {'table_name': 'cn_cpi', 'column': 'cnt_accu'}],
    ('cnt_accu', 'm', 'None'):                        ['农村累计值', 'reference',
                                                       {'table_name': 'cn_cpi', 'column': 'cnt_accu'}],
    ('ppi_yoy', 'm', 'None'):                         ['PPI：全部工业品：当月同比', 'reference',
                                                       {'table_name': 'cn_ppi', 'column': 'ppi_yoy'}],
    ('ppi_mp_yoy', 'm', 'None'):                      ['PPI：生产资料：当月同比', 'reference',
                                                       {'table_name': 'cn_ppi', 'column': 'ppi_mp_yoy'}],
    ('ppi_mp_qm_yoy', 'm', 'None'):                   ['PPI：生产资料：采掘业：当月同比', 'reference',
                                                       {'table_name': 'cn_ppi', 'column': 'ppi_mp_qm_yoy'}],
    ('ppi_mp_rm_yoy', 'm', 'None'):                   ['PPI：生产资料：原料业：当月同比', 'reference',
                                                       {'table_name': 'cn_ppi', 'column': 'ppi_mp_rm_yoy'}],
    ('ppi_mp_p_yoy', 'm', 'None'):                    ['PPI：生产资料：加工业：当月同比', 'reference',
                                                       {'table_name': 'cn_ppi', 'column': 'ppi_mp_p_yoy'}],
    ('ppi_cg_yoy', 'm', 'None'):                      ['PPI：生活资料：当月同比', 'reference',
                                                       {'table_name': 'cn_ppi', 'column': 'ppi_cg_yoy'}],
    ('ppi_cg_f_yoy', 'm', 'None'):                    ['PPI：生活资料：食品类：当月同比', 'reference',
                                                       {'table_name': 'cn_ppi', 'column': 'ppi_cg_f_yoy'}],
    ('ppi_cg_c_yoy', 'm', 'None'):                    ['PPI：生活资料：衣着类：当月同比', 'reference',
                                                       {'table_name': 'cn_ppi', 'column': 'ppi_cg_c_yoy'}],
    ('ppi_cg_adu_yoy', 'm', 'None'):                  ['PPI：生活资料：一般日用品类：当月同比', 'reference',
                                                       {'table_name': 'cn_ppi', 'column': 'ppi_cg_adu_yoy'}],
    ('ppi_cg_dcg_yoy', 'm', 'None'):                  ['PPI：生活资料：耐用消费品类：当月同比', 'reference',
                                                       {'table_name': 'cn_ppi', 'column': 'ppi_cg_dcg_yoy'}],
    ('ppi_mom', 'm', 'None'):                         ['PPI：全部工业品：环比', 'reference',
                                                       {'table_name': 'cn_ppi', 'column': 'ppi_mom'}],
    ('ppi_mp_mom', 'm', 'None'):                      ['PPI：生产资料：环比', 'reference',
                                                       {'table_name': 'cn_ppi', 'column': 'ppi_mp_mom'}],
    ('ppi_mp_qm_mom', 'm', 'None'):                   ['PPI：生产资料：采掘业：环比', 'reference',
                                                       {'table_name': 'cn_ppi', 'column': 'ppi_mp_qm_mom'}],
    ('ppi_mp_rm_mom', 'm', 'None'):                   ['PPI：生产资料：原料业：环比', 'reference',
                                                       {'table_name': 'cn_ppi', 'column': 'ppi_mp_rm_mom'}],
    ('ppi_mp_p_mom', 'm', 'None'):                    ['PPI：生产资料：加工业：环比', 'reference',
                                                       {'table_name': 'cn_ppi', 'column': 'ppi_mp_p_mom'}],
    ('ppi_cg_mom', 'm', 'None'):                      ['PPI：生活资料：环比', 'reference',
                                                       {'table_name': 'cn_ppi', 'column': 'ppi_cg_mom'}],
    ('ppi_cg_f_mom', 'm', 'None'):                    ['PPI：生活资料：食品类：环比', 'reference',
                                                       {'table_name': 'cn_ppi', 'column': 'ppi_cg_f_mom'}],
    ('ppi_cg_c_mom', 'm', 'None'):                    ['PPI：生活资料：衣着类：环比', 'reference',
                                                       {'table_name': 'cn_ppi', 'column': 'ppi_cg_c_mom'}],
    ('ppi_cg_adu_mom', 'm', 'None'):                  ['PPI：生活资料：一般日用品类：环比', 'reference',
                                                       {'table_name': 'cn_ppi', 'column': 'ppi_cg_adu_mom'}],
    ('ppi_cg_dcg_mom', 'm', 'None'):                  ['PPI：生活资料：耐用消费品类：环比', 'reference',
                                                       {'table_name': 'cn_ppi', 'column': 'ppi_cg_dcg_mom'}],
    ('ppi_accu', 'm', 'None'):                        ['PPI：全部工业品：累计同比', 'reference',
                                                       {'table_name': 'cn_ppi', 'column': 'ppi_accu'}],
    ('ppi_mp_accu', 'm', 'None'):                     ['PPI：生产资料：累计同比', 'reference',
                                                       {'table_name': 'cn_ppi', 'column': 'ppi_mp_accu'}],
    ('ppi_mp_qm_accu', 'm', 'None'):                  ['PPI：生产资料：采掘业：累计同比', 'reference',
                                                       {'table_name': 'cn_ppi', 'column': 'ppi_mp_qm_accu'}],
    ('ppi_mp_rm_accu', 'm', 'None'):                  ['PPI：生产资料：原料业：累计同比', 'reference',
                                                       {'table_name': 'cn_ppi', 'column': 'ppi_mp_rm_accu'}],
    ('ppi_mp_p_accu', 'm', 'None'):                   ['PPI：生产资料：加工业：累计同比', 'reference',
                                                       {'table_name': 'cn_ppi', 'column': 'ppi_mp_p_accu'}],
    ('ppi_cg_accu', 'm', 'None'):                     ['PPI：生活资料：累计同比', 'reference',
                                                       {'table_name': 'cn_ppi', 'column': 'ppi_cg_accu'}],
    ('ppi_cg_f_accu', 'm', 'None'):                   ['PPI：生活资料：食品类：累计同比', 'reference',
                                                       {'table_name': 'cn_ppi', 'column': 'ppi_cg_f_accu'}],
    ('ppi_cg_c_accu', 'm', 'None'):                   ['PPI：生活资料：衣着类：累计同比', 'reference',
                                                       {'table_name': 'cn_ppi', 'column': 'ppi_cg_c_accu'}],
    ('ppi_cg_adu_accu', 'm', 'None'):                 ['PPI：生活资料：一般日用品类：累计同比', 'reference',
                                                       {'table_name': 'cn_ppi', 'column': 'ppi_cg_adu_accu'}],
    ('ppi_cg_dcg_accu', 'm', 'None'):                 ['PPI：生活资料：耐用消费品类：累计同比', 'reference',
                                                       {'table_name': 'cn_ppi', 'column': 'ppi_cg_dcg_accu'}],
    ('cn_m0', 'm', 'None'):                           ['M0（亿元）', 'reference',
                                                       {'table_name': 'cn_money', 'column': 'm0'}],
    ('cn_m0_yoy', 'm', 'None'):                       ['M0同比（%）', 'reference',
                                                       {'table_name': 'cn_money', 'column': 'm0_yoy'}],
    ('cn_m0_mom', 'm', 'None'):                       ['M0环比（%）', 'reference',
                                                       {'table_name': 'cn_money', 'column': 'm0_mom'}],
    ('cn_m1', 'm', 'None'):                           ['M1（亿元）', 'reference',
                                                       {'table_name': 'cn_money', 'column': 'm1'}],
    ('cn_m1_yoy', 'm', 'None'):                       ['M1同比（%）', 'reference',
                                                       {'table_name': 'cn_money', 'column': 'm1_yoy'}],
    ('cn_m1_mom', 'm', 'None'):                       ['M1环比（%）', 'reference',
                                                       {'table_name': 'cn_money', 'column': 'm1_mom'}],
    ('cn_m2', 'm', 'None'):                           ['M2（亿元）', 'reference',
                                                       {'table_name': 'cn_money', 'column': 'm2'}],
    ('cn_m2_yoy', 'm', 'None'):                       ['M2同比（%）', 'reference',
                                                       {'table_name': 'cn_money', 'column': 'm2_yoy'}],
    ('cn_m2_mom', 'm', 'None'):                       ['M2环比（%）', 'reference',
                                                       {'table_name': 'cn_money', 'column': 'm2_mom'}],
    ('inc_month', 'm', 'None'):                       ['社融增量当月值（亿元）', 'reference',
                                                       {'table_name': 'cn_sf', 'column': 'inc_month'}],
    ('inc_cumval', 'm', 'None'):                      ['社融增量累计值（亿元）', 'reference',
                                                       {'table_name': 'cn_sf', 'column': 'inc_cumval'}],
    ('stk_endval', 'm', 'None'):                      ['社融存量期末值（万亿元）', 'reference',
                                                       {'table_name': 'cn_sf', 'column': 'stk_endval'}],
    ('pmi010000', 'm', 'None'):                       ['制造业PMI', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi010000'}],
    ('pmi010100', 'm', 'None'):                       ['制造业PMI:企业规模/大型企业', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi010100'}],
    ('pmi010200', 'm', 'None'):                       ['制造业PMI:企业规模/中型企业', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi010200'}],
    ('pmi010300', 'm', 'None'):                       ['制造业PMI:企业规模/小型企业', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi010300'}],
    ('pmi010400', 'm', 'None'):                       ['制造业PMI:构成指数/生产指数', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi010400'}],
    ('pmi010401', 'm', 'None'):                       ['制造业PMI:构成指数/生产指数:企业规模/大型企业', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi010401'}],
    ('pmi010402', 'm', 'None'):                       ['制造业PMI:构成指数/生产指数:企业规模/中型企业', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi010402'}],
    ('pmi010403', 'm', 'None'):                       ['制造业PMI:构成指数/生产指数:企业规模/小型企业', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi010403'}],
    ('pmi010500', 'm', 'None'):                       ['制造业PMI:构成指数/新订单指数', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi010500'}],
    ('pmi010501', 'm', 'None'):                       ['制造业PMI:构成指数/新订单指数:企业规模/大型企业', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi010501'}],
    ('pmi010502', 'm', 'None'):                       ['制造业PMI:构成指数/新订单指数:企业规模/中型企业', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi010502'}],
    ('pmi010503', 'm', 'None'):                       ['制造业PMI:构成指数/新订单指数:企业规模/小型企业', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi010503'}],
    ('pmi010600', 'm', 'None'):                       ['制造业PMI:构成指数/供应商配送时间指数', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi010600'}],
    ('pmi010601', 'm', 'None'):                       ['制造业PMI:构成指数/供应商配送时间指数:企业规模/大型企业',
                                                       'reference', {'table_name': 'cn_pmi', 'column': 'pmi010601'}],
    ('pmi010602', 'm', 'None'):                       ['制造业PMI:构成指数/供应商配送时间指数:企业规模/中型企业',
                                                       'reference', {'table_name': 'cn_pmi', 'column': 'pmi010602'}],
    ('pmi010603', 'm', 'None'):                       ['制造业PMI:构成指数/供应商配送时间指数:企业规模/小型企业',
                                                       'reference', {'table_name': 'cn_pmi', 'column': 'pmi010603'}],
    ('pmi010700', 'm', 'None'):                       ['制造业PMI:构成指数/原材料库存指数', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi010700'}],
    ('pmi010701', 'm', 'None'):                       ['制造业PMI:构成指数/原材料库存指数:企业规模/大型企业',
                                                       'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi010701'}],
    ('pmi010702', 'm', 'None'):                       ['制造业PMI:构成指数/原材料库存指数:企业规模/中型企业',
                                                       'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi010702'}],
    ('pmi010703', 'm', 'None'):                       ['制造业PMI:构成指数/原材料库存指数:企业规模/小型企业',
                                                       'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi010703'}],
    ('pmi010800', 'm', 'None'):                       ['制造业PMI:构成指数/从业人员指数', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi010800'}],
    ('pmi010801', 'm', 'None'):                       ['制造业PMI:构成指数/从业人员指数:企业规模/大型企业', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi010801'}],
    ('pmi010802', 'm', 'None'):                       ['制造业PMI:构成指数/从业人员指数:企业规模/中型企业', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi010802'}],
    ('pmi010803', 'm', 'None'):                       ['制造业PMI:构成指数/从业人员指数:企业规模/小型企业', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi010803'}],
    ('pmi010900', 'm', 'None'):                       ['制造业PMI:其他/新出口订单', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi010900'}],
    ('pmi011000', 'm', 'None'):                       ['制造业PMI:其他/进口', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi011000'}],
    ('pmi011100', 'm', 'None'):                       ['制造业PMI:其他/采购量', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi011100'}],
    ('pmi011200', 'm', 'None'):                       ['制造业PMI:其他/主要原材料购进价格', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi011200'}],
    ('pmi011300', 'm', 'None'):                       ['制造业PMI:其他/出厂价格', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi011300'}],
    ('pmi011400', 'm', 'None'):                       ['制造业PMI:其他/产成品库存', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi011400'}],
    ('pmi011500', 'm', 'None'):                       ['制造业PMI:其他/在手订单', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi011500'}],
    ('pmi011600', 'm', 'None'):                       ['制造业PMI:其他/生产经营活动预期', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi011600'}],
    ('pmi011700', 'm', 'None'):                       ['制造业PMI:分行业/装备制造业', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi011700'}],
    ('pmi011800', 'm', 'None'):                       ['制造业PMI:分行业/高技术制造业', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi011800'}],
    ('pmi011900', 'm', 'None'):                       ['制造业PMI:分行业/基础原材料制造业', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi011900'}],
    ('pmi012000', 'm', 'None'):                       ['制造业PMI:分行业/消费品制造业', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi012000'}],
    ('pmi020100', 'm', 'None'):                       ['非制造业PMI:商务活动', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi020100'}],
    ('pmi020101', 'm', 'None'):                       ['非制造业PMI:商务活动:分行业/建筑业', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi020101'}],
    ('pmi020102', 'm', 'None'):                       ['非制造业PMI:商务活动:分行业/服务业业', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi020102'}],
    ('pmi020200', 'm', 'None'):                       ['非制造业PMI:新订单指数', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi020200'}],
    ('pmi020201', 'm', 'None'):                       ['非制造业PMI:新订单指数:分行业/建筑业', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi020201'}],
    ('pmi020202', 'm', 'None'):                       ['非制造业PMI:新订单指数:分行业/服务业', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi020202'}],
    ('pmi020300', 'm', 'None'):                       ['非制造业PMI:投入品价格指数', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi020300'}],
    ('pmi020301', 'm', 'None'):                       ['非制造业PMI:投入品价格指数:分行业/建筑业', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi020301'}],
    ('pmi020302', 'm', 'None'):                       ['非制造业PMI:投入品价格指数:分行业/服务业', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi020302'}],
    ('pmi020400', 'm', 'None'):                       ['非制造业PMI:销售价格指数', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi020400'}],
    ('pmi020401', 'm', 'None'):                       ['非制造业PMI:销售价格指数:分行业/建筑业', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi020401'}],
    ('pmi020402', 'm', 'None'):                       ['非制造业PMI:销售价格指数:分行业/服务业', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi020402'}],
    ('pmi020500', 'm', 'None'):                       ['非制造业PMI:从业人员指数', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi020500'}],
    ('pmi020501', 'm', 'None'):                       ['非制造业PMI:从业人员指数:分行业/建筑业', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi020501'}],
    ('pmi020502', 'm', 'None'):                       ['非制造业PMI:从业人员指数:分行业/服务业', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi020502'}],
    ('pmi020600', 'm', 'None'):                       ['非制造业PMI:业务活动预期指数', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi020600'}],
    ('pmi020601', 'm', 'None'):                       ['非制造业PMI:业务活动预期指数:分行业/建筑业', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi020601'}],
    ('pmi020602', 'm', 'None'):                       ['非制造业PMI:业务活动预期指数:分行业/服务业', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi020602'}],
    ('pmi020700', 'm', 'None'):                       ['非制造业PMI:新出口订单', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi020700'}],
    ('pmi020800', 'm', 'None'):                       ['非制造业PMI:在手订单', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi020800'}],
    ('pmi020900', 'm', 'None'):                       ['非制造业PMI:存货', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi020900'}],
    ('pmi021000', 'm', 'None'):                       ['非制造业PMI:供应商配送时间', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi021000'}],
    ('pmi030000', 'm', 'None'):                       ['中国综合PMI:产出指数', 'reference',
                                                       {'table_name': 'cn_pmi', 'column': 'pmi030000'}],
    ('p_change_min', 'd', 'E'):                       ['预告净利润变动幅度下限(%)', 'event_signal',
                                                       {'table_name': 'forecast', 'column': 'p_change_min'}],
    ('p_change_max', 'd', 'E'):                       ['预告净利润变动幅度上限(%)', 'event_signal',
                                                       {'table_name': 'forecast', 'column': 'p_change_max'}],
    ('net_profit_min', 'd', 'E'):                     ['预告净利润下限(万元)', 'event_signal',
                                                       {'table_name': 'forecast', 'column': 'net_profit_min'}],
    ('net_profit_max', 'd', 'E'):                     ['预告净利润上限(万元)', 'event_signal',
                                                       {'table_name': 'forecast', 'column': 'net_profit_max'}],
    ('last_parent_net', 'd', 'E'):                    ['上年同期归属母公司净利润', 'event_signal',
                                                       {'table_name': 'forecast', 'column': 'last_parent_net'}],
    ('first_ann_date', 'd', 'E'):                     ['首次公告日', 'event_signal',
                                                       {'table_name': 'forecast', 'column': 'first_ann_date'}],
    ('summary', 'd', 'E'):                            ['业绩预告摘要', 'event_signal',
                                                       {'table_name': 'forecast', 'column': 'summary'}],
    ('change_reason', 'd', 'E'):                      ['业绩变动原因', 'event_signal',
                                                       {'table_name': 'forecast', 'column': 'change_reason'}],
    ('block_trade_price', 'd', 'E'):                  ['大宗交易 - 成交价', 'event_signal',
                                                       {'table_name': 'block_trade', 'column': 'price'}],
    ('block_trade_vol', 'd', 'E'):                    ['大宗交易 - 成交量（万股）', 'event_signal',
                                                       {'table_name': 'block_trade', 'column': 'vol'}],
    ('block_trade_amount', 'd', 'E'):                 ['大宗交易 - 成交金额', 'event_signal',
                                                       {'table_name': 'block_trade', 'column': 'amount'}],
    ('block_trade_buyer', 'd', 'E'):                  ['大宗交易 - 买方营业部', 'event_signal',
                                                       {'table_name': 'block_trade', 'column': 'buyer'}],
    ('block_trade_seller', 'd', 'E'):                 ['大宗交易 - 卖方营业部', 'event_signal',
                                                       {'table_name': 'block_trade', 'column': 'seller'}],
    ('stock_holder_trade_name', 'd', 'E'):            ['股东交易 - 股东名称', 'event_signal',
                                                       {'table_name': 'stock_holder_trade', 'column': 'holder_name'}],
    ('stock_holder_trade_type', 'd', 'E'):            ['股东交易 - 股东类型G高管P个人C公司', 'event_signal',
                                                       {'table_name': 'stock_holder_trade', 'column': 'holder_type'}],
    ('stock_holder_trade_in_de', 'd', 'E'):           ['股东交易 - 类型IN增持DE减持', 'event_signal',
                                                       {'table_name': 'stock_holder_trade', 'column': 'in_de'}],
    ('stock_holder_trade_change_vol', 'd', 'E'):      ['股东交易 - 变动数量', 'event_signal',
                                                       {'table_name': 'stock_holder_trade', 'column': 'change_vol'}],
    ('stock_holder_trade_change_ratio', 'd', 'E'):    ['股东交易 - 占流通比例（%）', 'event_signal',
                                                       {'table_name': 'stock_holder_trade', 'column': 'change_ratio'}],
    ('stock_holder_trade_after_share', 'd', 'E'):     ['股东交易 - 变动后持股', 'event_signal',
                                                       {'table_name': 'stock_holder_trade', 'column': 'after_share'}],
    ('stock_holder_trade_after_ratio', 'd', 'E'):     ['股东交易 - 变动后占流通比例（%）', 'event_signal',
                                                       {'table_name': 'stock_holder_trade', 'column': 'after_ratio'}],
    ('stock_holder_trade_avg_price', 'd', 'E'):       ['股东交易 - 平均价格', 'event_signal',
                                                       {'table_name': 'stock_holder_trade', 'column': 'avg_price'}],
    ('stock_holder_trade_total_share', 'd', 'E'):     ['股东交易 - 持股总数', 'event_signal',
                                                       {'table_name': 'stock_holder_trade', 'column': 'total_share'}],
    ('stock_holder_trade_begin_date', 'd', 'E'):      ['股东交易 - 增减持开始日期', 'event_signal',
                                                       {'table_name': 'stock_holder_trade', 'column': 'begin_date'}],
    ('stock_holder_trade_close_date', 'd', 'E'):      ['股东交易 - 增减持结束日期', 'event_signal',
                                                       {'table_name': 'stock_holder_trade', 'column': 'close_date'}],
    ('margin_detail_rzye', 'd', 'E'):                 ['融资融券交易明细 - 融资余额(元)', 'event_signal',
                                                       {'table_name': 'margin_detail', 'column': 'rzye'}],
    ('margin_detail_rqye', 'd', 'E'):                 ['融资融券交易明细 - 融券余额(元)', 'event_signal',
                                                       {'table_name': 'margin_detail', 'column': 'rqye'}],
    ('margin_detail_rzmre', 'd', 'E'):                ['融资融券交易明细 - 融资买入额(元)', 'event_signal',
                                                       {'table_name': 'margin_detail', 'column': 'rzmre'}],
    ('margin_detail_rqyl', 'd', 'E'):                 ['融资融券交易明细 - 融券余量（股）', 'event_signal',
                                                       {'table_name': 'margin_detail', 'column': 'rqyl'}],
    ('margin_detail_rzche', 'd', 'E'):                ['融资融券交易明细 - 融资偿还额(元)', 'event_signal',
                                                       {'table_name': 'margin_detail', 'column': 'rzche'}],
    ('margin_detail_rqchl', 'd', 'E'):                ['融资融券交易明细 - 融券偿还量(股)', 'event_signal',
                                                       {'table_name': 'margin_detail', 'column': 'rqchl'}],
    ('margin_detail_rqmcl', 'd', 'E'):                ['融资融券交易明细 - 融券卖出量(股,份,手)', 'event_signal',
                                                       {'table_name': 'margin_detail', 'column': 'rqmcl'}],
    ('margin_detail_rzrqye', 'd', 'E'):               ['融资融券交易明细 - 融资融券余额(元)', 'event_signal',
                                                       {'table_name': 'margin_detail', 'column': 'rzrqye'}]
}

USER_DATA_TYPE_MAP = {
}


def _expand_df_index(df: pd.DataFrame, starts: str, ends: str) -> pd.DataFrame:
    """将DataFrame的索引扩展到包含开始和结束日期"""

    starts = pd.to_datetime(starts)
    ends = pd.to_datetime(ends)

    df.index = pd.to_datetime(df.index)
    expanded_index = df.index.to_list()
    if starts not in expanded_index:
        expanded_index.append(starts)
    if ends not in expanded_index:
        expanded_index.append(ends)
    return df.reindex(expanded_index).sort_index(ascending=True)


def get_history_data_from_source(
        datasource,
        htypes: [DataType], *,
        qt_codes: [str] = None,
        start: str = None,
        end: str = None,
        freq: str = None,
        combine_htype_names: bool = False,
        row_count: int = None,
) -> {str: pd.DataFrame}:
    """ 根据给出的历史数据类型对象，获取相应的数据并组装成一个标准的DataFrame-Dict并返回
    如果给出qt_codes/start/end参数，则返回符合要求的数据范围，或者返回最近的row_count行数据
    历史数据返回的结果为column为qt_codes，index为时间的DataFrame，因此只有htype的freq
    不是'none‘，且asset_type也不为'none'时，才能返回正确的数据

    Parameters
    ----------
    datasource: DataSource
        数据源对象，用于获取历史数据
    htypes: [DataType]
        需要获取的历史数据类型，必须是合法的历史数据类型对象，可以是一个或多个
    qt_codes: [str],  Optional
        合法的qt_code代码列表，如果为None，则获取所有数据
    freq: str, Optional
        获取的历史数据的目标频率，
        如果下载的数据频率与目标freq不相同，将通过升频或降频使其与目标频率相同
    start: str, optional
        YYYYMMDD HH:MM:SS 格式的日期/时间，获取的历史数据的开始日期/时间(如果可用)
    end: str, optional
        YYYYMMDD HH:MM:SS 格式的日期/时间，获取的历史数据的结束日期/时间(如果可用)
    combine_htype_names: bool, optional, default False
        在输入的数据类型中可能有相同的htype_names，例如pe(IDX)@'d'与pe(E)@'d'
        这两个htype的名称相同，只是数据类型不同。此时可以选择是否是否合并相同的htype name，
        如果为True，则下载的数据会被合并为一个pe类型，同时包含IDX与E类型的数据
        例如：
        pe:         000300.SH, 000001.SZ
        2020-01-01      22.34,     18.00
        2020-01-01      22.35,     18.50

        如果选择不合并，则pe(IDX)与pe(E)的数据会被分开罗列
        例如：

        pe(IDX):    000300.SH, 000001.SZ
        2020-01-01      22.34,       NaN
        2020-01-01      22.35,       NaN
        pe(E):      000300.SH, 000001.SZ
        2020-01-01        NaN,     18.00
        2020-01-01        NaN,     18.50

    row_count: int, optional, default 100
        获取的历史数据的行数，如果指定了start和end，则忽略此参数
        否则返回最近的row_count行数据

    Returns
    -------
    Dict of DataFrame: {htype: DataFrame[shares]}
        一个标准的DataFrame-Dict，满足stack_dataframes()函数的输入要求，以便组装成
        HistoryPanel对象
    """

    history_data_acquired = {}
    history_data_to_be_re_freqed = {}
    row_count_adj_factors = {
        '1min':  240,
        '5min':  48,
        '15min': 16,
        '30min': 8,
        'h':     4,
        'w':     0.14,
        'm':     0.03,
    }

    if (start is not None) and (end is not None):
        row_count = None

    if row_count is not None:
        trade_day_offset = ceil(row_count / row_count_adj_factors.get(freq, 1)) + 1
    else:
        trade_day_offset = None

    if all(param is None for param in (start, end, row_count)):
        raise ValueError(f'parameter "start", "end", "row_count" can not be all None, '
                         f'you should provide at least two of them')

    # calculate days offset between start and end based on row_count
    if start is None and end is None:
        raise ValueError(f'at least one of start or end should be given, both are None!')
    if start is None:
        # TODO:
        #  the best solution is to check the trade calendar and find out the previous
        #  N-th trade day based on the end date
        # if end is Monday then start should be Friday (this is still temporary)
        end = pd.to_datetime(end)
        if end.weekday() == 0:
            trade_day_offset += 2
        start = end - pd.Timedelta(days=trade_day_offset)
    if end is None:
        start = pd.to_datetime(start)
        if start.weekday() == 4:
            trade_day_offset += 2
        # start and row_count should be given in this case
        end = start + pd.Timedelta(days=trade_day_offset)

    if not htypes:
        raise ValueError(f'at least one DataType should be given, 0 is given!')

    # 逐个获取每一个历史数据类型的数据
    for htype in htypes:
        # 检查数据类型是否属于历史数据，参考数据和基本信息数据不能通过此方法获取
        if htype.freq == 'none' or htype.asset_type == 'none':
            raise ValueError(f'Invalid data type {htype.name}, not a history data type')
        # 从数据源获取数据，
        df = htype.get_data_from_source(datasource, symbols=qt_codes, starts=start, ends=end)
        if not combine_htype_names:
            # 下载的数据不会按htype.name合并，而是分别按htype.id存储
            history_data_acquired[htype.id] = df
            history_data_to_be_re_freqed[htype.id] = True if htype.freq != freq else False
        else:
            # 下载的数据会按htype.name合并，如果htype.name已经有了数据，则新的数据会被concat（按列）到已有的数据中
            original_df = history_data_acquired.get(htype.name)
            if original_df is None:
                history_data_acquired[htype.name] = df
            else:
                new_df = pd.concat([original_df, df], axis=1, copy=False)
                history_data_acquired[htype.name] = new_df
            history_data_to_be_re_freqed[htype.name] = True if htype.freq != freq else False

    # 如果提取的数据全部为空DF，说明DataSource可能数据不足，报错并建议
    if all(df.empty for df in history_data_acquired.values()):
        err = RuntimeError(f'Empty data extracted from {datasource} with parameters:\n'
                           f'shares: {qt_codes}\n'
                           f'htypes: {htypes}\n'
                           f'start/end/freq: {start}/{end}/"{freq}"\n'
                           f'To check data availability, use one of the following:\n'
                           f'Availability of all tables:     qt.get_table_overview()，or\n'
                           f'Availability of <table_name>:   qt.get_table_info(\'table_name\')\n'
                           f'To fill datasource:             qt.refill_data_source(table=\'table_name\', '
                           f'**kwargs)')
        raise err

    # 整理数据，确保每一个htype的DataFrame的columns与shares相同
    qt_codes = str_to_list(qt_codes)

    for htyp, df in history_data_acquired.items():
        df = df.reindex(columns=qt_codes)
        if row_count:
            df = df.tail(row_count)
        history_data_acquired[htyp] = df

    return history_data_acquired


def get_reference_data_from_source(
        datasource,
        htypes: [DataType], *,
        start: str = None,
        end: str = None,
        freq: str = None,
        row_count: int = 100,
) -> {str: pd.Series}:
    """ 根据给出的参考数据类型对象，获取相应的数据并组装成一个标准的Series-Dict并返回

    由于获取的数据是参考数据，因此数据是一个Series，index为时间，value为数据值，该数据
    并不针对具体的证券，因此普遍应该从不含证券代码的数据表中获取数据，如货币数据、国债数据等。
    如果需要用某证券的数据作为参考数据，可以给出证券代码，但该证券代码会作为Series的index
    而不会作为column返回。

    Parameters
    ----------
    datasource: DataSource
        数据源对象，用于获取参考数据
    htypes: [DataType]
        需要获取的参考数据类型，必须是合法的参考数据类型对象，可以是一个或多个
    freq: str, Optional
        获取的参考数据的目标频率，
        如果下载的数据频率与目标freq不相同，将通过升频或降频使其与目标频率相同
    start: str, optional
        YYYYMMDD HH:MM:SS 格式的日期/时间，获取的参考数据的开始日期/时间(如果可用)
    end: str, optional
        YYYYMMDD HH:MM:SS 格式的日期/时间，获取的参考数据的结束日期/时间(如果可用)
    row_count: int, optional, default 100
        获取的参考数据的行数，如果指定了start和end，则忽略此参数

    Returns
    -------
    Dict of Series: {rtype: Series[qt_code]}
    """

    row_count_adj_factors = {
        '1min':  240,
        '5min':  48,
        '15min': 16,
        '30min': 8,
        'h':     4,
        'w':     0.14,
        'm':     0.03,
    }

    if (start is not None) and (end is not None):
        row_count = None

    if row_count is not None:
        adjusted_row_count = ceil(row_count / row_count_adj_factors.get(freq, 1)) + 1
    else:
        adjusted_row_count = None

    if all(param is None for param in (start, end, row_count)):
        raise ValueError(f'parameter "start", "end", "row_count" can not be all None, '
                         f'you should provide at least two of them')

    if start is None:
        # end should be given in this case
        start = pd.to_datetime(end) - pd.Timedelta(days=adjusted_row_count)
    if end is None:
        # start and row_count should be given in this case
        end = pd.to_datetime(start) + pd.Timedelta(days=adjusted_row_count)

    if not htypes:
        err = ValueError(f'data types should not be empty!')
        raise err

    reference_data_acquired = {}
    reference_data_to_be_refreqed = {}

    # 逐个获取每一个历史数据类型的数据
    for htype in htypes:
        # 检查数据类型是否属于参考数据，历史数据和基本信息数据不能通过此方法获取
        if htype.freq == 'None':
            err = ValueError(f'Invalid data type {htype.name}, not a reference data type')
            raise err
        if (htype.asset_type != 'None') and (htype.unsymbolizer is None):
            err = TypeError(f'data type ({htype.__str__()}) is a history data, not a reference data, '
                            f'consider using unsymbolizer, to convert it to reference data, such as "close-000651.SZ"')
            raise err

        if htype.unsymbolizer is not None:
            qt_code = htype.unsymbolizer
        else:
            qt_code = None

        # 从数据源获取数据
        ser = htype.get_data_from_source(datasource, symbols=qt_code, starts=start, ends=end)

        ser.name = htype.name

        already_ser = reference_data_acquired.get(htype.name)
        if already_ser is None:
            reference_data_acquired[htype.name] = ser
        else:  # 如果尚未找到有意义的数据，则将新的数据赋值给reference_data_acquired
            if already_ser.empty:
                reference_data_acquired[htype.name] = ser

        reference_data_to_be_refreqed[htype.name] = True if htype.freq != freq else False

    # 如果提取的数据全部为空DF，说明DataSource可能数据不足，报错并建议
    if all(ser.empty for ser in reference_data_acquired.values()):
        err = RuntimeError(f'Empty data extracted from {datasource} with parameters:\n'
                           f'htypes: {htypes}\n'
                           f'start/end/freq: {start}/{end}/"{freq}"\n'
                           f'To check data availability, use one of the following:\n'
                           f'Availability of all tables:     qt.get_table_overview()，or\n'
                           f'Availability of <table_name>:   qt.get_table_info(\'table_name\')\n'
                           f'To fill datasource:             qt.refill_data_source(table=\'table_name\', '
                           f'**kwargs)')
        raise err

    for htyp, ser in reference_data_acquired.items():
        if isinstance(ser, pd.DataFrame) and not ser.empty:
            # import pdb
            # pdb.set_trace()
            pass

    return reference_data_acquired


def get_data_type(htype, *, symbols=None, starts=None, ends=None, target_freq=None):
    """ DataSource类的主要获取数据的方法，根据数据类型，获取数据并输出

    如果symbols为None，则输出为un-symbolised数据，否则输出为symbolised数据

    Parameters
    ----------
    htype: DataType
    """
    return htype.get_data_from_source(symbols=symbols, starts=starts, ends=ends, target_freq=target_freq)


def find_history_data(s, match_description=False, fuzzy=False, freq=None, asset_type=None, match_threshold=0.85):
    """ 根据输入的字符串，查找或匹配历史数据类型,并且显示该历史数据的详细信息。支持模糊查找、支持通配符、支持通过英文字符或中文
    查找匹配的历史数据类型。

    Parameters
    ----------
    s: str
        一个字符串，用于查找或匹配历史数据类型
    match_description: bool, Default: False
        是否模糊匹配数据描述，如果给出的字符串中含有非Ascii字符，会自动转为True
         - False: 仅匹配数据名称
         - True:  同时匹配数据描述
    fuzzy: bool, Default: False
        是否模糊匹配数据名称，如果给出的字符串中含有非Ascii字符或通配符*/?，会自动转为True
         - False: 精确匹配数据名称
         - True:  模糊匹配数据名称或数据描述
    freq: str, Default: None
        数据频率，如果提供，则只匹配该频率的数据
        可以输入单个频率，也可以输入逗号分隔的多个频率
    asset_type: str, Default: None
        证券类型，如果提供，则只匹配该证券类型的数据
        可以输入单个证券类型，也可以输入逗号分隔的多个证券类型
    match_threshold: float, default 0.85
        匹配度阈值，匹配度超过该阈值的项目会被判断为匹配

    Returns
    -------
    data_id: list
        匹配到的数据类型的data_id，可以用于qt.get_history_data()下载数据

    Examples
    --------
    >>> import qteasy as qt
    >>> qt.find_history_data('pe')
    matched following history data,
    use "qt.get_history_data()" to load these historical data by its name:
    ------------------------------------------------------------------------
               freq asset             table                            desc
    data_id
    initial_pe    d     E         new_share                  新股上市信息 - 发行市盈率
    pe            d   IDX   index_indicator                    指数技术指标 - 市盈率
    pe            d     E   stock_indicator  股票技术指标 - 市盈率（总市值/净利润， 亏损的PE为空）
    pe_2          d     E  stock_indicator2                  股票技术指标 - 动态市盈率
    ========================================================================

    >>> qt.find_history_data('ep*')
    matched following history data,
    use "qt.get_history_data()" to load these historical data by its data_id:
    ------------------------------------------------------------------------
                  freq asset      table                 desc
    data_id
    eps_last_year    q     E    express  上市公司业绩快报 - 去年同期每股收益
    eps              q     E  financial    上市公司财务指标 - 基本每股收益
    ========================================================================

    >>> qt.find_history_data('每股收益')
    matched following history data,
    use "qt.get_history_data()" to load these historical data by its data_id:
    ------------------------------------------------------------------------
                    freq asset      table                 desc
    data_id
    basic_eps              q     E     income           上市公司利润表 - 基本每股收益
    diluted_eps            q     E     income           上市公司利润表 - 稀释每股收益
    express_diluted_eps    q     E    express     上市公司业绩快报 - 每股收益(摊薄)(元)
    yoy_eps                q     E    express    上市公司业绩快报 - 同比增长率:基本每股收益
    eps_last_year          q     E    express        上市公司业绩快报 - 去年同期每股收益
    eps                    q     E  financial          上市公司财务指标 - 基本每股收益
    dt_eps                 q     E  financial          上市公司财务指标 - 稀释每股收益
    diluted2_eps           q     E  financial        上市公司财务指标 - 期末摊薄每股收益
    q_eps                  q     E  financial       上市公司财务指标 - 每股收益(单季度)
    basic_eps_yoy          q     E  financial  上市公司财务指标 - 基本每股收益同比增长率(%)
    dt_eps_yoy             q     E  financial  上市公司财务指标 - 稀释每股收益同比增长率(%)
    ========================================================================

    Raises
    ------
    TypeError: 输入的s不是字符串，或者freq/asset_type不是字符串或列表
    """

    if not isinstance(s, str):
        err = TypeError(f'input should be a string, got {type(s)} instead.')
        raise err
    # 判断输入是否ascii编码，如果是，匹配数据名称，否则，匹配数据描述
    try:
        s.encode('ascii')
    except UnicodeEncodeError:
        # is_ascii = False, 此时强制匹配description, 并且fuzzy匹配
        match_description = True
        fuzzy = True
    if match_description:
        fuzzy = True
    if ('?' in s) or ('*' in s):
        fuzzy = True  # 给出通配符时强制fuzzy匹配

    data_table_map = get_dtype_map()
    data_table_map['dtype_name'] = data_table_map.index.get_level_values(level=0)
    data_table_map['freq'] = data_table_map.index.get_level_values(level=1)
    data_table_map['asset_type'] = data_table_map.index.get_level_values(level=2)
    data_table_map['table_name'] = data_table_map.kwargs.apply(lambda x: x['table_name'])
    data_table_map['column'] = data_table_map.kwargs.apply(lambda x: x['column'])

    if freq is not None:
        if isinstance(freq, str):
            freq = str_to_list(freq)
        if not isinstance(freq, list):
            err = TypeError(f'freq should be a string or a list, got {type(freq)} instead')
            raise err
        data_table_map = data_table_map.loc[data_table_map['freq'].isin(freq)]
    if asset_type is not None:
        if isinstance(asset_type, str):
            asset_type = str_to_list(asset_type)
        if not isinstance(asset_type, list):
            err = TypeError(f'asset_type should be a string or a list, got {type(asset_type)} instead')
            raise err
        data_table_map = data_table_map.loc[data_table_map['asset_type'].isin(asset_type)]

    data_table_map['n_matched'] = 0  # name列的匹配度，模糊匹配的情况下，匹配度为0～1之间的数字
    data_table_map['d_matched'] = 0  # description列的匹配度，模糊匹配的情况下，匹配度为0～1之间的数字

    if (not fuzzy) and (not match_description):
        # match data type id
        data_table_map['n_matched'] = data_table_map['dtype_name'] == s
        data_table_map['n_matched'] = data_table_map['n_matched'].astype('int')
    else:
        if match_description:
            where_to_look = ['dtype_name', 'description']
            match_how = [_lev_ratio, _partial_lev_ratio]
            result_columns = ['n_matched', 'd_matched']
        elif fuzzy:
            where_to_look = ['dtype_name']
            match_how = [_partial_lev_ratio]
            result_columns = ['n_matched']
        else:
            where_to_look = ['dtype_name']
            match_how = [_lev_ratio]
            result_columns = ['n_matched']

        for where, how, res in zip(where_to_look, match_how, result_columns):
            if ('?' in s) or ('*' in s):
                matched = _wildcard_match(s, data_table_map[where])
                match_values = [1 if item in matched else 0 for item in data_table_map[where]]
            else:
                match_values = list(map(how, [s] * len(data_table_map[where]), data_table_map[where]))
            data_table_map[res] = match_values

    data_table_map['matched'] = data_table_map['n_matched'] + data_table_map['d_matched']
    data_table_map = data_table_map.loc[data_table_map['matched'] >= match_threshold]
    data_table_map = data_table_map[['dtype_name', 'freq', 'asset_type', 'table_name', 'column', 'description']]
    # data_table_map.drop(columns=['n_matched', 'd_matched', 'matched'], inplace=True)
    data_table_map.index = data_table_map.index.get_level_values(level=0)
    data_table_map.index.name = 'data_id'
    print(f'matched following history data, \n'
          f'use "qt.get_history_data()" to load these historical data by its data_id:\n'
          f'------------------------------------------------------------------------')
    print(
            data_table_map.to_string(
                    columns=['dtype_name',
                             'freq',
                             'asset_type',
                             'table_name',
                             'column',
                             'description'],
                    header=['name',
                            'freq',
                            'asset',
                            'table',
                            'column',
                            'desc'],
            )
    )
    print(f'========================================================================')
    return list(data_table_map.index)


def get_tables_by_dtypes(
        dtypes: [str] = None,
        freqs: [str] = None,
        asset_types: [str] = None) -> set:
    """根据输入的数据类型反推相关的数据表名称"""

    # 如果给出了dtypes，freq、asset_types中的任意一个，将用这三个参数作为
    # 数据类型，反推需要下载的数据表
    dtype_slice = [slice(None)] if dtypes is None else dtypes
    freq_slice = [slice(None)] if freqs is None else freqs
    asset_slice = [slice(None)] if asset_types is None else asset_types

    from itertools import product
    dtype_filters = product(dtype_slice, freq_slice, asset_slice)

    tables_to_keep = set()
    for dtype_filter in dtype_filters:
        # find out the table name from dtype definition
        dtype_map = _get_built_in_data_type_map()
        matched_kwargs = dtype_map.loc[dtype_filter].kwargs
        # 此时如果只有一个match，会返回dict，否则是一个series，需要分别处理
        if isinstance(matched_kwargs, dict):
            tables_to_keep.add(matched_kwargs['table_name'])
        else:
            # 此时返回一个Series，包含多个dict，需要逐个处理
            for kw in matched_kwargs:
                tables_to_keep.update(
                        [kw['table_name']]
                )

    return tables_to_keep