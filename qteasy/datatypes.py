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
    get_data_type_map()


@lru_cache(maxsize=1)
def get_data_type_map() -> pd.DataFrame:
    """get a DataFrame of DATA_TYPE_MAP for checking."""
    type_map = pd.DataFrame(DATA_TYPE_MAP).T
    type_map.columns = DATA_TYPE_MAP_COLUMNS
    type_map.index.names = DATA_TYPE_MAP_INDEX_NAMES

    return type_map


def get_user_data_type_map() -> pd.DataFrame:
    """get a DataFrame of USER_DATA_TYPE_MAP for checking."""

    if not USER_DATA_TYPE_MAP:
        return pd.DataFrame()

    type_map = pd.DataFrame(USER_DATA_TYPE_MAP).T
    type_map.columns = DATA_TYPE_MAP_COLUMNS
    type_map.index.names = DATA_TYPE_MAP_INDEX_NAMES

    return type_map


def parse_name_and_params(name: str) -> tuple:
    """parse the name string into name and parameters

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
    """
    if ':' in name:
        search_name, params = name.split(':')
        search_name = search_name + ':%'
        return search_name, params
    else:
        return name, None


def parse_built_in_type_id(name: str) -> tuple:
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
    data_map = get_data_type_map()

    matched_types = data_map.loc[(name, slice(None), slice(None))]

    if matched_types.empty:
        return tuple(), tuple()
    else:
        return matched_types.index.get_level_values('freq').unique(), \
            matched_types.index.get_level_values('asset_type').unique()


def parse_user_defined_type_id(name: str) -> tuple:
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
    type_map = get_user_data_type_map()

    if type_map.empty:
        return tuple(), tuple()

    matched_types = type_map.loc[(name, slice(None), slice(None))]

    if matched_types.empty:
        return tuple(), tuple()
    else:
        return matched_types.index.get_level_values('freq').unique(), \
            matched_types.index.get_level_values('asset_type').unique()


def parse_aquisition_parameters(search_name, name_par, freq, asset_type, built_in_tables=True) -> tuple:
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
    """

    aquisition_types = [
        'basics',
            # 直接获取数据表中与资产有关的一个数据字段，该数据与日期无关，输出index为qt_code的Series
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
            # 事件状态型。从表中查询事件的发生日期并在事件影响区间内填充不同状态的，如停牌，改名等
        'event_multi_stat',
            # 多事件状态型。从表中查询多个事件的发生日期并在事件影响区间内填充多个不同的状态，如管理层名单等
        'event_signal',
            # 事件信号型。从表中查询事件的发生日期并在事件发生时产生信号的，如涨跌停，上板上榜，分红配股等
            # {'table_name': table, 'column': output_col}
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
        如果用户仅输入名称，将尝试从DATA_TYPE_MAP中匹配相应的参数，如果找到唯一匹配，则生成该类型的实例，否则抛出异常并给出提示。

        用户自定义的数据类型也在上述查找匹配范围内。而用户需要通过datatypes.define()方法将自定义的数据类型添加到DATA_TYPE_MAP中。

        Parameters
        ----------
        name: str
            数据类型的名称
        freq: str, optional
            数据的频率: d(日), w(周), m(月), q(季), y(年)
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
        ValueError
            如果用户输入的参数不完整，在DATA_TYPE_MAP中无法匹配到唯一的数据类型
            ValueError: Input matches multiple data types in DATA_TYPE_MAP, specify your input: {types}?.
        """
        if not isinstance(name, str):
            raise TypeError(f'name must be a string, got {type(name)}')

        search_name, name_pars = parse_name_and_params(name)

        # 根据用户输入的name查找所有匹配的频率和资产类型
        built_in_freqs, built_in_asset_types = parse_built_in_type_id(search_name)
        user_defined_freqs, user_defined_asset_types = parse_user_defined_type_id(search_name)

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
        description, acquisition_type, kwargs = parse_aquisition_parameters(
                search_name=search_name,
                name_par=name_pars,
                freq=default_freq,
                asset_type=default_asset_type,
                built_in_tables=built_in_freqs is not None,
        )

        self._name = name
        self._name_pars = None
        self._default_freq = default_freq
        self._default_asset_type = default_asset_type
        self._all_built_in_freqs = None
        self._all_built_in_asset_types = None
        self._all_user_defined_freqs = None
        self._all_user_defined_asset_types = None
        self._description = description
        self._acquisition_type = acquisition_type

        self._kwargs = kwargs

    @property
    def name(self):
        return self._name

    @property
    def freq(self):
        return self._default_freq

    @property
    def asset_type(self):
        return self._default_asset_type

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

    # 真正的顶层数据获取API接口函数
    def get_data_from(self, datasource, *, symbols=None, starts=None, ends=None, target_freq=None):
        """ Datatype类从DataSource类获取数据的方法，根据数据类型的获取方式，调用相应的方法获取数据并输出

        如果symbols为None，则输出为un-symbolised数据，否则输出为symbolised数据

        Parameters
        ----------
        datasource: DataSource
            数据类型对象
        symbols: list
            股票代码列表
        starts: str
            开始日期
        ends: str
            结束日期
        target_freq: str, optional
            用户要求的频率

        """

        acquisition_type = self.acquisition_type
        kwargs = self.kwargs

        if acquisition_type == 'basics':
            acquired_data = self._get_basics(datasource, symbols=symbols, **kwargs)
        elif acquisition_type == 'selection':
            acquired_data = self._get_selection(datasource, **kwargs)
        elif acquisition_type == 'direct':
            acquired_data = self._get_direct(datasource, symbols=symbols, starts=starts, ends=ends, **kwargs)
        elif acquisition_type == 'adjustment':
            acquired_data = self._get_adjustment(datasource, symbols=symbols, starts=starts, ends=ends, **kwargs)
        elif acquisition_type == 'operation':
            acquired_data = self._get_operation(datasource, symbols=symbols, starts=starts, ends=ends, **kwargs)
        elif acquisition_type == 'relations':
            acquired_data = self._get_relations(datasource, symbols=symbols, starts=starts, ends=ends, **kwargs)
        elif acquisition_type == 'event_multi_stat':
            acquired_data = self._get_event_multi_stat(datasource, symbols=symbols, starts=starts, ends=ends, **kwargs)
        elif acquisition_type == 'event_status':
            acquired_data = self._get_event_status(datasource, symbols=symbols, starts=starts, ends=ends, **kwargs)
        elif acquisition_type == 'event_signal':
            acquired_data = self._get_event_signal(datasource, symbols=symbols, starts=starts, ends=ends, **kwargs)
        elif acquisition_type == 'composition':
            acquired_data = self._get_composition(datasource, symbols=symbols, starts=starts, ends=ends, **kwargs)
        elif acquisition_type == 'category':
            acquired_data = self._get_category(datasource, symbols=symbols, **kwargs)
        elif acquisition_type == 'complex':
            acquired_data = self._get_complex(datasource, symbols=symbols, date=starts, **kwargs)
        else:
            raise ValueError(f'Unknown acquisition type: {acquisition_type}')

        if acquisition_type == 'basics':
            return acquired_data

        if acquired_data.empty:
            return acquired_data

        if target_freq is not None and target_freq != self.freq:
            acquired_data = self._adjust_freq(acquired_data, target_freq)

        if symbols is None:
            return self._unsymbolised(acquired_data)

        return self._symbolised(acquired_data)

    # 下面获取数据的方法都放在datasource中
    def _get_basics(self, datasource, *, symbols=None, starts=None, ends=None, **kwargs) -> pd.Series:
        """基本数据的获取方法：
        从table_name表中选出column列的数据并输出。
        如果给出symbols则筛选出symbols的数据，否则输出全部数据。
        start和end无效，只是为了保持接口一致性。
        """

        # try to get arguments from kwargs
        table_name = kwargs.get('table_name')
        column = kwargs.get('column')

        if table_name is None or column is None:
            raise ValueError('table_name and column must be provided for basics data type')

        acquired_data = datasource.read_table_data(table_name, shares=symbols, start=starts, end=ends)

        if acquired_data.empty:
            return pd.Series()

        if column not in acquired_data.columns:
            raise KeyError(f'column {column} not in table data: {acquired_data.columns}')

        return acquired_data[column]

    def _get_selection(self, datasource, *, symbols=None, starts=None, ends=None, **kwargs) -> pd.Series:
        """筛选型的数据获取方法：
        从table_name表中筛选出sel_by=keys的数据并输出column列数据
        如果给出symbols则筛选出symbols的数据，否则输出全部数据。
        start和end无效，只是为了保持接口一致性。
        """

        # try to get arguments from kwargs
        table_name = kwargs.get('table_name')
        column = kwargs.get('column')
        sel_by = kwargs.get('sel_by')
        keys = kwargs.get('keys')

        if table_name is None or column is None or sel_by is None or keys is None:
            import pdb; pdb.set_trace()
            raise ValueError('table_name, column, sel_by and keys must be provided for selection data type')

        acquired_data = datasource.read_table_data(table_name, shares=symbols, start=starts, end=ends)

        if acquired_data.empty:
            return pd.Series()

        if sel_by not in acquired_data.columns:
            raise KeyError(f'sel_by {sel_by} not in table data: {acquired_data.columns}')

        selected_data = acquired_data[acquired_data[sel_by].isin(keys)]
        return selected_data[column]

    def _get_direct(self, datasource, *, symbols, starts, ends, **kwargs) -> pd.DataFrame:
        """直读从时间序列数据表中读取数据
        从table_name表中选出column列的数据并输出。
        必须给出symbols数据，以输出index为datetime，column为symbols的DataFrame
        必须给出start和end以筛选出在start和end之间的数据
        """
        if starts is None or ends is None:
            raise ValueError('start and end must be provided for direct data type')

        data_series = self._get_basics(datasource, symbols=symbols, starts=starts, ends=ends, **kwargs)

        if data_series.empty:
            return pd.DataFrame()

        unstacked_df = data_series.unstack(level=0)

        return unstacked_df

    def _get_adjustment(self, datasource, *, symbols, starts, ends, **kwargs) -> pd.DataFrame:
        """修正型的数据获取方法
        从table_name表中选出column列的数据，并从adj_table表中选出adj_column列数据，根据adj_type调整后输出
        必须给出symbols数据，以输出index为datetime，column为symbols的DataFrame
        必须给出start和end以筛选出在start和end之间的数据
        """
        table_name = kwargs.get('table_name')
        column = kwargs.get('column')
        adj_table = kwargs.get('adj_table')
        adj_column = kwargs.get('adj_column')
        adj_type = kwargs.get('adj_type')

        if table_name is None or column is None or adj_table is None or adj_column is None:
            raise ValueError(
                    'table_name_A, column_A, table_name_B and column_B must be provided for adjustment data type')

        acquired_data = datasource.read_table_data(table_name, shares=symbols, start=starts, end=ends)
        acquired_data = acquired_data[column].unstack(level=0)

        adj_factors = datasource.read_table_data(adj_table, shares=symbols, start=starts, end=ends)
        adj_factors = adj_factors[adj_column].unstack(level=0)

        adj_factors = adj_factors.reindex(acquired_data.index, method='ffill')
        back_adj_data = acquired_data * adj_factors

        if adj_type == 'backward':
            return back_adj_data

        fwd_adj_data = back_adj_data / adj_factors.iloc[-1]
        return fwd_adj_data

    def _get_operation(self, datasource, *, symbols=None, starts=None, ends=None, **kwargs) -> pd.DataFrame:
        """数据操作型的数据获取方法"""
        raise NotImplementedError

    def _get_relations(self, datasource, *, symbols=None, starts=None, ends=None, **kwargs) -> pd.DataFrame:
        """数据关联型的数据获取方法"""
        raise NotImplementedError

    def _get_event_multi_stat(self, datasource, *, symbols=None, starts=None, ends=None, **kwargs) -> pd.DataFrame:
        """事件多状态型的数据获取方法

        Parameters
        ----------
        symbols: list
            股票代码列表
        starts: str
            开始日期
        ends: str
            结束日期
        **kwargs
            table_name: str
                数据表名
            column: str
                数据表中的列名
            id_index: str
                数据表中的id列名
            start_col: str
                数据表中的开始时间列名
            end_col: str
                数据表中的结束时间列名

        Returns
        -------
        DataFrame
        """

        from .database import (
            get_built_in_table_schema,
            set_primary_key_frame,
        )

        if symbols is None:
            raise ValueError('symbols must be provided for event status data type')
        if starts is None or ends is None:
            raise ValueError('start and end must be provided for event status data type')

        table_name = kwargs.get('table_name')
        column = kwargs.get('column')
        id_index = kwargs.get('id_index')
        start_col = kwargs.get('start_col')
        end_col = kwargs.get('end_col')

        if table_name is None or column is None:
            raise ValueError('table_name and column must be provided for basics data type')

        acquired_data = datasource.read_table_data(
                table_name,
                shares=symbols,
                start=starts,
                end=ends,
                primary_key_in_index=False,
        )
        columns, dtypes, primary_keys, pk_dtypes = get_built_in_table_schema(table_name, with_primary_keys=True)
        cols_to_keep = [start_col, end_col, column]
        cols_to_keep.extend(primary_keys)
        acquired_data = acquired_data[cols_to_keep]
        # create id_index and column pairs
        acquired_data[column] = acquired_data[id_index] + '-' + acquired_data[column].astype(str)

        if acquired_data.empty:
            return pd.DataFrame()

        # make group and combine events on the same date for the same symbol
        grouped = acquired_data.groupby(['ts_code', start_col])
        events = grouped[column].apply(lambda x: list(x))
        events = events.unstack(level=0)

        # expand the index to include starts and ends dates
        events = _expand_df_index(events, starts, ends).ffill()

        # filter out events that are not in the date range
        date_mask = (events.index >= starts) & (events.index <= ends)
        events = events.loc[date_mask]

        return events

    def _get_event_status(self, datasource, *, symbols=None, starts=None, ends=None, **kwargs) -> pd.DataFrame:
        """事件状态型的数据获取方法

        Parameters
        ----------
        symbols: list
            股票代码列表
        starts: str
            开始日期
        ends: str
            结束日期
        **kwargs
            table_name: str
                数据表名
            column: str
                数据表中的列名
            id_index: str
                数据表中的id列名
            start_col: str
                数据表中的开始时间列名
            end_col: str
                数据表中的结束时间列名

        Returns
        -------
        DataFrame
        """

        if symbols is None:
            raise ValueError('symbols must be provided for event status data type')
        if starts is None or ends is None:
            raise ValueError('start and end must be provided for event status data type')

        # acquire data with out time thus status can be ffilled from previous dates
        data_series = self._get_basics(datasource, symbols=symbols, starts=None, ends=None, **kwargs)

        if data_series.empty:
            return pd.DataFrame()

        data_df = data_series.unstack(level='ts_code')

        # expand the index to include starts and ends dates
        status = _expand_df_index(data_df, starts, ends).ffill()

        # filter out events that are not in the date range
        date_mask = (status.index >= starts) & (status.index <= ends)
        status = status.loc[date_mask]

        return status

    def _get_event_signal(self, datasource, *, symbols=None, starts=None, ends=None, **kwargs) -> pd.DataFrame:
        """事件信号型的数据获取方法

        Parameters
        ----------
        symbols: list
            股票代码列表
        starts: str
            开始日期
        ends: str
            结束日期
        **kwargs
            table_name: str
                数据表名
            column: str
                数据表中的列名
            id_index: str
                数据表中的id列名
            start_col: str
                数据表中的开始时间列名
            end_col: str
                数据表中的结束时间列名

        Returns
        -------
        DataFrame
        """

        if symbols is None:
            raise ValueError('symbols must be provided for event status data type')
        if starts is None or ends is None:
            raise ValueError('start and end must be provided for event status data type')

        data_series = self._get_basics(datasource, symbols=symbols, starts=starts, ends=ends, **kwargs)

        if data_series.empty:
            return pd.DataFrame()

        signals = data_series.unstack(level='ts_code')

        # if index is a MultiIndex with multiple datetime levels, use the last level as the date index
        if isinstance(signals.index, pd.MultiIndex):
            signals.index = signals.index.get_level_values(-1)

        return signals

    def _get_composition(self, datasource, *, symbols=None, starts=None, ends=None, **kwargs) -> pd.DataFrame:
        """成份查询型的数据获取方法

        Parameters
        ----------
        symbols: list
            股票代码列表
        starts: str
            开始日期
        ends: str
            结束日期
        **kwargs
            table_name: str
                数据表名
            column: str
                数据表中的列名
            comp_column: str
                数据表中的成份列名
            index: str
                数据表中的索引列名

        Returns
        -------
        DataFrame
        """

        table_name = kwargs.get('table_name')
        column = kwargs.get('column')
        comp_column = kwargs.get('comp_column')
        index = kwargs.get('index')

        weight_data = datasource.read_table_data(table_name, shares=index, start=starts, end=ends)
        if not weight_data.empty:
            weight_data = weight_data.unstack()
        else:
            # return empty data
            return weight_data

        weight_data.columns = weight_data.columns.get_level_values(1)
        weight_data.index = weight_data.index.get_level_values(1)

        if symbols is not None:
            weight_data = weight_data.reindex(columns=symbols)

        return weight_data

    def _get_category(self, datasource, *, symbols=None, **kwargs) -> pd.DataFrame:
        """成份查询型的数据获取方法

                Parameters
                ----------
                symbols: list
                    股票代码列表
                starts: str
                    开始日期
                ends: str
                    结束日期
                **kwargs
                    table_name: str
                        数据表名
                    column: str
                        数据表中的列名
                    comp_column: str
                        数据表中的成份列名
                    index: str
                        数据表中的索引列名

                Returns
                -------
                DataFrame
                """

        table_name = kwargs.get('table_name')
        column = kwargs.get('column')
        comp_column = kwargs.get('comp_column')

        category_data = datasource.read_table_data(table_name)
        category = category_data.index.to_frame()
        category.index = category[column]

        category = category.reindex(index=symbols)

        return category[comp_column]

    def _get_complex(self, datasource, *, symbols=None, date=None, **kwargs) -> pd.DataFrame:
        """复合型的数据获取方法"""
        raise NotImplementedError

    def _adjust_freq(self, acquired_data, freq) -> pd.DataFrame:
        """调整获取的数据的频率"""
        raise NotImplementedError

    def _symbolised(self, acquired_data) -> pd.DataFrame:
        """将数据转换为symbolised格式"""
        return acquired_data

    def _unsymbolised(self, acquired_data) -> pd.Series:
        """将数据转换为un-symbolised格式"""
        return acquired_data


