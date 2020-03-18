# coding=utf-8

import pandas as pd
import tushare as ts
import numpy as np
from datetime import datetime
import datetime as dt

TUSHARE_TOKEN = '14f96621db7a937c954b1943a579f52c09bbd5022ed3f03510b77369'
ts.set_token(TUSHARE_TOKEN)


# TODO: 将History类重新定义为History模块，取消类的定义，转而使History模块变成对历史数据进行操作或读取的一个函数包的集合
# TODO: 增加HistData类，一个以Ndarray为基础的三维历史数据数组
# TODO: 需要详细定义这个函数的函数包的清单，以便其他模块调用
# TODO: 以tushare为基础定义历史数据公共函数库


class HistoryPanel():
    """The major data structure to be used for the qteasy quants system.

    data structure and class containing multiple types of array-like data framework
    axis 1: levels / share_pool
    axis 2: rows / index / hdates
    axis 3: columns / htypes
    """

    def __init__(self, values, levels=None, rows=None, columns=None):
        """

        :param values:
        :param levels:
        :param rows: datetime range or timestamp index of the data
        :param columns:
        """
        assert isinstance(values, np.ndarray), f'input value type should be numpy ndarray, got {type(value)}'
        assert len(values.shape) <= 3, \
            f'input array should be equal to or less than 3 dimensions, got {len(values.shape)}'

        if len(values.shape) == 1:
            values = values.reshape(1, 1, values.shape[0])
        elif len(values.shape) == 2:
            values = values.reshape(1, *values.shape)
        self._l_count, self._r_count, self._c_count = values.shape
        self._values = values

        if levels is None:
            levels = range(self._l_count)
        assert len(levels) == self._l_count, \
            f'length of level list does not fit the shape of input values! lenth {len(levels)} != {self._l_count}'
        self._levels = dict(zip(levels, range(self._l_count)))

        if rows is None:
            rows = range(self._r_count)
        assert len(rows) == self._r_count, \
            f'length of row list does not fit the shape of input values! lenth {len(rows)} != {self._r_count}'
        self._rows = dict(zip(rows, range(self._r_count)))

        if columns is None:
            columns = range(self._c_count)
        else:
            columns = list(map(str, columns))
            columns = list(map(str.lower, columns))
        assert len(columns) == self._c_count, \
            f'length of column list does not fit the shape of input values! lenth {len(columns)} != {self._c_count}'
        self._columns = dict(zip(columns, range(self._c_count)))

    @property
    def values(self):
        return self._values

    @property
    def levels(self):
        return self._levels

    @property
    def shares(self):
        return self._levels

    @property
    def level_count(self):
        return self._l_count

    @property
    def index(self):
        return self._rows

    @property
    def rows(self):
        return self._rows

    @property
    def hdates(self):
        return self._rows

    @property
    def row_count(self):
        return self._r_count

    @property
    def htypes(self):
        return self._columns

    @property
    def columns(self):
        return self._columns

    @property
    def column_count(self):
        return self._c_count

    @property
    def shape(self):
        return self._l_count, self._r_count, self._c_count

    def __getitem__(self, keys=None):
        """获取历史数据的一个切片，给定一个type、日期或股票代码

            contains three slice objects: htypes, share_pool, and hdates,

        input：
            :param keys: list/tuple/slice历史数据的类型名，为空时给出所有类型的数据
            参数row，str或pd.Timestamp，optional 历史数据的日期，为空时给出所有日期的数据
            参数share，str，optional：股票代码，为空时给出所有股票的数据
        输出：
            self.value的一个切片
        """

        key_is_tuple = isinstance(keys, tuple)
        key_is_list = isinstance(keys, list)
        key_is_slice = isinstance(keys, slice)
        key_is_string = isinstance(keys, str)
        key_is_number = isinstance(keys, int)

        # first make sure that htypes, share_pool, and hdates are either slice or list
        if key_is_tuple:
            if len(keys) == 2:
                htype_slice, share_slice = keys
                hdate_slice = slice(None, None, None)
            elif len(keys) == 3:
                htype_slice, share_slice, hdate_slice = keys
        elif key_is_slice or key_is_list or key_is_string or key_is_number:  # keys is a slice or list
            htype_slice = keys
            share_slice = slice(None, None, None)
            hdate_slice = slice(None, None, None)
        else:
            htype_slice = slice(None, None, None)
            share_slice = slice(None, None, None)
            hdate_slice = slice(None, None, None)

        # check and convert each of the slice segments to the right type: a slice or \
        # a list of indices
        htype_slice = _make_list_or_slice(htype_slice, self.htypes)
        share_slice = _make_list_or_slice(share_slice, self.shares)
        hdate_slice = _make_list_or_slice(hdate_slice, self.hdates)

        print('share_pool is ', share_slice, '\nhtypes is ', htype_slice,
              '\nhdates is ', hdate_slice)
        return self.values[share_slice, hdate_slice, htype_slice]

    def __mul__(self, arg):
        self._values = self._values * arg
        return self

    def info(self):
        print(type(self))
        print(f'Levels: {self.level_count}, htypes: {self.column_count}')
        print(f'total {self.row_count} entries: ')

    def fillna(self, with_val):
        np._values = np.where(np.isnan(self._values), with_val, self._values)
        return self

    def to_dataframe(self, htype: str) -> pd.DataFrame:
        v = self._values[:, :, self.htypes[htype]].T
        return pd.DataFrame(v, index=list(self._rows.keys()), columns=list(self._levels.keys()))


