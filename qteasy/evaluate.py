# coding=utf-8
# ======================================
# File:     evaluate.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-11-07
# Desc:
#   Back-test result evaluation functions.
# ======================================

import numpy as np
import pandas as pd

import qteasy
from .utilfuncs import str_to_list
from .space import ResultPool


# TODO: 改进evaluate：生成完整的evaluate参数DataFrame
def performance_statistics(performances: list, stats='mean'):
    """ 输入几个不同的评价指标，对它们进行统计分析，并输出统计分析的结果
    所有输入侧评价指标存储在一个列表中，每个指标都必须是dict类型，且所有的dict结构相同，

    Parameters
    ----------
    performances: List:
        一个列表，包含一个或多个不同的评价指标，所有评价指标
    stats: str:
        统计方法，确定输出所有评价指标的统计方法：
        'mean':     返回所有指标的均值
        'std':      返回所有指标的标准差
        'max':      返回所有指标的最大值
        'min':      返回所有指标的最小值
        'median':   返回所有指标的中值

    Returns
    -------
    dict: 一个字典，其结构和输入的字典结构相同，值为输入数据的统计值

    Examples
    --------
    例如：
    performances = [{'fv':     20000,
                     'rtn':    0.12,
                     'beta':   0.003},
                    {'fv':     18000,
                     'rtn':    0.10,
                     'beta':   0.002},
                     {'fv':     35070,
                     'rtn':    0.245,
                     'beta':   0.013}]
    上面的performances中含有三组参数的评价指标，每组评价指标中都有fv、rtn、beta三种指标的评分

    >>> performance_statistics(performances, stats='mean')
        res = {'fv':     24356.666666666668,
               'rtn':    0.155,
               'beta':   0.006}

    >>> performance_statistics(performances, stats='max')
        res = {'fv':     35070,
               'rtn':    0.245,
               'beta':   0.013}

    >>> performance_statistics(performances, stats='min')
        res = {'fv':     18000,
               'rtn':    0.10,
               'beta':   0.002}

    """
    assert isinstance(performances, list), \
        f'performance dicts should be a list of dicts, got {type(performances)} instead'
    assert all(isinstance(perf, dict) for perf in performances), \
        f'One or more of the performances dicts is not dict'
    assert any(bool(perf) for perf in performances), \
        f'One or more of the performance dicts is empty!\n' \
        f'got performances:\n{performances}'

    res = dict()

    # try:
    #     res['par'] = performances[0]['par']
    # except:
    #     print(f'\nERROR RAISED! \n'
    #           f'in performance statistics: performances[0]:\n{performances[0]}')
    res['loop_start'] = performances[0]['loop_start']
    res['loop_end'] = performances[-1]['loop_end']
    # TODO: 想一个更好的处理多重回测后多重回测数据的处理办法
    res['complete_values'] = performances[0]['complete_values']
    if 'oper_count' in performances[0]:
        res['oper_count'] = 0
        for perf in performances:
            res['oper_count'] += perf['oper_count']
        res['oper_count'] = res['oper_count'] / len(performances)
        res['sell_count'] = res['oper_count'].sell.sum()
        res['buy_count'] = res['oper_count'].buy.sum()
    if 'peak_date' in performances[0]:
        res['peak_date'] = performances[0]['peak_date']
        res['valley_date'] = performances[0]['valley_date']
        res['recover_date'] = performances[0]['recover_date']
        res['worst_drawdowns'] = performances[0]['worst_drawdowns']
    if 'rtn' in performances[0]:
        res['return_df'] = performances[0]['return_df']
    keys_to_process = [perf for perf in performances[0] if perf not in ['oper_count',
                                                                        'peak_date',
                                                                        'valley_date',
                                                                        'recover_date',
                                                                        'loop_start',
                                                                        'loop_end',
                                                                        'complete_values',
                                                                        'worst_drawdowns',
                                                                        'return_df']]
    for key in keys_to_process:
        values = np.array([perf[key] for perf in performances])
        if stats == 'mean':
            res[key] = values.mean()
        elif stats == 'std':
            res[key] = values.std()
        elif stats == 'max':
            res[key] = values.max()
        elif stats == 'min':
            res[key] = values.min()
        elif stats == 'median':
            res[key] = np.median(values)
        else:
            raise KeyError(f'the stats {stats} is not yet implemented!')

    return res


