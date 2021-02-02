# coding=utf-8
# evaluate.py

# ======================================
# This file contains functions that are
# used to evaluate back testing results.
# ======================================

import numpy as np
import pandas as pd

from .utilfuncs import str_to_list


def performance_statistics(performances: list, stats='mean'):
    """ 输入几个不同的评价指标，对它们进行统计分析，并输出统计分析的结果

    :param performance: 一个列表，包含一个或多个不同的评价指标，所有评价指标
    :return:
    """
    assert isinstance(performances, list), \
        f'performance dicts should be a list of dicts, got {type(performances)} instead'
    assert all(isinstance(perf, dict) for perf in performances),\
        f'One or more of the performances dicts is not dict'
    assert any(bool(perf) for perf in performances), \
        f'One or more of the performance dicts is empty!\n' \
        f'got performances:\n{performances}'

    # TODO: following calculations available only for numeric performances,
    # TODO: op_infos shall be excluded, op_infos like: oper_count(pd.DataFrame)
    # TODO:
    res = {}
    if 'oper_count' in performances[0]:
        res['oper_count'] = 0
        for perf in performances:
            res['oper_count'] += perf['oper_count']
        res['oper_count'] = res['oper_count'] / len(performances)
    if 'max_date' in performances[0]:
        res['max_date'] = performances[0]['max_date']
        res['low_date'] = performances[0]['low_date']
    keys_to_process = [perf for perf in performances[0] if perf not in ['oper_count', 'max_date', 'low_date']]
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
        else:
            raise KeyError(f'the stats {stats} is not yet implemented!')

    return res


def evaluate(op_list, looped_values, hist_reference, reference_data, cash_plan, indicators: str = 'final_value'):
    """ 根据args获取相应的性能指标，所谓性能指标是指根据生成的交易清单、回测结果、参考数据类型及投资计划输出各种性能指标
        返回一个dict，包含所有需要的indicators

    :param op_list: operator对象生成的交易清单
    :param hist_reference: 参考数据，通常为有参考意义的大盘数据，代表市场平均收益水平
    :param reference_data: 参考数据类型，当hist_reference中包含多重数据时，指定某一个数据类型（如close）为参考数据
    :param cash_plan: 投资计划
    :param indicators: 评价指标，逗号分隔的多个评价指标
    :return:
    :type looped_values: dict: 一个字典，每个指标的各种值
    """
    indicator_list = str_to_list(indicators)
    performance_dict = {}
    if any(indicator in indicator_list for indicator in ['years', 'oper_count', 'total_invest', 'total_fee', 'return']):
        years, oper_count, total_invest, total_fee = eval_operation(op_list=op_list,
                                                                    looped_value=looped_values,
                                                                    cash_plan=cash_plan)
        performance_dict['years'] = years
        performance_dict['oper_count'] = oper_count
        performance_dict['total_invest'] = total_invest
        performance_dict['total_fee'] = total_fee
    # 评价回测结果——计算回测终值
    if any(indicator in indicator_list for indicator in ['FV', 'fv', 'final_value']):
        performance_dict['final_value'] = eval_fv(looped_val=looped_values)
    # 评价回测结果——计算总投资收益率
    if any(indicator in indicator_list for indicator in ['return', 'rtn', 'total_return']):
        performance_dict['rtn'] = performance_dict['final_value'] / performance_dict['total_invest']
    # 评价回测结果——计算最大回撤比例以及最大回撤发生日期
    if any(indicator in indicator_list for indicator in ['mdd', 'max_drawdown']):
        mdd, max_date, low_date = eval_max_drawdown(looped_values)
        performance_dict['mdd'] = mdd
        performance_dict['max_date'] = max_date
        performance_dict['low_date'] = low_date
    # 评价回测结果——计算投资期间的波动率系数
    if any(indicator in indicator_list for indicator in ['volatility', 'v']):
        performance_dict['volatility'] = eval_volatility(looped_values)
    # 评价回测结果——计算参考数据收益率以及平均年化收益率
    if any(indicator in indicator_list for indicator in ['ref', 'ref_rtn', 'reference', 'ref_annual_rtn']):
        ref_rtn, ref_annual_rtn = eval_benchmark(looped_values, hist_reference, reference_data)
        performance_dict['ref_rtn'] = ref_rtn
        performance_dict['ref_annual_rtn'] = ref_annual_rtn
    # 评价回测结果——计算投资期间的beta贝塔系数
    if 'beta' in indicator_list:
        performance_dict['beta'] = eval_beta(looped_values, hist_reference, reference_data)
    # 评价回测结果——计算投资期间的夏普率
    if 'sharp' in indicator_list:
        performance_dict['sharp'] = eval_sharp(looped_values, total_invest, 0.035)
    # 评价回测结果——计算投资期间的alpha阿尔法系数
    if 'alpha' in indicator_list:
        performance_dict['alpha'] = eval_alpha(looped_values, total_invest, hist_reference, reference_data)
    # 评价回测结果——计算投资回报的信息比率
    if 'info' in indicator_list:
        performance_dict['info'] = eval_info_ratio(looped_values, hist_reference, reference_data)
    if bool(performance_dict):
        return performance_dict
    else:
        return performance_dict