def from_dataframe(df: pd.DataFrame = None):
    """ 根据DataFrame中的数据创建历史数据板HistoryPanel对象

    input:
        :param df:
    :return:
    """
    assert isinstance(df, pd.DataFrame), f'Input df should be pandas DataFrame! got {type(df)}.'
    return


def from_dataframes(*dfs):
    """ 根据多个DataFrame中的数据创建HistoryPanel对象

    input
    :param dfs: type list, containing multiple dataframes
    :return:
    """


def _make_list_or_slice(item, d):
    """

    :param item: slice or int/str or list of int/string
    :param d: a dictionary that contains strings as keys and integer as values
    :return:
        a list of slice that can be used to slice the Historical Data Object
    """
    if isinstance(item, slice):
        return item  # slice object can be directly used
    elif isinstance(item, int):  # number should be converted to a list containint itself
        return [item]
    elif isinstance(item, str):  # string should be converted to numbers
        return [d[item]]
    elif isinstance(item, list):
        res = []
        for i in item:  # convert all items into a number:
            res.extend(make_list_or_slice(i, d))
        return res
    else:
        return None


# ==================
# Historical Utility functions based on tushare
# ==================

# Basic Market Data
# ==================

def stock_basic(is_hs: str = None,
                list_status: str = None,
                exchange: str = None,
                fields: str = None):
    """ 获取基础信息数据，包括股票代码、名称、上市日期、退市日期等

    :param is_hs: optinal, 是否沪深港通标的，N否 H沪股通 S深股通
    :param list_status: optional, 上市状态： L上市 D退市 P暂停上市
    :param exchange: optional, 交易所 SSE上交所 SZSE深交所 HKEX港交所(未上线)
    :param fields: 逗号分隔的字段名称字符串，可选字段包括输出参数中的任意组合
    :return: pd.DataFrame:
        column      type    description
        ts_code,    str,    TS代码
        symbol,     str,    股票代码
        name,       str,    股票名称
        area,       str,    所在地域
        industry,   str,    所属行业
        fullname,   str,    股票全称
        ennamem     str,    英文全称
        market,     str,    市场类型 （主板/中小板/创业板/科创板）
        exchange,   str,    交易所代码
        curr_type,  str,    交易货币
        list_status,str,    上市状态： L上市 D退市 P暂停上市
        list_date,  str,    上市日期
        delist_date,str,    退市日期
        is_hs,      str,    是否沪深港通标的，N否 H沪股通 S深股通
    """
    if is_hs is None: is_hs = ''
    if list_status is None: list_status = 'L'
    if exchange is None: exchange = ''
    if fields is None: fields = 'ts_code,symbol,name,area,industry,list_date'
    pro = ts.pro_api()
    return pro.stock_basic(exchange=exchange,
                           list_status=list_status,
                           is_hs=is_hs,
                           fields=fields)


def trade_calendar(exchange: str = 'SSE',
                   start_date: str = None,
                   end_date: str = None,
                   is_open: str = None):
    """ 获取各大交易所交易日历数据,默认提取的是上交所

    :param exchange: 交易所 SSE上交所,SZSE深交所,CFFEX 中金所,SHFE 上期所,CZCE 郑商所,DCE 大商所,INE 上能源,IB 银行间,XHKG 港交所
    :param start_date: 开始日期
    :param end_date: 结束日期
    :param is_open: 是否交易 '0'休市 '1'交易
    :return: pd.DataFrame
        column          type    description
        exchange,       str,    交易所 SSE上交所 SZSE深交所
        cal_date,       str,    日历日期
        is_open,        str,    是否交易 0休市 1交易
        pretrade_date,  str,    默认不显示，  上一个交易日
    """
    pro = ts.pro_api()
    return pro.trade_cal(exchange=exchange,
                         start_date=start_date,
                         end_date=end_date,
                         is_open=is_open)