def evaluate(looped_values: pd.DataFrame,
             hist_benchmark: pd.DataFrame,
             benchmark_data: pd.DataFrame,
             cash_plan,
             indicators: str = 'final_value')->dict:
    """ 根据args获取相应的性能指标，所谓性能指标是指根据生成的交易清单、回测结果、参考数据类型及投资计划输出各种性能指标
        返回一个dict，包含所有需要的indicators

    这里生成的indicators包含：
    - final_value:        回测区间最后一天的总资产金额
    - loop_start:        回测区间起始日
    - loop_end:          回测区间终止日
    - complete_values:   完整的回测历史价格记录
                         此DF包含的数据如下：
                         - stocks;
                         - operation fee;
                         - own cash;
                         - total value;
                         - indicators like rolling sharp/rolling alpha/rolling beta/rolling volatility
    - days:              回测历史周期总天数
    - months:            回测历史周期总月数
    - years:             回测历史周期年份数
    - oper_count         操作数量
    - total_invest       总投入资金数量
    - total_fee          总交易费用
    - rtn:               回测的总回报率
    - annual_rtn:        回测的年均回报率
    - mdd:               最大回测
    - peak_date:         最大回测峰值日期
    - valley_date:       最大回测谷值日期
    - volatility:        回测区间波动率（最后一日波动率）
    - ref_rtn:           benchmark参照指标的回报率
    - ref_annual_rtn:    benchmark参照指标的年均回报率
    - beta:              回测区间的beta值
    - sharp:             回测区间的夏普率
    - alpha:             回测区间的阿尔法值
    - info:              回测区间的信息比率
    - worst_drawdowns    一个DataFrame，五次最大的回撤记录
    TODO: 增加Omega Ratio、Calma Ratio、Stability、Tail Ratio、Daily value at risk

    Parameters
    ----------
    looped_values: pd.DataFrame:
        回测区间的历史价格记录
    hist_benchmark: pd.DataFrame,
        参考数据，通常为有参考意义的大盘数据，代表市场平均收益水平
    benchmark_data: pd.DataFrame,
        参考数据类型，当hist_reference中包含多重数据时，指定某一个数据类型（如close）为参考数据
    cash_plan: CashPlan,
        投资计划
    indicators: str, Default: 'final_value'
        评价指标，逗号分隔的多个评价指标

    Returns
    -------
    performance_dict: dict: 一个字典，每个指标的各种值
    """
    indicator_list = str_to_list(indicators)
    performance_dict = dict()
    # 评价回测结果——计算回测终值，这是默认输出结果
    performance_dict['final_value'] = eval_fv(looped_val=looped_values)
    performance_dict['loop_start'] = looped_values.index[0]
    performance_dict['loop_end'] = looped_values.index[-1]
    performance_dict['complete_values'] = looped_values
    days, months, years, oper_count, total_invest, total_fee = eval_operation(looped_value=looped_values,
                                                                              cash_plan=cash_plan)
    performance_dict['days'] = days
    performance_dict['months'] = months
    performance_dict['years'] = years
    performance_dict['oper_count'] = oper_count
    performance_dict['total_invest'] = total_invest
    performance_dict['total_fee'] = total_fee
    # 评价回测结果——计算总投资收益率
    if any(indicator in indicator_list for indicator in ['return', 'rtn', 'total_return']):
        rtn, annual_rtn, skewness, kurtosis, rtn_df = eval_return(looped_values, cash_plan)
        performance_dict['rtn'] = rtn
        performance_dict['annual_rtn'] = annual_rtn
        performance_dict['skew'] = skewness
        performance_dict['kurtosis'] = kurtosis
        performance_dict['return_df'] = rtn_df
    # 评价回测结果——计算最大回撤比例以及最大回撤发生日期
    if any(indicator in indicator_list for indicator in ['mdd', 'max_drawdown']):
        mdd, peak_date, valley_date, recover_date, drawdown_list = eval_max_drawdown(looped_values)
        performance_dict['mdd'] = mdd
        performance_dict['peak_date'] = peak_date
        performance_dict['valley_date'] = valley_date
        performance_dict['recover_date'] = recover_date
        performance_dict['worst_drawdowns'] = drawdown_list
    # 评价回测结果——计算投资期间的波动率系数
    if any(indicator in indicator_list for indicator in ['volatility', 'v']):
        performance_dict['volatility'] = eval_volatility(looped_values)
    # 评价回测结果——计算参考数据收益率以及平均年化收益率
    if any(indicator in indicator_list for indicator in ['ref', 'ref_rtn', 'reference', 'ref_annual_rtn']):
        ref_rtn, ref_annual_rtn = eval_benchmark(looped_values, hist_benchmark, benchmark_data)
        performance_dict['ref_rtn'] = ref_rtn
        performance_dict['ref_annual_rtn'] = ref_annual_rtn
    # 评价回测结果——计算投资期间的beta贝塔系数
    if 'beta' in indicator_list:
        performance_dict['beta'] = eval_beta(looped_values, hist_benchmark, benchmark_data)
    # 评价回测结果——计算投资期间的夏普率
    if 'sharp' in indicator_list:
        interest_rate = cash_plan.ir
        performance_dict['sharp'] = eval_sharp(looped_values, interest_rate)
    # 评价回测结果——计算投资期间的alpha阿尔法系数
    if 'alpha' in indicator_list:
        performance_dict['alpha'] = eval_alpha(looped_values, total_invest, hist_benchmark, benchmark_data)
    # 评价回测结果——计算投资回报的信息比率
    if 'info' in indicator_list:
        performance_dict['info'] = eval_info_ratio(looped_values, hist_benchmark, benchmark_data)
    if 'calmar' in indicator_list:
        performance_dict['info'] = eval_calmar(looped_values)
    if bool(performance_dict):
        return performance_dict
    else:
        return performance_dict