# TODO: move all variable validations from evaluation sub functions to evaluate() function -> 2020/11/11
def _get_yearly_span(value_df: pd.DataFrame) -> float:
    """ 计算回测结果的时间跨度，单位为年。一年按照365天计算

    :param value_df: pd.DataFrame, 回测结果
    :return:
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

        :param looped_value:
        :param reference_value:
        :param reference_data:
        :return:
    """
    total_year = _get_yearly_span(looped_value)
    # debug
    # print(f'\nIn func eval_benchmark():\n'
    #       f'got parameters: \n'
    #       f'looped_value and info: {type(looped_value)}\n'
    #       f'reference_value and info: {type(reference_value)}'
    #       f'reference_data: {type(reference_data)}\n'
    #       f'info of looped_value and reference_value\n')
    # looped_value.info()
    # reference_value.info()
    rtn_data = reference_value[reference_data]
    rtn = (rtn_data[looped_value.index[-1]] / rtn_data[looped_value.index[0]])
    # # debug
    # print(f'\nIn func: eval_benchmark()\n')
    # print(f'total year is \n{total_year}')
    # print(f'total return is: \n{rtn_data[looped_value.index[-1]]} / {rtn_data[looped_value.index[0]]} = \n{rtn - 1}')
    # print(f'yearly return is:\n{rtn ** (1/total_year) - 1}')
    return rtn - 1, rtn ** (1 / total_year) - 1.


def eval_alpha(looped_value, total_invest, reference_value, reference_data, risk_free_ror: float = 0.035):
    """ 回测结果评价函数：alpha率

    阿尔法。具体计算方式为 (策略年化收益 - 无风险收益) - b × (参考标准年化收益 - 无风险收益)，
    这里的无风险收益指的是中国固定利率国债收益率曲线上10年期国债的年化到期收益率。
    :param looped_value:
    :param total_invest:
    :param reference_value:
    :param reference_data:
    :return:
    """
    total_year = _get_yearly_span(looped_value)
    final_value = eval_fv(looped_value)
    strategy_return = (final_value / total_invest) ** (1 / total_year) - 1
    reference_return, reference_yearly_return = eval_benchmark(looped_value, reference_value, reference_data)
    b = eval_beta(looped_value, reference_value, reference_data)
    return (strategy_return - risk_free_ror) - b * (reference_yearly_return - risk_free_ror)