def name_change(ts_code: str = None,
                start_date: str = None,
                end_date: str = None,
                fields: str = None):
    """ 历史名称变更记录

    :param ts_code:
    :param start_date:
    :param end_date:
    :return: pd.DataFrame
        column              type    default     description
        ts_code	            str	    Y	        TS代码
        name	            str	    Y	        证券名称
        start_date	        str	    Y	        开始日期
        end_date	        str	    Y	        结束日期
        ann_date	        str	    Y	        公告日期
        change_reason	    str	    Y	        变更原因
    example:
        pro = ts.pro_api()
        df = pro.namechange(ts_code='600848.SH',
                            fields='ts_code,name,start_date,end_date,change_reason')
    :output:
                ts_code     name      start_date   end_date      change_reason
        0       600848.SH   上海临港   20151118      None           改名
        1       600848.SH   自仪股份   20070514     20151117         撤销ST
        2       600848.SH   ST自仪     20061026    20070513         完成股改
        3       600848.SH   SST自仪   20061009     20061025        未股改加S
        4       600848.SH   ST自仪     20010508    20061008         ST
        5       600848.SH   自仪股份  19940324      20010507         其他
    """
    if fields is None: fields = 'ts_code,name,start_date,end_date,change_reason'
    pro = ts.pro_api()
    return pro.namechange(ts_code=ts_code,
                          start_date=start_date,
                          end_date=end_date,
                          fields=fields)


def new_share(start_date: str = None,
              end_date: str = None) -> pd.DataFrame:
    """

    :param start_date: str, 上网发行开始日期
    :param end_date: str, 上网发行结束日期
    :return: pd.DataFrame
        column              type    default     description
        ts_code		        str	    Y	        TS股票代码
        sub_code	        str	    Y	        申购代码
        name		        str	    Y	        名称
        ipo_date	        str	    Y	        上网发行日期
        issue_date	        str	    Y	        上市日期
        amount		        float	Y	        发行总量（万股）
        market_amount	    float	Y	        上网发行总量（万股）
        price		        float	Y	        发行价格
        pe		            float	Y	        市盈率
        limit_amount	    float	Y	        个人申购上限（万股）
        funds		        float	Y	        募集资金（亿元）
        ballot		        float	Y	        中签率
    example:
        pro = ts.pro_api()
        df = pro.new_share(start_date='20180901', end_date='20181018')
    output:
            ts_code     ub_code  name  ipo_date    issue_date   amount  market_amount  \
        0   002939.SZ   002939  长城证券  20181017       None  31034.0        27931.0
        1   002940.SZ   002940   昂利康  20181011   20181023   2250.0         2025.0
        2   601162.SH   780162  天风证券  20181009   20181019  51800.0        46620.0
        3   300694.SZ   300694  蠡湖股份  20180927   20181015   5383.0         4845.0
        4   300760.SZ   300760  迈瑞医疗  20180927   20181016  12160.0        10944.0
        5   300749.SZ   300749  顶固集创  20180913   20180925   2850.0         2565.0
        6   002937.SZ   002937  兴瑞科技  20180912   20180926   4600.0         4140.0
        7   601577.SH   780577  长沙银行  20180912   20180926  34216.0        30794.0
        8   603583.SH   732583  捷昌驱动  20180911   20180921   3020.0         2718.0
        9   002936.SZ   002936  郑州银行  20180907   20180919  60000.0        54000.0
        10  300748.SZ   300748  金力永磁  20180906   20180921   4160.0         3744.0
        11  603810.SH   732810  丰山集团  20180906   20180917   2000.0         2000.0
        12  002938.SZ   002938  鹏鼎控股  20180905   20180918  23114.0        20803.0

            price     pe  limit_amount   funds  ballot
        0    6.31  22.98          9.30  19.582    0.16
        1   23.07  22.99          0.90   5.191    0.03
        2    1.79  22.86         15.50   0.000    0.25
        3    9.89  22.98          2.15   5.324    0.04
        4   48.80  22.99          3.60  59.341    0.08
        5   12.22  22.99          1.10   3.483    0.03
        6    9.94  22.99          1.80   4.572    0.04
        7    7.99   6.97         10.20  27.338    0.17
        8   29.17  22.99          1.20   8.809    0.03
        9    4.59   6.50         18.00  27.540    0.25
        10   5.39  22.98          1.20   2.242    0.05
        11  25.43  20.39          2.00   5.086    0.02
        12  16.07  22.99          6.90  37.145    0.12
    """
    pro = ts.pro_api()
    return pro.new_share(start_date=start_date, end_date=end_date)