# TODO: move all variable validations from evaluation sub functions to evaluate() function -> 2020/11/11
def _get_yearly_span(value_df: pd.DataFrame) -> float:
    """ 计算回测结果的时间跨度，单位为年。一年按照365天计算

    Parameters
    ----------
    value_df: pd.DataFrame
        回测结果

    Returns
    -------
    total_year: float
    """
    if not isinstance(value_df, pd.DataFrame):
        raise TypeError(f'Looped value should be a pandas DataFrame, got {type(value_df)} instead!')
    first_day = value_df.index[0]
    last_day = value_df.index[-1]
    if isinstance(last_day, (int, float)) and isinstance(first_day, (int, float)):
        total_year = (last_day - first_day) / 365.
    else:
        try:
            total_year = (last_day - first_day).days / 365.
        except:
            raise ValueError(f'The yearly time span of the looped value can not be calculated, '
                             f'DataFrame index should be time or number format!, '
                             f'got {type(first_day)} and {type(last_day)}')
    return total_year


def eval_benchmark(looped_value, reference_value, reference_data):
    """ 参考标准年化收益率。具体计算方式为 （(参考标准最终指数 / 参考标准初始指数) ** 1 / 回测交易年数 - 1）

    Parameters
    ----------
    looped_value:
    reference_value:
    reference_data:

    Returns
    -------
    tuple: (total_rtn, annual_rtn)
    """
    total_year = _get_yearly_span(looped_value)
    try:
        rtn_data = reference_value[reference_data]
        rtn = (rtn_data[looped_value.index[-1]] / rtn_data[looped_value.index[0]])
        return rtn - 1, rtn ** (1 / total_year) - 1.
    except:
        pass
        return 0., 0.