def eval_beta(looped_value, reference_value, reference_data):
    """ 贝塔。具体计算方法为 策略每日收益与参考标准每日收益的协方差 / 参考标准每日收益的方差 。

    :param looped_value: pandas.DataFrame, 回测结果，需要计算Beta的股票价格或投资收益历史价格
    :param reference_value: pandas.DataFrame, 参考结果，用于评价股票价格波动的基准价格，通常用市场平均或股票指数价格代表，代表市场平均波动
    :param reference_data: str: 参考结果的数据类型，如close, open, low 等
    :return:
    """
    if not isinstance(reference_value, pd.DataFrame):
        raise TypeError(f'reference value should be pandas DataFrame, got {type(reference_value)} instead!')
    if not isinstance(looped_value, pd.DataFrame):
        raise TypeError(f'looped value should be pandas DataFrame, got {type(looped_value)} instead')
    if not reference_data in reference_value.columns:
        raise KeyError(f'reference data type \'{reference_data}\' can not be found in reference data')
    ret = (looped_value['value'] / looped_value['value'].shift(1)) - 1
    ret_dev = ret.var()
    ref = reference_value[reference_data]
    ref_ret = (ref / ref.shift(1)) - 1
    looped_value['ref'] = ref_ret
    looped_value['ret'] = ret
    # debug
    # print(f'return is:\n{looped_value.ret.values}')
    # print(f'reference value is:\n{looped_value.ref.values}')
    return looped_value.ref.cov(looped_value.ret) / ret_dev


def eval_sharp(looped_value, total_invest, riskfree_interest_rate: float = 0.035):
    """ 夏普比率。表示每承受一单位总风险，会产生多少的超额报酬。

    具体计算方法为 (策略年化收益率 - 回测起始交易日的无风险利率) / 策略收益波动率 。

    :param looped_value:
    :return:
    """
    total_year = _get_yearly_span(looped_value)
    final_value = eval_fv(looped_value)
    strategy_return = (final_value / total_invest) ** (1 / total_year) - 1
    volatility = eval_volatility(looped_value, logarithm=False)
    # debug
    # print(f'yearly return is: \n{final_value} / {total_invest} = \n{strategy_return}\n'
    #       f'volatility is:  \n{volatility}')
    return (strategy_return - riskfree_interest_rate) / volatility


def eval_volatility(looped_value, logarithm: bool = True):
    """ 策略收益波动率。用来测量资产的风险性。具体计算方法为 策略每日收益的年化标准差。可以使用logarithm参数指定是否计算对数收益率

    :param looped_value:
    :parma logarithm: 是否计算指数收益率，默认为True，计算对数收益率，为False时计算常规收益率
    :return:
    """
    assert isinstance(looped_value, pd.DataFrame), \
        f'TypeError, looped value should be pandas DataFrame, got {type(looped_value)} instead'
    if not looped_value.empty:
        if logarithm:
            ret = np.log(looped_value['value'] / looped_value['value'].shift(1))
        else:
            ret = (looped_value['value'] / looped_value['value'].shift(1)) - 1
        # debug
        # looped_value['ret'] = ret
        # print(f'return is \n {looped_value}')
        if len(ret) > 250:
            volatility = ret.rolling(250).std() * np.sqrt(250)
            # debug
            # print(f'standard deviations (a list rolling calculated) are {ret.rolling(250).std()}')
            return volatility.iloc[-1]
        else:
            volatility = ret.std() * np.sqrt(250)
            # debug
            # print(f'standard deviation (a single number with all data) is {ret.std()}')
            return volatility
    else:
        return -np.inf


def eval_info_ratio(looped_value, reference_value, reference_data):
    """ 信息比率。衡量超额风险带来的超额收益。具体计算方法为 (策略每日收益 - 参考标准每日收益)的年化均值 / 年化标准差 。
        information ratio = (portfolio return - reference return) / tracking error

    :param looped_value:
    :return:
    """
    ret = (looped_value['value'] / looped_value['value'].shift(1)) - 1
    ref = reference_value[reference_data]
    ref_ret = (ref / ref.shift(1)) - 1
    track_error = (ref_ret - ret).std(
            ddof=0)  # set ddof=0 to calculate population standard deviation, or 1 for sample deviation
    # debug
    # print(f'average return is {ret.mean()} from:\n{ret}\n'
    #       f'average reference return is {ref_ret.mean()} from: \n{ref_ret}\n'
    #       f'tracking error is {track_error} from difference of return:\n{ref_ret - ret}')
    return (ret.mean() - ref_ret.mean()) / track_error