def stock_company(ts_code: str = None,
                  exchange: str = None,
                  fields: str = None) -> pd.DataFrame:
    """

    :param ts_code: str, 股票代码
    :param exchange: str, 交易所代码 ，SSE上交所 SZSE深交所
    :param fields: str, 逗号分隔的字段名称字符串，可选字段包括输出参数中的任意组合
    :return: pd.DataFrame
        column              type    default     description
        ts_code		        str	    Y	        股票代码
        exchange	        str	    Y	        交易所代码 ，SSE上交所 SZSE深交所
        chairman	        str	    Y	        法人代表
        manager		        str	    Y	        总经理
        secretary	        str	    Y	        董秘
        reg_capital	        float	Y	        注册资本
        setup_date	        str	    Y	        注册日期
        province	        str	    Y	        所在省份
        city		        str	    Y	        所在城市
        introduction	    str	    N	        公司介绍
        website		        str	    Y	        公司主页
        email		        str	    Y	        电子邮件
        office		        str	    N	        办公室
        employees	        int	    Y	        员工人数
        main_business	    str	    N	        主要业务及产品
        business_scope	    str	    N	        经营范围
    example:
        pro = ts.pro_api()
        df = pro.stock_company(exchange='SZSE',
                               fields='ts_code,chairman,manager,secretary,reg_capital,setup_date,province')
    output:
               ts_code     chairman manager     secretary   reg_capital setup_date province  \
        0     000001.SZ      谢永林     胡跃飞        周强  1.717041e+06   19871222       广东
        1     000002.SZ       郁亮     祝九胜        朱旭  1.103915e+06   19840530       广东
        2     000003.SZ      马钟鸿     马钟鸿        安汪  3.334336e+04   19880208       广东
        3     000004.SZ      李林琳     李林琳       徐文苏  8.397668e+03   19860505       广东
        4     000005.SZ       丁芃     郑列列       罗晓春  1.058537e+05   19870730       广东
        5     000006.SZ      赵宏伟     朱新宏        杜汛  1.349995e+05   19850525       广东
        6     000007.SZ      智德宇     智德宇       陈伟彬  3.464480e+04   19830311       广东
        7     000008.SZ      王志全      钟岩       王志刚  2.818330e+05   19891011       北京
        8     000009.SZ      陈政立     陈政立       郭山清  2.149345e+05   19830706       广东
        9     000010.SZ       曾嵘     李德友       金小刚  8.198547e+04   19881231       广东
        10    000011.SZ      刘声向     王航军       范维平  5.959791e+04   19830117       广东
    """
    if fields is None: fields = 'ts_code,chairman,manager,secretary,reg_capital,setup_date,province'
    pro = ts.pro_api()
    return pro.stock_comapany(ts_code=ts_code, exchange=exchange, fields=fields)

# Bar price data
# ==================

def get_bar(share: str,
                   start: str,
                   end: str,
                   asset_type: str = 'E',
                   adj: str = 'None',
                   freq: str = 'D',
                   ma: list = None) -> pd.DataFrame:
    """ get historical prices with rehabilitation rights
        获取指数或股票的复权历史价格

    input:
        :param share: str, 证券代码
        :param start: str, 开始日期 (格式：YYYYMMDD)
        :param end: str, 结束日期 (格式：YYYYMMDD)
        :param asset_type: str, 资产类别：E股票 I沪深指数 C数字货币 F期货 FD基金 O期权，默认E
        :param adj: str, 复权类型(只针对股票)：None未复权 qfq前复权 hfq后复权 , 默认None
        :param freq: str, 数据频度 ：1MIN表示1分钟（1/5/15/30/60分钟） D日线 ，默认D
        :param ma: str, 均线，支持任意周期的均价和均量，输入任意合理int数值
    return: pd.DataFrame
        column          type    description
        ts_code         str     证券代码
        trade_date      str     交易日期，格式YYYYMMDD
        open            float   开盘价
        high            float   最高价
        low             float   最低价
        close           float   收盘价
        pre_close       float   前一收盘价
        change          float   收盘价涨跌
        pct_chg         float   收盘价涨跌百分比
        vol             float   交易量
        amount          float   交易额
    example:
        获取日k线数据，前复权：
        ts.pro_bar(ts_code='000001.SZ', adj='qfq', start_date='20180101', end_date='20181011')
        获取周K线数据，后复权：
        ts.pro_bar(ts_code='000001.SZ', freq='W', adj='hfq', start_date='20180101', end_date='20181011')
    output:
    前复权日K线数据
       ts_code trade_date     open     high      low    close  pre_close  change  pct_chg         vol       amount
    0    000001.SZ   20181011  10.0500  10.1600   9.7000   9.8600    10.4500 -0.5900  -5.6459  1995143.83  1994186.611
    1    000001.SZ   20181010  10.5400  10.6600  10.3800  10.4500    10.5600 -0.1100  -1.0417   995200.08  1045666.180
    2    000001.SZ   20181009  10.4600  10.7000  10.3900  10.5600    10.4500  0.1100   1.0526  1064084.26  1117946.550
    3    000001.SZ   20181008  10.7000  10.7900  10.4500  10.4500    11.0500 -0.6000  -5.4299  1686358.52  1793455.283
    4    000001.SZ   20180928  10.7800  11.2700  10.7800  11.0500    10.7400  0.3100   2.8864  2110242.67  2331358.288
    """
    assert isinstance(share, str), 'TypeError: share code should be a string'
    return ts.pro_bar(ts_code=share, start_date=start, end_date=end, asset=asset_type, adj=adj, freq=freq, ma=ma)


# Finance Data
# ================