def eval_alpha(looped_value, total_invest, reference_value, reference_data, risk_free_ror: float = 0.0035):
    """ 回测结果评价函数：alpha系数
    阿尔法系数(α)是基金的超额收益和按照β系数计算的期望收益之间的差额。 其计算方法如下：超额收益是基金的实际收益减去无
    风险投资收益(例如1年期银行定期存款收益)；期望收益是贝塔系数β和市场超额收益的乘积，反映基金由于市场整体变动而获得的收益；
    超额收益和期望收益的差额即α系数。

    阿尔法比率 alpha Ratio。具体计算方式为 (投资组合年化收益 - 无风险收益) - b × (基准组合年化收益 - 无风险收益)，

    Parameters
    ----------
    risk_free_ror: float
        无风险利率，默认值设置为0.35%
    looped_value: pd.DataFrame
        回测结果
    total_invest: float
        总投资金额
    reference_value: pd.DataFrame
        参考标准
    reference_data: str
        参考标准数据名称

    Returns
    -------
    alpha: float
    """
    loop_len = len(looped_value)
    # 计算alpha的过程需要用到beta，如果beta不存在则需要先计算beta
    if 'beta' not in looped_value.columns:
        b = eval_beta(looped_value, reference_value, reference_data)
    if loop_len <= 250:
        # 计算年化收益，如果回测期间小于一年，直接计算平均年收益率
        total_year = _get_yearly_span(looped_value)
        final_value = eval_fv(looped_value)
        strategy_return = (final_value / total_invest) ** (1 / total_year) - 1
        reference_return, reference_yearly_return = eval_benchmark(looped_value, reference_value, reference_data)
        b = eval_beta(looped_value, reference_value, reference_data)
        alpha = (strategy_return - risk_free_ror) - b * (reference_yearly_return - risk_free_ror)
        # 当回测期间小于1年时，填充空白alpha值
        looped_value['alpha'] = np.nan
        looped_value['alpha'].iloc[-1] = alpha
    else:  # loop_len > 250
        # 计算年化收益，如果回测期间大于一年，直接计算滚动年收益率（250天）
        year_ret = looped_value.value / looped_value['value'].shift(250) - 1
        bench = reference_value[reference_data]
        bench_ret = (bench / bench.shift(250)) - 1
        looped_value['alpha'] = (year_ret - risk_free_ror) - looped_value['beta'] * (bench_ret - risk_free_ror)
        alpha = looped_value['alpha'].mean()
    return alpha


def eval_beta(looped_value, reference_value, reference_data):
    """ 贝塔系数。考察投资组合与基准投资组合之间的相关性，它度量了投资组合相对于基准组合的风险大小或波动大小。
    贝塔系数越大，表示该投资组合相对于基准组合波动越大（通常使用市场平均水平作为基准）：
     - 当贝塔系数为1时，表示投资组合的波动等于市场平均水平
     - 当贝塔系数大于1时，投资组合的波动大于市场平均水平
     - 当贝塔系数小于1时，投资组合的波动小于市场平均水平
     - 当贝塔系数小于0时，投资组合的波动与市场平均水平相反

    具体计算方法为 策略每日收益与基准组合每日收益的协方差 / 基准组合每日收益的方差 。

    Parameters
    ----------
    looped_value:pd.DataFrame,
        回测结果，需要计算Beta的股票价格或投资收益历史价格
    reference_value: pd.DataFrame,
        参考结果，用于评价股票价格波动的基准价格，通常用市场平均或股票指数价格代表，代表市场平均波动
    reference_data: str:
        参考结果的数据类型，如close, open, low 等

    Returns
    -------
    beta: float
    """
    if not isinstance(reference_value, pd.DataFrame):
        raise TypeError(f'reference value should be pandas DataFrame, got {type(reference_value)} instead!')
    if not isinstance(looped_value, pd.DataFrame):
        raise TypeError(f'looped value should be pandas DataFrame, got {type(looped_value)} instead')
    if reference_data not in reference_value.columns:
        raise KeyError(f'reference data type \'{reference_data}\' can not be found in reference data')
    # 计算或获取每日收益率
    if 'pct_change' not in looped_value.columns:
        looped_value['pct_change'] = (looped_value['value'] / looped_value['value'].shift(1)) - 1
    ref = reference_value[reference_data]
    ref_ret = (ref / ref.shift(1)) - 1
    if len(looped_value) > 250:
        ret_dev = looped_value['pct_change'].rolling(250).var()
        looped_value['beta'] = looped_value['pct_change'].rolling(250).cov(ref_ret) / ret_dev
        return looped_value['beta'].mean()
    else:
        ret_dev = looped_value['pct_change'].var()
        beta = looped_value['pct_change'].cov(ref_ret) / ret_dev
        looped_value['beta'] = np.nan
        looped_value['beta'].iloc[-1] = beta
        return beta