DATA_TYPE_MAP_COLUMNS = ['description', 'acquisition_type', 'kwargs']
DATA_TYPE_MAP_INDEX_NAMES = ('dtype', 'freq', 'asset_type')
DATA_TYPE_MAP = {
('trade_cal', 'd', 'None'): ['交易日历','direct',{'table_name': 'trade_calendar', 'column': 'is_open'}],
('pre_trade_day', 'd', 'None'): ['交易日历','direct',{'table_name': 'trade_calendar', 'column': 'pretrade_date'}],
('stock_symbol','None','E'):	['股票基本信息 - 股票代码','basics',{'table_name': 'stock_basic', 'column': 'symbol'}],
('stock_name','None','E'):	['股票基本信息 - 股票名称','basics',{'table_name': 'stock_basic', 'column': 'name'}],
('area','None','E'):	['股票基本信息 - 地域','basics',{'table_name': 'stock_basic', 'column': 'area'}],
('industry','None','E'):	['股票基本信息 - 所属行业','basics',{'table_name': 'stock_basic', 'column': 'industry'}],
('fullname','None','E'):	['股票基本信息 - 股票全称','basics',{'table_name': 'stock_basic', 'column': 'fullname'}],
('enname','None','E'):	['股票基本信息 - 英文全称','basics',{'table_name': 'stock_basic', 'column': 'enname'}],
('cnspell','None','E'):	['股票基本信息 - 拼音缩写','basics',{'table_name': 'stock_basic', 'column': 'cnspell'}],
('market','None','E'):	['股票基本信息 - 市场类型','basics',{'table_name': 'stock_basic', 'column': 'market'}],
('exchange','None','E'):	['股票基本信息 - 交易所代码','basics',{'table_name': 'stock_basic', 'column': 'exchange'}],
('curr_type','None','E'):	['股票基本信息 - 交易货币','basics',{'table_name': 'stock_basic', 'column': 'curr_type'}],
('list_status','None','E'):	['股票基本信息 - 上市状态 L上市 D退市 P暂停上市','basics',{'table_name': 'stock_basic', 'column': 'list_status'}],
('list_date','None','E'):	['股票基本信息 - 上市日期','basics',{'table_name': 'stock_basic', 'column': 'list_date'}],
('delist_date','None','E'):	['股票基本信息 - 退市日期','basics',{'table_name': 'stock_basic', 'column': 'delist_date'}],
('is_hs','None','E'):	['股票基本信息 - 是否沪深港通标的','basics',{'table_name': 'stock_basic', 'column': 'is_hs'}],
('wt_idx:%','None','E'):	['股票在指数中所占权重 - %','composition',{'table_name': 'index_weight', 'column': 'weight', 'comp_column': 'index_code', 'index': '%'}],
('ths_category','None','E'):	['股票同花顺行业分类','category',{'table_name': 'ths_index_weight', 'column': 'code', 'comp_column': 'ts_code'}],
# ('sw_category','None','E'):	['股票行业分类 - 申万','category',{'table_name': 'sw_index_weight', 'column': 'weight', 'comp_column': 'index_code', 'index': '399011.SZ'}],
('market','None','IDX'):	['指数基本信息 - 市场','basics',{'table_name': 'index_basic', 'column': 'market'}],
('publisher','None','IDX'):	['指数基本信息 - 发布方','basics',{'table_name': 'index_basic', 'column': 'publisher'}],
('index_type','None','IDX'):	['指数基本信息 - 指数风格','basics',{'table_name': 'index_basic', 'column': 'index_type'}],
('category','None','IDX'):	['指数基本信息 - 指数类别','basics',{'table_name': 'index_basic', 'column': 'category'}],
('base_date','None','IDX'):	['指数基本信息 - 基期','basics',{'table_name': 'index_basic', 'column': 'base_date'}],
('base_point','None','IDX'):	['指数基本信息 - 基点','basics',{'table_name': 'index_basic', 'column': 'base_point'}],
('list_date','None','IDX'):	['指数基本信息 - 发布日期','basics',{'table_name': 'index_basic', 'column': 'list_date'}],
('weight_rule','None','IDX'):	['指数基本信息 - 加权方式','basics',{'table_name': 'index_basic', 'column': 'weight_rule'}],
('desc','None','IDX'):	['指数基本信息 - 描述','basics',{'table_name': 'index_basic', 'column': 'desc'}],
('exp_date','None','IDX'):	['指数基本信息 - 终止日期','basics',{'table_name': 'index_basic', 'column': 'exp_date'}],
('sw_industry_name','None','IDX'):	['申万行业分类 - 名称','basics',{'table_name': 'sw_industry_basic', 'column': 'industry_name'}],
('sw_parent_code','None','IDX'):	['申万行业分类 - 上级行业代码','basics',{'table_name': 'sw_industry_basic', 'column': 'parent_code'}],
('sw_level','None','IDX'):	['申万行业分类 - 级别','basics',{'table_name': 'sw_industry_basic', 'column': 'level'}],
('sw_industry_code','None','IDX'):	['申万行业分类 - 行业代码','basics',{'table_name': 'sw_industry_basic', 'column': 'industry_code'}],
('sw_published','None','IDX'):	['申万行业分类 - 是否发布','basics',{'table_name': 'sw_industry_basic', 'column': 'is_pub'}],
('sw_source','None','IDX'):	['申万行业分类 - 分类版本','basics',{'table_name': 'sw_industry_basic', 'column': 'src'}],
('sw_level:%','None','IDX'):	['申万行业分类筛选 - %','selection',{'table_name': 'sw_industry_basic', 'column': 'level', 'sel_by': 'level', 'keys': ['%']}],
('sw:%','None','IDX'):	['申万行业分类筛选 - %','selection',{'table_name': 'sw_industry_basic', 'column': 'src', 'sel_by': 'src', 'keys': ['%']}],
('ths_industry_name','None','IDX'):	['同花顺行业分类基本信息 - 行业名称','basics',{'table_name': 'ths_index_basic', 'column': 'name'}],
('ths_industry_count','None','IDX'):	['同花顺行业分类基本信息 - 股票数量','basics',{'table_name': 'ths_index_basic', 'column': 'count'}],
('ths_industry_exchange','None','IDX'):	['同花顺行业分类基本信息 - 交易所','basics',{'table_name': 'ths_index_basic', 'column': 'exchange'}],
('ths_industry_date','None','IDX'):	['同花顺行业分类基本信息 - 发布日期','basics',{'table_name': 'ths_index_basic', 'column': 'list_date'}],
('fund_name','None','FD'):	['基金基本信息 - 简称','basics',{'table_name': 'fund_basic', 'column': 'name'}],
('management','None','FD'):	['基金基本信息 - 管理人','basics',{'table_name': 'fund_basic', 'column': 'management'}],
('custodian','None','FD'):	['基金基本信息 - 托管人','basics',{'table_name': 'fund_basic', 'column': 'custodian'}],
('fund_type','None','FD'):	['基金基本信息 - 投资类型','basics',{'table_name': 'fund_basic', 'column': 'fund_type'}],
('found_date','None','FD'):	['基金基本信息 - 成立日期','basics',{'table_name': 'fund_basic', 'column': 'found_date'}],
('due_date','None','FD'):	['基金基本信息 - 到期日期','basics',{'table_name': 'fund_basic', 'column': 'due_date'}],
('list_date','None','FD'):	['基金基本信息 - 上市时间','basics',{'table_name': 'fund_basic', 'column': 'list_date'}],
('issue_date','None','FD'):	['基金基本信息 - 发行日期','basics',{'table_name': 'fund_basic', 'column': 'issue_date'}],
('delist_date','None','FD'):	['基金基本信息 - 退市日期','basics',{'table_name': 'fund_basic', 'column': 'delist_date'}],
('issue_amount','None','FD'):	['基金基本信息 - 发行份额(亿)','basics',{'table_name': 'fund_basic', 'column': 'issue_amount'}],
('m_fee','None','FD'):	['基金基本信息 - 管理费','basics',{'table_name': 'fund_basic', 'column': 'm_fee'}],
('c_fee','None','FD'):	['基金基本信息 - 托管费','basics',{'table_name': 'fund_basic', 'column': 'c_fee'}],
('duration_year','None','FD'):	['基金基本信息 - 存续期','basics',{'table_name': 'fund_basic', 'column': 'duration_year'}],
('p_value','None','FD'):	['基金基本信息 - 面值','basics',{'table_name': 'fund_basic', 'column': 'p_value'}],
('min_amount','None','FD'):	['基金基本信息 - 起点金额(万元)','basics',{'table_name': 'fund_basic', 'column': 'min_amount'}],
('exp_return','None','FD'):	['基金基本信息 - 预期收益率','basics',{'table_name': 'fund_basic', 'column': 'exp_return'}],
('benchmark','None','FD'):	['基金基本信息 - 业绩比较基准','basics',{'table_name': 'fund_basic', 'column': 'benchmark'}],
('status','None','FD'):	['基金基本信息 - 存续状态D摘牌 I发行 L已上市','basics',{'table_name': 'fund_basic', 'column': 'status'}],
('invest_type','None','FD'):	['基金基本信息 - 投资风格','basics',{'table_name': 'fund_basic', 'column': 'invest_type'}],
('type','None','FD'):	['基金基本信息 - 基金类型','basics',{'table_name': 'fund_basic', 'column': 'type'}],
('trustee','None','FD'):	['基金基本信息 - 受托人','basics',{'table_name': 'fund_basic', 'column': 'trustee'}],
('purc_startdate','None','FD'):	['基金基本信息 - 日常申购起始日','basics',{'table_name': 'fund_basic', 'column': 'purc_startdate'}],
('redm_startdate','None','FD'):	['基金基本信息 - 日常赎回起始日','basics',{'table_name': 'fund_basic', 'column': 'redm_startdate'}],
('market','None','FD'):	['基金基本信息 - E场内O场外','basics',{'table_name': 'fund_basic', 'column': 'market'}],
('symbol','None','FT'):	['期货基本信息 - 交易标识','basics',{'table_name': 'future_basic', 'column': 'symbol'}],
('exchange','None','FT'):	['期货基本信息 - 交易市场','basics',{'table_name': 'future_basic', 'column': 'exchange'}],
('name','None','FT'):	['期货基本信息 - 中文简称','basics',{'table_name': 'future_basic', 'column': 'name'}],
('fut_code','None','FT'):	['期货基本信息 - 合约产品代码','basics',{'table_name': 'future_basic', 'column': 'fut_code'}],
('multiplier','None','FT'):	['期货基本信息 - 合约乘数(只适用于国债期货、指数期货)','basics',{'table_name': 'future_basic', 'column': 'multiplier'}],
('trade_unit','None','FT'):	['期货基本信息 - 交易计量单位','basics',{'table_name': 'future_basic', 'column': 'trade_unit'}],
('per_unit','None','FT'):	['期货基本信息 - 交易单位(每手)','basics',{'table_name': 'future_basic', 'column': 'per_unit'}],
('quote_unit','None','FT'):	['期货基本信息 - 报价单位','basics',{'table_name': 'future_basic', 'column': 'quote_unit'}],
('quote_unit_desc','None','FT'):	['期货基本信息 - 最小报价单位说明','basics',{'table_name': 'future_basic', 'column': 'quote_unit_desc'}],
('d_mode_desc','None','FT'):	['期货基本信息 - 交割方式说明','basics',{'table_name': 'future_basic', 'column': 'd_mode_desc'}],
('list_date','None','FT'):	['期货基本信息 - 上市日期','basics',{'table_name': 'future_basic', 'column': 'list_date'}],
('delist_date','None','FT'):	['期货基本信息 - 最后交易日期','basics',{'table_name': 'future_basic', 'column': 'delist_date'}],
('d_month','None','FT'):	['期货基本信息 - 交割月份','basics',{'table_name': 'future_basic', 'column': 'd_month'}],
('last_ddate','None','FT'):	['期货基本信息 - 最后交割日','basics',{'table_name': 'future_basic', 'column': 'last_ddate'}],
('trade_time_desc','None','FT'):	['期货基本信息 - 交易时间说明','basics',{'table_name': 'future_basic', 'column': 'trade_time_desc'}],
('exchange','None','OPT'):	['期权基本信息 - 交易市场','basics',{'table_name': 'opt_basic', 'column': 'exchange'}],
('name','None','OPT'):	['期权基本信息 - 合约名称','basics',{'table_name': 'opt_basic', 'column': 'name'}],
('per_unit','None','OPT'):	['期权基本信息 - 合约单位','basics',{'table_name': 'opt_basic', 'column': 'per_unit'}],
('opt_code','None','OPT'):	['期权基本信息 - 标的合约代码','basics',{'table_name': 'opt_basic', 'column': 'opt_code'}],
('opt_type','None','OPT'):	['期权基本信息 - 合约类型','basics',{'table_name': 'opt_basic', 'column': 'opt_type'}],
('call_put','None','OPT'):	['期权基本信息 - 期权类型','basics',{'table_name': 'opt_basic', 'column': 'call_put'}],
('exercise_type','None','OPT'):	['期权基本信息 - 行权方式','basics',{'table_name': 'opt_basic', 'column': 'exercise_type'}],
('exercise_price','None','OPT'):	['期权基本信息 - 行权价格','basics',{'table_name': 'opt_basic', 'column': 'exercise_price'}],
('s_month','str','OPT'):	['期权基本信息 - 结算月','basics',{'table_name': 'opt_basic', 'column': 's_month'}],
('maturity_date','None','OPT'):	['期权基本信息 - 到期日','basics',{'table_name': 'opt_basic', 'column': 'maturity_date'}],
('list_price','None','OPT'):	['期权基本信息 - 挂牌基准价','basics',{'table_name': 'opt_basic', 'column': 'list_price'}],
('list_date','None','OPT'):	['期权基本信息 - 开始交易日期','basics',{'table_name': 'opt_basic', 'column': 'list_date'}],
('delist_date','None','OPT'):	['期权基本信息 - 最后交易日期','basics',{'table_name': 'opt_basic', 'column': 'delist_date'}],
('last_edate','None','OPT'):	['期权基本信息 - 最后行权日期','basics',{'table_name': 'opt_basic', 'column': 'last_edate'}],
('last_ddate','None','OPT'):	['期权基本信息 - 最后交割日期','basics',{'table_name': 'opt_basic', 'column': 'last_ddate'}],
('quote_unit','None','OPT'):	['期权基本信息 - 报价单位','basics',{'table_name': 'opt_basic', 'column': 'quote_unit'}],
('min_price_chg','None','OPT'):	['期权基本信息 - 最小价格波幅','basics',{'table_name': 'opt_basic', 'column': 'min_price_chg'}],
('chairman','d','E'):	['公司信息 - 法人代表','basics',{'table_name': 'stock_company', 'column': 'chairman'}],
('manager','d','E'):	['公司信息 - 总经理','basics',{'table_name': 'stock_company', 'column': 'manager'}],
('secretary','d','E'):	['公司信息 - 董秘','basics',{'table_name': 'stock_company', 'column': 'secretary'}],
('reg_capital','d','E'):	['公司信息 - 注册资本','basics',{'table_name': 'stock_company', 'column': 'reg_capital'}],
('setup_date','d','E'):	['公司信息 - 注册日期','basics',{'table_name': 'stock_company', 'column': 'setup_date'}],
('province','d','E'):	['公司信息 - 所在省份','basics',{'table_name': 'stock_company', 'column': 'province'}],
('city','d','E'):	['公司信息 - 所在城市','basics',{'table_name': 'stock_company', 'column': 'city'}],
('introduction','d','E'):	['公司信息 - 公司介绍','basics',{'table_name': 'stock_company', 'column': 'introduction'}],
('website','d','E'):	['公司信息 - 公司主页','basics',{'table_name': 'stock_company', 'column': 'website'}],
('email','d','E'):	['公司信息 - 电子邮件','basics',{'table_name': 'stock_company', 'column': 'email'}],
('office','d','E'):	['公司信息 - 办公室','basics',{'table_name': 'stock_company', 'column': 'office'}],
('employees','d','E'):	['公司信息 - 员工人数','basics',{'table_name': 'stock_company', 'column': 'employees'}],
('main_business','d','E'):	['公司信息 - 主要业务及产品','basics',{'table_name': 'stock_company', 'column': 'main_business'}],
('business_scope','d','E'):	['公司信息 - 经营范围','basics',{'table_name': 'stock_company', 'column': 'business_scope'}],
# ('managers_name','d','E'):	['公司高管信息 - 高管姓名','event_multi_stat',{'table_name': 'stk_managers', 'column': 'name', 'id_index': 'name', 'start_col': 'begin_date', 'end_col': 'end_date', ''}],
('managers_gender','d','E'):	['公司高管信息 - 性别','event_multi_stat',{'table_name': 'stk_managers', 'column': 'gender', 'id_index': 'name', 'start_col': 'begin_date', 'end_col': 'end_date'}],
('managers_lev','d','E'):	['公司高管信息 - 岗位类别','event_multi_stat',{'table_name': 'stk_managers', 'column': 'lev', 'id_index': 'name', 'start_col': 'begin_date', 'end_col': 'end_date'}],
('manager_title','d','E'):	['公司高管信息 - 岗位','event_multi_stat',{'table_name': 'stk_managers', 'column': 'title', 'id_index': 'name', 'start_col': 'begin_date', 'end_col': 'end_date'}],
('managers_edu','d','E'):	['公司高管信息 - 学历','event_multi_stat',{'table_name': 'stk_managers', 'column': 'edu', 'id_index': 'name', 'start_col': 'begin_date', 'end_col': 'end_date'}],
('managers_national','d','E'):	['公司高管信息 - 国籍','event_multi_stat',{'table_name': 'stk_managers', 'column': 'national', 'id_index': 'name', 'start_col': 'begin_date', 'end_col': 'end_date'}],
('managers_birthday','d','E'):	['公司高管信息 - 出生年月','event_multi_stat',{'table_name': 'stk_managers', 'column': 'birthday', 'id_index': 'name', 'start_col': 'begin_date', 'end_col': 'end_date'}],
('managers_resume','d','E'):	['公司高管信息 - 个人简历','event_multi_stat',{'table_name': 'stk_managers', 'column': 'resume', 'id_index': 'name', 'start_col': 'begin_date', 'end_col': 'end_date'}],
# ('manager_salary_name','d','E'):	['管理层薪酬 - 姓名','direct',{'table_name': 'stk_rewards', 'column': 'name'}],
# ('manager_salary_title','d','E'):	['管理层薪酬 - 职务','direct',{'table_name': 'stk_rewards', 'column': 'title'}],
# ('reward','d','E'):	['管理层薪酬 - 报酬','direct',{'table_name': 'stk_rewards', 'column': 'reward'}],
# ('hold_vol','d','E'):	['管理层薪酬 - 持股数','direct',{'table_name': 'stk_rewards', 'column': 'hold_vol'}],
('ipo_date','d','E'):	['新股上市信息 - 上网发行日期','basics',{'table_name': 'new_share', 'column': 'ipo_date'}],
('issue_date','d','E'):	['新股上市信息 - 上市日期','basics',{'table_name': 'new_share', 'column': 'issue_date'}],
('IPO_amount','d','E'):	['新股上市信息 - 发行总量（万股）','basics',{'table_name': 'new_share', 'column': 'amount'}],
('market_amount','d','E'):	['新股上市信息 - 上网发行总量（万股）','basics',{'table_name': 'new_share', 'column': 'market_amount'}],
('initial_price','d','E'):	['新股上市信息 - 发行价格','basics',{'table_name': 'new_share', 'column': 'price'}],
('initial_pe','d','E'):	['新股上市信息 - 发行市盈率','basics',{'table_name': 'new_share', 'column': 'pe'}],
('limit_amount','d','E'):	['新股上市信息 - 个人申购上限（万股）','basics',{'table_name': 'new_share', 'column': 'limit_amount'}],
('funds','d','E'):	['新股上市信息 - 募集资金（亿元）','basics',{'table_name': 'new_share', 'column': 'funds'}],
('ballot','d','E'):	['新股上市信息 - 中签率','basics',{'table_name': 'new_share', 'column': 'ballot'}],
('HK_top10_close','d','E'):	[' 港股通十大成交 - 收盘价','direct',{'table_name': 'HK_top10_stock', 'column': 'close'}],
('HK_top10_p_change','d','E'):	[' 港股通十大成交 - 涨跌幅','direct',{'table_name': 'HK_top10_stock', 'column': 'p_change'}],
('HK_top10_rank','d','E'):	[' 港股通十大成交 - 排名','direct',{'table_name': 'HK_top10_stock', 'column': 'rank'}],
('HK_top10_amount','d','E'):	[' 港股通十大成交 - 累计成交额（元）','direct',{'table_name': 'HK_top10_stock', 'column': 'amount'}],
('HK_top10_net_amount','d','E'):	[' 港股通十大成交 - 净买入金额（元）','direct',{'table_name': 'HK_top10_stock', 'column': 'net_amount'}],
('HK_top10_sh_amount','d','E'):	[' 港股通十大成交 - 沪市成交额（元）','direct',{'table_name': 'HK_top10_stock', 'column': 'sh_amount'}],
('HK_top10_sh_net_amount','d','E'):	[' 港股通十大成交 - 沪市净买入额（元）','direct',{'table_name': 'HK_top10_stock', 'column': 'sh_net_amount'}],
('HK_top10_sh_buy','d','E'):	[' 港股通十大成交 - 沪市买入金额（元）','direct',{'table_name': 'HK_top10_stock', 'column': 'sh_buy'}],
('HK_top10_sh_sell','d','E'):	[' 港股通十大成交 - 沪市卖出金额（元）','direct',{'table_name': 'HK_top10_stock', 'column': 'sh_sell'}],
('HK_top10_sz_amount','d','E'):	[' 港股通十大成交 - 深市成交金额（元）','direct',{'table_name': 'HK_top10_stock', 'column': 'sz_amount'}],
('HK_top10_sz_net_amount','d','E'):	[' 港股通十大成交 - 深市净买入额（元）','direct',{'table_name': 'HK_top10_stock', 'column': 'sz_net_amount'}],
('HK_top10_sh_buy','d','E'):	[' 港股通十大成交 - 深市净买入金额（元）','direct',{'table_name': 'HK_top10_stock', 'column': 'sz_buy'}],
('HK_top10_sh_sell','d','E'):	[' 港股通十大成交 - 深市净买入金额（元）','direct',{'table_name': 'HK_top10_stock', 'column': 'sz_sell'}],
('open:%','d','E'):	['股票日K线 - 复权开盘价-b:后复权f:前复权','adjustment',{'table_name': 'stock_daily', 'column': 'open', 'adj_table': 'stock_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('high:%','d','E'):	['股票日K线 - 复权最高价-b:后复权f:前复权','adjustment',{'table_name': 'stock_daily', 'column': 'high', 'adj_table': 'stock_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('low:%','d','E'):	['股票日K线 - 复权最低价-b:后复权f:前复权','adjustment',{'table_name': 'stock_daily', 'column': 'low', 'adj_table': 'stock_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('close:%','d','E'):	['股票日K线 - 复权收盘价-b:后复权f:前复权','adjustment',{'table_name': 'stock_daily', 'column': 'close', 'adj_table': 'stock_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('open','d','E'):	['股票日K线 - 开盘价','direct',{'table_name': 'stock_daily', 'column': 'open'}],
('high','d','E'):	['股票日K线 - 最高价','direct',{'table_name': 'stock_daily', 'column': 'high'}],
('low','d','E'):	['股票日K线 - 最低价','direct',{'table_name': 'stock_daily', 'column': 'low'}],
('close','d','E'):	['股票日K线 - 收盘价','direct',{'table_name': 'stock_daily', 'column': 'close'}],
('vol','d','E'):	['股票日K线 - 成交量 （手）','direct',{'table_name': 'stock_daily', 'column': 'vol'}],
('amount','d','E'):	['股票日K线 - 成交额 （千元）','direct',{'table_name': 'stock_daily', 'column': 'amount'}],
('open:%','w','E'):	['股票周K线 - 复权开盘价-b:后复权f:前复权','adjustment',{'table_name': 'stock_weekly', 'column': 'open', 'adj_table': 'stock_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('high:%','w','E'):	['股票周K线 - 复权最高价-b:后复权f:前复权','adjustment',{'table_name': 'stock_weekly', 'column': 'high', 'adj_table': 'stock_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('low:%','w','E'):	['股票周K线 - 复权最低价-b:后复权f:前复权','adjustment',{'table_name': 'stock_weekly', 'column': 'low', 'adj_table': 'stock_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('close:%','w','E'):	['股票周K线 - 复权收盘价-b:后复权f:前复权','adjustment',{'table_name': 'stock_weekly', 'column': 'close', 'adj_table': 'stock_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('open','w','E'):	['股票周K线 - 开盘价','direct',{'table_name': 'stock_weekly', 'column': 'open'}],
('high','w','E'):	['股票周K线 - 最高价','direct',{'table_name': 'stock_weekly', 'column': 'high'}],
('low','w','E'):	['股票周K线 - 最低价','direct',{'table_name': 'stock_weekly', 'column': 'low'}],
('close','w','E'):	['股票周K线 - 收盘价','direct',{'table_name': 'stock_weekly', 'column': 'close'}],
('vol','w','E'):	['股票周K线 - 成交量 （手）','direct',{'table_name': 'stock_weekly', 'column': 'vol'}],
('amount','w','E'):	['股票周K线 - 成交额 （千元）','direct',{'table_name': 'stock_weekly', 'column': 'amount'}],
('open:%','m','E'):	['股票月K线 - 复权开盘价-b:后复权f:前复权','adjustment',{'table_name': 'stock_monthly', 'column': 'open', 'adj_table': 'stock_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('high:%','m','E'):	['股票月K线 - 复权最高价-b:后复权f:前复权','adjustment',{'table_name': 'stock_monthly', 'column': 'high', 'adj_table': 'stock_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('low:%','m','E'):	['股票月K线 - 复权最低价-b:后复权f:前复权','adjustment',{'table_name': 'stock_monthly', 'column': 'low', 'adj_table': 'stock_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('close:%','m','E'):	['股票月K线 - 复权收盘价-b:后复权f:前复权','adjustment',{'table_name': 'stock_monthly', 'column': 'close', 'adj_table': 'stock_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('open','m','E'):	['股票月K线 - 开盘价','direct',{'table_name': 'stock_monthly', 'column': 'open'}],
('high','m','E'):	['股票月K线 - 最高价','direct',{'table_name': 'stock_monthly', 'column': 'high'}],
('low','m','E'):	['股票月K线 - 最低价','direct',{'table_name': 'stock_monthly', 'column': 'low'}],
('close','m','E'):	['股票月K线 - 收盘价','direct',{'table_name': 'stock_monthly', 'column': 'close'}],
('vol','m','E'):	['股票月K线 - 成交量 （手）','direct',{'table_name': 'stock_monthly', 'column': 'vol'}],
('amount','m','E'):	['股票月K线 - 成交额 （千元）','direct',{'table_name': 'stock_monthly', 'column': 'amount'}],
('open:%','1min','E'):	['股票60秒K线 - 复权开盘价-b:后复权f:前复权','adjustment',{'table_name': 'stock_1min', 'column': 'open', 'adj_table': 'stock_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('high:%','1min','E'):	['股票60秒K线 - 复权最高价-b:后复权f:前复权','adjustment',{'table_name': 'stock_1min', 'column': 'high', 'adj_table': 'stock_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('low:%','1min','E'):	['股票60秒K线 - 复权最低价-b:后复权f:前复权','adjustment',{'table_name': 'stock_1min', 'column': 'low', 'adj_table': 'stock_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('close:%','1min','E'):	['股票60秒K线 - 复权收盘价-b:后复权f:前复权','adjustment',{'table_name': 'stock_1min', 'column': 'close', 'adj_table': 'stock_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('open','1min','E'):	['股票60秒K线 - 开盘价','direct',{'table_name': 'stock_1min', 'column': 'open'}],
('high','1min','E'):	['股票60秒K线 - 最高价','direct',{'table_name': 'stock_1min', 'column': 'high'}],
('low','1min','E'):	['股票60秒K线 - 最低价','direct',{'table_name': 'stock_1min', 'column': 'low'}],
('close','1min','E'):	['股票60秒K线 - 收盘价','direct',{'table_name': 'stock_1min', 'column': 'close'}],
('vol','1min','E'):	['股票60秒K线 - 成交量 （手）','direct',{'table_name': 'stock_1min', 'column': 'vol'}],
('amount','1min','E'):	['股票60秒K线 - 成交额 （千元）','direct',{'table_name': 'stock_1min', 'column': 'amount'}],
('open:%','5min','E'):	['股票5分钟K线 - 复权开盘价-b:后复权f:前复权','adjustment',{'table_name': 'stock_5min', 'column': 'open', 'adj_table': 'stock_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('high:%','5min','E'):	['股票5分钟K线 - 复权最高价-b:后复权f:前复权','adjustment',{'table_name': 'stock_5min', 'column': 'high', 'adj_table': 'stock_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('low:%','5min','E'):	['股票5分钟K线 - 复权最低价-b:后复权f:前复权','adjustment',{'table_name': 'stock_5min', 'column': 'low', 'adj_table': 'stock_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('close:%','5min','E'):	['股票5分钟K线 - 复权收盘价-b:后复权f:前复权','adjustment',{'table_name': 'stock_5min', 'column': 'close', 'adj_table': 'stock_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('open','5min','E'):	['股票5分钟K线 - 开盘价','direct',{'table_name': 'stock_5min', 'column': 'open'}],
('high','5min','E'):	['股票5分钟K线 - 最高价','direct',{'table_name': 'stock_5min', 'column': 'high'}],
('low','5min','E'):	['股票5分钟K线 - 最低价','direct',{'table_name': 'stock_5min', 'column': 'low'}],
('close','5min','E'):	['股票5分钟K线 - 收盘价','direct',{'table_name': 'stock_5min', 'column': 'close'}],
('vol','5min','E'):	['股票5分钟K线 - 成交量 （手）','direct',{'table_name': 'stock_5min', 'column': 'vol'}],
('amount','5min','E'):	['股票5分钟K线 - 成交额 （千元）','direct',{'table_name': 'stock_5min', 'column': 'amount'}],
('open:%','15min','E'):	['股票15分钟K线 - 复权开盘价-b:后复权f:前复权','adjustment',{'table_name': 'stock_15min', 'column': 'open', 'adj_table': 'stock_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('high:%','15min','E'):	['股票15分钟K线 - 复权最高价-b:后复权f:前复权','adjustment',{'table_name': 'stock_15min', 'column': 'high', 'adj_table': 'stock_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('low:%','15min','E'):	['股票15分钟K线 - 复权最低价-b:后复权f:前复权','adjustment',{'table_name': 'stock_15min', 'column': 'low', 'adj_table': 'stock_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('close:%','15min','E'):	['股票15分钟K线 - 复权收盘价-b:后复权f:前复权','adjustment',{'table_name': 'stock_15min', 'column': 'close', 'adj_table': 'stock_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('open','15min','E'):	['股票15分钟K线 - 开盘价','direct',{'table_name': 'stock_15min', 'column': 'open'}],
('high','15min','E'):	['股票15分钟K线 - 最高价','direct',{'table_name': 'stock_15min', 'column': 'high'}],
('low','15min','E'):	['股票15分钟K线 - 最低价','direct',{'table_name': 'stock_15min', 'column': 'low'}],
('close','15min','E'):	['股票15分钟K线 - 收盘价','direct',{'table_name': 'stock_15min', 'column': 'close'}],
('vol','15min','E'):	['股票15分钟K线 - 成交量 （手）','direct',{'table_name': 'stock_15min', 'column': 'vol'}],
('amount','15min','E'):	['股票15分钟K线 - 成交额 （千元）','direct',{'table_name': 'stock_15min', 'column': 'amount'}],
('open:%','30min','E'):	['股票30分钟K线 - 复权开盘价-b:后复权f:前复权','adjustment',{'table_name': 'stock_30min', 'column': 'open', 'adj_table': 'stock_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('high:%','30min','E'):	['股票30分钟K线 - 复权最高价-b:后复权f:前复权','adjustment',{'table_name': 'stock_30min', 'column': 'high', 'adj_table': 'stock_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('low:%','30min','E'):	['股票30分钟K线 - 复权最低价-b:后复权f:前复权','adjustment',{'table_name': 'stock_30min', 'column': 'low', 'adj_table': 'stock_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('close:%','30min','E'):	['股票30分钟K线 - 复权收盘价-b:后复权f:前复权','adjustment',{'table_name': 'stock_30min', 'column': 'close', 'adj_table': 'stock_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('open','30min','E'):	['股票30分钟K线 - 开盘价','direct',{'table_name': 'stock_30min', 'column': 'open'}],
('high','30min','E'):	['股票30分钟K线 - 最高价','direct',{'table_name': 'stock_30min', 'column': 'high'}],
('low','30min','E'):	['股票30分钟K线 - 最低价','direct',{'table_name': 'stock_30min', 'column': 'low'}],
('close','30min','E'):	['股票30分钟K线 - 收盘价','direct',{'table_name': 'stock_30min', 'column': 'close'}],
('vol','30min','E'):	['股票30分钟K线 - 成交量 （手）','direct',{'table_name': 'stock_30min', 'column': 'vol'}],
('amount','30min','E'):	['股票30分钟K线 - 成交额 （千元）','direct',{'table_name': 'stock_30min', 'column': 'amount'}],
('open:%','h','E'):	['股票小时K线 - 复权开盘价-b:后复权f:前复权','adjustment',{'table_name': 'stock_hourly', 'column': 'open', 'adj_table': 'stock_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('high:%','h','E'):	['股票小时K线 - 复权最高价-b:后复权f:前复权','adjustment',{'table_name': 'stock_hourly', 'column': 'high', 'adj_table': 'stock_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('low:%','h','E'):	['股票小时K线 - 复权最低价-b:后复权f:前复权','adjustment',{'table_name': 'stock_hourly', 'column': 'low', 'adj_table': 'stock_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('close:%','h','E'):	['股票小时K线 - 复权收盘价-b:后复权f:前复权','adjustment',{'table_name': 'stock_hourly', 'column': 'close', 'adj_table': 'stock_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('open','h','E'):	['股票小时K线 - 开盘价','direct',{'table_name': 'stock_hourly', 'column': 'open'}],
('high','h','E'):	['股票小时K线 - 最高价','direct',{'table_name': 'stock_hourly', 'column': 'high'}],
('low','h','E'):	['股票小时K线 - 最低价','direct',{'table_name': 'stock_hourly', 'column': 'low'}],
('close','h','E'):	['股票小时K线 - 收盘价','direct',{'table_name': 'stock_hourly', 'column': 'close'}],
('vol','h','E'):	['股票小时K线 - 成交量 （手）','direct',{'table_name': 'stock_hourly', 'column': 'vol'}],
('amount','h','E'):	['股票小时K线 - 成交额 （千元）','direct',{'table_name': 'stock_hourly', 'column': 'amount'}],
('ths_open','d','IDX'):	['同花顺指数日K线 - 开盘价','direct',{'table_name': 'ths_index_daily', 'column': 'open'}],
('ths_high','d','IDX'):	['同花顺指数日K线 - 最高价','direct',{'table_name': 'ths_index_daily', 'column': 'high'}],
('ths_low','d','IDX'):	['同花顺指数日K线 - 最低价','direct',{'table_name': 'ths_index_daily', 'column': 'low'}],
('ths_close','d','IDX'):	['同花顺指数日K线 - 收盘价','direct',{'table_name': 'ths_index_daily', 'column': 'close'}],
('ths_change','d','IDX'):	['同花顺指数日K线 - 最低价','direct',{'table_name': 'ths_index_daily', 'column': 'change'}],
('ths_avg_price','d','IDX'):	['同花顺指数日K线 - 平均价','direct',{'table_name': 'ths_index_daily', 'column': 'avg_price'}],
('ths_pct_change','d','IDX'):	['同花顺指数日K线 - 涨跌幅','direct',{'table_name': 'ths_index_daily', 'column': 'pct_change'}],
('ths_vol','d','IDX'):	['同花顺指数日K线 - 成交量 （万股）','direct',{'table_name': 'ths_index_daily', 'column': 'vol'}],
('ths_turnover','d','IDX'):	['同花顺指数日K线 - 换手率','direct',{'table_name': 'ths_index_daily', 'column': 'turnover_rate'}],
('ths_pe','d','IDX'):	['同花顺指数日K线 - 市盈率','direct',{'table_name': 'ths_index_daily', 'column': 'pe'}],
('ths_pb','d','IDX'):	['同花顺指数日K线 - 市净率','direct',{'table_name': 'ths_index_daily', 'column': 'pb'}],
('ths_float_mv','d','IDX'):	['同花顺指数日K线 - 流通市值 （万元）','direct',{'table_name': 'ths_index_daily', 'column': 'float_mv'}],
('ths_total_mv','d','IDX'):	['同花顺指数日K线 - 总市值 （万元）','direct',{'table_name': 'ths_index_daily', 'column': 'total_mv'}],
('ci_open','d','IDX'):	['中信指数日K线 - 开盘价','direct',{'table_name': 'ci_index_daily', 'column': 'open'}],
('ci_high','d','IDX'):	['中信指数日K线 - 最高价','direct',{'table_name': 'ci_index_daily', 'column': 'high'}],
('ci_low','d','IDX'):	['中信指数日K线 - 最低价','direct',{'table_name': 'ci_index_daily', 'column': 'low'}],
('ci_close','d','IDX'):	['中信指数日K线 - 收盘价','direct',{'table_name': 'ci_index_daily', 'column': 'close'}],
('ci_change','d','IDX'):	['中信指数日K线 - 涨跌额','direct',{'table_name': 'ci_index_daily', 'column': 'change'}],
('ci_pct_change','d','IDX'):	['中信指数日K线 - 涨跌幅','direct',{'table_name': 'ci_index_daily', 'column': 'pct_change'}],
('ci_vol','d','IDX'):	['中信指数日K线 - 成交量 （万股）','direct',{'table_name': 'ci_index_daily', 'column': 'vol'}],
('ci_amount','d','IDX'):	['中信指数日K线 - 成交额 （万元）','direct',{'table_name': 'ci_index_daily', 'column': 'amount'}],
('ci_pre_close','d','IDX'):	['中信指数日K线 - 昨日收盘点位','direct',{'table_name': 'ci_index_daily', 'column': 'pre_close'}],
('sw_open','d','IDX'):	['申万指数日K线 - 开盘价','direct',{'table_name': 'sw_index_daily', 'column': 'open'}],
('sw_high','d','IDX'):	['申万指数日K线 - 最高价','direct',{'table_name': 'sw_index_daily', 'column': 'high'}],
('sw_low','d','IDX'):	['申万指数日K线 - 最低价','direct',{'table_name': 'sw_index_daily', 'column': 'low'}],
('sw_close','d','IDX'):	['申万指数日K线 - 收盘价','direct',{'table_name': 'sw_index_daily', 'column': 'close'}],
('sw_change','d','IDX'):	['申万指数日K线 - 涨跌额','direct',{'table_name': 'sw_index_daily', 'column': 'change'}],
('sw_pct_change','d','IDX'):	['申万指数日K线 - 涨跌幅','direct',{'table_name': 'sw_index_daily', 'column': 'pct_change'}],
('sw_vol','d','IDX'):	['申万指数日K线 - 成交量 （万股）','direct',{'table_name': 'sw_index_daily', 'column': 'vol'}],
('sw_amount','d','IDX'):	['申万指数日K线 - 成交额 （万元）','direct',{'table_name': 'sw_index_daily', 'column': 'amount'}],
('sw_pe','d','IDX'):	['申万指数日K线 - 市盈率','direct',{'table_name': 'sw_index_daily', 'column': 'pe'}],
('sw_pb','d','IDX'):	['申万指数日K线 - 市净率','direct',{'table_name': 'sw_index_daily', 'column': 'pb'}],
('sw_float_mv','d','IDX'):	['申万指数日K线 - 流通市值 （万元）','direct',{'table_name': 'sw_index_daily', 'column': 'float_mv'}],
('sw_total_mv','d','IDX'):	['申万指数日K线 - 总市值 （万元）','direct',{'table_name': 'sw_index_daily', 'column': 'total_mv'}],
('g_index_open','d','IDX'):	['全球指数日K线行情 - 开盘价','direct',{'table_name': 'global_index_daily', 'column': 'open'}],
('g_index_high','d','IDX'):	['全球指数日K线行情 - 最高价','direct',{'table_name': 'global_index_daily', 'column': 'high'}],
('g_index_low','d','IDX'):	['全球指数日K线行情 - 最低价','direct',{'table_name': 'global_index_daily', 'column': 'low'}],
('g_index_close','d','IDX'):	[' 全球指数日K线行情 - 收盘价','direct',{'table_name': 'global_index_daily', 'column': 'close'}],
('g_index_change','d','IDX'):	['全球指数日K线行情 - 最低价','direct',{'table_name': 'global_index_daily', 'column': 'change'}],
('g_index_pct_change','d','IDX'):	['全球指数日K线行情 - 收盘价','direct',{'table_name': 'global_index_daily', 'column': 'pct_chg'}],
('g_index_vol','d','IDX'):	['全球指数日K线行情 - 成交量','direct',{'table_name': 'global_index_daily', 'column': 'vol'}],
('g_index_amount','d','IDX'):	['全球指数日K线行情 - 成交额','direct',{'table_name': 'global_index_daily', 'column': 'amount'}],
('g_index_pre_close','d','IDX'):	['全球指数日K线行情 - 昨日收盘价','direct',{'table_name': 'global_index_daily', 'column': 'pre_close'}],
('g_index_swing','d','IDX'):	['全球指数日K线行情 - 振幅','direct',{'table_name': 'global_index_daily', 'column': 'swing'}],
('open','d','IDX'):	['指数日K线 - 开盘价','direct',{'table_name': 'index_daily', 'column': 'open'}],
('high','d','IDX'):	['指数日K线 - 最高价','direct',{'table_name': 'index_daily', 'column': 'high'}],
('low','d','IDX'):	['指数日K线 - 最低价','direct',{'table_name': 'index_daily', 'column': 'low'}],
('close','d','IDX'):	['指数日K线 - 收盘价','direct',{'table_name': 'index_daily', 'column': 'close'}],
('vol','d','IDX'):	['指数日K线 - 成交量 （手）','direct',{'table_name': 'index_daily', 'column': 'vol'}],
('amount','d','IDX'):	['指数日K线 - 成交额 （千元）','direct',{'table_name': 'index_daily', 'column': 'amount'}],
('open','w','IDX'):	['指数周K线 - 开盘价','direct',{'table_name': 'index_weekly', 'column': 'open'}],
('high','w','IDX'):	['指数周K线 - 最高价','direct',{'table_name': 'index_weekly', 'column': 'high'}],
('low','w','IDX'):	['指数周K线 - 最低价','direct',{'table_name': 'index_weekly', 'column': 'low'}],
('close','w','IDX'):	['指数周K线 - 收盘价','direct',{'table_name': 'index_weekly', 'column': 'close'}],
('vol','w','IDX'):	['指数周K线 - 成交量 （手）','direct',{'table_name': 'index_weekly', 'column': 'vol'}],
('amount','w','IDX'):	['指数周K线 - 成交额 （千元）','direct',{'table_name': 'index_weekly', 'column': 'amount'}],
('open','m','IDX'):	['指数月K线 - 开盘价','direct',{'table_name': 'index_monthly', 'column': 'open'}],
('high','m','IDX'):	['指数月K线 - 最高价','direct',{'table_name': 'index_monthly', 'column': 'high'}],
('low','m','IDX'):	['指数月K线 - 最低价','direct',{'table_name': 'index_monthly', 'column': 'low'}],
('close','m','IDX'):	['指数月K线 - 收盘价','direct',{'table_name': 'index_monthly', 'column': 'close'}],
('vol','m','IDX'):	['指数月K线 - 成交量 （手）','direct',{'table_name': 'index_monthly', 'column': 'vol'}],
('amount','m','IDX'):	['指数月K线 - 成交额 （千元）','direct',{'table_name': 'index_monthly', 'column': 'amount'}],
('open','1min','IDX'):	['指数60秒K线 - 开盘价','direct',{'table_name': 'index_1min', 'column': 'open'}],
('high','1min','IDX'):	['指数60秒K线 - 最高价','direct',{'table_name': 'index_1min', 'column': 'high'}],
('low','1min','IDX'):	['指数60秒K线 - 最低价','direct',{'table_name': 'index_1min', 'column': 'low'}],
('close','1min','IDX'):	['指数60秒K线 - 收盘价','direct',{'table_name': 'index_1min', 'column': 'close'}],
('vol','1min','IDX'):	['指数60秒K线 - 成交量 （手）','direct',{'table_name': 'index_1min', 'column': 'vol'}],
('amount','1min','IDX'):	['指数60秒K线 - 成交额 （千元）','direct',{'table_name': 'index_1min', 'column': 'amount'}],
('open','5min','IDX'):	['指数5分钟K线 - 开盘价','direct',{'table_name': 'index_5min', 'column': 'open'}],
('high','5min','IDX'):	['指数5分钟K线 - 最高价','direct',{'table_name': 'index_5min', 'column': 'high'}],
('low','5min','IDX'):	['指数5分钟K线 - 最低价','direct',{'table_name': 'index_5min', 'column': 'low'}],
('close','5min','IDX'):	['指数5分钟K线 - 收盘价','direct',{'table_name': 'index_5min', 'column': 'close'}],
('vol','5min','IDX'):	['指数5分钟K线 - 成交量 （手）','direct',{'table_name': 'index_5min', 'column': 'vol'}],
('amount','5min','IDX'):	['指数5分钟K线 - 成交额 （千元）','direct',{'table_name': 'index_5min', 'column': 'amount'}],
('open','15min','IDX'):	['指数15分钟K线 - 开盘价','direct',{'table_name': 'index_15min', 'column': 'open'}],
('high','15min','IDX'):	['指数15分钟K线 - 最高价','direct',{'table_name': 'index_15min', 'column': 'high'}],
('low','15min','IDX'):	['指数15分钟K线 - 最低价','direct',{'table_name': 'index_15min', 'column': 'low'}],
('close','15min','IDX'):	['指数15分钟K线 - 收盘价','direct',{'table_name': 'index_15min', 'column': 'close'}],
('vol','15min','IDX'):	['指数15分钟K线 - 成交量 （手）','direct',{'table_name': 'index_15min', 'column': 'vol'}],
('amount','15min','IDX'):	['指数15分钟K线 - 成交额 （千元）','direct',{'table_name': 'index_15min', 'column': 'amount'}],
('open','30min','IDX'):	['指数30分钟K线 - 开盘价','direct',{'table_name': 'index_30min', 'column': 'open'}],
('high','30min','IDX'):	['指数30分钟K线 - 最高价','direct',{'table_name': 'index_30min', 'column': 'high'}],
('low','30min','IDX'):	['指数30分钟K线 - 最低价','direct',{'table_name': 'index_30min', 'column': 'low'}],
('close','30min','IDX'):	['指数30分钟K线 - 收盘价','direct',{'table_name': 'index_30min', 'column': 'close'}],
('vol','30min','IDX'):	['指数30分钟K线 - 成交量 （手）','direct',{'table_name': 'index_30min', 'column': 'vol'}],
('amount','30min','IDX'):	['指数30分钟K线 - 成交额 （千元）','direct',{'table_name': 'index_30min', 'column': 'amount'}],
('open','h','IDX'):	['指数小时K线 - 开盘价','direct',{'table_name': 'index_hourly', 'column': 'open'}],
('high','h','IDX'):	['指数小时K线 - 最高价','direct',{'table_name': 'index_hourly', 'column': 'high'}],
('low','h','IDX'):	['指数小时K线 - 最低价','direct',{'table_name': 'index_hourly', 'column': 'low'}],
('close','h','IDX'):	['指数小时K线 - 收盘价','direct',{'table_name': 'index_hourly', 'column': 'close'}],
('vol','h','IDX'):	['指数小时K线 - 成交量 （手）','direct',{'table_name': 'index_hourly', 'column': 'vol'}],
('amount','h','IDX'):	['指数小时K线 - 成交额 （千元）','direct',{'table_name': 'index_hourly', 'column': 'amount'}],
('open','d','FT'):	['期货日K线 - 开盘价','direct',{'table_name': 'future_daily', 'column': 'open'}],
('high','d','FT'):	['期货日K线 - 最高价','direct',{'table_name': 'future_daily', 'column': 'high'}],
('low','d','FT'):	['期货日K线 - 最低价','direct',{'table_name': 'future_daily', 'column': 'low'}],
('close','d','FT'):	['期货日K线 - 收盘价','direct',{'table_name': 'future_daily', 'column': 'close'}],
('vol','d','FT'):	['期货日K线 - 成交量 （手）','direct',{'table_name': 'future_daily', 'column': 'vol'}],
('amount','d','FT'):	['期货日K线 - 成交额 （千元）','direct',{'table_name': 'future_daily', 'column': 'amount'}],
('settle','d','FT'):	['期货日K线 - 结算价','direct',{'table_name': 'future_daily', 'column': 'settle'}],
('close_chg','d','FT'):	['期货日K线 - 收盘价涨跌','direct',{'table_name': 'future_daily', 'column': 'change1'}],
('settle_chg','d','FT'):	['期货日K线 - 结算价涨跌','direct',{'table_name': 'future_daily', 'column': 'change2'}],
('oi','d','FT'):	['期货日K线 - 持仓量（手）','direct',{'table_name': 'future_daily', 'column': 'oi'}],
('oi_chg','d','FT'):	['期货日K线 - 持仓量变化','direct',{'table_name': 'future_daily', 'column': 'oi_chg'}],
('delf_settle','d','FT'):	['期货日K线 - 交割结算价','direct',{'table_name': 'future_daily', 'column': 'delv_settle'}],
('open','w','FT'):	['期货周K线 - 开盘价','direct',{'table_name': 'future_weekly', 'column': 'open'}],
('high','w','FT'):	['期货周K线 - 最高价','direct',{'table_name': 'future_weekly', 'column': 'high'}],
('low','w','FT'):	['期货周K线 - 最低价','direct',{'table_name': 'future_weekly', 'column': 'low'}],
('close','w','FT'):	['期货周K线 - 收盘价','direct',{'table_name': 'future_weekly', 'column': 'close'}],
('vol','w','FT'):	['期货周K线 - 成交量（手）','direct',{'table_name': 'future_weekly', 'column': 'vol'}],
('amount','w','FT'):	['期货周K线 - 成交额 （千元）','direct',{'table_name': 'future_weekly', 'column': 'amount'}],
('settle','w','FT'):	['期货周K线 - 结算价','direct',{'table_name': 'future_weekly', 'column': 'settle'}],
('close_chg','w','FT'):	['期货周K线 - 收盘价涨跌','direct',{'table_name': 'future_weekly', 'column': 'change1'}],
('settle_chg','w','FT'):	['期货周K线 - 结算价涨跌','direct',{'table_name': 'future_weekly', 'column': 'change2'}],
('oi','w','FT'):	['期货周K线 - 持仓量（手）','direct',{'table_name': 'future_weekly', 'column': 'oi'}],
('oi_chg','w','FT'):	['期货周K线 - 持仓量变化','direct',{'table_name': 'future_weekly', 'column': 'oi_chg'}],
('delf_settle','w','FT'):	['期货周K线 - 交割结算价','direct',{'table_name': 'future_weekly', 'column': 'delv_settle'}],
('open','m','FT'):	['期货月K线 - 开盘价','direct',{'table_name': 'future_monthly', 'column': 'open'}],
('high','m','FT'):	['期货月K线 - 最高价','direct',{'table_name': 'future_monthly', 'column': 'high'}],
('low','m','FT'):	['期货月K线 - 最低价','direct',{'table_name': 'future_monthly', 'column': 'low'}],
('close','m','FT'):	['期货月K线 - 收盘价','direct',{'table_name': 'future_monthly', 'column': 'close'}],
('vol','m','FT'):	['期货月K线 - 成交量（手）','direct',{'table_name': 'future_monthly', 'column': 'vol'}],
('amount','m','FT'):	['期货月K线 - 成交额 （千元）','direct',{'table_name': 'future_monthly', 'column': 'amount'}],
('settle','m','FT'):	['期货月K线 - 结算价','direct',{'table_name': 'future_monthly', 'column': 'settle'}],
('close_chg','m','FT'):	['期货月K线 - 收盘价涨跌','direct',{'table_name': 'future_monthly', 'column': 'change1'}],
('settle_chg','m','FT'):	['期货月K线 - 结算价涨跌','direct',{'table_name': 'future_monthly', 'column': 'change2'}],
('oi','m','FT'):	['期货月K线 - 持仓量（手）','direct',{'table_name': 'future_monthly', 'column': 'oi'}],
('oi_chg','m','FT'):	['期货月K线 - 持仓量变化','direct',{'table_name': 'future_monthly', 'column': 'oi_chg'}],
('delf_settle','m','FT'):	['期货月K线 - 交割结算价','direct',{'table_name': 'future_monthly', 'column': 'delv_settle'}],
('open','1min','FT'):	['期货60秒K线 - 开盘价','direct',{'table_name': 'future_1min', 'column': 'open'}],
('high','1min','FT'):	['期货60秒K线 - 最高价','direct',{'table_name': 'future_1min', 'column': 'high'}],
('low','1min','FT'):	['期货60秒K线 - 最低价','direct',{'table_name': 'future_1min', 'column': 'low'}],
('close','1min','FT'):	['期货60秒K线 - 收盘价','direct',{'table_name': 'future_1min', 'column': 'close'}],
('vol','1min','FT'):	['期货60秒K线 - 成交量 （手）','direct',{'table_name': 'future_1min', 'column': 'vol'}],
('amount','1min','FT'):	['期货60秒K线 - 成交额 （千元）','direct',{'table_name': 'future_1min', 'column': 'amount'}],
('open','5min','FT'):	['期货5分钟K线 - 开盘价','direct',{'table_name': 'future_5min', 'column': 'open'}],
('high','5min','FT'):	['期货5分钟K线 - 最高价','direct',{'table_name': 'future_5min', 'column': 'high'}],
('low','5min','FT'):	['期货5分钟K线 - 最低价','direct',{'table_name': 'future_5min', 'column': 'low'}],
('close','5min','FT'):	['期货5分钟K线 - 收盘价','direct',{'table_name': 'future_5min', 'column': 'close'}],
('vol','5min','FT'):	['期货5分钟K线 - 成交量 （手）','direct',{'table_name': 'future_5min', 'column': 'vol'}],
('amount','5min','FT'):	['期货5分钟K线 - 成交额 （千元）','direct',{'table_name': 'future_5min', 'column': 'amount'}],
('open','15min','FT'):	['期货15分钟K线 - 开盘价','direct',{'table_name': 'future_15min', 'column': 'open'}],
('high','15min','FT'):	['期货15分钟K线 - 最高价','direct',{'table_name': 'future_15min', 'column': 'high'}],
('low','15min','FT'):	['期货15分钟K线 - 最低价','direct',{'table_name': 'future_15min', 'column': 'low'}],
('close','15min','FT'):	['期货15分钟K线 - 收盘价','direct',{'table_name': 'future_15min', 'column': 'close'}],
('vol','15min','FT'):	['期货15分钟K线 - 成交量 （手）','direct',{'table_name': 'future_15min', 'column': 'vol'}],
('amount','15min','FT'):	['期货15分钟K线 - 成交额 （千元）','direct',{'table_name': 'future_15min', 'column': 'amount'}],
('open','30min','FT'):	['期货30分钟K线 - 开盘价','direct',{'table_name': 'future_30min', 'column': 'open'}],
('high','30min','FT'):	['期货30分钟K线 - 最高价','direct',{'table_name': 'future_30min', 'column': 'high'}],
('low','30min','FT'):	['期货30分钟K线 - 最低价','direct',{'table_name': 'future_30min', 'column': 'low'}],
('close','30min','FT'):	['期货30分钟K线 - 收盘价','direct',{'table_name': 'future_30min', 'column': 'close'}],
('vol','30min','FT'):	['期货30分钟K线 - 成交量 （手）','direct',{'table_name': 'future_30min', 'column': 'vol'}],
('amount','30min','FT'):	['期货30分钟K线 - 成交额 （千元）','direct',{'table_name': 'future_30min', 'column': 'amount'}],
('open','h','FT'):	['期货小时K线 - 开盘价','direct',{'table_name': 'future_hourly', 'column': 'open'}],
('high','h','FT'):	['期货小时K线 - 最高价','direct',{'table_name': 'future_hourly', 'column': 'high'}],
('low','h','FT'):	['期货小时K线 - 最低价','direct',{'table_name': 'future_hourly', 'column': 'low'}],
('close','h','FT'):	['期货小时K线 - 收盘价','direct',{'table_name': 'future_hourly', 'column': 'close'}],
('vol','h','FT'):	['期货小时K线 - 成交量 （手）','direct',{'table_name': 'future_hourly', 'column': 'vol'}],
('amount','h','FT'):	['期货小时K线 - 成交额 （千元）','direct',{'table_name': 'future_hourly', 'column': 'amount'}],
('open','d','OPT'):	['期权日K线 - 开盘价','direct',{'table_name': 'options_daily', 'column': 'open'}],
('high','d','OPT'):	['期权日K线 - 最高价','direct',{'table_name': 'options_daily', 'column': 'high'}],
('low','d','OPT'):	['期权日K线 - 最低价','direct',{'table_name': 'options_daily', 'column': 'low'}],
('close','d','OPT'):	['期权日K线 - 收盘价','direct',{'table_name': 'options_daily', 'column': 'close'}],
('vol','d','OPT'):	['期权日K线 - 成交量 （手）','direct',{'table_name': 'options_daily', 'column': 'vol'}],
('amount','d','OPT'):	['期权日K线 - 成交额 （千元）','direct',{'table_name': 'options_daily', 'column': 'amount'}],
('open','1min','OPT'):	['期权60秒K线 - 开盘价','direct',{'table_name': 'options_1min', 'column': 'open'}],
('high','1min','OPT'):	['期权60秒K线 - 最高价','direct',{'table_name': 'options_1min', 'column': 'high'}],
('low','1min','OPT'):	['期权60秒K线 - 最低价','direct',{'table_name': 'options_1min', 'column': 'low'}],
('close','1min','OPT'):	['期权60秒K线 - 收盘价','direct',{'table_name': 'options_1min', 'column': 'close'}],
('vol','1min','OPT'):	['期权60秒K线 - 成交量 （手）','direct',{'table_name': 'options_1min', 'column': 'vol'}],
('amount','1min','OPT'):	['期权60秒K线 - 成交额 （千元）','direct',{'table_name': 'options_1min', 'column': 'amount'}],
('open','5min','OPT'):	['期权5分钟K线 - 开盘价','direct',{'table_name': 'options_5min', 'column': 'open'}],
('high','5min','OPT'):	['期权5分钟K线 - 最高价','direct',{'table_name': 'options_5min', 'column': 'high'}],
('low','5min','OPT'):	['期权5分钟K线 - 最低价','direct',{'table_name': 'options_5min', 'column': 'low'}],
('close','5min','OPT'):	['期权5分钟K线 - 收盘价','direct',{'table_name': 'options_5min', 'column': 'close'}],
('vol','5min','OPT'):	['期权5分钟K线 - 成交量 （手）','direct',{'table_name': 'options_5min', 'column': 'vol'}],
('amount','5min','OPT'):	['期权5分钟K线 - 成交额 （千元）','direct',{'table_name': 'options_5min', 'column': 'amount'}],
('open','15min','OPT'):	['期权15分钟K线 - 开盘价','direct',{'table_name': 'options_15min', 'column': 'open'}],
('high','15min','OPT'):	['期权15分钟K线 - 最高价','direct',{'table_name': 'options_15min', 'column': 'high'}],
('low','15min','OPT'):	['期权15分钟K线 - 最低价','direct',{'table_name': 'options_15min', 'column': 'low'}],
('close','15min','OPT'):	['期权15分钟K线 - 收盘价','direct',{'table_name': 'options_15min', 'column': 'close'}],
('vol','15min','OPT'):	['期权15分钟K线 - 成交量 （手）','direct',{'table_name': 'options_15min', 'column': 'vol'}],
('amount','15min','OPT'):	['期权15分钟K线 - 成交额 （千元）','direct',{'table_name': 'options_15min', 'column': 'amount'}],
('open','30min','OPT'):	['期权30分钟K线 - 开盘价','direct',{'table_name': 'options_30min', 'column': 'open'}],
('high','30min','OPT'):	['期权30分钟K线 - 最高价','direct',{'table_name': 'options_30min', 'column': 'high'}],
('low','30min','OPT'):	['期权30分钟K线 - 最低价','direct',{'table_name': 'options_30min', 'column': 'low'}],
('close','30min','OPT'):	['期权30分钟K线 - 收盘价','direct',{'table_name': 'options_30min', 'column': 'close'}],
('vol','30min','OPT'):	['期权30分钟K线 - 成交量 （手）','direct',{'table_name': 'options_30min', 'column': 'vol'}],
('amount','30min','OPT'):	['期权30分钟K线 - 成交额 （千元）','direct',{'table_name': 'options_30min', 'column': 'amount'}],
('open','h','OPT'):	['期权小时K线 - 开盘价','direct',{'table_name': 'options_hourly', 'column': 'open'}],
('high','h','OPT'):	['期权小时K线 - 最高价','direct',{'table_name': 'options_hourly', 'column': 'high'}],
('low','h','OPT'):	['期权小时K线 - 最低价','direct',{'table_name': 'options_hourly', 'column': 'low'}],
('close','h','OPT'):	['期权小时K线 - 收盘价','direct',{'table_name': 'options_hourly', 'column': 'close'}],
('vol','h','OPT'):	['期权小时K线 - 成交量 （手）','direct',{'table_name': 'options_hourly', 'column': 'vol'}],
('amount','h','OPT'):	['期权小时K线 - 成交额 （千元）','direct',{'table_name': 'options_hourly', 'column': 'amount'}],
('open:%','d','FD'):	['基金日K线 - 复权开盘价-b:后复权f:前复权','adjustment',{'table_name': 'fund_daily', 'column': 'open', 'adj_table': 'fund_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('high:%','d','FD'):	['基金日K线 - 复权最高价-b:后复权f:前复权','adjustment',{'table_name': 'fund_daily', 'column': 'high', 'adj_table': 'fund_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('low:%','d','FD'):	['基金日K线 - 复权最低价-b:后复权f:前复权','adjustment',{'table_name': 'fund_daily', 'column': 'low', 'adj_table': 'fund_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('close:%','d','FD'):	['基金日K线 - 复权收盘价-b:后复权f:前复权','adjustment',{'table_name': 'fund_daily', 'column': 'close', 'adj_table': 'fund_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('open','d','FD'):	['基金日K线 - 开盘价','direct',{'table_name': 'fund_daily', 'column': 'open'}],
('high','d','FD'):	['基金日K线 - 最高价','direct',{'table_name': 'fund_daily', 'column': 'high'}],
('low','d','FD'):	['基金日K线 - 最低价','direct',{'table_name': 'fund_daily', 'column': 'low'}],
('close','d','FD'):	['基金日K线 - 收盘价','direct',{'table_name': 'fund_daily', 'column': 'close'}],
('vol','d','FD'):	['基金日K线 - 成交量 （手）','direct',{'table_name': 'fund_daily', 'column': 'vol'}],
('amount','d','FD'):	['基金日K线 - 成交额 （千元）','direct',{'table_name': 'fund_daily', 'column': 'amount'}],
('open:%','1min','FD'):	['基金60秒K线 - 复权开盘价-b:后复权f:前复权','adjustment',{'table_name': 'fund_1min', 'column': 'open', 'adj_table': 'fund_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('high:%','1min','FD'):	['基金60秒K线 - 复权最高价-b:后复权f:前复权','adjustment',{'table_name': 'fund_1min', 'column': 'high', 'adj_table': 'fund_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('low:%','1min','FD'):	['基金60秒K线 - 复权最低价-b:后复权f:前复权','adjustment',{'table_name': 'fund_1min', 'column': 'low', 'adj_table': 'fund_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('close:%','1min','FD'):	['基金60秒K线 - 复权收盘价-b:后复权f:前复权','adjustment',{'table_name': 'fund_1min', 'column': 'close', 'adj_table': 'fund_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('open','1min','FD'):	['基金60秒K线 - 开盘价','direct',{'table_name': 'fund_1min', 'column': 'open'}],
('high','1min','FD'):	['基金60秒K线 - 最高价','direct',{'table_name': 'fund_1min', 'column': 'high'}],
('low','1min','FD'):	['基金60秒K线 - 最低价','direct',{'table_name': 'fund_1min', 'column': 'low'}],
('close','1min','FD'):	['基金60秒K线 - 收盘价','direct',{'table_name': 'fund_1min', 'column': 'close'}],
('vol','1min','FD'):	['基金60秒K线 - 成交量 （手）','direct',{'table_name': 'fund_1min', 'column': 'vol'}],
('amount','1min','FD'):	['基金60秒K线 - 成交额 （千元）','direct',{'table_name': 'fund_1min', 'column': 'amount'}],
('open:%','5min','FD'):	['基金5分钟K线 - 复权开盘价-b:后复权f:前复权','adjustment',{'table_name': 'fund_5min', 'column': 'open', 'adj_table': 'fund_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('high:%','5min','FD'):	['基金5分钟K线 - 复权最高价-b:后复权f:前复权','adjustment',{'table_name': 'fund_5min', 'column': 'high', 'adj_table': 'fund_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('low:%','5min','FD'):	['基金5分钟K线 - 复权最低价-b:后复权f:前复权','adjustment',{'table_name': 'fund_5min', 'column': 'low', 'adj_table': 'fund_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('close:%','5min','FD'):	['基金5分钟K线 - 复权收盘价-b:后复权f:前复权','adjustment',{'table_name': 'fund_5min', 'column': 'close', 'adj_table': 'fund_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('open','5min','FD'):	['基金5分钟K线 - 开盘价','direct',{'table_name': 'fund_5min', 'column': 'open'}],
('high','5min','FD'):	['基金5分钟K线 - 最高价','direct',{'table_name': 'fund_5min', 'column': 'high'}],
('low','5min','FD'):	['基金5分钟K线 - 最低价','direct',{'table_name': 'fund_5min', 'column': 'low'}],
('close','5min','FD'):	['基金5分钟K线 - 收盘价','direct',{'table_name': 'fund_5min', 'column': 'close'}],
('vol','5min','FD'):	['基金5分钟K线 - 成交量 （手）','direct',{'table_name': 'fund_5min', 'column': 'vol'}],
('amount','5min','FD'):	['基金5分钟K线 - 成交额 （千元）','direct',{'table_name': 'fund_5min', 'column': 'amount'}],
('open:%','15min','FD'):	['基金15分钟K线 - 复权开盘价-b:后复权f:前复权','adjustment',{'table_name': 'fund_15min', 'column': 'open', 'adj_table': 'fund_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('high:%','15min','FD'):	['基金15分钟K线 - 复权最高价-b:后复权f:前复权','adjustment',{'table_name': 'fund_15min', 'column': 'high', 'adj_table': 'fund_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('low:%','15min','FD'):	['基金15分钟K线 - 复权最低价-b:后复权f:前复权','adjustment',{'table_name': 'fund_15min', 'column': 'low', 'adj_table': 'fund_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('close:%','15min','FD'):	['基金15分钟K线 - 复权收盘价-b:后复权f:前复权','adjustment',{'table_name': 'fund_15min', 'column': 'close', 'adj_table': 'fund_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('open','15min','FD'):	['基金15分钟K线 - 开盘价','direct',{'table_name': 'fund_15min', 'column': 'open'}],
('high','15min','FD'):	['基金15分钟K线 - 最高价','direct',{'table_name': 'fund_15min', 'column': 'high'}],
('low','15min','FD'):	['基金15分钟K线 - 最低价','direct',{'table_name': 'fund_15min', 'column': 'low'}],
('close','15min','FD'):	['基金15分钟K线 - 收盘价','direct',{'table_name': 'fund_15min', 'column': 'close'}],
('vol','15min','FD'):	['基金15分钟K线 - 成交量 （手）','direct',{'table_name': 'fund_15min', 'column': 'vol'}],
('amount','15min','FD'):	['基金15分钟K线 - 成交额 （千元）','direct',{'table_name': 'fund_15min', 'column': 'amount'}],
('open:%','30min','FD'):	['基金30分钟K线 - 复权开盘价-b:后复权f:前复权','adjustment',{'table_name': 'fund_30min', 'column': 'open', 'adj_table': 'fund_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('high:%','30min','FD'):	['基金30分钟K线 - 复权最高价-b:后复权f:前复权','adjustment',{'table_name': 'fund_30min', 'column': 'high', 'adj_table': 'fund_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('low:%','30min','FD'):	['基金30分钟K线 - 复权最低价-b:后复权f:前复权','adjustment',{'table_name': 'fund_30min', 'column': 'low', 'adj_table': 'fund_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('close:%','30min','FD'):	['基金30分钟K线 - 复权收盘价-b:后复权f:前复权','adjustment',{'table_name': 'fund_30min', 'column': 'close', 'adj_table': 'fund_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('open','30min','FD'):	['基金30分钟K线 - 开盘价','direct',{'table_name': 'fund_30min', 'column': 'open'}],
('high','30min','FD'):	['基金30分钟K线 - 最高价','direct',{'table_name': 'fund_30min', 'column': 'high'}],
('low','30min','FD'):	['基金30分钟K线 - 最低价','direct',{'table_name': 'fund_30min', 'column': 'low'}],
('close','30min','FD'):	['基金30分钟K线 - 收盘价','direct',{'table_name': 'fund_30min', 'column': 'close'}],
('vol','30min','FD'):	['基金30分钟K线 - 成交量 （手）','direct',{'table_name': 'fund_30min', 'column': 'vol'}],
('amount','30min','FD'):	['基金30分钟K线 - 成交额 （千元）','direct',{'table_name': 'fund_30min', 'column': 'amount'}],
('open:%','h','FD'):	['基金小时K线 - 复权开盘价-b:后复权f:前复权','adjustment',{'table_name': 'fund_hourly', 'column': 'open', 'adj_table': 'fund_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('high:%','h','FD'):	['基金小时K线 - 复权最高价-b:后复权f:前复权','adjustment',{'table_name': 'fund_hourly', 'column': 'high', 'adj_table': 'fund_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('low:%','h','FD'):	['基金小时K线 - 复权最低价-b:后复权f:前复权','adjustment',{'table_name': 'fund_hourly', 'column': 'low', 'adj_table': 'fund_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('close:%','h','FD'):	['基金小时K线 - 复权收盘价-b:后复权f:前复权','adjustment',{'table_name': 'fund_hourly', 'column': 'close', 'adj_table': 'fund_adj_factor', 'adj_column': 'adj_factor', 'adj_type': '%'}],
('open','h','FD'):	['基金小时K线 - 开盘价','direct',{'table_name': 'fund_hourly', 'column': 'open'}],
('high','h','FD'):	['基金小时K线 - 最高价','direct',{'table_name': 'fund_hourly', 'column': 'high'}],
('low','h','FD'):	['基金小时K线 - 最低价','direct',{'table_name': 'fund_hourly', 'column': 'low'}],
('close','h','FD'):	['基金小时K线 - 收盘价','direct',{'table_name': 'fund_hourly', 'column': 'close'}],
('vol','h','FD'):	['基金小时K线 - 成交量 （手）','direct',{'table_name': 'fund_hourly', 'column': 'vol'}],
('amount','h','FD'):	['基金小时K线 - 成交额 （千元）','direct',{'table_name': 'fund_hourly', 'column': 'amount'}],
('unit_nav','d','FD'):	['基金净值 - 单位净值','direct',{'table_name': 'fund_nav', 'column': 'unit_nav'}],
('accum_nav','d','FD'):	['基金净值 - 累计净值','direct',{'table_name': 'fund_nav', 'column': 'accum_nav'}],
('accum_div','d','FD'):	['基金净值 - 累计分红','direct',{'table_name': 'fund_nav', 'column': 'accum_div'}],
('net_asset','d','FD'):	['基金净值 - 资产净值','direct',{'table_name': 'fund_nav', 'column': 'net_asset'}],
('total_netasset','d','FD'):	['基金净值 - 累计资产净值','direct',{'table_name': 'fund_nav', 'column': 'total_netasset'}],
('adj_nav','d','FD'):	['基金净值 - 复权净值','direct',{'table_name': 'fund_nav', 'column': 'adj_nav'}],
('buy_sm_vol','d','E'):	['个股资金流向 - 小单买入量（手）','direct',{'table_name': 'money_flow', 'column': 'buy_sm_vol'}],
('buy_sm_amount','d','E'):	['个股资金流向 - 小单买入金额（万元）','direct',{'table_name': 'money_flow', 'column': 'buy_sm_amount'}],
('sell_sm_vol','d','E'):	['个股资金流向 - 小单卖出量（手）','direct',{'table_name': 'money_flow', 'column': 'sell_sm_vol'}],
('sell_sm_amount','d','E'):	['个股资金流向 - 小单卖出金额（万元）','direct',{'table_name': 'money_flow', 'column': 'sell_sm_amount'}],
('buy_md_vol','d','E'):	['个股资金流向 - 中单买入量（手）','direct',{'table_name': 'money_flow', 'column': 'buy_md_vol'}],
('buy_md_amount','d','E'):	['个股资金流向 - 中单买入金额（万元）','direct',{'table_name': 'money_flow', 'column': 'buy_md_amount'}],
('sell_md_vol','d','E'):	['个股资金流向 - 中单卖出量（手）','direct',{'table_name': 'money_flow', 'column': 'sell_md_vol'}],
('sell_md_amount','d','E'):	['个股资金流向 - 中单卖出金额（万元）','direct',{'table_name': 'money_flow', 'column': 'sell_md_amount'}],
('buy_lg_vol','d','E'):	['个股资金流向 - 大单买入量（手）','direct',{'table_name': 'money_flow', 'column': 'buy_lg_vol'}],
('buy_lg_amount','d','E'):	['个股资金流向 - 大单买入金额（万元）','direct',{'table_name': 'money_flow', 'column': 'buy_lg_amount'}],
('sell_lg_vol','d','E'):	['个股资金流向 - 大单卖出量（手）','direct',{'table_name': 'money_flow', 'column': 'sell_lg_vol'}],
('sell_lg_amount','d','E'):	['个股资金流向 - 大单卖出金额（万元）','direct',{'table_name': 'money_flow', 'column': 'sell_lg_amount'}],
('buy_elg_vol','d','E'):	['个股资金流向 - 特大单买入量（手）','direct',{'table_name': 'money_flow', 'column': 'buy_elg_vol'}],
('buy_elg_amount','d','E'):	['个股资金流向 - 特大单买入金额（万元）','direct',{'table_name': 'money_flow', 'column': 'buy_elg_amount'}],
('sell_elg_vol','d','E'):	['个股资金流向 - 特大单卖出量（手）','direct',{'table_name': 'money_flow', 'column': 'sell_elg_vol'}],
('sell_elg_amount','d','E'):	['个股资金流向 - 特大单卖出金额（万元）','direct',{'table_name': 'money_flow', 'column': 'sell_elg_amount'}],
('net_mf_vol','d','E'):	['个股资金流向 - 净流入量（手）','direct',{'table_name': 'money_flow', 'column': 'net_mf_vol'}],
('net_mf_amount','d','E'):	['个股资金流向 - 净流入额（万元）','direct',{'table_name': 'money_flow', 'column': 'net_mf_amount'}],
('up_limit','d','E'):	['涨停板 - 涨停价','direct',{'table_name': 'stock_limit', 'column': 'up_limit'}],
('down_limit','d','E'):	['跌停板 - 跌停价','direct',{'table_name': 'stock_limit', 'column': 'down_limit'}],
('ggt_ss','d','Any'):	['沪深港通资金流向 - 港股通（上海）','direct',{'table_name': 'HS_money_flow', 'column': 'ggt_ss'}],
('ggt_sz','d','Any'):	['沪深港通资金流向 - 港股通（深圳）','direct',{'table_name': 'HS_money_flow', 'column': 'ggt_sz'}],
('hgt','d','Any'):	['沪深港通资金流向 - 沪股通（百万元）','direct',{'table_name': 'HS_money_flow', 'column': 'hgt'}],
('sgt','d','Any'):	['沪深港通资金流向 - 深股通（百万元）','direct',{'table_name': 'HS_money_flow', 'column': 'sgt'}],
('north_money','d','Any'):	['沪深港通资金流向 - 北向资金（百万元）','direct',{'table_name': 'HS_money_flow', 'column': 'north_money'}],
('south_money','d','Any'):	['沪深港通资金流向 - 南向资金（百万元）','direct',{'table_name': 'HS_money_flow', 'column': 'south_money'}],
('basic_eps','q','E'):	['上市公司利润表 - 基本每股收益','direct',{'table_name': 'income', 'column': 'basic_eps'}],
('diluted_eps','q','E'):	['上市公司利润表 - 稀释每股收益','direct',{'table_name': 'income', 'column': 'diluted_eps'}],
('total_revenue','q','E'):	['上市公司利润表 - 营业总收入','direct',{'table_name': 'income', 'column': 'total_revenue'}],
('revenue','q','E'):	['上市公司利润表 - 营业收入','direct',{'table_name': 'income', 'column': 'revenue'}],
('int_income','q','E'):	['上市公司利润表 - 利息收入','direct',{'table_name': 'income', 'column': 'int_income'}],
('prem_earned','q','E'):	['上市公司利润表 - 已赚保费','direct',{'table_name': 'income', 'column': 'prem_earned'}],
('comm_income','q','E'):	['上市公司利润表 - 手续费及佣金收入','direct',{'table_name': 'income', 'column': 'comm_income'}],
('n_commis_income','q','E'):	['上市公司利润表 - 手续费及佣金净收入','direct',{'table_name': 'income', 'column': 'n_commis_income'}],
('n_oth_income','q','E'):	['上市公司利润表 - 其他经营净收益','direct',{'table_name': 'income', 'column': 'n_oth_income'}],
('n_oth_b_income','q','E'):	['上市公司利润表 - 加:其他业务净收益','direct',{'table_name': 'income', 'column': 'n_oth_b_income'}],
('prem_income','q','E'):	['上市公司利润表 - 保险业务收入','direct',{'table_name': 'income', 'column': 'prem_income'}],
('out_prem','q','E'):	['上市公司利润表 - 减:分出保费','direct',{'table_name': 'income', 'column': 'out_prem'}],
('une_prem_reser','q','E'):	['上市公司利润表 - 提取未到期责任准备金','direct',{'table_name': 'income', 'column': 'une_prem_reser'}],
('reins_income','q','E'):	['上市公司利润表 - 其中:分保费收入','direct',{'table_name': 'income', 'column': 'reins_income'}],
('n_sec_tb_income','q','E'):	['上市公司利润表 - 代理买卖证券业务净收入','direct',{'table_name': 'income', 'column': 'n_sec_tb_income'}],
('n_sec_uw_income','q','E'):	['上市公司利润表 - 证券承销业务净收入','direct',{'table_name': 'income', 'column': 'n_sec_uw_income'}],
('n_asset_mg_income','q','E'):	['上市公司利润表 - 受托客户资产管理业务净收入','direct',{'table_name': 'income', 'column': 'n_asset_mg_income'}],
('oth_b_income','q','E'):	['上市公司利润表 - 其他业务收入','direct',{'table_name': 'income', 'column': 'oth_b_income'}],
('fv_value_chg_gain','q','E'):	['上市公司利润表 - 加:公允价值变动净收益','direct',{'table_name': 'income', 'column': 'fv_value_chg_gain'}],
('invest_income','q','E'):	['上市公司利润表 - 加:投资净收益','direct',{'table_name': 'income', 'column': 'invest_income'}],
('ass_invest_income','q','E'):	['上市公司利润表 - 其中:对联营企业和合营企业的投资收益','direct',{'table_name': 'income', 'column': 'ass_invest_income'}],
('forex_gain','q','E'):	['上市公司利润表 - 加:汇兑净收益','direct',{'table_name': 'income', 'column': 'forex_gain'}],
('total_cogs','q','E'):	['上市公司利润表 - 营业总成本','direct',{'table_name': 'income', 'column': 'total_cogs'}],
('oper_cost','q','E'):	['上市公司利润表 - 减:营业成本','direct',{'table_name': 'income', 'column': 'oper_cost'}],
('int_exp','q','E'):	['上市公司利润表 - 减:利息支出','direct',{'table_name': 'income', 'column': 'int_exp'}],
('comm_exp','q','E'):	['上市公司利润表 - 减:手续费及佣金支出','direct',{'table_name': 'income', 'column': 'comm_exp'}],
('biz_tax_surchg','q','E'):	['上市公司利润表 - 减:营业税金及附加','direct',{'table_name': 'income', 'column': 'biz_tax_surchg'}],
('sell_exp','q','E'):	['上市公司利润表 - 减:销售费用','direct',{'table_name': 'income', 'column': 'sell_exp'}],
('admin_exp','q','E'):	['上市公司利润表 - 减:管理费用','direct',{'table_name': 'income', 'column': 'admin_exp'}],
('fin_exp','q','E'):	['上市公司利润表 - 减:财务费用','direct',{'table_name': 'income', 'column': 'fin_exp'}],
('assets_impair_loss','q','E'):	['上市公司利润表 - 减:资产减值损失','direct',{'table_name': 'income', 'column': 'assets_impair_loss'}],
('prem_refund','q','E'):	['上市公司利润表 - 退保金','direct',{'table_name': 'income', 'column': 'prem_refund'}],
('compens_payout','q','E'):	['上市公司利润表 - 赔付总支出','direct',{'table_name': 'income', 'column': 'compens_payout'}],
('reser_insur_liab','q','E'):	['上市公司利润表 - 提取保险责任准备金','direct',{'table_name': 'income', 'column': 'reser_insur_liab'}],
('div_payt','q','E'):	['上市公司利润表 - 保户红利支出','direct',{'table_name': 'income', 'column': 'div_payt'}],
('reins_exp','q','E'):	['上市公司利润表 - 分保费用','direct',{'table_name': 'income', 'column': 'reins_exp'}],
('oper_exp','q','E'):	['上市公司利润表 - 营业支出','direct',{'table_name': 'income', 'column': 'oper_exp'}],
('compens_payout_refu','q','E'):	['上市公司利润表 - 减:摊回赔付支出','direct',{'table_name': 'income', 'column': 'compens_payout_refu'}],
('insur_reser_refu','q','E'):	['上市公司利润表 - 减:摊回保险责任准备金','direct',{'table_name': 'income', 'column': 'insur_reser_refu'}],
('reins_cost_refund','q','E'):	['上市公司利润表 - 减:摊回分保费用','direct',{'table_name': 'income', 'column': 'reins_cost_refund'}],
('other_bus_cost','q','E'):	['上市公司利润表 - 其他业务成本','direct',{'table_name': 'income', 'column': 'other_bus_cost'}],
('operate_profit','q','E'):	['上市公司利润表 - 营业利润','direct',{'table_name': 'income', 'column': 'operate_profit'}],
('non_oper_income','q','E'):	['上市公司利润表 - 加:营业外收入','direct',{'table_name': 'income', 'column': 'non_oper_income'}],
('non_oper_exp','q','E'):	['上市公司利润表 - 减:营业外支出','direct',{'table_name': 'income', 'column': 'non_oper_exp'}],
('nca_disploss','q','E'):	['上市公司利润表 - 其中:减:非流动资产处置净损失','direct',{'table_name': 'income', 'column': 'nca_disploss'}],
('total_profit','q','E'):	['上市公司利润表 - 利润总额','direct',{'table_name': 'income', 'column': 'total_profit'}],
('income_tax','q','E'):	['上市公司利润表 - 所得税费用','direct',{'table_name': 'income', 'column': 'income_tax'}],
('net_income','q','E'):	['上市公司利润表 - 净利润(含少数股东损益)','direct',{'table_name': 'income', 'column': 'n_income'}],
('n_income_attr_p','q','E'):	['上市公司利润表 - 净利润(不含少数股东损益)','direct',{'table_name': 'income', 'column': 'n_income_attr_p'}],
('minority_gain','q','E'):	['上市公司利润表 - 少数股东损益','direct',{'table_name': 'income', 'column': 'minority_gain'}],
('oth_compr_income','q','E'):	['上市公司利润表 - 其他综合收益','direct',{'table_name': 'income', 'column': 'oth_compr_income'}],
('t_compr_income','q','E'):	['上市公司利润表 - 综合收益总额','direct',{'table_name': 'income', 'column': 't_compr_income'}],
('compr_inc_attr_p','q','E'):	['上市公司利润表 - 归属于母公司(或股东)的综合收益总额','direct',{'table_name': 'income', 'column': 'compr_inc_attr_p'}],
('compr_inc_attr_m_s','q','E'):	['上市公司利润表 - 归属于少数股东的综合收益总额','direct',{'table_name': 'income', 'column': 'compr_inc_attr_m_s'}],
('income_ebit','q','E'):	['上市公司利润表 - 息税前利润','direct',{'table_name': 'income', 'column': 'ebit'}],
('income_ebitda','q','E'):	['上市公司利润表 - 息税折旧摊销前利润','direct',{'table_name': 'income', 'column': 'ebitda'}],
('insurance_exp','q','E'):	['上市公司利润表 - 保险业务支出','direct',{'table_name': 'income', 'column': 'insurance_exp'}],
('undist_profit','q','E'):	['上市公司利润表 - 年初未分配利润','direct',{'table_name': 'income', 'column': 'undist_profit'}],
('distable_profit','q','E'):	['上市公司利润表 - 可分配利润','direct',{'table_name': 'income', 'column': 'distable_profit'}],
('income_rd_exp','q','E'):	['上市公司利润表 - 研发费用','direct',{'table_name': 'income', 'column': 'rd_exp'}],
('fin_exp_int_exp','q','E'):	['上市公司利润表 - 财务费用:利息费用','direct',{'table_name': 'income', 'column': 'fin_exp_int_exp'}],
('fin_exp_int_inc','q','E'):	['上市公司利润表 - 财务费用:利息收入','direct',{'table_name': 'income', 'column': 'fin_exp_int_inc'}],
('transfer_surplus_rese','q','E'):	['上市公司利润表 - 盈余公积转入','direct',{'table_name': 'income', 'column': 'transfer_surplus_rese'}],
('transfer_housing_imprest','q','E'):	['上市公司利润表 - 住房周转金转入','direct',{'table_name': 'income', 'column': 'transfer_housing_imprest'}],
('transfer_oth','q','E'):	['上市公司利润表 - 其他转入','direct',{'table_name': 'income', 'column': 'transfer_oth'}],
('adj_lossgain','q','E'):	['上市公司利润表 - 调整以前年度损益','direct',{'table_name': 'income', 'column': 'adj_lossgain'}],
('withdra_legal_surplus','q','E'):	['上市公司利润表 - 提取法定盈余公积','direct',{'table_name': 'income', 'column': 'withdra_legal_surplus'}],
('withdra_legal_pubfund','q','E'):	['上市公司利润表 - 提取法定公益金','direct',{'table_name': 'income', 'column': 'withdra_legal_pubfund'}],
('withdra_biz_devfund','q','E'):	['上市公司利润表 - 提取企业发展基金','direct',{'table_name': 'income', 'column': 'withdra_biz_devfund'}],
('withdra_rese_fund','q','E'):	['上市公司利润表 - 提取储备基金','direct',{'table_name': 'income', 'column': 'withdra_rese_fund'}],
('withdra_oth_ersu','q','E'):	['上市公司利润表 - 提取任意盈余公积金','direct',{'table_name': 'income', 'column': 'withdra_oth_ersu'}],
('workers_welfare','q','E'):	['上市公司利润表 - 职工奖金福利','direct',{'table_name': 'income', 'column': 'workers_welfare'}],
('distr_profit_shrhder','q','E'):	['上市公司利润表 - 可供股东分配的利润','direct',{'table_name': 'income', 'column': 'distr_profit_shrhder'}],
('prfshare_payable_dvd','q','E'):	['上市公司利润表 - 应付优先股股利','direct',{'table_name': 'income', 'column': 'prfshare_payable_dvd'}],
('comshare_payable_dvd','q','E'):	['上市公司利润表 - 应付普通股股利','direct',{'table_name': 'income', 'column': 'comshare_payable_dvd'}],
('capit_comstock_div','q','E'):	['上市公司利润表 - 转作股本的普通股股利','direct',{'table_name': 'income', 'column': 'capit_comstock_div'}],
('net_after_nr_lp_correct','q','E'):	['上市公司利润表 - 扣除非经常性损益后的净利润（更正前）','direct',{'table_name': 'income', 'column': 'net_after_nr_lp_correct'}],
('income_credit_impa_loss','q','E'):	['上市公司利润表 - 信用减值损失','direct',{'table_name': 'income', 'column': 'credit_impa_loss'}],
('net_expo_hedging_benefits','q','E'):	['上市公司利润表 - 净敞口套期收益','direct',{'table_name': 'income', 'column': 'net_expo_hedging_benefits'}],
('oth_impair_loss_assets','q','E'):	['上市公司利润表 - 其他资产减值损失','direct',{'table_name': 'income', 'column': 'oth_impair_loss_assets'}],
('total_opcost','q','E'):	['上市公司利润表 - 营业总成本（二）','direct',{'table_name': 'income', 'column': 'total_opcost'}],
('amodcost_fin_assets','q','E'):	['上市公司利润表 - 以摊余成本计量的金融资产终止确认收益','direct',{'table_name': 'income', 'column': 'amodcost_fin_assets'}],
('oth_income','q','E'):	['上市公司利润表 - 其他收益','direct',{'table_name': 'income', 'column': 'oth_income'}],
('asset_disp_income','q','E'):	['上市公司利润表 - 资产处置收益','direct',{'table_name': 'income', 'column': 'asset_disp_income'}],
('continued_net_profit','q','E'):	['上市公司利润表 - 持续经营净利润','direct',{'table_name': 'income', 'column': 'continued_net_profit'}],
('end_net_profit','q','E'):	['上市公司利润表 - 终止经营净利润','direct',{'table_name': 'income', 'column': 'end_net_profit'}],
('total_share','q','E'):	['上市公司资产负债表 - 期末总股本','direct',{'table_name': 'balance', 'column': 'total_share'}],
('cap_rese','q','E'):	['上市公司资产负债表 - 资本公积金','direct',{'table_name': 'balance', 'column': 'cap_rese'}],
('undistr_porfit','q','E'):	['上市公司资产负债表 - 未分配利润','direct',{'table_name': 'balance', 'column': 'undistr_porfit'}],
('surplus_rese','q','E'):	['上市公司资产负债表 - 盈余公积金','direct',{'table_name': 'balance', 'column': 'surplus_rese'}],
('special_rese','q','E'):	['上市公司资产负债表 - 专项储备','direct',{'table_name': 'balance', 'column': 'special_rese'}],
('money_cap','q','E'):	['上市公司资产负债表 - 货币资金','direct',{'table_name': 'balance', 'column': 'money_cap'}],
('trad_asset','q','E'):	['上市公司资产负债表 - 交易性金融资产','direct',{'table_name': 'balance', 'column': 'trad_asset'}],
('notes_receiv','q','E'):	['上市公司资产负债表 - 应收票据','direct',{'table_name': 'balance', 'column': 'notes_receiv'}],
('accounts_receiv','q','E'):	['上市公司资产负债表 - 应收账款','direct',{'table_name': 'balance', 'column': 'accounts_receiv'}],
('oth_receiv','q','E'):	['上市公司资产负债表 - 其他应收款','direct',{'table_name': 'balance', 'column': 'oth_receiv'}],
('prepayment','q','E'):	['上市公司资产负债表 - 预付款项','direct',{'table_name': 'balance', 'column': 'prepayment'}],
('div_receiv','q','E'):	['上市公司资产负债表 - 应收股利','direct',{'table_name': 'balance', 'column': 'div_receiv'}],
('int_receiv','q','E'):	['上市公司资产负债表 - 应收利息','direct',{'table_name': 'balance', 'column': 'int_receiv'}],
('inventories','q','E'):	['上市公司资产负债表 - 存货','direct',{'table_name': 'balance', 'column': 'inventories'}],
('amor_exp','q','E'):	['上市公司资产负债表 - 长期待摊费用','direct',{'table_name': 'balance', 'column': 'amor_exp'}],
('nca_within_1y','q','E'):	['上市公司资产负债表 - 一年内到期的非流动资产','direct',{'table_name': 'balance', 'column': 'nca_within_1y'}],
('sett_rsrv','q','E'):	['上市公司资产负债表 - 结算备付金','direct',{'table_name': 'balance', 'column': 'sett_rsrv'}],
('loanto_oth_bank_fi','q','E'):	['上市公司资产负债表 - 拆出资金','direct',{'table_name': 'balance', 'column': 'loanto_oth_bank_fi'}],
('premium_receiv','q','E'):	['上市公司资产负债表 - 应收保费','direct',{'table_name': 'balance', 'column': 'premium_receiv'}],
('reinsur_receiv','q','E'):	['上市公司资产负债表 - 应收分保账款','direct',{'table_name': 'balance', 'column': 'reinsur_receiv'}],
('reinsur_res_receiv','q','E'):	['上市公司资产负债表 - 应收分保合同准备金','direct',{'table_name': 'balance', 'column': 'reinsur_res_receiv'}],
('pur_resale_fa','q','E'):	['上市公司资产负债表 - 买入返售金融资产','direct',{'table_name': 'balance', 'column': 'pur_resale_fa'}],
('oth_cur_assets','q','E'):	['上市公司资产负债表 - 其他流动资产','direct',{'table_name': 'balance', 'column': 'oth_cur_assets'}],
('total_cur_assets','q','E'):	['上市公司资产负债表 - 流动资产合计','direct',{'table_name': 'balance', 'column': 'total_cur_assets'}],
('fa_avail_for_sale','q','E'):	['上市公司资产负债表 - 可供出售金融资产','direct',{'table_name': 'balance', 'column': 'fa_avail_for_sale'}],
('htm_invest','q','E'):	['上市公司资产负债表 - 持有至到期投资','direct',{'table_name': 'balance', 'column': 'htm_invest'}],
('lt_eqt_invest','q','E'):	['上市公司资产负债表 - 长期股权投资','direct',{'table_name': 'balance', 'column': 'lt_eqt_invest'}],
('invest_real_estate','q','E'):	['上市公司资产负债表 - 投资性房地产','direct',{'table_name': 'balance', 'column': 'invest_real_estate'}],
('time_deposits','q','E'):	['上市公司资产负债表 - 定期存款','direct',{'table_name': 'balance', 'column': 'time_deposits'}],
('oth_assets','q','E'):	['上市公司资产负债表 - 其他资产','direct',{'table_name': 'balance', 'column': 'oth_assets'}],
('lt_rec','q','E'):	['上市公司资产负债表 - 长期应收款','direct',{'table_name': 'balance', 'column': 'lt_rec'}],
('fix_assets','q','E'):	['上市公司资产负债表 - 固定资产','direct',{'table_name': 'balance', 'column': 'fix_assets'}],
('cip','q','E'):	['上市公司资产负债表 - 在建工程','direct',{'table_name': 'balance', 'column': 'cip'}],
('const_materials','q','E'):	['上市公司资产负债表 - 工程物资','direct',{'table_name': 'balance', 'column': 'const_materials'}],
('fixed_assets_disp','q','E'):	['上市公司资产负债表 - 固定资产清理','direct',{'table_name': 'balance', 'column': 'fixed_assets_disp'}],
('produc_bio_assets','q','E'):	['上市公司资产负债表 - 生产性生物资产','direct',{'table_name': 'balance', 'column': 'produc_bio_assets'}],
('oil_and_gas_assets','q','E'):	['上市公司资产负债表 - 油气资产','direct',{'table_name': 'balance', 'column': 'oil_and_gas_assets'}],
('intan_assets','q','E'):	['上市公司资产负债表 - 无形资产','direct',{'table_name': 'balance', 'column': 'intan_assets'}],
('r_and_d','q','E'):	['上市公司资产负债表 - 研发支出','direct',{'table_name': 'balance', 'column': 'r_and_d'}],
('goodwill','q','E'):	['上市公司资产负债表 - 商誉','direct',{'table_name': 'balance', 'column': 'goodwill'}],
('lt_amor_exp','q','E'):	['上市公司资产负债表 - 长期待摊费用','direct',{'table_name': 'balance', 'column': 'lt_amor_exp'}],
('defer_tax_assets','q','E'):	['上市公司资产负债表 - 递延所得税资产','direct',{'table_name': 'balance', 'column': 'defer_tax_assets'}],
('decr_in_disbur','q','E'):	['上市公司资产负债表 - 发放贷款及垫款','direct',{'table_name': 'balance', 'column': 'decr_in_disbur'}],
('oth_nca','q','E'):	['上市公司资产负债表 - 其他非流动资产','direct',{'table_name': 'balance', 'column': 'oth_nca'}],
('total_nca','q','E'):	['上市公司资产负债表 - 非流动资产合计','direct',{'table_name': 'balance', 'column': 'total_nca'}],
('cash_reser_cb','q','E'):	['上市公司资产负债表 - 现金及存放中央银行款项','direct',{'table_name': 'balance', 'column': 'cash_reser_cb'}],
('depos_in_oth_bfi','q','E'):	['上市公司资产负债表 - 存放同业和其它金融机构款项','direct',{'table_name': 'balance', 'column': 'depos_in_oth_bfi'}],
('prec_metals','q','E'):	['上市公司资产负债表 - 贵金属','direct',{'table_name': 'balance', 'column': 'prec_metals'}],
('deriv_assets','q','E'):	['上市公司资产负债表 - 衍生金融资产','direct',{'table_name': 'balance', 'column': 'deriv_assets'}],
('rr_reins_une_prem','q','E'):	['上市公司资产负债表 - 应收分保未到期责任准备金','direct',{'table_name': 'balance', 'column': 'rr_reins_une_prem'}],
('rr_reins_outstd_cla','q','E'):	['上市公司资产负债表 - 应收分保未决赔款准备金','direct',{'table_name': 'balance', 'column': 'rr_reins_outstd_cla'}],
('rr_reins_lins_liab','q','E'):	['上市公司资产负债表 - 应收分保寿险责任准备金','direct',{'table_name': 'balance', 'column': 'rr_reins_lins_liab'}],
('rr_reins_lthins_liab','q','E'):	['上市公司资产负债表 - 应收分保长期健康险责任准备金','direct',{'table_name': 'balance', 'column': 'rr_reins_lthins_liab'}],
('refund_depos','q','E'):	['上市公司资产负债表 - 存出保证金','direct',{'table_name': 'balance', 'column': 'refund_depos'}],
('ph_pledge_loans','q','E'):	['上市公司资产负债表 - 保户质押贷款','direct',{'table_name': 'balance', 'column': 'ph_pledge_loans'}],
('refund_cap_depos','q','E'):	['上市公司资产负债表 - 存出资本保证金','direct',{'table_name': 'balance', 'column': 'refund_cap_depos'}],
('indep_acct_assets','q','E'):	['上市公司资产负债表 - 独立账户资产','direct',{'table_name': 'balance', 'column': 'indep_acct_assets'}],
('client_depos','q','E'):	['上市公司资产负债表 - 其中：客户资金存款','direct',{'table_name': 'balance', 'column': 'client_depos'}],
('client_prov','q','E'):	['上市公司资产负债表 - 其中：客户备付金','direct',{'table_name': 'balance', 'column': 'client_prov'}],
('transac_seat_fee','q','E'):	['上市公司资产负债表 - 其中:交易席位费','direct',{'table_name': 'balance', 'column': 'transac_seat_fee'}],
('invest_as_receiv','q','E'):	['上市公司资产负债表 - 应收款项类投资','direct',{'table_name': 'balance', 'column': 'invest_as_receiv'}],
('total_assets','q','E'):	['上市公司资产负债表 - 资产总计','direct',{'table_name': 'balance', 'column': 'total_assets'}],
('lt_borr','q','E'):	['上市公司资产负债表 - 长期借款','direct',{'table_name': 'balance', 'column': 'lt_borr'}],
('st_borr','q','E'):	['上市公司资产负债表 - 短期借款','direct',{'table_name': 'balance', 'column': 'st_borr'}],
('cb_borr','q','E'):	['上市公司资产负债表 - 向中央银行借款','direct',{'table_name': 'balance', 'column': 'cb_borr'}],
('depos_ib_deposits','q','E'):	['上市公司资产负债表 - 吸收存款及同业存放','direct',{'table_name': 'balance', 'column': 'depos_ib_deposits'}],
('loan_oth_bank','q','E'):	['上市公司资产负债表 - 拆入资金','direct',{'table_name': 'balance', 'column': 'loan_oth_bank'}],
('trading_fl','q','E'):	['上市公司资产负债表 - 交易性金融负债','direct',{'table_name': 'balance', 'column': 'trading_fl'}],
('notes_payable','q','E'):	['上市公司资产负债表 - 应付票据','direct',{'table_name': 'balance', 'column': 'notes_payable'}],
('acct_payable','q','E'):	['上市公司资产负债表 - 应付账款','direct',{'table_name': 'balance', 'column': 'acct_payable'}],
('adv_receipts','q','E'):	['上市公司资产负债表 - 预收款项','direct',{'table_name': 'balance', 'column': 'adv_receipts'}],
('sold_for_repur_fa','q','E'):	['上市公司资产负债表 - 卖出回购金融资产款','direct',{'table_name': 'balance', 'column': 'sold_for_repur_fa'}],
('comm_payable','q','E'):	['上市公司资产负债表 - 应付手续费及佣金','direct',{'table_name': 'balance', 'column': 'comm_payable'}],
('payroll_payable','q','E'):	['上市公司资产负债表 - 应付职工薪酬','direct',{'table_name': 'balance', 'column': 'payroll_payable'}],
('taxes_payable','q','E'):	['上市公司资产负债表 - 应交税费','direct',{'table_name': 'balance', 'column': 'taxes_payable'}],
('int_payable','q','E'):	['上市公司资产负债表 - 应付利息','direct',{'table_name': 'balance', 'column': 'int_payable'}],
('div_payable','q','E'):	['上市公司资产负债表 - 应付股利','direct',{'table_name': 'balance', 'column': 'div_payable'}],
('oth_payable','q','E'):	['上市公司资产负债表 - 其他应付款','direct',{'table_name': 'balance', 'column': 'oth_payable'}],
('acc_exp','q','E'):	['上市公司资产负债表 - 预提费用','direct',{'table_name': 'balance', 'column': 'acc_exp'}],
('deferred_inc','q','E'):	['上市公司资产负债表 - 递延收益','direct',{'table_name': 'balance', 'column': 'deferred_inc'}],
('st_bonds_payable','q','E'):	['上市公司资产负债表 - 应付短期债券','direct',{'table_name': 'balance', 'column': 'st_bonds_payable'}],
('payable_to_reinsurer','q','E'):	['上市公司资产负债表 - 应付分保账款','direct',{'table_name': 'balance', 'column': 'payable_to_reinsurer'}],
('rsrv_insur_cont','q','E'):	['上市公司资产负债表 - 保险合同准备金','direct',{'table_name': 'balance', 'column': 'rsrv_insur_cont'}],
('acting_trading_sec','q','E'):	['上市公司资产负债表 - 代理买卖证券款','direct',{'table_name': 'balance', 'column': 'acting_trading_sec'}],
('acting_uw_sec','q','E'):	['上市公司资产负债表 - 代理承销证券款','direct',{'table_name': 'balance', 'column': 'acting_uw_sec'}],
('non_cur_liab_due_1y','q','E'):	['上市公司资产负债表 - 一年内到期的非流动负债','direct',{'table_name': 'balance', 'column': 'non_cur_liab_due_1y'}],
('oth_cur_liab','q','E'):	['上市公司资产负债表 - 其他流动负债','direct',{'table_name': 'balance', 'column': 'oth_cur_liab'}],
('total_cur_liab','q','E'):	['上市公司资产负债表 - 流动负债合计','direct',{'table_name': 'balance', 'column': 'total_cur_liab'}],
('bond_payable','q','E'):	['上市公司资产负债表 - 应付债券','direct',{'table_name': 'balance', 'column': 'bond_payable'}],
('lt_payable','q','E'):	['上市公司资产负债表 - 长期应付款','direct',{'table_name': 'balance', 'column': 'lt_payable'}],
('specific_payables','q','E'):	['上市公司资产负债表 - 专项应付款','direct',{'table_name': 'balance', 'column': 'specific_payables'}],
('estimated_liab','q','E'):	['上市公司资产负债表 - 预计负债','direct',{'table_name': 'balance', 'column': 'estimated_liab'}],
('defer_tax_liab','q','E'):	['上市公司资产负债表 - 递延所得税负债','direct',{'table_name': 'balance', 'column': 'defer_tax_liab'}],
('defer_inc_non_cur_liab','q','E'):	['上市公司资产负债表 - 递延收益-非流动负债','direct',{'table_name': 'balance', 'column': 'defer_inc_non_cur_liab'}],
('oth_ncl','q','E'):	['上市公司资产负债表 - 其他非流动负债','direct',{'table_name': 'balance', 'column': 'oth_ncl'}],
('total_ncl','q','E'):	['上市公司资产负债表 - 非流动负债合计','direct',{'table_name': 'balance', 'column': 'total_ncl'}],
('depos_oth_bfi','q','E'):	['上市公司资产负债表 - 同业和其它金融机构存放款项','direct',{'table_name': 'balance', 'column': 'depos_oth_bfi'}],
('deriv_liab','q','E'):	['上市公司资产负债表 - 衍生金融负债','direct',{'table_name': 'balance', 'column': 'deriv_liab'}],
('depos','q','E'):	['上市公司资产负债表 - 吸收存款','direct',{'table_name': 'balance', 'column': 'depos'}],
('agency_bus_liab','q','E'):	['上市公司资产负债表 - 代理业务负债','direct',{'table_name': 'balance', 'column': 'agency_bus_liab'}],
('oth_liab','q','E'):	['上市公司资产负债表 - 其他负债','direct',{'table_name': 'balance', 'column': 'oth_liab'}],
('prem_receiv_adva','q','E'):	['上市公司资产负债表 - 预收保费','direct',{'table_name': 'balance', 'column': 'prem_receiv_adva'}],
('depos_received','q','E'):	['上市公司资产负债表 - 存入保证金','direct',{'table_name': 'balance', 'column': 'depos_received'}],
('ph_invest','q','E'):	['上市公司资产负债表 - 保户储金及投资款','direct',{'table_name': 'balance', 'column': 'ph_invest'}],
('reser_une_prem','q','E'):	['上市公司资产负债表 - 未到期责任准备金','direct',{'table_name': 'balance', 'column': 'reser_une_prem'}],
('reser_outstd_claims','q','E'):	['上市公司资产负债表 - 未决赔款准备金','direct',{'table_name': 'balance', 'column': 'reser_outstd_claims'}],
('reser_lins_liab','q','E'):	['上市公司资产负债表 - 寿险责任准备金','direct',{'table_name': 'balance', 'column': 'reser_lins_liab'}],
('reser_lthins_liab','q','E'):	['上市公司资产负债表 - 长期健康险责任准备金','direct',{'table_name': 'balance', 'column': 'reser_lthins_liab'}],
('indept_acc_liab','q','E'):	['上市公司资产负债表 - 独立账户负债','direct',{'table_name': 'balance', 'column': 'indept_acc_liab'}],
('pledge_borr','q','E'):	['上市公司资产负债表 - 其中:质押借款','direct',{'table_name': 'balance', 'column': 'pledge_borr'}],
('indem_payable','q','E'):	['上市公司资产负债表 - 应付赔付款','direct',{'table_name': 'balance', 'column': 'indem_payable'}],
('policy_div_payable','q','E'):	['上市公司资产负债表 - 应付保单红利','direct',{'table_name': 'balance', 'column': 'policy_div_payable'}],
('total_liab','q','E'):	['上市公司资产负债表 - 负债合计','direct',{'table_name': 'balance', 'column': 'total_liab'}],
('treasury_share','q','E'):	['上市公司资产负债表 - 减:库存股','direct',{'table_name': 'balance', 'column': 'treasury_share'}],
('ordin_risk_reser','q','E'):	['上市公司资产负债表 - 一般风险准备','direct',{'table_name': 'balance', 'column': 'ordin_risk_reser'}],
('forex_differ','q','E'):	['上市公司资产负债表 - 外币报表折算差额','direct',{'table_name': 'balance', 'column': 'forex_differ'}],
('invest_loss_unconf','q','E'):	['上市公司资产负债表 - 未确认的投资损失','direct',{'table_name': 'balance', 'column': 'invest_loss_unconf'}],
('minority_int','q','E'):	['上市公司资产负债表 - 少数股东权益','direct',{'table_name': 'balance', 'column': 'minority_int'}],
('total_hldr_eqy_exc_min_int','q','E'):	['上市公司资产负债表 - 股东权益合计(不含少数股东权益)','direct',{'table_name': 'balance', 'column': 'total_hldr_eqy_exc_min_int'}],
('total_hldr_eqy_inc_min_int','q','E'):	['上市公司资产负债表 - 股东权益合计(含少数股东权益)','direct',{'table_name': 'balance', 'column': 'total_hldr_eqy_inc_min_int'}],
('total_liab_hldr_eqy','q','E'):	['上市公司资产负债表 - 负债及股东权益总计','direct',{'table_name': 'balance', 'column': 'total_liab_hldr_eqy'}],
('lt_payroll_payable','q','E'):	['上市公司资产负债表 - 长期应付职工薪酬','direct',{'table_name': 'balance', 'column': 'lt_payroll_payable'}],
('oth_comp_income','q','E'):	['上市公司资产负债表 - 其他综合收益','direct',{'table_name': 'balance', 'column': 'oth_comp_income'}],
('oth_eqt_tools','q','E'):	['上市公司资产负债表 - 其他权益工具','direct',{'table_name': 'balance', 'column': 'oth_eqt_tools'}],
('oth_eqt_tools_p_shr','q','E'):	['上市公司资产负债表 - 其他权益工具(优先股)','direct',{'table_name': 'balance', 'column': 'oth_eqt_tools_p_shr'}],
('lending_funds','q','E'):	['上市公司资产负债表 - 融出资金','direct',{'table_name': 'balance', 'column': 'lending_funds'}],
('acc_receivable','q','E'):	['上市公司资产负债表 - 应收款项','direct',{'table_name': 'balance', 'column': 'acc_receivable'}],
('st_fin_payable','q','E'):	['上市公司资产负债表 - 应付短期融资款','direct',{'table_name': 'balance', 'column': 'st_fin_payable'}],
('payables','q','E'):	['上市公司资产负债表 - 应付款项','direct',{'table_name': 'balance', 'column': 'payables'}],
('hfs_assets','q','E'):	['上市公司资产负债表 - 持有待售的资产','direct',{'table_name': 'balance', 'column': 'hfs_assets'}],
('hfs_sales','q','E'):	['上市公司资产负债表 - 持有待售的负债','direct',{'table_name': 'balance', 'column': 'hfs_sales'}],
('cost_fin_assets','q','E'):	['上市公司资产负债表 - 以摊余成本计量的金融资产','direct',{'table_name': 'balance', 'column': 'cost_fin_assets'}],
('fair_value_fin_assets','q','E'):	['上市公司资产负债表 - 以公允价值计量且其变动计入其他综合收益的金融资产','direct',{'table_name': 'balance', 'column': 'fair_value_fin_assets'}],
('cip_total','q','E'):	['上市公司资产负债表 - 在建工程(合计)(元)','direct',{'table_name': 'balance', 'column': 'cip_total'}],
('oth_pay_total','q','E'):	['上市公司资产负债表 - 其他应付款(合计)(元)','direct',{'table_name': 'balance', 'column': 'oth_pay_total'}],
('long_pay_total','q','E'):	['上市公司资产负债表 - 长期应付款(合计)(元)','direct',{'table_name': 'balance', 'column': 'long_pay_total'}],
('debt_invest','q','E'):	['上市公司资产负债表 - 债权投资(元)','direct',{'table_name': 'balance', 'column': 'debt_invest'}],
('oth_debt_invest','q','E'):	['上市公司资产负债表 - 其他债权投资(元)','direct',{'table_name': 'balance', 'column': 'oth_debt_invest'}],
('oth_eq_invest','q','E'):	['上市公司资产负债表 - 其他权益工具投资(元)','direct',{'table_name': 'balance', 'column': 'oth_eq_invest'}],
('oth_illiq_fin_assets','q','E'):	['上市公司资产负债表 - 其他非流动金融资产(元)','direct',{'table_name': 'balance', 'column': 'oth_illiq_fin_assets'}],
('oth_eq_ppbond','q','E'):	['上市公司资产负债表 - 其他权益工具:永续债(元)','direct',{'table_name': 'balance', 'column': 'oth_eq_ppbond'}],
('receiv_financing','q','E'):	['上市公司资产负债表 - 应收款项融资','direct',{'table_name': 'balance', 'column': 'receiv_financing'}],
('use_right_assets','q','E'):	['上市公司资产负债表 - 使用权资产','direct',{'table_name': 'balance', 'column': 'use_right_assets'}],
('lease_liab','q','E'):	['上市公司资产负债表 - 租赁负债','direct',{'table_name': 'balance', 'column': 'lease_liab'}],
('contract_assets','q','E'):	['上市公司资产负债表 - 合同资产','direct',{'table_name': 'balance', 'column': 'contract_assets'}],
('contract_liab','q','E'):	['上市公司资产负债表 - 合同负债','direct',{'table_name': 'balance', 'column': 'contract_liab'}],
('accounts_receiv_bill','q','E'):	['上市公司资产负债表 - 应收票据及应收账款','direct',{'table_name': 'balance', 'column': 'accounts_receiv_bill'}],
('accounts_pay','q','E'):	['上市公司资产负债表 - 应付票据及应付账款','direct',{'table_name': 'balance', 'column': 'accounts_pay'}],
('oth_rcv_total','q','E'):	['上市公司资产负债表 - 其他应收款(合计)（元）','direct',{'table_name': 'balance', 'column': 'oth_rcv_total'}],
('fix_assets_total','q','E'):	['上市公司资产负债表 - 固定资产(合计)(元)','direct',{'table_name': 'balance', 'column': 'fix_assets_total'}],
('net_profit','q','E'):	['上市公司现金流量表 - 净利润','direct',{'table_name': 'cashflow', 'column': 'net_profit'}],
('finan_exp','q','E'):	['上市公司现金流量表 - 财务费用','direct',{'table_name': 'cashflow', 'column': 'finan_exp'}],
('c_fr_sale_sg','q','E'):	['上市公司现金流量表 - 销售商品、提供劳务收到的现金','direct',{'table_name': 'cashflow', 'column': 'c_fr_sale_sg'}],
('recp_tax_rends','q','E'):	['上市公司现金流量表 - 收到的税费返还','direct',{'table_name': 'cashflow', 'column': 'recp_tax_rends'}],
('n_depos_incr_fi','q','E'):	['上市公司现金流量表 - 客户存款和同业存放款项净增加额','direct',{'table_name': 'cashflow', 'column': 'n_depos_incr_fi'}],
('n_incr_loans_cb','q','E'):	['上市公司现金流量表 - 向中央银行借款净增加额','direct',{'table_name': 'cashflow', 'column': 'n_incr_loans_cb'}],
('n_inc_borr_oth_fi','q','E'):	['上市公司现金流量表 - 向其他金融机构拆入资金净增加额','direct',{'table_name': 'cashflow', 'column': 'n_inc_borr_oth_fi'}],
('prem_fr_orig_contr','q','E'):	['上市公司现金流量表 - 收到原保险合同保费取得的现金','direct',{'table_name': 'cashflow', 'column': 'prem_fr_orig_contr'}],
('n_incr_insured_dep','q','E'):	['上市公司现金流量表 - 保户储金净增加额','direct',{'table_name': 'cashflow', 'column': 'n_incr_insured_dep'}],
('n_reinsur_prem','q','E'):	['上市公司现金流量表 - 收到再保业务现金净额','direct',{'table_name': 'cashflow', 'column': 'n_reinsur_prem'}],
('n_incr_disp_tfa','q','E'):	['上市公司现金流量表 - 处置交易性金融资产净增加额','direct',{'table_name': 'cashflow', 'column': 'n_incr_disp_tfa'}],
('ifc_cash_incr','q','E'):	['上市公司现金流量表 - 收取利息和手续费净增加额','direct',{'table_name': 'cashflow', 'column': 'ifc_cash_incr'}],
('n_incr_disp_faas','q','E'):	['上市公司现金流量表 - 处置可供出售金融资产净增加额','direct',{'table_name': 'cashflow', 'column': 'n_incr_disp_faas'}],
('n_incr_loans_oth_bank','q','E'):	['上市公司现金流量表 - 拆入资金净增加额','direct',{'table_name': 'cashflow', 'column': 'n_incr_loans_oth_bank'}],
('n_cap_incr_repur','q','E'):	['上市公司现金流量表 - 回购业务资金净增加额','direct',{'table_name': 'cashflow', 'column': 'n_cap_incr_repur'}],
('c_fr_oth_operate_a','q','E'):	['上市公司现金流量表 - 收到其他与经营活动有关的现金','direct',{'table_name': 'cashflow', 'column': 'c_fr_oth_operate_a'}],
('c_inf_fr_operate_a','q','E'):	['上市公司现金流量表 - 经营活动现金流入小计','direct',{'table_name': 'cashflow', 'column': 'c_inf_fr_operate_a'}],
('c_paid_goods_s','q','E'):	['上市公司现金流量表 - 购买商品、接受劳务支付的现金','direct',{'table_name': 'cashflow', 'column': 'c_paid_goods_s'}],
('c_paid_to_for_empl','q','E'):	['上市公司现金流量表 - 支付给职工以及为职工支付的现金','direct',{'table_name': 'cashflow', 'column': 'c_paid_to_for_empl'}],
('c_paid_for_taxes','q','E'):	['上市公司现金流量表 - 支付的各项税费','direct',{'table_name': 'cashflow', 'column': 'c_paid_for_taxes'}],
('n_incr_clt_loan_adv','q','E'):	['上市公司现金流量表 - 客户贷款及垫款净增加额','direct',{'table_name': 'cashflow', 'column': 'n_incr_clt_loan_adv'}],
('n_incr_dep_cbob','q','E'):	['上市公司现金流量表 - 存放央行和同业款项净增加额','direct',{'table_name': 'cashflow', 'column': 'n_incr_dep_cbob'}],
('c_pay_claims_orig_inco','q','E'):	['上市公司现金流量表 - 支付原保险合同赔付款项的现金','direct',{'table_name': 'cashflow', 'column': 'c_pay_claims_orig_inco'}],
('pay_handling_chrg','q','E'):	['上市公司现金流量表 - 支付手续费的现金','direct',{'table_name': 'cashflow', 'column': 'pay_handling_chrg'}],
('pay_comm_insur_plcy','q','E'):	['上市公司现金流量表 - 支付保单红利的现金','direct',{'table_name': 'cashflow', 'column': 'pay_comm_insur_plcy'}],
('oth_cash_pay_oper_act','q','E'):	['上市公司现金流量表 - 支付其他与经营活动有关的现金','direct',{'table_name': 'cashflow', 'column': 'oth_cash_pay_oper_act'}],
('st_cash_out_act','q','E'):	['上市公司现金流量表 - 经营活动现金流出小计','direct',{'table_name': 'cashflow', 'column': 'st_cash_out_act'}],
('n_cashflow_act','q','E'):	['上市公司现金流量表 - 经营活动产生的现金流量净额','direct',{'table_name': 'cashflow', 'column': 'n_cashflow_act'}],
('oth_recp_ral_inv_act','q','E'):	['上市公司现金流量表 - 收到其他与投资活动有关的现金','direct',{'table_name': 'cashflow', 'column': 'oth_recp_ral_inv_act'}],
('c_disp_withdrwl_invest','q','E'):	['上市公司现金流量表 - 收回投资收到的现金','direct',{'table_name': 'cashflow', 'column': 'c_disp_withdrwl_invest'}],
('c_recp_return_invest','q','E'):	['上市公司现金流量表 - 取得投资收益收到的现金','direct',{'table_name': 'cashflow', 'column': 'c_recp_return_invest'}],
('n_recp_disp_fiolta','q','E'):	['上市公司现金流量表 - 处置固定资产、无形资产和其他长期资产收回的现金净额','direct',{'table_name': 'cashflow', 'column': 'n_recp_disp_fiolta'}],
('n_recp_disp_sobu','q','E'):	['上市公司现金流量表 - 处置子公司及其他营业单位收到的现金净额','direct',{'table_name': 'cashflow', 'column': 'n_recp_disp_sobu'}],
('stot_inflows_inv_act','q','E'):	['上市公司现金流量表 - 投资活动现金流入小计','direct',{'table_name': 'cashflow', 'column': 'stot_inflows_inv_act'}],
('c_pay_acq_const_fiolta','q','E'):	['上市公司现金流量表 - 购建固定资产、无形资产和其他长期资产支付的现金','direct',{'table_name': 'cashflow', 'column': 'c_pay_acq_const_fiolta'}],
('c_paid_invest','q','E'):	['上市公司现金流量表 - 投资支付的现金','direct',{'table_name': 'cashflow', 'column': 'c_paid_invest'}],
('n_disp_subs_oth_biz','q','E'):	['上市公司现金流量表 - 取得子公司及其他营业单位支付的现金净额','direct',{'table_name': 'cashflow', 'column': 'n_disp_subs_oth_biz'}],
('oth_pay_ral_inv_act','q','E'):	['上市公司现金流量表 - 支付其他与投资活动有关的现金','direct',{'table_name': 'cashflow', 'column': 'oth_pay_ral_inv_act'}],
('n_incr_pledge_loan','q','E'):	['上市公司现金流量表 - 质押贷款净增加额','direct',{'table_name': 'cashflow', 'column': 'n_incr_pledge_loan'}],
('stot_out_inv_act','q','E'):	['上市公司现金流量表 - 投资活动现金流出小计','direct',{'table_name': 'cashflow', 'column': 'stot_out_inv_act'}],
('n_cashflow_inv_act','q','E'):	['上市公司现金流量表 - 投资活动产生的现金流量净额','direct',{'table_name': 'cashflow', 'column': 'n_cashflow_inv_act'}],
('c_recp_borrow','q','E'):	['上市公司现金流量表 - 取得借款收到的现金','direct',{'table_name': 'cashflow', 'column': 'c_recp_borrow'}],
('proc_issue_bonds','q','E'):	['上市公司现金流量表 - 发行债券收到的现金','direct',{'table_name': 'cashflow', 'column': 'proc_issue_bonds'}],
('oth_cash_recp_ral_fnc_act','q','E'):	['上市公司现金流量表 - 收到其他与筹资活动有关的现金','direct',{'table_name': 'cashflow', 'column': 'oth_cash_recp_ral_fnc_act'}],
('stot_cash_in_fnc_act','q','E'):	['上市公司现金流量表 - 筹资活动现金流入小计','direct',{'table_name': 'cashflow', 'column': 'stot_cash_in_fnc_act'}],
('free_cashflow','q','E'):	['上市公司现金流量表 - 企业自由现金流量','direct',{'table_name': 'cashflow', 'column': 'free_cashflow'}],
('c_prepay_amt_borr','q','E'):	['上市公司现金流量表 - 偿还债务支付的现金','direct',{'table_name': 'cashflow', 'column': 'c_prepay_amt_borr'}],
('c_pay_dist_dpcp_int_exp','q','E'):	['上市公司现金流量表 - 分配股利、利润或偿付利息支付的现金','direct',{'table_name': 'cashflow', 'column': 'c_pay_dist_dpcp_int_exp'}],
('incl_dvd_profit_paid_sc_ms','q','E'):	['上市公司现金流量表 - 其中:子公司支付给少数股东的股利、利润','direct',{'table_name': 'cashflow', 'column': 'incl_dvd_profit_paid_sc_ms'}],
('oth_cashpay_ral_fnc_act','q','E'):	['上市公司现金流量表 - 支付其他与筹资活动有关的现金','direct',{'table_name': 'cashflow', 'column': 'oth_cashpay_ral_fnc_act'}],
('stot_cashout_fnc_act','q','E'):	['上市公司现金流量表 - 筹资活动现金流出小计','direct',{'table_name': 'cashflow', 'column': 'stot_cashout_fnc_act'}],
('n_cash_flows_fnc_act','q','E'):	['上市公司现金流量表 - 筹资活动产生的现金流量净额','direct',{'table_name': 'cashflow', 'column': 'n_cash_flows_fnc_act'}],
('eff_fx_flu_cash','q','E'):	['上市公司现金流量表 - 汇率变动对现金的影响','direct',{'table_name': 'cashflow', 'column': 'eff_fx_flu_cash'}],
('n_incr_cash_cash_equ','q','E'):	['上市公司现金流量表 - 现金及现金等价物净增加额','direct',{'table_name': 'cashflow', 'column': 'n_incr_cash_cash_equ'}],
('c_cash_equ_beg_period','q','E'):	['上市公司现金流量表 - 期初现金及现金等价物余额','direct',{'table_name': 'cashflow', 'column': 'c_cash_equ_beg_period'}],
('c_cash_equ_end_period','q','E'):	['上市公司现金流量表 - 期末现金及现金等价物余额','direct',{'table_name': 'cashflow', 'column': 'c_cash_equ_end_period'}],
('c_recp_cap_contrib','q','E'):	['上市公司现金流量表 - 吸收投资收到的现金','direct',{'table_name': 'cashflow', 'column': 'c_recp_cap_contrib'}],
('incl_cash_rec_saims','q','E'):	['上市公司现金流量表 - 其中:子公司吸收少数股东投资收到的现金','direct',{'table_name': 'cashflow', 'column': 'incl_cash_rec_saims'}],
('uncon_invest_loss','q','E'):	['上市公司现金流量表 - 未确认投资损失','direct',{'table_name': 'cashflow', 'column': 'uncon_invest_loss'}],
('prov_depr_assets','q','E'):	['上市公司现金流量表 - 加:资产减值准备','direct',{'table_name': 'cashflow', 'column': 'prov_depr_assets'}],
('depr_fa_coga_dpba','q','E'):	['上市公司现金流量表 - 固定资产折旧、油气资产折耗、生产性生物资产折旧','direct',{'table_name': 'cashflow', 'column': 'depr_fa_coga_dpba'}],
('amort_intang_assets','q','E'):	['上市公司现金流量表 - 无形资产摊销','direct',{'table_name': 'cashflow', 'column': 'amort_intang_assets'}],
('lt_amort_deferred_exp','q','E'):	['上市公司现金流量表 - 长期待摊费用摊销','direct',{'table_name': 'cashflow', 'column': 'lt_amort_deferred_exp'}],
('decr_deferred_exp','q','E'):	['上市公司现金流量表 - 待摊费用减少','direct',{'table_name': 'cashflow', 'column': 'decr_deferred_exp'}],
('incr_acc_exp','q','E'):	['上市公司现金流量表 - 预提费用增加','direct',{'table_name': 'cashflow', 'column': 'incr_acc_exp'}],
('loss_disp_fiolta','q','E'):	['上市公司现金流量表 - 处置固定、无形资产和其他长期资产的损失','direct',{'table_name': 'cashflow', 'column': 'loss_disp_fiolta'}],
('loss_scr_fa','q','E'):	['上市公司现金流量表 - 固定资产报废损失','direct',{'table_name': 'cashflow', 'column': 'loss_scr_fa'}],
('loss_fv_chg','q','E'):	['上市公司现金流量表 - 公允价值变动损失','direct',{'table_name': 'cashflow', 'column': 'loss_fv_chg'}],
('invest_loss','q','E'):	['上市公司现金流量表 - 投资损失','direct',{'table_name': 'cashflow', 'column': 'invest_loss'}],
('decr_def_inc_tax_assets','q','E'):	['上市公司现金流量表 - 递延所得税资产减少','direct',{'table_name': 'cashflow', 'column': 'decr_def_inc_tax_assets'}],
('incr_def_inc_tax_liab','q','E'):	['上市公司现金流量表 - 递延所得税负债增加','direct',{'table_name': 'cashflow', 'column': 'incr_def_inc_tax_liab'}],
('decr_inventories','q','E'):	['上市公司现金流量表 - 存货的减少','direct',{'table_name': 'cashflow', 'column': 'decr_inventories'}],
('decr_oper_payable','q','E'):	['上市公司现金流量表 - 经营性应收项目的减少','direct',{'table_name': 'cashflow', 'column': 'decr_oper_payable'}],
('incr_oper_payable','q','E'):	['上市公司现金流量表 - 经营性应付项目的增加','direct',{'table_name': 'cashflow', 'column': 'incr_oper_payable'}],
('others','q','E'):	['上市公司现金流量表 - 其他','direct',{'table_name': 'cashflow', 'column': 'others'}],
('im_net_cashflow_oper_act','q','E'):	['上市公司现金流量表 - 经营活动产生的现金流量净额(间接法)','direct',{'table_name': 'cashflow', 'column': 'im_net_cashflow_oper_act'}],
('conv_debt_into_cap','q','E'):	['上市公司现金流量表 - 债务转为资本','direct',{'table_name': 'cashflow', 'column': 'conv_debt_into_cap'}],
('conv_copbonds_due_within_1y','q','E'):	['上市公司现金流量表 - 一年内到期的可转换公司债券','direct',{'table_name': 'cashflow', 'column': 'conv_copbonds_due_within_1y'}],
('fa_fnc_leases','q','E'):	['上市公司现金流量表 - 融资租入固定资产','direct',{'table_name': 'cashflow', 'column': 'fa_fnc_leases'}],
('im_n_incr_cash_equ','q','E'):	['上市公司现金流量表 - 现金及现金等价物净增加额(间接法)','direct',{'table_name': 'cashflow', 'column': 'im_n_incr_cash_equ'}],
('net_dism_capital_add','q','E'):	['上市公司现金流量表 - 拆出资金净增加额','direct',{'table_name': 'cashflow', 'column': 'net_dism_capital_add'}],
('net_cash_rece_sec','q','E'):	['上市公司现金流量表 - 代理买卖证券收到的现金净额(元)','direct',{'table_name': 'cashflow', 'column': 'net_cash_rece_sec'}],
('cashflow_credit_impa_loss','q','E'):	['上市公司现金流量表 - 信用减值损失','direct',{'table_name': 'cashflow', 'column': 'credit_impa_loss'}],
('use_right_asset_dep','q','E'):	['上市公司现金流量表 - 使用权资产折旧','direct',{'table_name': 'cashflow', 'column': 'use_right_asset_dep'}],
('oth_loss_asset','q','E'):	['上市公司现金流量表 - 其他资产减值损失','direct',{'table_name': 'cashflow', 'column': 'oth_loss_asset'}],
('end_bal_cash','q','E'):	['上市公司现金流量表 - 现金的期末余额','direct',{'table_name': 'cashflow', 'column': 'end_bal_cash'}],
('beg_bal_cash','q','E'):	['上市公司现金流量表 - 减:现金的期初余额','direct',{'table_name': 'cashflow', 'column': 'beg_bal_cash'}],
('end_bal_cash_equ','q','E'):	['上市公司现金流量表 - 加:现金等价物的期末余额','direct',{'table_name': 'cashflow', 'column': 'end_bal_cash_equ'}],
('beg_bal_cash_equ','q','E'):	['上市公司现金流量表 - 减:现金等价物的期初余额','direct',{'table_name': 'cashflow', 'column': 'beg_bal_cash_equ'}],
('express_revenue','q','E'):	['上市公司业绩快报 - 营业收入(元)','direct',{'table_name': 'express', 'column': 'revenue'}],
('express_operate_profit','q','E'):	['上市公司业绩快报 - 营业利润(元)','direct',{'table_name': 'express', 'column': 'operate_profit'}],
('express_total_profit','q','E'):	['上市公司业绩快报 - 利润总额(元)','direct',{'table_name': 'express', 'column': 'total_profit'}],
('express_n_income','q','E'):	['上市公司业绩快报 - 净利润(元)','direct',{'table_name': 'express', 'column': 'n_income'}],
('express_total_assets','q','E'):	['上市公司业绩快报 - 总资产(元)','direct',{'table_name': 'express', 'column': 'total_assets'}],
('express_total_hldr_eqy_exc_min_int','q','E'):	['上市公司业绩快报 - 股东权益合计(不含少数股东权益)(元)','direct',{'table_name': 'express', 'column': 'total_hldr_eqy_exc_min_int'}],
('express_diluted_eps','q','E'):	['上市公司业绩快报 - 每股收益(摊薄)(元)','direct',{'table_name': 'express', 'column': 'diluted_eps'}],
('diluted_roe','q','E'):	['上市公司业绩快报 - 净资产收益率(摊薄)(%)','direct',{'table_name': 'express', 'column': 'diluted_roe'}],
('yoy_net_profit','q','E'):	['上市公司业绩快报 - 去年同期修正后净利润','direct',{'table_name': 'express', 'column': 'yoy_net_profit'}],
('bps','q','E'):	['上市公司业绩快报 - 每股净资产','direct',{'table_name': 'express', 'column': 'bps'}],
('yoy_sales','q','E'):	['上市公司业绩快报 - 同比增长率:营业收入','direct',{'table_name': 'express', 'column': 'yoy_sales'}],
('yoy_op','q','E'):	['上市公司业绩快报 - 同比增长率:营业利润','direct',{'table_name': 'express', 'column': 'yoy_op'}],
('yoy_tp','q','E'):	['上市公司业绩快报 - 同比增长率:利润总额','direct',{'table_name': 'express', 'column': 'yoy_tp'}],
('yoy_dedu_np','q','E'):	['上市公司业绩快报 - 同比增长率:归属母公司股东的净利润','direct',{'table_name': 'express', 'column': 'yoy_dedu_np'}],
('yoy_eps','q','E'):	['上市公司业绩快报 - 同比增长率:基本每股收益','direct',{'table_name': 'express', 'column': 'yoy_eps'}],
('yoy_roe','q','E'):	['上市公司业绩快报 - 同比增减:加权平均净资产收益率','direct',{'table_name': 'express', 'column': 'yoy_roe'}],
('growth_assets','q','E'):	['上市公司业绩快报 - 比年初增长率:总资产','direct',{'table_name': 'express', 'column': 'growth_assets'}],
('yoy_equity','q','E'):	['上市公司业绩快报 - 比年初增长率:归属母公司的股东权益','direct',{'table_name': 'express', 'column': 'yoy_equity'}],
('growth_bps','q','E'):	['上市公司业绩快报 - 比年初增长率:归属于母公司股东的每股净资产','direct',{'table_name': 'express', 'column': 'growth_bps'}],
('or_last_year','q','E'):	['上市公司业绩快报 - 去年同期营业收入','direct',{'table_name': 'express', 'column': 'or_last_year'}],
('op_last_year','q','E'):	['上市公司业绩快报 - 去年同期营业利润','direct',{'table_name': 'express', 'column': 'op_last_year'}],
('tp_last_year','q','E'):	['上市公司业绩快报 - 去年同期利润总额','direct',{'table_name': 'express', 'column': 'tp_last_year'}],
('np_last_year','q','E'):	['上市公司业绩快报 - 去年同期净利润','direct',{'table_name': 'express', 'column': 'np_last_year'}],
('eps_last_year','q','E'):	['上市公司业绩快报 - 去年同期每股收益','direct',{'table_name': 'express', 'column': 'eps_last_year'}],
('open_net_assets','q','E'):	['上市公司业绩快报 - 期初净资产','direct',{'table_name': 'express', 'column': 'open_net_assets'}],
('open_bps','q','E'):	['上市公司业绩快报 - 期初每股净资产','direct',{'table_name': 'express', 'column': 'open_bps'}],
('perf_summary','q','E'):	['上市公司业绩快报 - 业绩简要说明','direct',{'table_name': 'express', 'column': 'perf_summary'}],
('eps','q','E'):	['上市公司财务指标 - 基本每股收益','direct',{'table_name': 'financial', 'column': 'eps'}],
('dt_eps','q','E'):	['上市公司财务指标 - 稀释每股收益','direct',{'table_name': 'financial', 'column': 'dt_eps'}],
('total_revenue_ps','q','E'):	['上市公司财务指标 - 每股营业总收入','direct',{'table_name': 'financial', 'column': 'total_revenue_ps'}],
('revenue_ps','q','E'):	['上市公司财务指标 - 每股营业收入','direct',{'table_name': 'financial', 'column': 'revenue_ps'}],
('capital_rese_ps','q','E'):	['上市公司财务指标 - 每股资本公积','direct',{'table_name': 'financial', 'column': 'capital_rese_ps'}],
('surplus_rese_ps','q','E'):	['上市公司财务指标 - 每股盈余公积','direct',{'table_name': 'financial', 'column': 'surplus_rese_ps'}],
('undist_profit_ps','q','E'):	['上市公司财务指标 - 每股未分配利润','direct',{'table_name': 'financial', 'column': 'undist_profit_ps'}],
('extra_item','q','E'):	['上市公司财务指标 - 非经常性损益','direct',{'table_name': 'financial', 'column': 'extra_item'}],
('profit_dedt','q','E'):	['上市公司财务指标 - 扣除非经常性损益后的净利润（扣非净利润）','direct',{'table_name': 'financial', 'column': 'profit_dedt'}],
('gross_margin','q','E'):	['上市公司财务指标 - 毛利','direct',{'table_name': 'financial', 'column': 'gross_margin'}],
('current_ratio','q','E'):	['上市公司财务指标 - 流动比率','direct',{'table_name': 'financial', 'column': 'current_ratio'}],
('quick_ratio','q','E'):	['上市公司财务指标 - 速动比率','direct',{'table_name': 'financial', 'column': 'quick_ratio'}],
('cash_ratio','q','E'):	['上市公司财务指标 - 保守速动比率','direct',{'table_name': 'financial', 'column': 'cash_ratio'}],
('invturn_days','q','E'):	['上市公司财务指标 - 存货周转天数','direct',{'table_name': 'financial', 'column': 'invturn_days'}],
('arturn_days','q','E'):	['上市公司财务指标 - 应收账款周转天数','direct',{'table_name': 'financial', 'column': 'arturn_days'}],
('inv_turn','q','E'):	['上市公司财务指标 - 存货周转率','direct',{'table_name': 'financial', 'column': 'inv_turn'}],
('ar_turn','q','E'):	['上市公司财务指标 - 应收账款周转率','direct',{'table_name': 'financial', 'column': 'ar_turn'}],
('ca_turn','q','E'):	['上市公司财务指标 - 流动资产周转率','direct',{'table_name': 'financial', 'column': 'ca_turn'}],
('fa_turn','q','E'):	['上市公司财务指标 - 固定资产周转率','direct',{'table_name': 'financial', 'column': 'fa_turn'}],
('assets_turn','q','E'):	['上市公司财务指标 - 总资产周转率','direct',{'table_name': 'financial', 'column': 'assets_turn'}],
('op_income','q','E'):	['上市公司财务指标 - 经营活动净收益','direct',{'table_name': 'financial', 'column': 'op_income'}],
('valuechange_income','q','E'):	['上市公司财务指标 - 价值变动净收益','direct',{'table_name': 'financial', 'column': 'valuechange_income'}],
('interst_income','q','E'):	['上市公司财务指标 - 利息费用','direct',{'table_name': 'financial', 'column': 'interst_income'}],
('daa','q','E'):	['上市公司财务指标 - 折旧与摊销','direct',{'table_name': 'financial', 'column': 'daa'}],
('ebit','q','E'):	['上市公司财务指标 - 息税前利润','direct',{'table_name': 'financial', 'column': 'ebit'}],
('ebitda','q','E'):	['上市公司财务指标 - 息税折旧摊销前利润','direct',{'table_name': 'financial', 'column': 'ebitda'}],
('fcff','q','E'):	['上市公司财务指标 - 企业自由现金流量','direct',{'table_name': 'financial', 'column': 'fcff'}],
('fcfe','q','E'):	['上市公司财务指标 - 股权自由现金流量','direct',{'table_name': 'financial', 'column': 'fcfe'}],
('current_exint','q','E'):	['上市公司财务指标 - 无息流动负债','direct',{'table_name': 'financial', 'column': 'current_exint'}],
('noncurrent_exint','q','E'):	['上市公司财务指标 - 无息非流动负债','direct',{'table_name': 'financial', 'column': 'noncurrent_exint'}],
('interestdebt','q','E'):	['上市公司财务指标 - 带息债务','direct',{'table_name': 'financial', 'column': 'interestdebt'}],
('netdebt','q','E'):	['上市公司财务指标 - 净债务','direct',{'table_name': 'financial', 'column': 'netdebt'}],
('tangible_asset','q','E'):	['上市公司财务指标 - 有形资产','direct',{'table_name': 'financial', 'column': 'tangible_asset'}],
('working_capital','q','E'):	['上市公司财务指标 - 营运资金','direct',{'table_name': 'financial', 'column': 'working_capital'}],
('networking_capital','q','E'):	['上市公司财务指标 - 营运流动资本','direct',{'table_name': 'financial', 'column': 'networking_capital'}],
('invest_capital','q','E'):	['上市公司财务指标 - 全部投入资本','direct',{'table_name': 'financial', 'column': 'invest_capital'}],
('retained_earnings','q','E'):	['上市公司财务指标 - 留存收益','direct',{'table_name': 'financial', 'column': 'retained_earnings'}],
('diluted2_eps','q','E'):	['上市公司财务指标 - 期末摊薄每股收益','direct',{'table_name': 'financial', 'column': 'diluted2_eps'}],
('express_bps','q','E'):	['上市公司财务指标 - 每股净资产','direct',{'table_name': 'financial', 'column': 'bps'}],
('ocfps','q','E'):	['上市公司财务指标 - 每股经营活动产生的现金流量净额','direct',{'table_name': 'financial', 'column': 'ocfps'}],
('retainedps','q','E'):	['上市公司财务指标 - 每股留存收益','direct',{'table_name': 'financial', 'column': 'retainedps'}],
('cfps','q','E'):	['上市公司财务指标 - 每股现金流量净额','direct',{'table_name': 'financial', 'column': 'cfps'}],
('ebit_ps','q','E'):	['上市公司财务指标 - 每股息税前利润','direct',{'table_name': 'financial', 'column': 'ebit_ps'}],
('fcff_ps','q','E'):	['上市公司财务指标 - 每股企业自由现金流量','direct',{'table_name': 'financial', 'column': 'fcff_ps'}],
('fcfe_ps','q','E'):	['上市公司财务指标 - 每股股东自由现金流量','direct',{'table_name': 'financial', 'column': 'fcfe_ps'}],
('netprofit_margin','q','E'):	['上市公司财务指标 - 销售净利率','direct',{'table_name': 'financial', 'column': 'netprofit_margin'}],
('grossprofit_margin','q','E'):	['上市公司财务指标 - 销售毛利率','direct',{'table_name': 'financial', 'column': 'grossprofit_margin'}],
('cogs_of_sales','q','E'):	['上市公司财务指标 - 销售成本率','direct',{'table_name': 'financial', 'column': 'cogs_of_sales'}],
('expense_of_sales','q','E'):	['上市公司财务指标 - 销售期间费用率','direct',{'table_name': 'financial', 'column': 'expense_of_sales'}],
('profit_to_gr','q','E'):	['上市公司财务指标 - 净利润/营业总收入','direct',{'table_name': 'financial', 'column': 'profit_to_gr'}],
('saleexp_to_gr','q','E'):	['上市公司财务指标 - 销售费用/营业总收入','direct',{'table_name': 'financial', 'column': 'saleexp_to_gr'}],
('adminexp_of_gr','q','E'):	['上市公司财务指标 - 管理费用/营业总收入','direct',{'table_name': 'financial', 'column': 'adminexp_of_gr'}],
('finaexp_of_gr','q','E'):	['上市公司财务指标 - 财务费用/营业总收入','direct',{'table_name': 'financial', 'column': 'finaexp_of_gr'}],
('impai_ttm','q','E'):	['上市公司财务指标 - 资产减值损失/营业总收入','direct',{'table_name': 'financial', 'column': 'impai_ttm'}],
('gc_of_gr','q','E'):	['上市公司财务指标 - 营业总成本/营业总收入','direct',{'table_name': 'financial', 'column': 'gc_of_gr'}],
('op_of_gr','q','E'):	['上市公司财务指标 - 营业利润/营业总收入','direct',{'table_name': 'financial', 'column': 'op_of_gr'}],
('ebit_of_gr','q','E'):	['上市公司财务指标 - 息税前利润/营业总收入','direct',{'table_name': 'financial', 'column': 'ebit_of_gr'}],
('roe','q','E'):	['上市公司财务指标 - 净资产收益率','direct',{'table_name': 'financial', 'column': 'roe'}],
('roe_waa','q','E'):	['上市公司财务指标 - 加权平均净资产收益率','direct',{'table_name': 'financial', 'column': 'roe_waa'}],
('roe_dt','q','E'):	['上市公司财务指标 - 净资产收益率(扣除非经常损益)','direct',{'table_name': 'financial', 'column': 'roe_dt'}],
('roa','q','E'):	['上市公司财务指标 - 总资产报酬率','direct',{'table_name': 'financial', 'column': 'roa'}],
('npta','q','E'):	['上市公司财务指标 - 总资产净利润','direct',{'table_name': 'financial', 'column': 'npta'}],
('roic','q','E'):	['上市公司财务指标 - 投入资本回报率','direct',{'table_name': 'financial', 'column': 'roic'}],
('roe_yearly','q','E'):	['上市公司财务指标 - 年化净资产收益率','direct',{'table_name': 'financial', 'column': 'roe_yearly'}],
('roa2_yearly','q','E'):	['上市公司财务指标 - 年化总资产报酬率','direct',{'table_name': 'financial', 'column': 'roa2_yearly'}],
('roe_avg','q','E'):	['上市公司财务指标 - 平均净资产收益率(增发条件)','direct',{'table_name': 'financial', 'column': 'roe_avg'}],
('opincome_of_ebt','q','E'):	['上市公司财务指标 - 经营活动净收益/利润总额','direct',{'table_name': 'financial', 'column': 'opincome_of_ebt'}],
('investincome_of_ebt','q','E'):	['上市公司财务指标 - 价值变动净收益/利润总额','direct',{'table_name': 'financial', 'column': 'investincome_of_ebt'}],
('n_op_profit_of_ebt','q','E'):	['上市公司财务指标 - 营业外收支净额/利润总额','direct',{'table_name': 'financial', 'column': 'n_op_profit_of_ebt'}],
('tax_to_ebt','q','E'):	['上市公司财务指标 - 所得税/利润总额','direct',{'table_name': 'financial', 'column': 'tax_to_ebt'}],
('dtprofit_to_profit','q','E'):	['上市公司财务指标 - 扣除非经常损益后的净利润/净利润','direct',{'table_name': 'financial', 'column': 'dtprofit_to_profit'}],
('salescash_to_or','q','E'):	['上市公司财务指标 - 销售商品提供劳务收到的现金/营业收入','direct',{'table_name': 'financial', 'column': 'salescash_to_or'}],
('ocf_to_or','q','E'):	['上市公司财务指标 - 经营活动产生的现金流量净额/营业收入','direct',{'table_name': 'financial', 'column': 'ocf_to_or'}],
('ocf_to_opincome','q','E'):	['上市公司财务指标 - 经营活动产生的现金流量净额/经营活动净收益','direct',{'table_name': 'financial', 'column': 'ocf_to_opincome'}],
('capitalized_to_da','q','E'):	['上市公司财务指标 - 资本支出/折旧和摊销','direct',{'table_name': 'financial', 'column': 'capitalized_to_da'}],
('debt_to_assets','q','E'):	['上市公司财务指标 - 资产负债率','direct',{'table_name': 'financial', 'column': 'debt_to_assets'}],
('assets_to_eqt','q','E'):	['上市公司财务指标 - 权益乘数','direct',{'table_name': 'financial', 'column': 'assets_to_eqt'}],
('dp_assets_to_eqt','q','E'):	['上市公司财务指标 - 权益乘数(杜邦分析)','direct',{'table_name': 'financial', 'column': 'dp_assets_to_eqt'}],
('ca_to_assets','q','E'):	['上市公司财务指标 - 流动资产/总资产','direct',{'table_name': 'financial', 'column': 'ca_to_assets'}],
('nca_to_assets','q','E'):	['上市公司财务指标 - 非流动资产/总资产','direct',{'table_name': 'financial', 'column': 'nca_to_assets'}],
('tbassets_to_totalassets','q','E'):	['上市公司财务指标 - 有形资产/总资产','direct',{'table_name': 'financial', 'column': 'tbassets_to_totalassets'}],
('int_to_talcap','q','E'):	['上市公司财务指标 - 带息债务/全部投入资本','direct',{'table_name': 'financial', 'column': 'int_to_talcap'}],
('eqt_to_talcapital','q','E'):	['上市公司财务指标 - 归属于母公司的股东权益/全部投入资本','direct',{'table_name': 'financial', 'column': 'eqt_to_talcapital'}],
('currentdebt_to_debt','q','E'):	['上市公司财务指标 - 流动负债/负债合计','direct',{'table_name': 'financial', 'column': 'currentdebt_to_debt'}],
('longdeb_to_debt','q','E'):	['上市公司财务指标 - 非流动负债/负债合计','direct',{'table_name': 'financial', 'column': 'longdeb_to_debt'}],
('ocf_to_shortdebt','q','E'):	['上市公司财务指标 - 经营活动产生的现金流量净额/流动负债','direct',{'table_name': 'financial', 'column': 'ocf_to_shortdebt'}],
('debt_to_eqt','q','E'):	['上市公司财务指标 - 产权比率','direct',{'table_name': 'financial', 'column': 'debt_to_eqt'}],
('eqt_to_debt','q','E'):	['上市公司财务指标 - 归属于母公司的股东权益/负债合计','direct',{'table_name': 'financial', 'column': 'eqt_to_debt'}],
('eqt_to_interestdebt','q','E'):	['上市公司财务指标 - 归属于母公司的股东权益/带息债务','direct',{'table_name': 'financial', 'column': 'eqt_to_interestdebt'}],
('tangibleasset_to_debt','q','E'):	['上市公司财务指标 - 有形资产/负债合计','direct',{'table_name': 'financial', 'column': 'tangibleasset_to_debt'}],
('tangasset_to_intdebt','q','E'):	['上市公司财务指标 - 有形资产/带息债务','direct',{'table_name': 'financial', 'column': 'tangasset_to_intdebt'}],
('tangibleasset_to_netdebt','q','E'):	['上市公司财务指标 - 有形资产/净债务','direct',{'table_name': 'financial', 'column': 'tangibleasset_to_netdebt'}],
('ocf_to_debt','q','E'):	['上市公司财务指标 - 经营活动产生的现金流量净额/负债合计','direct',{'table_name': 'financial', 'column': 'ocf_to_debt'}],
('ocf_to_interestdebt','q','E'):	['上市公司财务指标 - 经营活动产生的现金流量净额/带息债务','direct',{'table_name': 'financial', 'column': 'ocf_to_interestdebt'}],
('ocf_to_netdebt','q','E'):	['上市公司财务指标 - 经营活动产生的现金流量净额/净债务','direct',{'table_name': 'financial', 'column': 'ocf_to_netdebt'}],
('ebit_to_interest','q','E'):	['上市公司财务指标 - 已获利息倍数(EBIT/利息费用)','direct',{'table_name': 'financial', 'column': 'ebit_to_interest'}],
('longdebt_to_workingcapital','q','E'):	['上市公司财务指标 - 长期债务与营运资金比率','direct',{'table_name': 'financial', 'column': 'longdebt_to_workingcapital'}],
('ebitda_to_debt','q','E'):	['上市公司财务指标 - 息税折旧摊销前利润/负债合计','direct',{'table_name': 'financial', 'column': 'ebitda_to_debt'}],
('turn_days','q','E'):	['上市公司财务指标 - 营业周期','direct',{'table_name': 'financial', 'column': 'turn_days'}],
('roa_yearly','q','E'):	['上市公司财务指标 - 年化总资产净利率','direct',{'table_name': 'financial', 'column': 'roa_yearly'}],
('roa_dp','q','E'):	['上市公司财务指标 - 总资产净利率(杜邦分析)','direct',{'table_name': 'financial', 'column': 'roa_dp'}],
('fixed_assets','q','E'):	['上市公司财务指标 - 固定资产合计','direct',{'table_name': 'financial', 'column': 'fixed_assets'}],
('profit_prefin_exp','q','E'):	['上市公司财务指标 - 扣除财务费用前营业利润','direct',{'table_name': 'financial', 'column': 'profit_prefin_exp'}],
('non_op_profit','q','E'):	['上市公司财务指标 - 非营业利润','direct',{'table_name': 'financial', 'column': 'non_op_profit'}],
('op_to_ebt','q','E'):	['上市公司财务指标 - 营业利润／利润总额','direct',{'table_name': 'financial', 'column': 'op_to_ebt'}],
('nop_to_ebt','q','E'):	['上市公司财务指标 - 非营业利润／利润总额','direct',{'table_name': 'financial', 'column': 'nop_to_ebt'}],
('ocf_to_profit','q','E'):	['上市公司财务指标 - 经营活动产生的现金流量净额／营业利润','direct',{'table_name': 'financial', 'column': 'ocf_to_profit'}],
('cash_to_liqdebt','q','E'):	['上市公司财务指标 - 货币资金／流动负债','direct',{'table_name': 'financial', 'column': 'cash_to_liqdebt'}],
('cash_to_liqdebt_withinterest','q','E'):	['上市公司财务指标 - 货币资金／带息流动负债','direct',{'table_name': 'financial', 'column': 'cash_to_liqdebt_withinterest'}],
('op_to_liqdebt','q','E'):	['上市公司财务指标 - 营业利润／流动负债','direct',{'table_name': 'financial', 'column': 'op_to_liqdebt'}],
('op_to_debt','q','E'):	['上市公司财务指标 - 营业利润／负债合计','direct',{'table_name': 'financial', 'column': 'op_to_debt'}],
('roic_yearly','q','E'):	['上市公司财务指标 - 年化投入资本回报率','direct',{'table_name': 'financial', 'column': 'roic_yearly'}],
('total_fa_trun','q','E'):	['上市公司财务指标 - 固定资产合计周转率','direct',{'table_name': 'financial', 'column': 'total_fa_trun'}],
('profit_to_op','q','E'):	['上市公司财务指标 - 利润总额／营业收入','direct',{'table_name': 'financial', 'column': 'profit_to_op'}],
('q_opincome','q','E'):	['上市公司财务指标 - 经营活动单季度净收益','direct',{'table_name': 'financial', 'column': 'q_opincome'}],
('q_investincome','q','E'):	['上市公司财务指标 - 价值变动单季度净收益','direct',{'table_name': 'financial', 'column': 'q_investincome'}],
('q_dtprofit','q','E'):	['上市公司财务指标 - 扣除非经常损益后的单季度净利润','direct',{'table_name': 'financial', 'column': 'q_dtprofit'}],
('q_eps','q','E'):	['上市公司财务指标 - 每股收益(单季度)','direct',{'table_name': 'financial', 'column': 'q_eps'}],
('q_netprofit_margin','q','E'):	['上市公司财务指标 - 销售净利率(单季度)','direct',{'table_name': 'financial', 'column': 'q_netprofit_margin'}],
('q_gsprofit_margin','q','E'):	['上市公司财务指标 - 销售毛利率(单季度)','direct',{'table_name': 'financial', 'column': 'q_gsprofit_margin'}],
('q_exp_to_sales','q','E'):	['上市公司财务指标 - 销售期间费用率(单季度)','direct',{'table_name': 'financial', 'column': 'q_exp_to_sales'}],
('q_profit_to_gr','q','E'):	['上市公司财务指标 - 净利润／营业总收入(单季度)','direct',{'table_name': 'financial', 'column': 'q_profit_to_gr'}],
('q_saleexp_to_gr','q','E'):	['上市公司财务指标 - 销售费用／营业总收入 (单季度)','direct',{'table_name': 'financial', 'column': 'q_saleexp_to_gr'}],
('q_adminexp_to_gr','q','E'):	['上市公司财务指标 - 管理费用／营业总收入 (单季度)','direct',{'table_name': 'financial', 'column': 'q_adminexp_to_gr'}],
('q_finaexp_to_gr','q','E'):	['上市公司财务指标 - 财务费用／营业总收入 (单季度)','direct',{'table_name': 'financial', 'column': 'q_finaexp_to_gr'}],
('q_impair_to_gr_ttm','q','E'):	['上市公司财务指标 - 资产减值损失／营业总收入(单季度)','direct',{'table_name': 'financial', 'column': 'q_impair_to_gr_ttm'}],
('q_gc_to_gr','q','E'):	['上市公司财务指标 - 营业总成本／营业总收入 (单季度)','direct',{'table_name': 'financial', 'column': 'q_gc_to_gr'}],
('q_op_to_gr','q','E'):	['上市公司财务指标 - 营业利润／营业总收入(单季度)','direct',{'table_name': 'financial', 'column': 'q_op_to_gr'}],
('q_roe','q','E'):	['上市公司财务指标 - 净资产收益率(单季度)','direct',{'table_name': 'financial', 'column': 'q_roe'}],
('q_dt_roe','q','E'):	['上市公司财务指标 - 净资产单季度收益率(扣除非经常损益)','direct',{'table_name': 'financial', 'column': 'q_dt_roe'}],
('q_npta','q','E'):	['上市公司财务指标 - 总资产净利润(单季度)','direct',{'table_name': 'financial', 'column': 'q_npta'}],
('q_opincome_to_ebt','q','E'):	['上市公司财务指标 - 经营活动净收益／利润总额(单季度)','direct',{'table_name': 'financial', 'column': 'q_opincome_to_ebt'}],
('q_investincome_to_ebt','q','E'):	['上市公司财务指标 - 价值变动净收益／利润总额(单季度)','direct',{'table_name': 'financial', 'column': 'q_investincome_to_ebt'}],
('q_dtprofit_to_profit','q','E'):	['上市公司财务指标 - 扣除非经常损益后的净利润／净利润(单季度)','direct',{'table_name': 'financial', 'column': 'q_dtprofit_to_profit'}],
('q_salescash_to_or','q','E'):	['上市公司财务指标 - 销售商品提供劳务收到的现金／营业收入(单季度)','direct',{'table_name': 'financial', 'column': 'q_salescash_to_or'}],
('q_ocf_to_sales','q','E'):	['上市公司财务指标 - 经营活动产生的现金流量净额／营业收入(单季度)','direct',{'table_name': 'financial', 'column': 'q_ocf_to_sales'}],
('q_ocf_to_or','q','E'):	['上市公司财务指标 - 经营活动产生的现金流量净额／经营活动净收益(单季度)','direct',{'table_name': 'financial', 'column': 'q_ocf_to_or'}],
('basic_eps_yoy','q','E'):	['上市公司财务指标 - 基本每股收益同比增长率(%)','direct',{'table_name': 'financial', 'column': 'basic_eps_yoy'}],
('dt_eps_yoy','q','E'):	['上市公司财务指标 - 稀释每股收益同比增长率(%)','direct',{'table_name': 'financial', 'column': 'dt_eps_yoy'}],
('cfps_yoy','q','E'):	['上市公司财务指标 - 每股经营活动产生的现金流量净额同比增长率(%)','direct',{'table_name': 'financial', 'column': 'cfps_yoy'}],
('op_yoy','q','E'):	['上市公司财务指标 - 营业利润同比增长率(%)','direct',{'table_name': 'financial', 'column': 'op_yoy'}],
('ebt_yoy','q','E'):	['上市公司财务指标 - 利润总额同比增长率(%)','direct',{'table_name': 'financial', 'column': 'ebt_yoy'}],
('netprofit_yoy','q','E'):	['上市公司财务指标 - 归属母公司股东的净利润同比增长率(%)','direct',{'table_name': 'financial', 'column': 'netprofit_yoy'}],
('dt_netprofit_yoy','q','E'):	['上市公司财务指标 - 归属母公司股东的净利润-扣除非经常损益同比增长率(%)','direct',{'table_name': 'financial', 'column': 'dt_netprofit_yoy'}],
('ocf_yoy','q','E'):	['上市公司财务指标 - 经营活动产生的现金流量净额同比增长率(%)','direct',{'table_name': 'financial', 'column': 'ocf_yoy'}],
('roe_yoy','q','E'):	['上市公司财务指标 - 净资产收益率(摊薄)同比增长率(%)','direct',{'table_name': 'financial', 'column': 'roe_yoy'}],
('bps_yoy','q','E'):	['上市公司财务指标 - 每股净资产相对年初增长率(%)','direct',{'table_name': 'financial', 'column': 'bps_yoy'}],
('assets_yoy','q','E'):	['上市公司财务指标 - 资产总计相对年初增长率(%)','direct',{'table_name': 'financial', 'column': 'assets_yoy'}],
('eqt_yoy','q','E'):	['上市公司财务指标 - 归属母公司的股东权益相对年初增长率(%)','direct',{'table_name': 'financial', 'column': 'eqt_yoy'}],
('tr_yoy','q','E'):	['上市公司财务指标 - 营业总收入同比增长率(%)','direct',{'table_name': 'financial', 'column': 'tr_yoy'}],
('or_yoy','q','E'):	['上市公司财务指标 - 营业收入同比增长率(%)','direct',{'table_name': 'financial', 'column': 'or_yoy'}],
('q_gr_yoy','q','E'):	['上市公司财务指标 - 营业总收入同比增长率(%)(单季度)','direct',{'table_name': 'financial', 'column': 'q_gr_yoy'}],
('q_gr_qoq','q','E'):	['上市公司财务指标 - 营业总收入环比增长率(%)(单季度)','direct',{'table_name': 'financial', 'column': 'q_gr_qoq'}],
('q_sales_yoy','q','E'):	['上市公司财务指标 - 营业收入同比增长率(%)(单季度)','direct',{'table_name': 'financial', 'column': 'q_sales_yoy'}],
('q_sales_qoq','q','E'):	['上市公司财务指标 - 营业收入环比增长率(%)(单季度)','direct',{'table_name': 'financial', 'column': 'q_sales_qoq'}],
('q_op_yoy','q','E'):	['上市公司财务指标 - 营业利润同比增长率(%)(单季度)','direct',{'table_name': 'financial', 'column': 'q_op_yoy'}],
('q_op_qoq','q','E'):	['上市公司财务指标 - 营业利润环比增长率(%)(单季度)','direct',{'table_name': 'financial', 'column': 'q_op_qoq'}],
('q_profit_yoy','q','E'):	['上市公司财务指标 - 净利润同比增长率(%)(单季度)','direct',{'table_name': 'financial', 'column': 'q_profit_yoy'}],
('q_profit_qoq','q','E'):	['上市公司财务指标 - 净利润环比增长率(%)(单季度)','direct',{'table_name': 'financial', 'column': 'q_profit_qoq'}],
('q_netprofit_yoy','q','E'):	['上市公司财务指标 - 归属母公司股东的净利润同比增长率(%)(单季度)','direct',{'table_name': 'financial', 'column': 'q_netprofit_yoy'}],
('q_netprofit_qoq','q','E'):	['上市公司财务指标 - 归属母公司股东的净利润环比增长率(%)(单季度)','direct',{'table_name': 'financial', 'column': 'q_netprofit_qoq'}],
('equity_yoy','q','E'):	['上市公司财务指标 - 净资产同比增长率','direct',{'table_name': 'financial', 'column': 'equity_yoy'}],
('rd_exp','q','E'):	['上市公司财务指标 - 研发费用','direct',{'table_name': 'financial', 'column': 'rd_exp'}],
('rzye','d','Any'):	['融资融券交易汇总 - 融资余额(元)','direct',{'table_name': 'margin', 'column': 'rzye'}],
('rzmre','d','Any'):	['融资融券交易汇总 - 融资买入额(元)','direct',{'table_name': 'margin', 'column': 'rzmre'}],
('rzche','d','Any'):	['融资融券交易汇总 - 融资偿还额(元)','direct',{'table_name': 'margin', 'column': 'rzche'}],
('rqye','d','Any'):	['融资融券交易汇总 - 融券余额(元)','direct',{'table_name': 'margin', 'column': 'rqye'}],
('rqmcl','d','Any'):	['融资融券交易汇总 - 融券卖出量(股,份,手)','direct',{'table_name': 'margin', 'column': 'rqmcl'}],
('rzrqye','d','Any'):	['融资融券交易汇总 - 融资融券余额(元)','direct',{'table_name': 'margin', 'column': 'rzrqye'}],
('rqyl','d','Any'):	['融资融券交易汇总 - 融券余量(股,份,手)','direct',{'table_name': 'margin', 'column': 'rqyl'}],
('top_list_close','d','E'):	['龙虎榜交易明细 - 收盘价','event_signal',{'table_name': 'top_list', 'column': 'close'}],
('top_list_pct_change','d','E'):	['龙虎榜交易明细 - 涨跌幅','event_signal',{'table_name': 'top_list', 'column': 'pct_change'}],
('top_list_turnover_rate','d','E'):	['龙虎榜交易明细 - 换手率','event_signal',{'table_name': 'top_list', 'column': 'turnover_rate'}],
('top_list_amount','d','E'):	['龙虎榜交易明细 - 总成交额','event_signal',{'table_name': 'top_list', 'column': 'amount'}],
('top_list_l_sell','d','E'):	['龙虎榜交易明细 - 龙虎榜卖出额','event_signal',{'table_name': 'top_list', 'column': 'l_sell'}],
('top_list_l_buy','d','E'):	['龙虎榜交易明细 - 龙虎榜买入额','event_signal',{'table_name': 'top_list', 'column': 'l_buy'}],
('top_list_l_amount','d','E'):	['龙虎榜交易明细- 龙虎榜成交额','event_signal',{'table_name': 'top_list', 'column': 'l_amount'}],
('top_list_net_amount','d','E'):	['龙虎榜交易明细 - 龙虎榜净买入额','event_signal',{'table_name': 'top_list', 'column': 'net_amount'}],
('top_list_net_rate','d','E'):	['龙虎榜交易明细 - 龙虎榜净买额占比','event_signal',{'table_name': 'top_list', 'column': 'net_rate'}],
('top_list_amount_rate','d','E'):	['龙虎榜交易明细 - 龙虎榜成交额占比','event_signal',{'table_name': 'top_list', 'column': 'amount_rate'}],
('top_list_float_values','d','E'):	['龙虎榜交易明细 - 当日流通市值','event_signal',{'table_name': 'top_list', 'column': 'float_values'}],
('top_list_reason','d','E'):	['龙虎榜交易明细 - 上榜理由','event_signal',{'table_name': 'top_list', 'column': 'reason'}],
('total_mv','d','IDX'):	['指数技术指标 - 当日总市值（元）','direct',{'table_name': 'index_indicator', 'column': 'total_mv'}],
('float_mv','d','IDX'):	['指数技术指标 - 当日流通市值（元）','direct',{'table_name': 'index_indicator', 'column': 'float_mv'}],
('total_share     float','d','IDX'):	['指数技术指标 - 当日总股本（股）','direct',{'table_name': 'index_indicator', 'column': 'total_share'}],
('float_share','d','IDX'):	['指数技术指标 - 当日流通股本（股）','direct',{'table_name': 'index_indicator', 'column': 'float_share'}],
('free_share','d','IDX'):	['指数技术指标 - 当日自由流通股本（股）','direct',{'table_name': 'index_indicator', 'column': 'free_share'}],
('turnover_rate','d','IDX'):	['指数技术指标 - 换手率','direct',{'table_name': 'index_indicator', 'column': 'turnover_rate'}],
('turnover_rate_f','d','IDX'):	['指数技术指标 - 换手率(基于自由流通股本)','direct',{'table_name': 'index_indicator', 'column': 'turnover_rate_f'}],
('pe','d','IDX'):	['指数技术指标 - 市盈率','direct',{'table_name': 'index_indicator', 'column': 'pe'}],
('pe_ttm','d','IDX'):	['指数技术指标 - 市盈率TTM','direct',{'table_name': 'index_indicator', 'column': 'pe_ttm'}],
('pb','d','IDX'):	['指数技术指标 - 市净率','direct',{'table_name': 'index_indicator', 'column': 'pb'}],
('turnover_rate','d','E'):	['股票技术指标 - 换手率（%）','direct',{'table_name': 'stock_indicator', 'column': 'turnover_rate'}],
('turnover_rate_f','d','E'):	['股票技术指标 - 换手率（自由流通股）','direct',{'table_name': 'stock_indicator', 'column': 'turnover_rate_f'}],
('volume_ratio','d','E'):	['股票技术指标 - 量比','direct',{'table_name': 'stock_indicator', 'column': 'volume_ratio'}],
('pe','d','E'):	['股票技术指标 - 市盈率（总市值/净利润， 亏损的PE为空）','direct',{'table_name': 'stock_indicator', 'column': 'pe'}],
('pe_ttm','d','E'):	['股票技术指标 - 市盈率（TTM，亏损的PE为空）','direct',{'table_name': 'stock_indicator', 'column': 'pe_ttm'}],
('pb','d','E'):	['股票技术指标 - 市净率（总市值/净资产）','direct',{'table_name': 'stock_indicator', 'column': 'pb'}],
('ps','d','E'):	['股票技术指标 - 市销率','direct',{'table_name': 'stock_indicator', 'column': 'ps'}],
('ps_ttm','d','E'):	['股票技术指标 - 市销率（TTM）','direct',{'table_name': 'stock_indicator', 'column': 'ps_ttm'}],
('dv_ratio','d','E'):	['股票技术指标 - 股息率 （%）','direct',{'table_name': 'stock_indicator', 'column': 'dv_ratio'}],
('dv_ttm','d','E'):	['股票技术指标 - 股息率（TTM）（%）','direct',{'table_name': 'stock_indicator', 'column': 'dv_ttm'}],
('total_share','d','E'):	['股票技术指标 - 总股本 （万股）','direct',{'table_name': 'stock_indicator', 'column': 'total_share'}],
('float_share','d','E'):	['股票技术指标 - 流通股本 （万股）','direct',{'table_name': 'stock_indicator', 'column': 'float_share'}],
('free_share','d','E'):	['股票技术指标 - 自由流通股本 （万）','direct',{'table_name': 'stock_indicator', 'column': 'free_share'}],
('total_mv','d','E'):	['股票技术指标 - 总市值 （万元）','direct',{'table_name': 'stock_indicator', 'column': 'total_mv'}],
('circ_mv','d','E'):	['股票技术指标 - 流通市值（万元）','direct',{'table_name': 'stock_indicator', 'column': 'circ_mv'}],
('vol_ratio','d','E'):	['股票技术指标 - 量比','direct',{'table_name': 'stock_indicator2', 'column': 'vol_ratio'}],
('turn_over','d','E'):	['股票技术指标 - 换手率','direct',{'table_name': 'stock_indicator2', 'column': 'turn_over'}],
('swing','d','E'):	['股票技术指标 - 振幅','direct',{'table_name': 'stock_indicator2', 'column': 'swing'}],
('selling','d','E'):	['股票技术指标 - 内盘（主动卖，手）','direct',{'table_name': 'stock_indicator2', 'column': 'selling'}],
('buying','d','E'):	['股票技术指标 - 外盘（主动买， 手）','direct',{'table_name': 'stock_indicator2', 'column': 'buying'}],
('total_share_b','d','E'):	['股票技术指标 - 总股本(亿)','direct',{'table_name': 'stock_indicator2', 'column': 'total_share'}],
('float_share_b','d','E'):	['股票技术指标 - 流通股本(亿)','direct',{'table_name': 'stock_indicator2', 'column': 'float_share'}],
('pe_2','d','E'):	['股票技术指标 - 动态市盈率','direct',{'table_name': 'stock_indicator2', 'column': 'pe'}],
('float_mv_2','d','E'):	['股票技术指标 - 流通市值','direct',{'table_name': 'stock_indicator2', 'column': 'float_mv'}],
('total_mv_2','d','E'):	['股票技术指标 - 总市值','direct',{'table_name': 'stock_indicator2', 'column': 'total_mv'}],
('avg_price','d','E'):	['股票技术指标 - 平均价','direct',{'table_name': 'stock_indicator2', 'column': 'avg_price'}],
('strength','d','E'):	['股票技术指标 - 强弱度(%)','direct',{'table_name': 'stock_indicator2', 'column': 'strength'}],
('activity','d','E'):	['股票技术指标 - 活跃度(%)','direct',{'table_name': 'stock_indicator2', 'column': 'activity'}],
('avg_turnover','d','E'):	['股票技术指标 - 笔换手','direct',{'table_name': 'stock_indicator2', 'column': 'avg_turnover'}],
('attack','d','E'):	['股票技术指标 - 攻击波(%)','direct',{'table_name': 'stock_indicator2', 'column': 'attack'}],
('interval_3','d','E'):	['股票技术指标 - 近3月涨幅','direct',{'table_name': 'stock_indicator2', 'column': 'interval_3'}],
('interval_6','d','E'):	['股票技术指标 - 近6月涨幅','direct',{'table_name': 'stock_indicator2', 'column': 'interval_6'}],
('cur_name','d','E'):	['股票 - 当前最新证券名称','event_status',{'table_name': 'stock_names', 'column': 'name'}],
('change_reason','d','E'):	['股票更名 - 变更原因','event_signal',{'table_name': 'stock_names', 'column': 'change_reason'}],
('suspend_timing','d','E'):	['日内停牌时间段','event_signal',{'table_name': 'stock_suspend', 'column': 'suspend_timing'}],
('is_suspended','d','E'):	['停复牌类型：S-停牌，R-复牌','event_signal',{'table_name': 'stock_suspend', 'column': 'suspend_type'}],
('is_HS_top10','d','E'):	['沪深港通十大成交股上榜','event_signal',{'table_name': 'HS_top10_stock', 'column': 'name'}],
('top10_close','d','E'):	['沪深港通十大成交股上榜 - 收盘价','event_signal',{'table_name': 'HS_top10_stock', 'column': 'close'}],
('top10_change','d','E'):	['沪深港通十大成交股上榜 - 涨跌额','event_signal',{'table_name': 'HS_top10_stock', 'column': 'change'}],
('top10_rank','d','E'):	['沪深港通十大成交股上榜 - 资金排名','event_signal',{'table_name': 'HS_top10_stock', 'column': 'rank'}],
('top10_amount','d','E'):	['沪深港通十大成交股上榜 - 成交金额（元）','event_signal',{'table_name': 'HS_top10_stock', 'column': 'amount'}],
('top10_net_amount','d','E'):	['沪深港通十大成交股上榜 - 净成交金额（元）','event_signal',{'table_name': 'HS_top10_stock', 'column': 'net_amount'}],
('top10_buy','d','E'):	['沪深港通十大成交股上榜 - 买入金额（元）','event_signal',{'table_name': 'HS_top10_stock', 'column': 'buy'}],
('top10_sell','d','E'):	['沪深港通十大成交股上榜 - 卖出金额（元）','event_signal',{'table_name': 'HS_top10_stock', 'column': 'sell'}],
('fd_share','d','FD'):	['基金份额（万）','direct',{'table_name': 'fund_share', 'column': 'fd_share'}],
('managers_name','d','FD'):	['基金经理姓名','event_multi_stat',{'table_name': 'fund_manager', 'column': 'name', 'id_index': 'name', 'start_col': 'begin_date', 'end_col': 'end_date'}],
('managers_gender','d','FD'):	['基金经理 - 性别','event_multi_stat',{'table_name': 'fund_manager', 'column': 'gender', 'id_index': 'name', 'start_col': 'begin_date', 'end_col': 'end_date'}],
('managers_birth_year','d','FD'):	['基金经理 - 出生年份','event_multi_stat',{'table_name': 'fund_manager', 'column': 'birth_year', 'id_index': 'name', 'start_col': 'begin_date', 'end_col': 'end_date'}],
('managers_edu','d','FD'):	['基金经理 - 学历','event_multi_stat',{'table_name': 'fund_manager', 'column': 'edu', 'id_index': 'name', 'start_col': 'begin_date', 'end_col': 'end_date'}],
('nationality','d','FD'):	['基金经理 - 国籍','event_multi_stat',{'table_name': 'fund_manager', 'column': 'nationality', 'id_index': 'name', 'start_col': 'begin_date', 'end_col': 'end_date'}],
('managers_resume','d','FD'):	['基金经理 - 简历','event_multi_stat',{'table_name': 'fund_manager', 'column': 'resume', 'id_index': 'name', 'start_col': 'begin_date', 'end_col': 'end_date'}],
('div_proc','d','E'):	['实施进度','event_status',{'table_name': 'dividend', 'column': 'div_proc'}],
('stk_div','d','E'):	['每股送转','event_status',{'table_name': 'dividend', 'column': 'stk_div'}],
('stk_bo_rate','d','E'):	['每股送股比例','event_status',{'table_name': 'dividend', 'column': 'stk_bo_rate'}],
('stk_co_rate','d','E'):	['每股转增比例','event_status',{'table_name': 'dividend', 'column': 'stk_co_rate'}],
('cash_div','d','E'):	['每股分红（税后）','event_status',{'table_name': 'dividend', 'column': 'cash_div'}],
('cash_div_tax','d','E'):	['每股分红（税前）','event_status',{'table_name': 'dividend', 'column': 'cash_div_tax'}],
('record_date','d','E'):	['股权登记日','event_signal',{'table_name': 'dividend', 'column': 'record_date'}],
('ex_date','d','E'):	['除权除息日','event_signal',{'table_name': 'dividend', 'column': 'ex_date'}],
('pay_date','d','E'):	['派息日','event_signal',{'table_name': 'dividend', 'column': 'pay_date'}],
('imp_ann_date','d','E'):	['实施公告日','event_signal',{'table_name': 'dividend', 'column': 'imp_ann_date'}],
('base_date','d','E'):	['基准日','event_signal',{'table_name': 'dividend', 'column': 'base_date'}],
('base_share','d','E'):	['基准股本（万）','event_status',{'table_name': 'dividend', 'column': 'base_share'}],
('exalter','d','E'):	['龙虎榜机构明细 - 营业部名称','event_signal',{'table_name': 'top_inst', 'column': 'exalter'}],
('side','d','E'):	['龙虎榜机构明细 - 买卖类型0：买入金额最大的前5名， 1：卖出金额最大的前5名','event_signal',{'table_name': 'top_inst', 'column': 'side'}],
('buy','d','E'):	['龙虎榜机构明细 - 买入额（元）','event_signal',{'table_name': 'top_inst', 'column': 'buy'}],
('buy_rate','d','E'):	['龙虎榜机构明细 - 买入占总成交比例','event_signal',{'table_name': 'top_inst', 'column': 'buy_rate'}],
('sell','d','E'):	['龙虎榜机构明细 - 卖出额（元）','event_signal',{'table_name': 'top_inst', 'column': 'sell'}],
('sell_rate','d','E'):	['龙虎榜机构明细 - 卖出占总成交比例','event_signal',{'table_name': 'top_inst', 'column': 'sell_rate'}],
('net_buy','d','E'):	['龙虎榜机构明细 - 净成交额（元）','event_signal',{'table_name': 'top_inst', 'column': 'net_buy'}],
('reason','d','E'):	['龙虎榜机构明细 - 上榜理由','event_signal',{'table_name': 'top_inst', 'column': 'reason'}],
('shibor:%','d','None'):	['上海银行间行业拆放利率(SHIBOR) - %','direct',{'table_name': 'shibor', 'column': '%'}],
('libor_usd:%','d','None'):	['伦敦银行间行业拆放利率(LIBOR) USD - %','selection',{'table_name': 'libor', 'column': '%', 'sel_by': 'curr_type', 'keys': ['usd']}],
('libor_eur:%','d','None'):	['伦敦银行间行业拆放利率(LIBOR) EUR - %','selection',{'table_name': 'libor', 'column': '%', 'sel_by': 'curr_type', 'keys': ['eur']}],
('libor_gbp:%','d','None'):	['伦敦银行间行业拆放利率(LIBOR) GBP - %','selection',{'table_name': 'libor', 'column': '%', 'sel_by': 'curr_type', 'keys': ['gbp']}],
('hibor:%','d','None'):	['香港银行间行业拆放利率(HIBOR) - %','direct',{'table_name': 'hibor', 'column': '%'}],
('wz_comp','d','None'): ['温州民间融资综合利率指数','direct',{'table_name': 'wz_index', 'column': 'comp_rate'}],
('wz_center','d','None'): ['民间借贷服务中心利率','direct',{'table_name': 'wz_index', 'column': 'center_rate'}],
('wz_micro','d','None'): ['小额贷款公司放款利率','direct',{'table_name': 'wz_index', 'column': 'micro_rate'}],
('wz_cm','d','None'): ['民间资本管理公司融资价格','direct',{'table_name': 'wz_index', 'column': 'cm_rate'}],
('wz_sdb','d','None'): ['社会直接借贷利率','direct',{'table_name': 'wz_index', 'column': 'sdb_rate'}],
('wz_om','d','None'): ['其他市场主体利率','direct',{'table_name': 'wz_index', 'column': 'om_rate'}],
('wz_aa','d','None'): ['农村互助会互助金费率','direct',{'table_name': 'wz_index', 'column': 'aa_rate'}],
('wz_m1','d','None'): ['温州地区民间借贷分期限利率（一月期）','direct',{'table_name': 'wz_index', 'column': 'm1_rate'}],
('wz_m3','d','None'): ['温州地区民间借贷分期限利率（三月期）','direct',{'table_name': 'wz_index', 'column': 'm3_rate'}],
('wz_m6','d','None'): ['温州地区民间借贷分期限利率（六月期）','direct',{'table_name': 'wz_index', 'column': 'm6_rate'}],
('wz_m12','d','None'): ['温州地区民间借贷分期限利率（一年期）','direct',{'table_name': 'wz_index', 'column': 'm12_rate'}],
('wz_long','d','None'): ['温州地区民间借贷分期限利率（长期）','direct',{'table_name': 'wz_index', 'column': 'long_rate'}],
('gz_d10','d','None'): ['小额贷市场平均利率（十天）','direct',{'table_name': 'gz_index', 'column': 'd10_rate'}],
('gz_m1','d','None'): ['小额贷市场平均利率（一月期）','direct',{'table_name': 'gz_index', 'column': 'm1_rate'}],
('gz_m3','d','None'): ['小额贷市场平均利率（三月期）','direct',{'table_name': 'gz_index', 'column': 'm3_rate'}],
('gz_m6','d','None'): ['小额贷市场平均利率（六月期）','direct',{'table_name': 'gz_index', 'column': 'm6_rate'}],
('gz_m12','d','None'): ['小额贷市场平均利率（一年期）','direct',{'table_name': 'gz_index', 'column': 'm12_rate'}],
('gz_long','d','None'): ['小额贷市场平均利率（长期）','direct',{'table_name': 'gz_index', 'column': 'long_rate'}],
('cn_gdp','q','None'): ['GDP累计值（亿元）','direct',{'table_name': 'cn_gdp', 'column': 'gdp'}],
('cn_gdp_yoy','q','None'): ['当季同比增速（%）','direct',{'table_name': 'cn_gdp', 'column': 'gdp_yoy'}],
('cn_gdp_pi','q','None'): ['第一产业累计值（亿元）','direct',{'table_name': 'cn_gdp', 'column': 'pi'}],
('cn_gdp_pi_yoy','q','None'): ['第一产业同比增速（%）','direct',{'table_name': 'cn_gdp', 'column': 'pi_yoy'}],
('cn_gdp_si','q','None'): ['第二产业累计值（亿元）','direct',{'table_name': 'cn_gdp', 'column': 'si'}],
('cn_gdp_si_yoy','q','None'): ['第二产业同比增速（%）','direct',{'table_name': 'cn_gdp', 'column': 'si_yoy'}],
('cn_gdp_ti','q','None'): ['第三产业累计值（亿元）','direct',{'table_name': 'cn_gdp', 'column': 'ti'}],
('cn_gdp_ti_yoy','q','None'): ['第三产业同比增速（%）','direct',{'table_name': 'cn_gdp', 'column': 'ti_yoy'}],
('nt_val','m','None'): ['全国当月值','direct',{'table_name': 'cn_cpi', 'column': 'nt_val'}],
('nt_yoy','m','None'): ['全国同比（%）','direct',{'table_name': 'cn_cpi', 'column': 'nt_yoy'}],
('nt_mom','m','None'): ['全国环比（%）','direct',{'table_name': 'cn_cpi', 'column': 'nt_mom'}],
('nt_accu','m','None'): ['全国累计值','direct',{'table_name': 'cn_cpi', 'column': 'nt_accu'}],
('town_val','m','None'): ['城市当月值','direct',{'table_name': 'cn_cpi', 'column': 'town_val'}],
('town_yoy','m','None'): ['城市同比（%）','direct',{'table_name': 'cn_cpi', 'column': 'town_yoy'}],
('town_mom','m','None'): ['城市环比（%）','direct',{'table_name': 'cn_cpi', 'column': 'town_mom'}],
('town_accu','m','None'): ['城市累计值','direct',{'table_name': 'cn_cpi', 'column': 'town_accu'}],
('cnt_val','m','None'): ['农村当月值','direct',{'table_name': 'cn_cpi', 'column': 'cnt_val'}],
('cnt_yoy','m','None'): ['农村同比（%）','direct',{'table_name': 'cn_cpi', 'column': 'cnt_yoy'}],
('cnt_mom','m','None'): ['农村环比（%）','direct',{'table_name': 'cn_cpi', 'column': 'cnt_mom'}],
('cnt_accu','m','None'): ['农村累计值','direct',{'table_name': 'cn_cpi', 'column': 'cnt_accu'}],
('cnt_accu','m','None'): ['农村累计值','direct',{'table_name': 'cn_cpi', 'column': 'cnt_accu'}],
('ppi_yoy','m','None'): ['PPI：全部工业品：当月同比','direct',{'table_name': 'cn_ppi', 'column': 'ppi_yoy'}],
('ppi_mp_yoy','m','None'): ['PPI：生产资料：当月同比','direct',{'table_name': 'cn_ppi', 'column': 'ppi_mp_yoy'}],
('ppi_mp_qm_yoy','m','None'): ['PPI：生产资料：采掘业：当月同比','direct',{'table_name': 'cn_ppi', 'column': 'ppi_mp_qm_yoy'}],
('ppi_mp_rm_yoy','m','None'): ['PPI：生产资料：原料业：当月同比','direct',{'table_name': 'cn_ppi', 'column': 'ppi_mp_rm_yoy'}],
('ppi_mp_p_yoy','m','None'): ['PPI：生产资料：加工业：当月同比','direct',{'table_name': 'cn_ppi', 'column': 'ppi_mp_p_yoy'}],
('ppi_cg_yoy','m','None'): ['PPI：生活资料：当月同比','direct',{'table_name': 'cn_ppi', 'column': 'ppi_cg_yoy'}],
('ppi_cg_f_yoy','m','None'): ['PPI：生活资料：食品类：当月同比','direct',{'table_name': 'cn_ppi', 'column': 'ppi_cg_f_yoy'}],
('ppi_cg_c_yoy','m','None'): ['PPI：生活资料：衣着类：当月同比','direct',{'table_name': 'cn_ppi', 'column': 'ppi_cg_c_yoy'}],
('ppi_cg_adu_yoy','m','None'): ['PPI：生活资料：一般日用品类：当月同比','direct',{'table_name': 'cn_ppi', 'column': 'ppi_cg_adu_yoy'}],
('ppi_cg_dcg_yoy','m','None'): ['PPI：生活资料：耐用消费品类：当月同比','direct',{'table_name': 'cn_ppi', 'column': 'ppi_cg_dcg_yoy'}],
('ppi_mom','m','None'): ['PPI：全部工业品：环比','direct',{'table_name': 'cn_ppi', 'column': 'ppi_mom'}],
('ppi_mp_mom','m','None'): ['PPI：生产资料：环比','direct',{'table_name': 'cn_ppi', 'column': 'ppi_mp_mom'}],
('ppi_mp_qm_mom','m','None'): ['PPI：生产资料：采掘业：环比','direct',{'table_name': 'cn_ppi', 'column': 'ppi_mp_qm_mom'}],
('ppi_mp_rm_mom','m','None'): ['PPI：生产资料：原料业：环比','direct',{'table_name': 'cn_ppi', 'column': 'ppi_mp_rm_mom'}],
('ppi_mp_p_mom','m','None'): ['PPI：生产资料：加工业：环比','direct',{'table_name': 'cn_ppi', 'column': 'ppi_mp_p_mom'}],
('ppi_cg_mom','m','None'): ['PPI：生活资料：环比','direct',{'table_name': 'cn_ppi', 'column': 'ppi_cg_mom'}],
('ppi_cg_f_mom','m','None'): ['PPI：生活资料：食品类：环比','direct',{'table_name': 'cn_ppi', 'column': 'ppi_cg_f_mom'}],
('ppi_cg_c_mom','m','None'): ['PPI：生活资料：衣着类：环比','direct',{'table_name': 'cn_ppi', 'column': 'ppi_cg_c_mom'}],
('ppi_cg_adu_mom','m','None'): ['PPI：生活资料：一般日用品类：环比','direct',{'table_name': 'cn_ppi', 'column': 'ppi_cg_adu_mom'}],
('ppi_cg_dcg_mom','m','None'): ['PPI：生活资料：耐用消费品类：环比','direct',{'table_name': 'cn_ppi', 'column': 'ppi_cg_dcg_mom'}],
('ppi_accu','m','None'): ['PPI：全部工业品：累计同比','direct',{'table_name': 'cn_ppi', 'column': 'ppi_accu'}],
('ppi_mp_accu','m','None'): ['PPI：生产资料：累计同比','direct',{'table_name': 'cn_ppi', 'column': 'ppi_mp_accu'}],
('ppi_mp_qm_accu','m','None'): ['PPI：生产资料：采掘业：累计同比','direct',{'table_name': 'cn_ppi', 'column': 'ppi_mp_qm_accu'}],
('ppi_mp_rm_accu','m','None'): ['PPI：生产资料：原料业：累计同比','direct',{'table_name': 'cn_ppi', 'column': 'ppi_mp_rm_accu'}],
('ppi_mp_p_accu','m','None'): ['PPI：生产资料：加工业：累计同比','direct',{'table_name': 'cn_ppi', 'column': 'ppi_mp_p_accu'}],
('ppi_cg_accu','m','None'): ['PPI：生活资料：累计同比','direct',{'table_name': 'cn_ppi', 'column': 'ppi_cg_accu'}],
('ppi_cg_f_accu','m','None'): ['PPI：生活资料：食品类：累计同比','direct',{'table_name': 'cn_ppi', 'column': 'ppi_cg_f_accu'}],
('ppi_cg_c_accu','m','None'): ['PPI：生活资料：衣着类：累计同比','direct',{'table_name': 'cn_ppi', 'column': 'ppi_cg_c_accu'}],
('ppi_cg_adu_accu','m','None'): ['PPI：生活资料：一般日用品类：累计同比','direct',{'table_name': 'cn_ppi', 'column': 'ppi_cg_adu_accu'}],
('ppi_cg_dcg_accu','m','None'): ['PPI：生活资料：耐用消费品类：累计同比','direct',{'table_name': 'cn_ppi', 'column': 'ppi_cg_dcg_accu'}],
('cn_m0','m','None'): ['M0（亿元）','direct',{'table_name': 'cn_money', 'column': 'm0'}],
('cn_m0_yoy','m','None'): ['M0同比（%）','direct',{'table_name': 'cn_money', 'column': 'm0_yoy'}],
('cn_m0_mom','m','None'): ['M0环比（%）','direct',{'table_name': 'cn_money', 'column': 'm0_mom'}],
('cn_m1','m','None'): ['M1（亿元）','direct',{'table_name': 'cn_money', 'column': 'm1'}],
('cn_m1_yoy','m','None'): ['M1同比（%）','direct',{'table_name': 'cn_money', 'column': 'm1_yoy'}],
('cn_m1_mom','m','None'): ['M1环比（%）','direct',{'table_name': 'cn_money', 'column': 'm1_mom'}],
('cn_m2','m','None'): ['M2（亿元）','direct',{'table_name': 'cn_money', 'column': 'm2'}],
('cn_m2_yoy','m','None'): ['M2同比（%）','direct',{'table_name': 'cn_money', 'column': 'm2_yoy'}],
('cn_m2_mom','m','None'): ['M2环比（%）','direct',{'table_name': 'cn_money', 'column': 'm2_mom'}],
('inc_month','m','None'): ['社融增量当月值（亿元）','direct',{'table_name': 'cn_sf', 'column': 'inc_month'}],
('inc_cumval','m','None'): ['社融增量累计值（亿元）','direct',{'table_name': 'cn_sf', 'column': 'inc_cumval'}],
('stk_endval','m','None'): ['社融存量期末值（万亿元）','direct',{'table_name': 'cn_sf', 'column': 'stk_endval'}],
('pmi010000','m','None'): ['制造业PMI','direct',{'table_name': 'cn_pmi', 'column': 'pmi010000'}],
('pmi010100','m','None'): ['制造业PMI:企业规模/大型企业','direct',{'table_name': 'cn_pmi', 'column': 'pmi010100'}],
('pmi010200','m','None'): ['制造业PMI:企业规模/中型企业','direct',{'table_name': 'cn_pmi', 'column': 'pmi010200'}],
('pmi010300','m','None'): ['制造业PMI:企业规模/小型企业','direct',{'table_name': 'cn_pmi', 'column': 'pmi010300'}],
('pmi010400','m','None'): ['制造业PMI:构成指数/生产指数','direct',{'table_name': 'cn_pmi', 'column': 'pmi010400'}],
('pmi010401','m','None'): ['制造业PMI:构成指数/生产指数:企业规模/大型企业','direct',{'table_name': 'cn_pmi', 'column': 'pmi010401'}],
('pmi010402','m','None'): ['制造业PMI:构成指数/生产指数:企业规模/中型企业','direct',{'table_name': 'cn_pmi', 'column': 'pmi010402'}],
('pmi010403','m','None'): ['制造业PMI:构成指数/生产指数:企业规模/小型企业','direct',{'table_name': 'cn_pmi', 'column': 'pmi010403'}],
('pmi010500','m','None'): ['制造业PMI:构成指数/新订单指数','direct',{'table_name': 'cn_pmi', 'column': 'pmi010500'}],
('pmi010501','m','None'): ['制造业PMI:构成指数/新订单指数:企业规模/大型企业','direct',{'table_name': 'cn_pmi', 'column': 'pmi010501'}],
('pmi010502','m','None'): ['制造业PMI:构成指数/新订单指数:企业规模/中型企业','direct',{'table_name': 'cn_pmi', 'column': 'pmi010502'}],
('pmi010503','m','None'): ['制造业PMI:构成指数/新订单指数:企业规模/小型企业','direct',{'table_name': 'cn_pmi', 'column': 'pmi010503'}],
('pmi010600','m','None'): ['制造业PMI:构成指数/供应商配送时间指数','direct',{'table_name': 'cn_pmi', 'column': 'pmi010600'}],
('pmi010601','m','None'): ['制造业PMI:构成指数/供应商配送时间指数:企业规模/大型企业','direct',{'table_name': 'cn_pmi', 'column': 'pmi010601'}],
('pmi010602','m','None'): ['制造业PMI:构成指数/供应商配送时间指数:企业规模/中型企业','direct',{'table_name': 'cn_pmi', 'column': 'pmi010602'}],
('pmi010603','m','None'): ['制造业PMI:构成指数/供应商配送时间指数:企业规模/小型企业','direct',{'table_name': 'cn_pmi', 'column': 'pmi010603'}],
('pmi010700','m','None'): ['制造业PMI:构成指数/原材料库存指数','direct',{'table_name': 'cn_pmi', 'column': 'pmi010700'}],
('pmi010701','m','None'): ['制造业PMI:构成指数/原材料库存指数:企业规模/大型企业','direct',{'table_name': 'cn_pmi', 'column': 'pmi010701'}],
('pmi010702','m','None'): ['制造业PMI:构成指数/原材料库存指数:企业规模/中型企业','direct',{'table_name': 'cn_pmi', 'column': 'pmi010702'}],
('pmi010703','m','None'): ['制造业PMI:构成指数/原材料库存指数:企业规模/小型企业','direct',{'table_name': 'cn_pmi', 'column': 'pmi010703'}],
('pmi010800','m','None'): ['制造业PMI:构成指数/从业人员指数','direct',{'table_name': 'cn_pmi', 'column': 'pmi010800'}],
('pmi010801','m','None'): ['制造业PMI:构成指数/从业人员指数:企业规模/大型企业','direct',{'table_name': 'cn_pmi', 'column': 'pmi010801'}],
('pmi010802','m','None'): ['制造业PMI:构成指数/从业人员指数:企业规模/中型企业','direct',{'table_name': 'cn_pmi', 'column': 'pmi010802'}],
('pmi010803','m','None'): ['制造业PMI:构成指数/从业人员指数:企业规模/小型企业','direct',{'table_name': 'cn_pmi', 'column': 'pmi010803'}],
('pmi010900','m','None'): ['制造业PMI:其他/新出口订单','direct',{'table_name': 'cn_pmi', 'column': 'pmi010900'}],
('pmi011000','m','None'): ['制造业PMI:其他/进口','direct',{'table_name': 'cn_pmi', 'column': 'pmi011000'}],
('pmi011100','m','None'): ['制造业PMI:其他/采购量','direct',{'table_name': 'cn_pmi', 'column': 'pmi011100'}],
('pmi011200','m','None'): ['制造业PMI:其他/主要原材料购进价格','direct',{'table_name': 'cn_pmi', 'column': 'pmi011200'}],
('pmi011300','m','None'): ['制造业PMI:其他/出厂价格','direct',{'table_name': 'cn_pmi', 'column': 'pmi011300'}],
('pmi011400','m','None'): ['制造业PMI:其他/产成品库存','direct',{'table_name': 'cn_pmi', 'column': 'pmi011400'}],
('pmi011500','m','None'): ['制造业PMI:其他/在手订单','direct',{'table_name': 'cn_pmi', 'column': 'pmi011500'}],
('pmi011600','m','None'): ['制造业PMI:其他/生产经营活动预期','direct',{'table_name': 'cn_pmi', 'column': 'pmi011600'}],
('pmi011700','m','None'): ['制造业PMI:分行业/装备制造业','direct',{'table_name': 'cn_pmi', 'column': 'pmi011700'}],
('pmi011800','m','None'): ['制造业PMI:分行业/高技术制造业','direct',{'table_name': 'cn_pmi', 'column': 'pmi011800'}],
('pmi011900','m','None'): ['制造业PMI:分行业/基础原材料制造业','direct',{'table_name': 'cn_pmi', 'column': 'pmi011900'}],
('pmi012000','m','None'): ['制造业PMI:分行业/消费品制造业','direct',{'table_name': 'cn_pmi', 'column': 'pmi012000'}],
('pmi020100','m','None'): ['非制造业PMI:商务活动','direct',{'table_name': 'cn_pmi', 'column': 'pmi020100'}],
('pmi020101','m','None'): ['非制造业PMI:商务活动:分行业/建筑业','direct',{'table_name': 'cn_pmi', 'column': 'pmi020101'}],
('pmi020102','m','None'): ['非制造业PMI:商务活动:分行业/服务业业','direct',{'table_name': 'cn_pmi', 'column': 'pmi020102'}],
('pmi020200','m','None'): ['非制造业PMI:新订单指数','direct',{'table_name': 'cn_pmi', 'column': 'pmi020200'}],
('pmi020201','m','None'): ['非制造业PMI:新订单指数:分行业/建筑业','direct',{'table_name': 'cn_pmi', 'column': 'pmi020201'}],
('pmi020202','m','None'): ['非制造业PMI:新订单指数:分行业/服务业','direct',{'table_name': 'cn_pmi', 'column': 'pmi020202'}],
('pmi020300','m','None'): ['非制造业PMI:投入品价格指数','direct',{'table_name': 'cn_pmi', 'column': 'pmi020300'}],
('pmi020301','m','None'): ['非制造业PMI:投入品价格指数:分行业/建筑业','direct',{'table_name': 'cn_pmi', 'column': 'pmi020301'}],
('pmi020302','m','None'): ['非制造业PMI:投入品价格指数:分行业/服务业','direct',{'table_name': 'cn_pmi', 'column': 'pmi020302'}],
('pmi020400','m','None'): ['非制造业PMI:销售价格指数','direct',{'table_name': 'cn_pmi', 'column': 'pmi020400'}],
('pmi020401','m','None'): ['非制造业PMI:销售价格指数:分行业/建筑业','direct',{'table_name': 'cn_pmi', 'column': 'pmi020401'}],
('pmi020402','m','None'): ['非制造业PMI:销售价格指数:分行业/服务业','direct',{'table_name': 'cn_pmi', 'column': 'pmi020402'}],
('pmi020500','m','None'): ['非制造业PMI:从业人员指数','direct',{'table_name': 'cn_pmi', 'column': 'pmi020500'}],
('pmi020501','m','None'): ['非制造业PMI:从业人员指数:分行业/建筑业','direct',{'table_name': 'cn_pmi', 'column': 'pmi020501'}],
('pmi020502','m','None'): ['非制造业PMI:从业人员指数:分行业/服务业','direct',{'table_name': 'cn_pmi', 'column': 'pmi020502'}],
('pmi020600','m','None'): ['非制造业PMI:业务活动预期指数','direct',{'table_name': 'cn_pmi', 'column': 'pmi020600'}],
('pmi020601','m','None'): ['非制造业PMI:业务活动预期指数:分行业/建筑业','direct',{'table_name': 'cn_pmi', 'column': 'pmi020601'}],
('pmi020602','m','None'): ['非制造业PMI:业务活动预期指数:分行业/服务业','direct',{'table_name': 'cn_pmi', 'column': 'pmi020602'}],
('pmi020700','m','None'): ['非制造业PMI:新出口订单','direct',{'table_name': 'cn_pmi', 'column': 'pmi020700'}],
('pmi020800','m','None'): ['非制造业PMI:在手订单','direct',{'table_name': 'cn_pmi', 'column': 'pmi020800'}],
('pmi020900','m','None'): ['非制造业PMI:存货','direct',{'table_name': 'cn_pmi', 'column': 'pmi020900'}],
('pmi021000','m','None'): ['非制造业PMI:供应商配送时间','direct',{'table_name': 'cn_pmi', 'column': 'pmi021000'}],
('pmi030000','m','None'): ['中国综合PMI:产出指数','direct',{'table_name': 'cn_pmi', 'column': 'pmi030000'}],
('p_change_min','d','E'): ['预告净利润变动幅度下限(%)','event_signal',{'table_name': 'forecast', 'column': 'p_change_min'}],
('p_change_max','d','E'): ['预告净利润变动幅度上限(%)','event_signal',{'table_name': 'forecast', 'column': 'p_change_max'}],
('net_profit_min','d','E'): ['预告净利润下限(万元)','event_signal',{'table_name': 'forecast', 'column': 'net_profit_min'}],
('net_profit_max','d','E'): ['预告净利润上限(万元)','event_signal',{'table_name': 'forecast', 'column': 'net_profit_max'}],
('last_parent_net','d','E'): ['上年同期归属母公司净利润','event_signal',{'table_name': 'forecast', 'column': 'last_parent_net'}],
('first_ann_date','d','E'): ['首次公告日','event_signal',{'table_name': 'forecast', 'column': 'first_ann_date'}],
('summary','d','E'): ['业绩预告摘要','event_signal',{'table_name': 'forecast', 'column': 'summary'}],
('change_reason','d','E'): ['业绩变动原因','event_signal',{'table_name': 'forecast', 'column': 'change_reason'}],
('block_trade_price','d','E'): ['大宗交易 - 成交价','event_signal',{'table_name': 'block_trade', 'column': 'price'}],
('block_trade_vol','d','E'): ['大宗交易 - 成交量（万股）','event_signal',{'table_name': 'block_trade', 'column': 'vol'}],
('block_trade_amount','d','E'): ['大宗交易 - 成交金额','event_signal',{'table_name': 'block_trade', 'column': 'amount'}],
('block_trade_buyer','d','E'): ['大宗交易 - 买方营业部','event_signal',{'table_name': 'block_trade', 'column': 'buyer'}],
('block_trade_seller','d','E'): ['大宗交易 - 卖方营业部','event_signal',{'table_name': 'block_trade', 'column': 'seller'}],
('stock_holder_trade_name','d','E'): ['股东交易 - 股东名称','event_signal',{'table_name': 'stock_holder_trade', 'column': 'holder_name'}],
('stock_holder_trade_type','d','E'): ['股东交易 - 股东类型G高管P个人C公司','event_signal',{'table_name': 'stock_holder_trade', 'column': 'holder_type'}],
('stock_holder_trade_in_de','d','E'): ['股东交易 - 类型IN增持DE减持','event_signal',{'table_name': 'stock_holder_trade', 'column': 'in_de'}],
('stock_holder_trade_change_vol','d','E'): ['股东交易 - 变动数量','event_signal',{'table_name': 'stock_holder_trade', 'column': 'change_vol'}],
('stock_holder_trade_change_ratio','d','E'): ['股东交易 - 占流通比例（%）','event_signal',{'table_name': 'stock_holder_trade', 'column': 'change_ratio'}],
('stock_holder_trade_after_share','d','E'): ['股东交易 - 变动后持股','event_signal',{'table_name': 'stock_holder_trade', 'column': 'after_share'}],
('stock_holder_trade_after_ratio','d','E'): ['股东交易 - 变动后占流通比例（%）','event_signal',{'table_name': 'stock_holder_trade', 'column': 'after_ratio'}],
('stock_holder_trade_avg_price','d','E'): ['股东交易 - 平均价格','event_signal',{'table_name': 'stock_holder_trade', 'column': 'avg_price'}],
('stock_holder_trade_total_share','d','E'): ['股东交易 - 持股总数','event_signal',{'table_name': 'stock_holder_trade', 'column': 'total_share'}],
('stock_holder_trade_begin_date','d','E'): ['股东交易 - 增减持开始日期','event_signal',{'table_name': 'stock_holder_trade', 'column': 'begin_date'}],
('stock_holder_trade_close_date','d','E'): ['股东交易 - 增减持结束日期','event_signal',{'table_name': 'stock_holder_trade', 'column': 'close_date'}],
('margin_detail_rzye','d','E'): ['融资融券交易明细 - 融资余额(元)','event_signal',{'table_name': 'margin_detail', 'column': 'rzye'}],
('margin_detail_rqye','d','E'): ['融资融券交易明细 - 融券余额(元)','event_signal',{'table_name': 'margin_detail', 'column': 'rqye'}],
('margin_detail_rzmre','d','E'): ['融资融券交易明细 - 融资买入额(元)','event_signal',{'table_name': 'margin_detail', 'column': 'rzmre'}],
('margin_detail_rqyl','d','E'): ['融资融券交易明细 - 融券余量（股）','event_signal',{'table_name': 'margin_detail', 'column': 'rqyl'}],
('margin_detail_rzche','d','E'): ['融资融券交易明细 - 融资偿还额(元)','event_signal',{'table_name': 'margin_detail', 'column': 'rzche'}],
('margin_detail_rqchl','d','E'): ['融资融券交易明细 - 融券偿还量(股)','event_signal',{'table_name': 'margin_detail', 'column': 'rqchl'}],
('margin_detail_rqmcl','d','E'): ['融资融券交易明细 - 融券卖出量(股,份,手)','event_signal',{'table_name': 'margin_detail', 'column': 'rqmcl'}],
('margin_detail_rzrqye','d','E'): ['融资融券交易明细 - 融资融券余额(元)','event_signal',{'table_name': 'margin_detail', 'column': 'rzrqye'}]
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