def income(ts_code: str,
           ann_date: str = None,
           start_date: str = None,
           end_date: str = None,
           period: str = None,
           report_type: str = None,
           comp_type: str = None,
           fields: str = None) -> pd.DataFrame:
    """ 获取上市公司财务利润表数据

    :param ts_code: 股票代码
    :param ann_date: optional 公告日期
    :param start_date: optional 公告开始日期
    :param end_date: optional 公告结束日期
    :param period: optional 报告期(每个季度最后一天的日期，比如20171231表示年报)
    :param report_type: optional 报告类型： 参考下表说明
    :param comp_type: optional 公司类型：1一般工商业 2银行 3保险 4证券
    :param fields: str, 输出数据，结果DataFrame的数据列名，用逗号分隔
    :return: pd.DataFrame:
        column              type   dft  description
        ts_code	            str	    Y   TS代码
        ann_date	        str	    Y	公告日期
        f_ann_date	        str	    Y	实际公告日期
        end_date	        str	    Y	报告期
        report_type	        str	    Y	报告类型 1合并报表                  上市公司最新报表（默认）
                                                2单季合并                  单一季度的合并报表
                                                3调整单季合并表            调整后的单季合并报表（如果有）
                                                4调整合并报表             本年度公布上年同期的财务报表数据，报告期为上年度
                                                5调整前合并报表            数据发生变更，将原数据进行保留，即调整前的原数据
                                                6母公司报表              该公司母公司的财务报表数据
                                                7母公司单季表             母公司的单季度表
                                                8 母公司调整单季表         母公司调整后的单季表
                                                9母公司调整表             该公司母公司的本年度公布上年同期的财务报表数据
                                                10母公司调整前报表          母公司调整之前的原始财务报表数据
                                                11调整前合并报表           调整之前合并报表原数据
                                                12母公司调整前报表          母公司报表发生变更前保留的原数据
        comp_type	        str	    Y	公司类型(1一般工商业2银行3保险4证券)
        basic_eps	        float	Y	基本每股收益
        diluted_eps	        float	Y	稀释每股收益
        total_revenue	    float	Y	营业总收入
        revenue	            float	Y	营业收入
        int_income	        float	Y	利息收入
        prem_earned	        float	Y	已赚保费
        comm_income	        float	Y	手续费及佣金收入
        n_commis_income	    float	Y	手续费及佣金净收入
        n_oth_income	    float	Y	其他经营净收益
        n_oth_b_income	    float	Y	加:其他业务净收益
        prem_income	        float	Y	保险业务收入
        out_prem	        float	Y	减:分出保费
        une_prem_reser	    float	Y	提取未到期责任准备金
        reins_income	    float	Y	其中:分保费收入
        n_sec_tb_income	    float	Y	代理买卖证券业务净收入
        n_sec_uw_income	    float	Y	证券承销业务净收入
        n_asset_mg_income	float	Y	受托客户资产管理业务净收入
        oth_b_income	    float	Y	其他业务收入
        fv_value_chg_gain	float	Y	加:公允价值变动净收益
        invest_income	    float	Y	加:投资净收益
        ass_invest_income	float	Y	其中:对联营企业和合营企业的投资收益
        forex_gain	        float	Y	加:汇兑净收益
        total_cogs	        float	Y	营业总成本
        oper_cost	        float	Y	减:营业成本
        int_exp	            float	Y	减:利息支出
        comm_exp	        float	Y	减:手续费及佣金支出
        biz_tax_surchg	    float	Y	减:营业税金及附加
        sell_exp	        float	Y	减:销售费用
        admin_exp	        float	Y	减:管理费用
        fin_exp	            float	Y	减:财务费用
        assets_impair_loss	float	Y	减:资产减值损失
        prem_refund	        float	Y	退保金
        compens_payout	    float	Y	赔付总支出
        reser_insur_liab	float	Y	提取保险责任准备金
        div_payt	        float	Y	保户红利支出
        reins_exp	        float	Y	分保费用
        oper_exp	        float	Y	营业支出
        compens_payout_refu	float	Y	减:摊回赔付支出
        insur_reser_refu	float	Y	减:摊回保险责任准备金
        reins_cost_refund	float	Y	减:摊回分保费用
        other_bus_cost	    float	Y	其他业务成本
        operate_profit	    float	Y	营业利润
        non_oper_income	    float	Y	加:营业外收入
        non_oper_exp	    float	Y	减:营业外支出
        nca_disploss	    float	Y	其中:减:非流动资产处置净损失
        total_profit	    float	Y	利润总额
        income_tax	        float	Y	所得税费用
        n_income	        float	Y	净利润(含少数股东损益)
        n_income_attr_p	    float	Y	净利润(不含少数股东损益)
        minority_gain	    float	Y	少数股东损益
        oth_compr_income	float	Y	其他综合收益
        t_compr_income	    float	Y	综合收益总额
        compr_inc_attr_p	float	Y	归属于母公司(或股东)的综合收益总额
        compr_inc_attr_m_s	float	Y	归属于少数股东的综合收益总额
        ebit	            float	Y	息税前利润
        ebitda	            float	Y	息税折旧摊销前利润
        insurance_exp	    float	Y	保险业务支出
        undist_profit	    float	Y	年初未分配利润
        distable_profit	    float	Y	可分配利润
        update_flag	        str	    N	更新标识，0未修改1更正过
    :example
        income(ts_code='600000.SH', start_date='20180101',
               end_date='20180730',
               fields='ts_code,ann_date,f_ann_date,end_date,report_type,comp_type,basic_eps,diluted_eps')
    """
    if fields is None: fields = 'ts_code,ann_date,f_ann_date,end_date,report_type,comp_type,basic_eps,diluted_eps'
    pro = ts.pro_api()
    return pro.income(ts_code=ts_code,
                      ann_date=ann_date,
                      start_date=start_date,
                      end_date=end_date,
                      period=period,
                      report_type=report_type,
                      comp_type=comp_type,
                      fields=fields)