def eval_sharp(looped_value, riskfree_interest_rate: float = 0.0035):
    """ 夏普比率。表示每承受一单位总风险，会产生多少的超额报酬。

    具体计算方法为 (策略年化收益率 - 回测起始交易日的无风险利率) / 策略收益波动率 。

    Parameters
    ----------
    looped_value: pd.DataFrame,
        回测结果，需要计算sharp率的股票价格或投资收益历史价格
    riskfree_interest_rate: float, Default: 0.0035
        无风险利率，用于计算超额收益，通常使用国债收益率作为无风险利率，如2019年国债收益率为3.35%，则riskfree_interest_rate=0.0035
    :return:
    """
    loop_len = len(looped_value)
    # 计算年化收益，如果回测期间大于一年，直接计算滚动年收益率（250天）
    ret = looped_value['value'] / looped_value['value'].shift(1) - 1
    volatility = eval_volatility(looped_value, logarithm=False)
    if loop_len <= 250:
        yearly_return = ret.mean() * 250
        sharp = (yearly_return - riskfree_interest_rate) / volatility
        looped_value['sharp'] = np.nan
        looped_value['sharp'].iloc[-1] = sharp
        return sharp
    else:  # loop_len > 250
        roll_yearly_return = ret.rolling(250).mean() * 250
        looped_value['sharp'] = (roll_yearly_return - riskfree_interest_rate) / looped_value['volatility']
        return looped_value['sharp'].mean()


def eval_volatility(looped_value, logarithm: bool = True):
    """ 策略收益波动率。用来测量资产的风险性。具体计算方法为 策略每日收益的年化标准差。可以使用logarithm参数指定是否计算对数收益率

    Parameters
    ----------
    looped_value: pd.DataFrame,
        回测结果，需要计算volatility的股票价格或投资收益历史价格
    logarithm: bool, Default: True
        是否计算指数收益率，默认为True，计算对数收益率，为False时计算常规收益率

    Returns
    -------
    volatility: float
    """
    assert isinstance(looped_value, pd.DataFrame), \
        f'TypeError, looped value should be pandas DataFrame, got {type(looped_value)} instead'
    if looped_value.empty:
        return -np.inf
    if logarithm:
        ret = np.log(looped_value['value'] / looped_value['value'].shift(1))
    else:
        ret = (looped_value['value'] / looped_value['value'].shift(1)) - 1
    if len(ret) > 250:
        volatility = ret.rolling(250).std() * np.sqrt(250)
        looped_value['volatility'] = volatility
        return volatility.mean()
    else:
        volatility = ret.std() * np.sqrt(250)
        looped_value['volatility'] = np.nan
        looped_value['volatility'].iloc[-1] = volatility
        return volatility


def eval_info_ratio(looped_value, reference_value, reference_data):
    """ 信息比率。衡量超额风险带来的超额收益。具体计算方法为 (策略每日收益 - 参考标准每日收益)的年化均值 / 年化标准差 。
        information ratio = (portfolio return - reference return) / tracking error

    Parameters
    ----------
    looped_value: pd.DataFrame,
        回测结果，需要计算info_ratio的股票价格或投资收益历史价格

    Returns
    -------
    info_ratio: float
    """
    ret = (looped_value['value'] / looped_value['value'].shift(1)) - 1
    ref = reference_value[reference_data]
    ref_ret = (ref / ref.shift(1)) - 1
    track_error = (ref_ret - ret).std(
            ddof=0)  # set ddof=0 to calculate population standard deviation, or 1 for sample deviation
    return (ret.mean() - ref_ret.mean()) / track_error