def eval_max_drawdown(looped_value):
    """ 最大回撤。描述策略可能出现的最糟糕的情况。具体计算方法为 max(1 - 策略当日价值 / 当日之前虚拟账户最高价值)

    :param looped_value:
    :return:
    """
    assert isinstance(looped_value, pd.DataFrame), \
        f'TypeError, looped value should be pandas DataFrame, got {type(looped_value)} instead'
    if not looped_value.empty:
        max_val = 0.
        drawdown = 0.
        max_drawdown = 0.
        current_max_date = 0.
        max_value_date = 0.
        max_drawdown_date = 0.
        for date, value in looped_value.value.iteritems():
            if value > max_val:
                max_val = value
                current_max_date = date
            if max_val != 0:
                drawdown = 1 - value / max_val
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                max_drawdown_date = date
                max_value_date = current_max_date
        return max_drawdown, max_value_date, max_drawdown_date
    else:
        return -np.inf


def eval_fv(looped_val):
    """评价函数 Future Value 终值评价

    '投资模拟期最后一个交易日的资产总值

    input:
        :param looped_val，ndarray，回测器生成输出的交易模拟记录
    return:
        perf: float，应用该评价方法对回测模拟结果的评价分数

"""
    assert isinstance(looped_val, pd.DataFrame), \
        f'TypeError, looped value should be pandas DataFrame, got {type(looped_val)} instead'
    # debug
    # print(f'======================================\n'
    #       f'=                                    =\n'
    #       f'=   Start Evaluation of final value  =\n'
    #       f'=                                    =\n'
    #       f'======================================\n'
    #       f'IN EVAL_FV:\n'
    #       f'got DataFrame as following: \n{looped_val.info()}')
    if not looped_val.empty:
        try:
            perf = looped_val['value'].iloc[-1]
            return perf
        except:
            raise KeyError(f'the key \'value\' can not be found in given looped value!')
    else:
        return -np.inf


def eval_operation(op_list, looped_value, cash_plan):
    """ 评价函数，统计操作过程中的基本信息:

    对回测过程进行统计，输出以下内容：
    1，总交易次数：买入操作次数、卖出操作次数，总操作次数。由于针对不同的股票分别统计，因此操作次数并不是一个数字，而是一个DataFrame
    2，总投资额
    3，总交易费用
    4，回测时间长度

    :param looped_value:
    :param cash_plan:
    :return:
    """
    total_year = np.round((looped_value.index[-1] - looped_value.index[0]).days / 365., 1)
    sell_counts = []
    buy_counts = []
    # 循环统计op_list交易清单中每个个股
    for share, ser in op_list.iteritems():
        # 初始化计数变量
        sell_count = 0
        buy_count = 0
        current_pos = -1
        # 循环统计个股交易清单中的每条交易信号
        for i, value in ser.iteritems():
            if np.sign(value) != current_pos:
                current_pos = np.sign(value)
                if current_pos == 1:
                    buy_count += 1
                else:
                    sell_count += 1
        sell_counts.append(sell_count)
        buy_counts.append(buy_count)
    # 所有统计数字组装成一个DataFrame对象
    op_counts = pd.DataFrame(sell_counts, index=op_list.columns, columns=['sell'])
    op_counts['buy'] = buy_counts
    op_counts['total'] = op_counts.buy + op_counts.sell
    total_op_fee = looped_value.fee.sum()
    total_investment = cash_plan.total
    # 返回所有输出变量
    return total_year, op_counts, total_investment, total_op_fee