class History:
    '历史数据管理类，使用一个“历史数据仓库 Historical Warehouse”来管理所有的历史数据'
    '''使用tushare包来下载各种历史数据，将所有历史数据打包存储为历史数据仓库格式，在需要使用的时候
    从仓库中读取数据并确保数据格式的统一。统一的数据格式为Universal Historical Format'''
    # 类属性：
    # 数据仓库存储文件夹（未来可以考虑使用某种数据库格式来存储所有的历史数据）
    __warehouse_dir = 'qteasy/history/'
    # 不同类型的数据
    __intervals = {'d': 'daily', 'w': 'weekly', '30': '30min', '15': '15min'}

    PRICE_TYPES = ['close',
                   'open',
                   'high',
                   'low',
                   'volume',
                   'value']

    def __init__(self):
        # 可用的历史数据通过extract方法存储到extract属性中
        # 所有数据通过整理后存储在数据仓库中 warehouse
        # 在磁盘上可以同时保存多个不同的数据仓库，数据仓库必须打开后才能导出数据，同时只能打开一个数据仓库 
        # 每个数据仓库就是一张数据表，包含所有股票在一定历史时期内的一种特定的数据类型，如5分钟开盘价
        # 以上描述为第一个版本的数据组织方式，以后可以考虑采用数据库来组织数据
        # 对象属性：

        self.days_work = [1, 2, 3, 4, 5]  # 每周工作日
        self.__warehouse = pd.DataFrame()  # 打开的warehouse
        self.__open_wh_file = ''  #
        self.__open_price_type = ''
        self.__open_interval = ''
        self.__open_wh_shares = set()
        self.__warehouse_is_open = False
        self.__extract = pd.DataFrame()
        self.__extracted = False

        # =========================
        # set up tushare token and account
        # =========================
        token = '14f96621db7a937c954b1943a579f52c09bbd5022ed3f03510b77369'
        self.ts_pro = ts.pro_api(token)

    # 以下为只读对象属性
    @property
    def wh_path(self):  # 当前打开的仓库的路径和文件名
        return self.__open_wh_file

    @property
    def wh_is_open(self):  # 当有仓库文件打开时返回True
        return self.__warehouse_is_open

    @property
    def price_type(self):  # 当前打开的仓库文件的数据类型
        return self.__open_price_type

    @property
    def freq(self):  # 当前打开的仓库文件的数据间隔
        return self.__open_interval

    @property
    def wh_shares(self):  # 当前打开的仓库文件包含的股票
        return self.__open_wh_shares

    @property
    def warehouse(self):  # 返回当前打开的数据仓库
        return self.__warehouse

    @property
    def hist_list(self):  # 返回当前提取出来的数据表
        return self.__extract

    # 对象方法：
    def hist_list(self, shares=None, start=None, end=None, freq=None):
        # 提取一张新的数据表
        raise NotImplementedError

    def info(self):
        # 打印当前数据仓库的关键信息
        if self.__warehouse_is_open:
            print('warehouse is open: ')
            print('warehouse path: ', self.__open_wh_file)
            print('price type: ', self.__open_price_type, 'time freq:', self.__open_interval)
            print('warehouse info: ')
            print(self.__warehouse.info())
        else:
            print('No warehouse history')

    def read_warehouse(self, price_type='close', interval='d'):
        # 从磁盘上读取数据仓库
        # 输入：
        # price_type： 数据类型
        # interval： 数据间隔
        # 输出：=====
        # data： 读取的数据（DataFrame对象）
        # fname：所读取的文件名
        # intervals = {'d': 'daily', 'w': 'weekly', '30': '30min', '15': '15min'}
        fname = self.__warehouse_dir + '_share_' + self.__intervals[interval] + '_' + price_type + '.csv'
        data = pd.read_csv(fname, index_col='date')
        data.index = pd.to_datetime(data.index, format='%Y-%m-%d')
        return data, fname

    def warehouse_new(self, code, price_type, hist_data):
        # 读取磁盘上现有的数据，并生成一个数据仓库
        raise NotImplementedError

    def warehouse_open(self, price_type='close', interval='d'):
        # 打开一个新的数据仓库，关闭并存储之前打开的那一个
        if self.__open_price_type != price_type or self.__open_interval != interval:
            data, fname = self.read_warehouse(price_type, interval)
            self.__warehouse = data
            self.__open_wh_file = fname
            self.__open_price_type = price_type
            self.__open_interval = interval
            self.__open_wh_shares = set(self.__warehouse.columns)
            self.__warehouse_is_open = True

    def warehouse_update(self, codes, interval):
        # 读取最新的历史数据并更新已读取的数据仓库文件添加新增的数据
        # basics = pd.read_csv('qteasy/__share_basics.csv', index_col='code')
        # print basics.head()
        code_set = self.__make_share_set(codes)
        # print 'code set', code_set, 'len', len(code_set)
        # print code_set.issubset(set(basics.index))
        # if code_set.issubset(set(basics.index)) and len(code_set) > 0:
        if len(code_set) > 0:
            print('loading warehouses...')
            wh_close, f1 = self.read_warehouse('close', interval)
            wh_open, f2 = self.read_warehouse('open', interval)
            wh_high, f3 = self.read_warehouse('high', interval)
            wh_low, f4 = self.read_warehouse('low', interval)
            wh_vol, f5 = self.read_warehouse('volume', interval)
            wh_dict = {'close': wh_close, 'open': wh_open, 'high': wh_high,
                       'low': wh_low, 'volume': wh_vol}
            # update the shape of all wharehouses by merging new columns or new rows
            # and then update
            print('generating expanding dataframe...')
            last_day = wh_close.index[-1].date()
            codes_in_wh = set(wh_close.columns)
            new_code_set = code_set.difference(codes_in_wh)
            # create the expanding df that contains extended rows and columns
            days = self.trade_days(start=last_day, freq=interval)
            # print days
            index = pd.Index(days, name='date')
            expand_df = pd.DataFrame(index=index, columns=new_code_set)
            # print 'expand_df:', expand_df
            # merge all temp wh one by one
            # in order to update the warehouse, the size of dataframe should be modified
            if len(expand_df.index) > 0 or len(expand_df.columns) > 0:
                # if not expand_df.empty:
                print('df merged')
                for tp in ['close', 'open', 'high', 'low', 'volume']:
                    wh_dict[tp] = pd.merge(wh_dict[tp], expand_df, left_index=True,
                                           right_index=True, how='outer')
            # print 'warehouse merged: ', wh_dict['close'].index
            # read data and update all warehouses
            # print 'code_set:', code_set
            print('reading tushare data and updating warehouse...')
            count = 0
            for code in code_set:
                count += 1
                try:
                    data = self.get_new_price(code, interval)
                    # print data
                    msg = 'reading data ' + str(code) + ', progress: ' + str(count) + ' of ' + str(len(code_set))
                    print(msg, end='\r')
                    for tp in ['close', 'open', 'high', 'low', 'volume']:
                        # in order to update the warehouse, the size of dataframe should be modified
                        df = pd.DataFrame(data[tp])
                        df.columns = [code]
                        # print df.tail()
                        # print wh_dict[tp].tail().loc[:][code]
                        wh_dict[tp].update(df)
                        # print 'dataFrame updated: ', wh_dict[tp][code].tail()
                except:
                    print('data cannot be read:', code, 'resume next,', count, 'of', len(code_set))
                    # save all updated warehouses
            print('\n', 'data updated, saving warehouses...')
            for tp in ['close', 'open', 'high', 'low', 'volume']:
                # in order to update the warehouse, the size of dataframe should be modified
                fname = self.__warehouse_dir + '_share_' + self.__intervals[interval] + '_' + tp + '.csv'
                wh_dict[tp].to_csv(fname)
            return True

    def warehouse_save(self):
        # 保存但不关闭数据仓库
        self.__warehouse.to_csv(self.__open_wh_file)
        pass

    def warehouse_close(self):
        # 关闭但不保存数据仓库
        if self.__warehouse_is_open:
            self.__warehouse = pd.DataFrame()
            self.__open_wh_file = ''
            self.__open_price_type = ''
            self.__open_interval = ''
            self.__open_wh_shares = set()
            self.__warehouse_is_open = False
        else:
            print('no warehouse opened')
        return self.__warehouse_is_open

    def warehouse_extract(self, shares, start, end):
        # 从打开的数据仓库中提取数据
        share_set = self.__make_share_set(shares)
        if share_set.issubset(self.__open_wh_shares):
            try:
                start = pd.to_datetime(start)
                end = pd.to_datetime(end)
                data = self.__warehouse.loc[start:end][shares]
                self.__extracted = True
                self.__extract = data
            except:
                print('Data Not extracted: date format should be %Y-%m-%d!')
                self.remove_extract()
        else:
            print('Data NOT extracted: one or more share(s) is not in the warehouse, check your input')
            self.remove_extract()
        return self.__extract

    def warehouse_get_last(self, code):
        # 从打开的数据仓库中提取指定股票的最后的数据及日期
        if self.__warehouse_is_open:
            if code in self.__warehouse.columns:
                data = self.__warehouse
                # print data.head()
                col = code
                # print col
                record = data[col]
                # print record.tail()
                if len(record) > 0:
                    date = record.last_valid_index()
                    price = record[date]
                else:
                    date = datetime.today() + dt.timedelta(-1077)
                    price = 0.0
                return date, price
            else:
                return dt.date(2018, 1, 1), 0.0

    def get_new_price(self, code, interval='d'):
        # 使用tushare读取某只股票的最新数据，指定数据间隔
        # print 'running get_new_price'
        if self.__open_price_type != 'close' and self.__open_interval != interval:
            self.warehouse_open(price_type='close', interval=interval)
        pre_date, pre_close = self.warehouse_get_last(code=code)
        # print pre_date, pre_close
        start = (pre_date + dt.timedelta(1)).strftime('%Y-%m-%d')
        # print code, start, interval
        data = ts.get_hist_data(code, start=start, ktype=interval)
        data = data[::-1][['open', 'close', 'low', 'high', 'volume', 'price_change']]
        # print data.head()
        if pre_close == 0.0:
            pre_close = data.iloc[0].close
        data['price_close'] = data.price_change.cumsum() + pre_close
        data['diff'] = data.price_close - data.close
        # print data.head()
        for tp in ['open', 'high', 'low']:
            data[tp] = np.round(data[tp] + data['diff'], 2)
        # print data.head()
        data.close = np.round(data.price_close, 2)
        data.index = pd.to_datetime(data.index, format='%Y-%m-%d')
        # print data.head()
        # print 'price_get completed!!'
        return data[['open', 'close', 'low', 'high', 'volume']]

    def extract(self, shares, price_type='close', start=None, end=None, interval='d'):
        # 从打开的数据仓库中提取所需的数据
        start, end = self.__check_default_dates(start, end)
        self.warehouse_open(price_type=price_type, interval=interval)
        return self.warehouse_extract(shares, start, end)

    def remove_extract(self):
        # 清空已经提取的数据表
        self.__extract = pd.DataFrame()
        self.__extracted = False

    def work_days(self, start=None, end=None, freq='d'):
        # 生成开始到结束日之间的所有工作日（根据对象属性工作日确定）
        # 公共假日没有考虑在本方法中
        start, end = self.__check_default_dates(start, end)
        w_days = []
        tag_date = start
        while tag_date < end:
            if tag_date.weekday() in self.days_work:
                w_days.append(tag_date)
            tag_date += dt.timedelta(days=1)
        return w_days

    def trade_days(self, start=None, end=None, freq='d'):
        # 生成开始日到结束日之间的所有交易日
        # 根据freq参数生成交易日序列内的交易时间点序列
        open_AM = '10:00:00'
        close_AM = '11:30:00'
        open_PM = '13:30:00'
        close_PM = '15:00:00'
        start, end = self.__check_default_dates(start, end)
        day0 = dt.date(1990, 12, 19)  # the first trade day in the trade day list
        end = (end - day0).days
        start = (start - day0).days
        trade_list = ts.trade_cal()
        trade_list = trade_list[start:end][trade_list['isOpen'] == 1]['calendarDate']
        if freq == 'd' or freq == 'D':
            return trade_list.values
        elif freq == '30' or freq == '15':
            T_list = []
            for days in trade_list.values:
                open_ = days + ' ' + open_AM
                close_ = days + ' ' + close_AM
                T_list.extend(pd.date_range(start=open_, end=close_, freq=freq + 'min').values)
                open_ = days + ' ' + open_PM
                close_ = days + ' ' + close_PM
                T_list.extend(pd.date_range(start=open_, end=close_, freq=freq + 'min').values)
            return T_list
        elif freq == 'w':
            pass
        else:
            pass

    def __check_default_dates(self, start, end):
        # 生成默认的开始和结束日（当其中一个或两者都为None时）
        if end == None:
            end = datetime.today().date()  # 如果end为None则设置end为今天
        if start == None:
            start = end + dt.timedelta(-30)  # 如果start为None则设置Start为end前30天
        return start, end

    def __make_share_set(self, shares):
        # 创建包含列表中所有股票元素的集合（去掉重复的股票）
        if type(shares) == str:
            share_set = set()
            share_set.add(shares)
        else:
            share_set = set(shares)
        return share_set
        # all_share.to_csv('qteasy/__share_basics.csv')
        # all_share.to_hdf('qteasy/__share_basics.hdf', 'key1', mode = 'w')