def eval_calmar(looped_value):
    """ Calmar ratio, 卡尔玛比率，定义为平均年化收益率与最大回撤比率的比值，定义每一份回撤获得多大的年化收益

    Parameters
    ----------
    looped_value: pd.DataFrame,
        回测结果，需要计算calmar的股票价格或投资收益历史价格

    Returns
    -------
    calmar: float
    """
    value = looped_value['value']
    cummax = value.cummax()
    drawdown = (cummax - value) / cummax
    if len(looped_value) > 250:
        ret = value / value.shift(250) - 1
        looped_value['calmar'] = ret / drawdown.rolling(250).max()
        return looped_value['calmar'].mean()
    else:  # len(looped_value <= 250
        ret = value[-1] / value[0] - 1
        calmar = ret / drawdown.max()
        looped_value['calmar'] = np.nan
        looped_value['calmar'].iloc[-1] = calmar
        return calmar


def eval_max_drawdown(looped_value):
    """ 最大回撤。描述策略可能出现的最糟糕的情况。具体计算方法为 max(1 - 策略当日价值 / 当日之前虚拟账户最高价值)
        除了计算最大回撤以外，同时还找到最大的五个回撤区间，分别找到他们的峰值日期、谷值日期、回撤率、回复日期
        并将上述信息放入一个DataFrame中与最大回撤相关数据一起返回

    Parameters
    ----------
    looped_value: pd.DataFrame,
        完整的回测历史价值数据，包括价格、现金、总价值

    Returns
    -------
    tuple: (max_drawdown, peak_date, valley_date, recover_date, dd_df)
    max_drawdown: 最大回撤
    peak_date: 峰值日期
    valley_date: 谷值日期
    recover_date: 回撤恢复日期
    dd_df:   完整的DataFrame，包含最大的五个回撤区间的全部信息
    """
    assert isinstance(looped_value, pd.DataFrame), \
        f'TypeError, looped value should be pandas DataFrame, got {type(looped_value)} instead'
    if looped_value.empty:
        return -np.inf
    cummax = looped_value['value'].cummax()
    looped_value['underwater'] = (looped_value['value'] - cummax) / cummax
    drawdown_sign = np.sign(looped_value.underwater)
    diff = drawdown_sign - drawdown_sign.shift(1)
    drawdown_starts = np.where(diff == -1)[0]
    drawdown_ends = np.where(diff == 1)[0]
    drawdown_count = min(len(drawdown_starts), len(drawdown_ends))
    dd_pool = ResultPool(5)
    for i_start, i_end in zip(drawdown_starts[:drawdown_count], drawdown_ends[:drawdown_count]):
        dd_start = looped_value.index[i_start - 1]
        dd_end = looped_value.index[i_end]
        dd_min = looped_value['underwater'].iloc[i_start:i_end].idxmin()
        dd = looped_value['underwater'].loc[dd_min]
        dd_pool.in_pool((dd_start, dd_min, dd_end, dd), dd)
    if len(drawdown_starts) > drawdown_count:
        dd_start = looped_value.index[drawdown_starts[-1] - 1]
        dd_end = np.nan
        dd_min = looped_value['underwater'].iloc[drawdown_starts[-1]:].idxmin()
        dd = looped_value['underwater'].loc[dd_min]
        dd_pool.in_pool((dd_start, dd_min, dd_end, dd), dd)
    dd_pool.cut(keep_largest=False)
    # 生成包含所有dd的DataFrame
    dd_df = pd.DataFrame(dd_pool.items, columns=['peak_date', 'valley_date', 'recover_date', 'drawdown'])
    dd_df.sort_values(by='drawdown', inplace=True)
    if dd_df.empty:  # 出现这种情况的一种可能是没有drawdown，因此drawdown应该为0
        output_date = looped_value.index[-1]
        return 0, output_date, output_date, output_date, dd_df
    else:
        mdd = dd_df.loc[0]
        max_drawdown = -mdd.drawdown
        peak_date = mdd.peak_date
        valley_date = mdd.valley_date
        recover_date = mdd.recover_date
        return max_drawdown, peak_date, valley_date, recover_date, dd_df


def eval_fv(looped_val):
    """评价函数 Future Value 终值评价

    '投资模拟期最后一个交易日的资产总值

    Parameters
    ----------
    looped_val: ndarray，
        回测器生成输出的交易模拟记录

    Returns
    -------
    perf: float，应用该评价方法对回测模拟结果的评价分数

    """
    if not isinstance(looped_val, pd.DataFrame):
        raise TypeError(f'looped value should be pandas DataFrame, got {type(looped_val)} instead')
    if looped_val.empty:
        return -np.inf
    if 'value' not in looped_val:
        raise KeyError(f'the key \'value\' can not be found in given looped value!')

    perf = looped_val['value'].iloc[-1]
    return perf


def eval_return(looped_val, cash_plan):
    """ 评价函数 Return Rate 收益率评价，在looped_value中补充完整的收益率和年化收益率数据
        在looped_val中添加以下数据：
        - invest:       每个交易日累计投入资金总额
        - rtn:          计算investment return投资回报率，也就是资产总额和投资总额的比率
        - annual_rtn:   年化投资收益率，每个交易日累计投资收益率的年化收益
        - pct_change:   每日收益率，也就是今天资产相对于昨天增值的比例
        - skew:         峰度
        - kurtosis:     偏度

    '滚动计算回测收益的年化收益率和总收益率，输出最后一天的总收益率和年化收益率

    Parameters
    ----------
    looped_val: pd.DataFrame，
        回测器生成输出的交易模拟记录
    cash_plan: qteasy.CashPlan，
        回测器生成的资金计划

    Returns
    -------
    tuple: (perf, annual_perf, skew, kurtosis, looped_val)
    perf: float，应用该评价方法对回测模拟结果的评价分数
    annual_perf: float，应用该评价方法对回测模拟结果的评价分数
    skew: float，应用该评价方法对回测模拟结果的评价分数
    kurtosis: float，应用该评价方法对回测模拟结果的评价分数
    looped_val: pd.DataFrame，回测器生成输出的交易模拟记录
    """
    assert isinstance(looped_val, pd.DataFrame), \
        f'TypeError, looped value should be pandas DataFrame, got {type(looped_val)} instead'
    assert isinstance(cash_plan, qteasy.CashPlan), \
        f'TypeError, cash plan type not valid, got {type(cash_plan)} instead'
    if looped_val.empty:
        return -np.inf, -np.inf, np.nan, np.nan, pd.DataFrame()
    invest_plan = cash_plan.plan
    looped_val['invest'] = invest_plan.amount
    looped_val = looped_val.fillna(0)
    looped_val['invest'] = looped_val.invest.cumsum()
    looped_val['rtn'] = looped_val.value / looped_val['invest'] - 1
    ys = (looped_val.index - looped_val.index[0]).days / 365.
    looped_val['annual_rtn'] = (looped_val.rtn + 1) ** (1 / ys) - 1
    looped_val['pct_change'] = looped_val.value / looped_val.value.shift(1) - 1
    skewness = looped_val['pct_change'].skew()
    kurtosis = looped_val['pct_change'].kurtosis()

    first_year = looped_val.index[0].year
    last_year = looped_val.index[-1].year
    starts = pd.date_range(start=str(first_year - 1) + '1231',
                           end=str(last_year) + '1130',
                           freq='M') + pd.Timedelta(1, 'd')
    ends = pd.date_range(start=str(first_year) + '0101',
                         end=str(last_year) + '1231',
                         freq='M')
    # 计算每个月的收益率
    monthly_returns = list()
    for start, end in zip(starts, ends):
        val = looped_val['value'].loc[start:end]
        if len(val) > 0:
            monthly_returns.append(val.iloc[-1] / val.iloc[0] - 1)
        else:
            monthly_returns.append(np.nan)
    year_count = len(monthly_returns) // 12
    monthly_returns = np.array(monthly_returns).reshape(year_count, 12)
    monthly_return_df = pd.DataFrame(monthly_returns,
                                     columns=['Jan', 'Feb', 'Mar', 'Apr',
                                              'May', 'Jun', 'Jul', 'Aug',
                                              'Sep', 'Oct', 'Nov', 'Dec'],
                                     index=range(first_year, last_year + 1))
    # 计算每年的收益率
    starts = pd.date_range(start=str(first_year - 1) + '1231',
                           end=str(last_year) + '1130',
                           freq='Y') + pd.Timedelta(1, 'd')
    ends = pd.date_range(start=str(first_year) + '0101',
                         end=str(last_year) + '1231',
                         freq='Y')
    # 组装出月度、年度收益率矩阵
    yearly_returns = list()
    for start, end in zip(starts, ends):
        val = looped_val['value'].loc[start:end]
        if len(val) > 0:
            yearly_returns.append(val.iloc[-1] / val.iloc[0] - 1)
        else:
            yearly_returns.append(np.nan)
    monthly_return_df['y-cum'] = yearly_returns
    return looped_val.rtn.iloc[-1], looped_val.annual_rtn.iloc[-1], skewness, kurtosis, monthly_return_df


def eval_operation(looped_value, cash_plan):
    """ 评价函数，统计操作过程中的基本信息:

    对回测过程进行统计，输出以下内容：
    1，总交易次数：买入操作次数、卖出操作次数，总操作次数。由于针对不同的股票分别统计，因此操作次数并不是一个数字，而是一个DataFrame
    2，总投资额
    3，总交易费用
    4，回测时间长度, 分别用年、月、日数表示，年的类型为float，月和日的类型都是int

    Parameters
    ----------
    looped_value: pd.DataFrame
        回测器生成输出的交易模拟记录
    cash_plan: qteasy.CashPlan
        回测器生成输出的资金计划

    Returns
    -------
    tuple: (total_days, total_months, total_years, total_trades, total_invest, total_fee)
    total_days: int 回测时间长度，以日数表示
    total_months: int 回测时间长度，以月数表示
    total_years: float 回测时间长度，以年数表示
    total_trades: pd.DataFrame 总交易次数，包括买入、卖出、总操作次数
    total_invest: float 总投资额
    total_fee: float 总交易费用
    """

    total_rounds = len(looped_value.index)
    total_days = (looped_value.index[-1] - looped_value.index[0]).days
    total_years = total_days / 365.
    total_months = int(np.round(total_days / 30))
    # 使用looped_values统计交易过程中的多空持仓时间比例
    holding_stocks = looped_value.copy()
    holding_stocks.drop(columns=['cash', 'fee', 'value', 'reference'], inplace=True)
    # 计算股票每一轮交易后的变化，增加者为买入，减少者为卖出
    holding_movements = holding_stocks - holding_stocks.shift(1)
    # 分别标记多仓/空仓，买入/卖出的位置，全部取sign（）以便后续方便加总统计数量
    holding_long = np.where(holding_stocks>0, np.sign(holding_stocks), 0)
    holding_short = np.where(holding_stocks<0, np.sign(holding_stocks), 0)
    holding_inc = np.where(holding_movements>0, np.sign(holding_movements), 0)
    holding_dec = np.where(holding_movements<0, np.sign(holding_movements), 0)
    # 统计数量
    sell_counts = -holding_dec.sum(axis=0)
    buy_counts = holding_inc.sum(axis=0)
    long_percent = holding_long.sum(axis=0) / total_rounds
    short_percent = -holding_short.sum(axis=0) / total_rounds

    op_counts = pd.DataFrame(sell_counts, index=holding_stocks.columns, columns=['sell'])
    op_counts['buy'] = buy_counts
    op_counts['total'] = op_counts.buy + op_counts.sell
    op_counts['long'] = long_percent
    op_counts['short'] = short_percent
    op_counts['empty'] = 1 - op_counts.long - op_counts.short
    total_op_fee = looped_value.fee.sum()
    total_investment = cash_plan.total
    # 返回所有输出变量
    return total_days, total_months, total_years, op_counts, total_investment, total_op_fee