# coding=utf-8
# ======================================
# File:     utilfuncs.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-02-21
# Desc:
#   Commonly used utility functions.
# ======================================

import numpy as np
import pandas as pd
import sys
import re
import qteasy
import time
from numba import njit
from functools import wraps

TIME_FREQ_LEVELS = {
    'Y':      10,
    'Q':      20,
    'M':      30,
    'W':      40,
    'D':      50,
    'H':      60,
    '30MIN':  70,
    '15MIN':  80,
    '5MIN':   90,
    '1MIN':   100,
    'MIN':    100,
    'T':      110,
    'TICK':   110,
}
TIME_FREQ_STRINGS = list(TIME_FREQ_LEVELS.keys())
AVAILABLE_ASSET_TYPES = ['E', 'IDX', 'FT', 'FD', 'OPT']
PROGRESS_BAR = {0:  '----------------------------------------', 1: '#---------------------------------------',
                2:  '##--------------------------------------', 3: '###-------------------------------------',
                4:  '####------------------------------------', 5: '#####-----------------------------------',
                6:  '######----------------------------------', 7: '#######---------------------------------',
                8:  '########--------------------------------', 9: '#########-------------------------------',
                10: '##########------------------------------', 11: '###########-----------------------------',
                12: '############----------------------------', 13: '#############---------------------------',
                14: '##############--------------------------', 15: '###############-------------------------',
                16: '################------------------------', 17: '#################-----------------------',
                18: '##################----------------------', 19: '###################---------------------',
                20: '####################--------------------', 21: '#####################-------------------',
                22: '######################------------------', 23: '#######################-----------------',
                24: '########################----------------', 25: '#########################---------------',
                26: '##########################--------------', 27: '###########################-------------',
                28: '############################------------', 29: '#############################-----------',
                30: '##############################----------', 31: '###############################---------',
                32: '################################--------', 33: '#################################-------',
                34: '##################################------', 35: '###################################-----',
                36: '####################################----', 37: '#####################################---',
                38: '######################################--', 39: '#######################################-',
                40: '########################################'
                }
NUMBER_IDENTIFIER = re.compile(r'^-?(0|[1-9]\d*)?(\.\d+)?(?<=\d)$')
BLENDER_STRATEGY_INDEX_IDENTIFIER = re.compile(r's\d*\d$')
ALL_COST_PARAMETERS = ['buy_fix', 'sell_fix', 'buy_rate', 'sell_rate', 'buy_min', 'sell_min', 'slipage']

AVAILABLE_SIGNAL_TYPES = {'position target':   'pt',
                          'proportion signal': 'ps',
                          'volume signal':     'vs'}
AVAILABLE_OP_TYPES = ['batch', 'stepwise', 'step', 'st', 's', 'b']


def retry(exception_to_check, tries=3, delay=1, backoff=2., mute=False, logger=None):
    """一个装饰器，当被装饰的函数抛出异常时，反复重试直至次数耗尽，重试前等待并延长等待时间.

    Parameters
    ----------
    exception_to_check: Exception 或 tuple
        需要检测的异常，当发生此异常时重试，可以用tuple给出多个异常
    tries: int
        最终放弃前的尝试次数
    delay: float
        第一次重试前等待的延迟时间（秒）
    backoff: float
        延迟倍增乘数，每多一次重试延迟时间就延长该倍数
    mute: bool, Default: False
        静默功能，True时不打印信息也不输出logger.warning, 只输出logger.info()
    logger: logging.Logger 对象
        日志logger对象. 如果给出None, 则打印结果
    """

    def deco_retry(f):

        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except exception_to_check as e:
                    # import pdb; pdb.set_trace()
                    msg = f'Error in {f.__name__}: {e.__class__}:{str(e)}, Retrying in {mdelay} seconds...'
                    if mute:
                        if logger:
                            logger.info(msg)
                    else:
                        if logger:
                            logger.warning(msg)
                        else:
                            print(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry


def mask_to_signal(lst):
    """将持仓蒙板转化为交易信号.

    转换的规则为比较前后两个交易时间点的持仓比率，如果持仓比率提高，
    则产生相应的补仓买入信号；如果持仓比率降低，则产生相应的卖出信号将仓位降低到目标水平。
    生成的信号范围在(-1, 1)之间，负数代表卖出，正数代表买入，且具体的买卖信号signal意义如下：
    signal > 0时，表示用总资产的 signal * 100% 买入该资产， 如0.35表示用当期总资产的35%买入该投资产品，如果
        现金总额不足，则按比例调降买入比率，直到用尽现金。
    signal < 0时，表示卖出本期持有的该资产的 signal * 100% 份额，如-0.75表示当期应卖出持有该资产的75%份额。
    signal = 0时，表示不进行任何操作

    Parameters
    ----------
    lst，ndarray
        持仓蒙板

    Returns
    -------
    op，ndarray，交易信号矩阵
    """
    np.seterr(divide='ignore', invalid='ignore')
    if lst.ndim == 2:  # 如果输入信号是2D的，则逐行操作（axis=0）
        # 比较本期交易时间点和上期之间的持仓比率差额，差额大于0者可以直接作为补仓买入信号，如上期为0.35，
        # 本期0.7，买入信号为0.35，即使用总资金的35%买入该股，加仓到70%
        op = (lst - np.roll(lst, shift=1, axis=0))
        # 差额小于0者需要计算差额与上期持仓数之比，作为卖出信号的强度，如上期为0.7，本期为0.35，差额为-0.35，则卖出信号强度
        # 为 (0.7 - 0.35) / 0.35 = 0.5即卖出50%的持仓数额，从70%仓位减仓到35%
        op = np.where(op < 0, (op / np.roll(lst, shift=1, axis=0)), op)
        # 补齐因为计算差额导致的第一行数据为NaN值的问题
        # print(f'creating operation signals, first signal is {lst[0]}')
        op[0] = lst[0]
    else:  # 如果输入信号是3D的，同样逐行操作，但Axis和2D情形不同(axis=1)
        op = (lst - np.roll(lst, shift=1, axis=1))
        op = np.where(op < 0, (op / np.roll(lst, shift=1, axis=1)), op)
        op[:, 0, :] = lst[:, 0, :]
    return op.clip(-1, 1)


def unify(arr):
    """调整输入矩阵每一行的元素，通过等比例缩小（或放大）后使得所有元素的和为1

    Parameters
    ----------
    arr: np.ndarray

    Returns
    -------
    ndarray

    examples
    --------
    >>> unify(np.array([[3.0, 2.0, 5.0], [1.0, 1.0, 1.0]]))
    array([[0.3   , 0.2   , 0.5   ],
           [0.3333, 0.3333, 0.3333]])
    """
    if isinstance(arr, np.ndarray):  # Input should be ndarray! got {type(arr)}'
        s = arr.sum(1)
        shape = (s.shape[0], 1)
        return arr / s.reshape(shape)
    if isinstance(arr, (int, float)):
        return arr
    raise TypeError(f'Input should be ndarray! got {type(arr)}')


def time_str_format(t: float, estimation: bool = False, short_form: bool = False):
    """ 将int或float形式的时间(秒数)转化为便于打印的字符串格式

    Parameters
    ----------
    t: float
        输入时间，单位为秒
    estimation: bool, Default: False
        True时返回结果精确到最大单位
    short_form: bool, Default: False
        时间输出形式，
        False时输出格式为"XX hour XX day XX min XX sec",
        True时输出"XXD XXH XX'XX".XXX"

    Returns
    -------
    str: 时间字符串格式
    """

    assert isinstance(t, (float, int)), f'TypeError: t should be a number, got {type(t)}'
    t = float(t)
    assert t >= 0, f'ValueError, t should be greater than 0, got minus number'

    str_element = []
    enough_accuracy = False
    if t >= 86400 and not enough_accuracy:
        if estimation:
            enough_accuracy = True
        days = t // 86400
        t = t - days * 86400
        str_element.append(str(int(days)))
        if short_form:
            str_element.append('D')
        else:
            str_element.append('days ')
    if t >= 3600 and not enough_accuracy:
        if estimation:
            enough_accuracy = True
        hours = t // 3600
        t = t - hours * 3600
        str_element.append(str(int(hours)))
        if short_form:
            str_element.append('H')
        else:
            str_element.append('hrs ')
    if t >= 60 and not enough_accuracy:
        if estimation:
            enough_accuracy = True
        minutes = t // 60
        t = t - minutes * 60
        str_element.append(str(int(minutes)))
        if short_form:
            str_element.append('\'')
        else:
            str_element.append('min ')
    if t >= 1 and not enough_accuracy:
        if estimation:
            enough_accuracy = True
        seconds = np.floor(t)
        t = t - seconds
        str_element.append(str(int(seconds)))
        if short_form:
            str_element.append('\"')
        else:
            str_element.append('s ')
    if not enough_accuracy:
        milliseconds = np.round(t * 1000, 1)
        if short_form:
            str_element.append(f'{int(np.round(milliseconds)):03d}')
        else:
            str_element.append(str(milliseconds))
            str_element.append('ms')

    return ''.join(str_element)


def list_or_slice(unknown_input: [slice, int, str, list], str_int_dict):
    """ 将输入的item转化为slice或数字列表的形式,用于生成HistoryPanel的数据切片：

    1，当输入item为slice时，直接返回slice
    2 输入数据为string, 根据string的分隔符类型确定选择的切片：
        2.1, 当字符串不包含分隔符时，直接输出对应的单片数据, 如'close'输出为[0]
        2.2, 当字符串以逗号分隔时，输出每个字段对应的切片，如'close,open', 输出[0, 2]
        2.3, 当字符串以冒号分割时，输出第一个字段起第二个字段止的切片，如'close:open',输出[0:2] -> [0,1,2]
    3 输入数据为列表时，检查列表元素的类型（不支持混合数据类型的列表如['close', 1, True]）：
        3.1 如果列表元素为string，输出每个字段名对应的列表编号，如['close','open'] 输出为 [0,2]
        3.2 如果列表元素为int时，输出对应的列表编号，如[0,1,3] 输出[0,1,3]
        3.3 如果列表元素为boolean时，输出True对应的切片编号，如[True, True, False, False] 输出为[0,1]
    4 输入数据为int型时，输出相应的切片，如输入0的输出为[0]

    Parameters
    ----------
    unknown_input: slice, int, str or list of int/str
    str_int_dict: dict: {str: int}

    Returns
    -------
    list of slice/list that can be used to slice the Historical Data Object
    """

    if isinstance(unknown_input, slice):
        return unknown_input  # slice object can be directly used
    elif isinstance(unknown_input, int):  # number should be converted to a list containing itself
        return np.array([unknown_input])
    elif isinstance(unknown_input, str):  # string should be converted to numbers
        string_input = unknown_input
        if string_input.find(',') > 0:
            string_list = str_to_list(input_string=string_input, sep_char=',')
            res = [str_int_dict[string] for string in string_list]
            return np.array(res)
        elif string_input.find(':') > 0:
            start_end_strings = str_to_list(input_string=string_input, sep_char=':')
            start = str_int_dict[start_end_strings[0]]
            end = str_int_dict[start_end_strings[1]]
            if start > end:
                start, end = end, start
            return np.arange(start, end + 1)
        else:
            return [str_int_dict[string_input]]
    elif isinstance(unknown_input, list):
        is_list_of_str = isinstance(unknown_input[0], str)
        is_list_of_int = isinstance(unknown_input[0], int)
        is_list_of_bool = isinstance(unknown_input[0], bool)
        if is_list_of_bool:
            return np.array(list(str_int_dict.values()))[unknown_input]
        else:
            # convert all items into a number:
            if is_list_of_str:
                res = [str_int_dict[list_item] for list_item in unknown_input]
            elif is_list_of_int:
                res = [list_item for list_item in unknown_input]
            else:
                return None
            return np.array(res)
    else:
        return None


def labels_to_dict(input_labels: [list, str], target_list: [list, range]) -> dict:
    """ 给target_list中的元素打上标签，建立标签-元素序号映射以方便通过标签访问元素

    根据输入的参数生成一个字典序列，这个字典的键为input_labels中的内容，值为一个[0~N]的range，且N=target_list中的元素的数量
    这个函数生成的字典可以生成一个适合快速访问的label与target_list中的元素映射，使得可以快速地通过label访问列表中的元素

    本函数对输入的input_labels进行合法性检查，确保input_labels中没有重复的标签，且标签的数量与target_list相同

    Parameters
    ----------
    input_labels:
        输入标签，可以接受两种形式的输入：
        字符串形式: 如:     'first,second,third'
        列表形式，如:      ['first', 'second', 'third']
    target_list:
        需要进行映射的目标列表

    Returns
    -------

    Examples
    --------
    例如，列表target_list 中含有三个元素，分别是[100, 130, 170]
    现在输入一个label清单，作为列表中三个元素的标签，分别为：['first', 'second', 'third']
    使用labels_to_dict函数生成一个字典ID如下：
    ID:  {'first' : 0
          'second': 1
          'third' : 2}
    通过这个字典，可以容易且快速地使用标签访问target_list中的元素：
    target_list[ID['first']] == target_list[0] == 100

    """
    if isinstance(input_labels, str):
        input_labels = str_to_list(input_string=input_labels)
    unique_count = len(set(input_labels))
    assert len(input_labels) == unique_count, \
        f'InputError, label duplicated, count of target list is {len(target_list)},' \
        f' got {unique_count} unique labels only.'
    assert unique_count == len(target_list), \
        f'InputError, length of input labels does not equal to that of target list, expect ' \
        f'{len(target_list)}, got {unique_count} unique labels instead.'
    return dict(zip(input_labels, range(len(target_list))))


def str_to_list(input_string, sep_char: str = ',', case=None, dim=None, padder=None):
    """将逗号或其他分割字符分隔的字符串序列去除多余的空格后分割成字符串列表，分割字符可自定义

    Parameters
    ----------
    input_string: str:
        需要分割的字符串
    sep_char: str:
        字符串分隔符， 默认','
    case: str
        默认None, 是否改变大小写，upper输出全大写, lower输出全小写
    dim: int
        需要生成的目标list的元素数量
    padder: str
        当元素数量不足的时候用来补充的元素

    Returns
    -------
    list of str: 字符串分割后的列表
    """
    assert isinstance(input_string, str), f'InputError, input is not a string!, got {type(input_string)}'
    if input_string == "":
        return list()
    res = input_string.replace(' ', '').split(sep_char)
    if case == 'upper':
        res = [string.upper() for string in res]
    elif case == 'lower':
        res = [string.lower() for string in res]
    else:
        pass
    res_len = len(res)
    if dim is None:
        dim = res_len
    if (res_len < dim) and (padder is not None):
        res.extend([padder] * dim - res_len)
    return res


def input_to_list(pars, dim, padder=None):
    """将输入的参数转化为List，同时确保输出的List对象中元素的数量至少为dim，不足dim的用padder补足

    Parameters
    ----------
    pars: int or list of int or list of str
        需要转化为list对象的输出对象
    dim: int
        需要生成的目标list的元素数量
    padder: Any
        当元素数量不足的时候用来补充的元素

    Returns
    -------
    items, list 转化好的元素清单
    """
    if isinstance(pars, (str, int, np.int64)):  # 处理字符串类型的输入
        pars = [pars] * dim
    else:
        pars = list(pars)  # 正常处理，输入转化为列表类型
    par_dim = len(pars)
    # 当给出的两个输入参数长度不一致时，用padder补齐type输入，或者忽略多余的部分
    if par_dim < dim:
        pars.extend([padder] * (dim - par_dim))
    return pars


def regulate_date_format(date_str: [str, object]) -> str:
    """ 把YYYY-MM-DD或YYYY/MM/DD等各种格式的日期转化为YYYYMMDD格式

    :param date_str:
    :return:
    """
    try:
        date_time = pd.to_datetime(date_str)
        return date_time.strftime('%Y%m%d')
    except:
        raise ValueError(f'Input string {date_str} can not be converted to a time format')


def list_to_str_format(str_list: [list, str]) -> str:
    """ 将list型的str数据转变为逗号分隔的str类型，

    Parameters
    ----------
    str_list: list[str]
        需要转化为str的列表

    Returns
    -------
    str: 组合后的字符串

    Examples
    --------
    >>> list_to_str_format(['close', 'open', 'high', 'low'])
    'close, open, high, low'
    """
    assert isinstance(str_list, (list, str)), f'TypeError: expect list[str] or str type, got {type(str_list)} instead'
    if isinstance(str_list, str):
        str_list = str_list.split(' ')
    res = ''.join([item.replace(' ', '') + ',' for item in str_list if isinstance(item, str)])
    return res[0:-1]


def progress_bar(prog: int, total: int = 100, comments: str = ''):
    """根据输入的数字生成进度条字符串并刷新

    Parameters
    ----------
    prog: int
        当前进度，用整数表示
    total: int
        总体进度，默认为100
    comments: str, optional
        需要显示在进度条中的文字信息
    """
    if total > 0:
        if prog > total:
            prog = total
        progress_str = f'\r \r[{PROGRESS_BAR[int(prog / total * 40)]}]' \
                       f'{prog}/{total}-{np.round(prog / total * 100, 1)}%  {comments}'
        sys.stdout.write(progress_str)
        sys.stdout.flush()


def maybe_trade_day(date):
    """ 判断一个日期是否交易日（或然判断，只剔除明显不是交易日的日期）准确率有限但是效率高

    Parameters
    ----------
    date: datetime-like
        可以转化为时间日期格式的字符串或其他类型对象

    Raises
    ------
    ValueError, 当字符串无法被转化为datetime时

    :return:
    bool
    """
    # public_holidays 是一个含两个list的tuple，存储了闭市的公共假期，第一个list是代表月份的数字，第二个list是代表日期的数字
    public_holidays = ([1, 1, 1, 4, 4, 4, 5, 5, 5, 10, 10, 10, 10, 10, 10, 10],
                       [1, 2, 3, 3, 4, 5, 1, 2, 3, 1, 2, 3, 4, 5, 6, 7])
    try:
        date = pd.to_datetime(date)
    except Exception:
        raise ValueError('date is not a valid date time format, cannot be converted to timestamp')
    if date.weekday() > 4:
        return False
    for m, d in zip(public_holidays[0], public_holidays[1]):
        if date.month == m and date.day == d:
            return False
    return True


def prev_trade_day(date):
    """ 找到一个日期的前一个或然交易日

    :param date:
    :return:
    """
    if maybe_trade_day(date):
        return date

    d = pd.to_datetime(date)
    prev = d - pd.Timedelta(1, 'd')
    while not maybe_trade_day(prev):
        prev = prev - pd.Timedelta(1, 'd')
    return prev


def next_trade_day(date):
    """ 返回一个日期的下一个或然交易日

    :param date:
    :return:
    """
    if maybe_trade_day(date):
        return date

    d = pd.to_datetime(date)
    next = d + pd.Timedelta(1, 'd')
    while not maybe_trade_day(next):
        next = next + pd.Timedelta(1, 'd')
    return next


def is_market_trade_day(date, exchange: str = 'SSE'):
    """ 根据交易所发布的交易日历判断一个日期是否是交易日，

    Parameters
    ----------
    date: str datetime like
        可以转化为时间日期格式的字符串或其他类型对象
    exchange: str
        交易所代码:
            SSE:    上交所, SZSE:   深交所,
            CFFEX:  中金所, SHFE:   上期所,
            CZCE:   郑商所, DCE:    大商所,
            INE:    上能源, IB:     银行间,
            XHKG:   港交所

    Raises
    ------
    NotImplementedError: 要求在本地DataSource中必须存在'trade_calendar'表，否则报错

    :return:
    bool
    """
    try:
        _date = pd.to_datetime(date)
    except Exception as ex:
        ex.extra_info = f'{date} is not a valid date time format, cannot be converted to timestamp'
        raise
    if _date is None:
        raise TypeError(f'{date} is not a valid date')
    if not isinstance(exchange, str) and exchange in ['SSE', 'SZSE', 'CFFEX', 'SHFE', 'CZCE',
                                                      'DCE', 'INE', 'IB', 'XHKG']:
        raise TypeError(f'exchange \'{exchange}\' is not a valid input')
    if qteasy.QT_TRADE_CALENDAR is not None:
        try:
            exchange_trade_cal = qteasy.QT_TRADE_CALENDAR.loc[exchange]
        except KeyError as e:
            raise KeyError(f'Trade Calender for exchange: {e} was not properly downloaded, please refill data')
        try:
            is_open = exchange_trade_cal.loc[_date].is_open
        except KeyError:
            raise ValueError(f'The date {_date} is out of trade calendar range, please refill data')
        return is_open == 1
    else:
        # TODO: Not yet implemented
        #  提供一种足够简单但不太精确的方式大致估算交易日期；
        #  或者直接使用maybe_trade_day()函数
        raise NotImplementedError


def prev_market_trade_day(date, exchange='SSE'):
    """ 根据交易所发布的交易日历找到某一日的上一交易日，需要提前准备QT_TRADE_CALENDAR数据

    - 如果date是交易日，则返回上一个交易日，如2020-12-24是交易日，它的前一天也是交易日，返回上一日2020-12-23
    - 如果date不是交易日，则返回它最近交易日的上一个交易日，如2020-12-25不是交易日，但2020-12-24是交易日，则
        返回2020-12-24的上一交易日即2020-12-23

    Parameters
    ----------
    date: str datetime like
        可以转化为时间日期格式的字符串或其他类型对象
    exchange: str
        交易所代码

    Returns
    -------
    pd.TimeStamp

    Raises
    ------
    NotImplementedError: 要求在本地DataSource中必须存在'trade_calendar'表，否则报错

    See Also
    --------
    is_market_trade_day()
    """
    try:
        _date = pd.to_datetime(date)
    except Exception as ex:
        ex.extra_info = f'{date} is not a valid date time format, cannot be converted to timestamp'
        raise
    if qteasy.QT_TRADE_CALENDAR is not None:
        exchange_trade_cal = qteasy.QT_TRADE_CALENDAR.loc[exchange]
        pretrade_date = exchange_trade_cal.loc[_date].pretrade_date
        return pretrade_date
    else:
        raise NotImplementedError


def nearest_market_trade_day(date, exchange='SSE'):
    """ 根据交易所发布的交易日历找到某一日的最近交易日，需要提前准备QT_TRADE_CALENDAR数据

    - 如果date是交易日，返回当日，如2020-12-24日是交易日，返回2020-12-24
    - 如果date不是交易日，返回date的前一个交易日，如2020-12-25是休息日，但它的前一天是交易日，因此返回2020-12-24

    Parameters
    ----------
    date: str datetime like
        可以转化为时间日期格式的字符串或其他类型对象
    exchange: str
        交易所代码

    Returns
    -------
    pd.TimeStamp

    See Also
    --------
    is_market_trade_day()
    """
    try:
        _date = pd.to_datetime(date)
    except Exception as ex:
        ex.extra_info = f'{date} is not a valid date time format, cannot be converted to timestamp'
        raise
    assert _date is not None, f'{date} is not a valide date'
    # TODO: 这里有bug: _date的上限和下限需要从trade_calendar中动态读取，而不能硬编码到源代码中
    if _date < pd.to_datetime('19910101') or _date > pd.to_datetime('20231231'):
        return None
    if is_market_trade_day(_date, exchange):
        return _date
    else:
        prev = _date - pd.Timedelta(1, 'd')
        while not is_market_trade_day(prev):
            prev = prev - pd.Timedelta(1, 'd')
        return prev


def next_market_trade_day(date, exchange='SSE'):
    """ 根据交易所发布的交易日历找到它的前一个交易日，准确性高但需要读取网络数据，因此效率较低

    Parameters
    ----------
    date: str datetime like
        可以转化为时间日期格式的字符串或其他类型对象
    exchange: str
        交易所代码

    Returns
    -------
    pd.TimeStamp

    Raises
    ------
    NotImplementedError: 要求在本地DataSource中必须存在'trade_calendar'表，否则报错

    See Also
    --------
    is_market_trade_day()
    """
    try:
        _date = pd.to_datetime(date)
    except Exception:
        raise TypeError(f'{date} is not a valid date time format, cannot be converted to datetime')
    assert _date is not None, f'{date} is not a valide date'
    if _date < pd.to_datetime('19910101') or _date > pd.to_datetime('20211231'):
        return None
    if is_market_trade_day(_date, exchange):
        return _date
    else:
        next = _date + pd.Timedelta(1, 'd')
        while not is_market_trade_day(next):
            next = next + pd.Timedelta(1, 'd')
        return next


def weekday_name(weekday: int):
    """ 将weekday数字转化为易于理解的人类语言

    Parameters
    ----------
    weekday: int
        需要转化的星期数字

    Returns
    -------
    str
    """
    weekday_names = {0: 'Monday',
                     1: 'Tuesday',
                     2: 'Wednesday',
                     3: 'Thursday',
                     4: 'Friday',
                     5: 'Saturday',
                     6: 'Sunday'}
    return weekday_names[weekday]


def list_truncate(lst, trunc_size):
    """ 将一个list切分成若干个等长的sublist，除最末一个列表以外，所有列表的元素数量都为trunc_size

    Parameters
    ----------
    lst: list
        需要被切分的列表
    trunc_size: int
        列表中元素数量

    Returns
    -------
    nested list, 切分好的子列表

    Examples
    --------
    >>> list_truncate([1,2,3,4,5,6,7,8,9,0], 4)
    >>> [[1,2,3,4], [5,6,7,8], [9,0]]
    """

    assert isinstance(lst, list), f'first parameter should be a list, got {type(lst)}'
    assert isinstance(trunc_size, int), f'second parameter should be an integer larger than 0'
    assert trunc_size > 0, f'second parameter should be an integer larger than 0, got {trunc_size}'
    total = len(lst)
    if total <= trunc_size:
        return [lst]
    else:
        sub_lists = []
        begin = 0
        end = trunc_size
        while begin < total:
            sub_lists.append(lst[begin:end])
            begin += trunc_size
            end += trunc_size
        return sub_lists


def is_number_like(key: [str, int, float]) -> bool:
    """ 判断一个字符串是否是一个合法的数字，使用re比原来的版本快5～10倍

    Parameters
    ----------
    key: [str, int, float], 需要检查的输入

    Returns
    -------
    bool
    """
    if isinstance(key, (float, int)):
        return True
    if not isinstance(key, str):
        return False
    if NUMBER_IDENTIFIER.match(key):
        return True
    return False
    # if len(key) == 0:
    #     return False
    # if all(ch in '-0123456789.' for ch in key):
    #     if key.count('.') + key.count('-') == len(key):
    #         return False
    #     if key.count('.') > 1 or key.count('-') > 1:
    #         return False
    #     if key.count('-') == 1 and key[0] != '-':
    #         return False
    #     if len(key) >= 2:
    #         if key[0] == '0' and key[1] != '.':
    #             return False
    #     return True
    # return False


def match_ts_code(code: str, asset_types='all', match_full_name=False):
    """ 根据输入匹配证券代码或证券名称，输出一个字典，包含在不同资产类别下找到的匹配项以及匹配总数

    如果给出asset_types参数，则限定只返回符合asset_types的结果
    - 输入六位证券代码匹配相应的证券
    - 输入证券名称模糊匹配
    - 输入带通配符的证券名称查找匹配的证券

    Parameters
    ----------
    code: str
        字母或数字代码，可以用于匹配股票、基金、指数、期货或期权的ts_code代码
    asset_types: str
        返回结果类型，以逗号分隔的资产类型代码，如"E,FD"代表只返回股票和基金代码
    match_full_name: bool
        是否匹配股票或基金全名，默认不匹配

    Returns
    -------
    Dict {'E':      [equity codes 股票代码],
          'IDX':    [index codes 指数代码],
          'FD':     [fund codes 基金代码],
          'FT':     [futures codes 期货代码],
          'OPT':    [options codes 期权代码]}

    Examples
    --------
    如果输入字符串全部为数字，则匹配证券代码ts_code，如：
        输入：
            000001
        匹配：
            '000001.SZ': '平安银行'，
            '000001.CZC': '农期指数',
            '000001.SH': '上证指数' ...

    输入的证券名称可以包含通配符，则进行模式匹配，如：
    - '?' 匹配一个字符，如
        输入：
            "中?集团"
        匹配
            '000039.SZ': '中集集团',
            '000759.SZ': '中百集团',
            '002309.SZ': '中利集团',
            '600252.SH': '中恒集团',
            '601512.SH': '中新集团'
    - '*' 匹配多个字符，如
        输入：
            "中*金"
        匹配：
            '600489.SH': '中金黄金',
            '600916.SH': '中国黄金'

    输入的证券名称如果不含通配符，将进行模糊匹配：并按匹配程度从高到低输出相似的名称，如：
        输入：
            '工商银行'
        匹配：
            '601398.SH': '工商银行',
            '600036.SH': '招商银行',
            '601916.SH': '浙商银行'
    """
    from qteasy import QT_DATA_SOURCE
    ds = QT_DATA_SOURCE
    df_s, df_i, df_f, df_ft, df_o = ds.get_all_basic_table_data()
    asset_type_basics = {k: v for k, v in zip(AVAILABLE_ASSET_TYPES, [df_s, df_i, df_ft, df_f, df_o])}

    if asset_types is None:
        asset_types = 'all'
    if isinstance(asset_types, str):
        asset_types = str_to_list(asset_types)
    if 'all' in asset_types:
        asset_types = AVAILABLE_ASSET_TYPES
    else:
        asset_types = [item for item in asset_types if item in AVAILABLE_ASSET_TYPES]

    asset_types_with_name = [item for item in asset_types if item in ['E', 'IDX', 'FD', 'FT', 'OPT']]
    code_matched = {}
    count = 0
    import re
    if re.match('[0-9A-Z]+\.[a-zA-Z]+$', code):
        # if code like "000100.SH"
        for at in asset_types:
            basic = asset_type_basics[at]
            ts_code = basic.loc[basic.index == code].name.to_dict()
            count += len(ts_code)
            code_matched.update({at: ts_code})
    elif re.match('[0-9A-Z]+$', code):
        # if code like all number inputs
        for at in asset_types:
            basic = asset_type_basics[at]
            basic['symbol'] = [item.split('.')[0] for item in basic.index]
            ts_code = basic.loc[basic.symbol == code].name.to_dict()
            count += len(ts_code)
            code_matched.update({at: ts_code})
    else:
        for at in asset_types_with_name:
            basic = asset_type_basics[at]
            names = basic.name.to_list()
            full_names = []
            match_full_name = (at in ['E', 'IDX']) and match_full_name
            if match_full_name:
                # 当需要匹配全名时
                full_names = basic.fullname.to_list()
            if ('?' in code) or ('*' in code):
                matched = _wildcard_match(code, names)
                code_matched[at] = basic.loc[basic.name.isin(matched)].name.to_dict()
                if match_full_name:
                    full_name_matched = _wildcard_match(code, full_names)
                    code_matched[at].update(basic.loc[basic.name.isin(full_name_matched)].name.to_dict())
            else:
                match_values = list(map(_partial_lev_ratio, [code] * len(names), names))
                basic['match_value'] = match_values
                sort_matched = basic.loc[basic.match_value >= 0.75].sort_values(by='match_value',
                                                                                ascending=False)
                code_matched[at] = sort_matched.name.to_dict()
                if match_full_name:
                    full_name_match_values = list(map(_partial_lev_ratio, [code] * len(full_names), full_names))
                    basic['full_name_match_value'] = full_name_match_values
                    full_name_sort_matched = \
                        basic.loc[basic.full_name_match_value >= 0.75].sort_values(
                                by='full_name_match_value',
                                ascending=False
                        )
                    code_matched[at].update(full_name_sort_matched.name.to_dict())
            count += len(code_matched[at])

    code_matched.update({'count': count})
    code_matched = {k: v for k, v in code_matched.items() if v != {}}
    return code_matched


def human_file_size(file_size: int) -> str:
    """ 将一个整型数字转化为以GB/MB/KB/Byte为单位的文件大小字符串

    :param file_size: int 表示文件大小的数字，单位为字节
    :return:
    """
    if not isinstance(file_size, (float, int)):
        return f'{file_size}'
    if file_size > 2 ** 40:
        return f'{file_size / 1048576 / 1048576 :.3f}TB'
    if file_size > 2 ** 30:
        return f'{file_size / 1048576 / 1024 :.2f}GB'
    elif file_size > 2 ** 20:
        return f'{file_size / 1048576 :.1f}MB'
    elif file_size > 2 ** 10:
        return f'{file_size / 1024 :.0f}KB'
    else:
        return f'{file_size}Byte'


def human_units(number: int, short_form=True) -> str:
    """ 将一个整型数字转化为以K/M/B/T为单位的文件大小字符串

    Parameters
    ----------
    number: int
        表示文件大小的数字，单位为字节
    short_form: bool, Default: True
        True时使用K/M/B/T 代表 thousand/million/billion/trillion

    Returns
    -------
    str: 字符串形式的数字
    """
    if not isinstance(number, (float, int)):
        return f'{number}'
    unit_dict = {'K': 'thousand',
                 'M': 'million',
                 'B': 'billion',
                 'T': 'trillion'}
    if short_form:
        unit_form = list(unit_dict.keys())
    else:
        unit_form = list(unit_dict.values())
    if number > 1E12:
        return f'{number / 1000000 / 1000000 :.3f}{unit_form[3]}'
    if number > 1E9:
        return f'{number / 1000000 / 1000 :.2f}{unit_form[2]}'
    elif number > 1E6:
        return f'{number / 1000000 :.1f}{unit_form[1]}'
    elif number > 1E3:
        return f'{number / 1000 :.0f}{unit_form[0]}'
    else:
        return f'{number}'


@njit()
def _lev_ratio(s, t):
    """ 比较两个字符串的相似度，计算两个字符串的 Levenshtein ratio,此处忽略大小写字母的区别

    Parameters
    ----------
    s, t: str  第一个和第二个字符串

    Returns
    -------
    float： 两个字符串的levenshtein ratio
    """

    s = s.lower()
    t = t.lower()
    # Initialize matrix of zeros
    rows = len(s) + 1
    cols = len(t) + 1
    distance = np.zeros((rows, cols))

    # Populate matrix of zeros with the indeces of each character of both strings
    for i in range(1, rows):
        for k in range(1, cols):
            distance[i][0] = i
            distance[0][k] = k

    # Iterate over the matrix to compute the cost of deletions,insertions and/or substitutions
    for col in range(1, cols):
        for row in range(1, rows):
            if s[row - 1] == t[col - 1]:
                cost = 0  # If the characters are the same in the two strings in a given position [i,j] then the cost
                # is 0
            else:
                cost = 2
            distance[row][col] = min(distance[row - 1][col] + 1,  # Cost of deletions
                                     distance[row][col - 1] + 1,  # Cost of insertions
                                     distance[row - 1][col - 1] + cost)  # Cost of substitutions
    # Computation of the Levenshtein Distance Ratio
    ratio = ((len(s) + len(t)) - distance[row][col]) / (len(s) + len(t))
    return ratio


@njit()
def _partial_lev_ratio(s, t):
    """ 比较两个字符串的局部相似度，返回最大相似度，此处忽略大小写的区别

    Parameters
    ----------
    s, t: str
        第一个和第二个字符串

    Returns
    -------
    float, 两个字符串的局部相似度值
    """

    s = s.lower()
    t = t.lower()
    if len(s) > len(t):
        longer = s
        shorter = t
    else:
        longer = t
        shorter = s
    l_short = len(shorter)
    l_long = len(longer)
    length = l_long - l_short + 1
    ratios = np.zeros((length,))

    for i in range(length):
        ratios[i] = _lev_ratio(shorter, longer[i:i + l_short])

    return ratios.max()


def _wildcard_match(mode, wordlist):
    """ 在字符串列表或序列中搜索符合模式的字符串

    Parameters
    ----------
    mode: str
        带通配符wildcard的字符串
    wordlist: iterable
        一个列表、元组、生成器或任何可循环的对象，包含一系列需要匹配的字符串

    Returns
    -------
    list: 匹配成功的字符串
    """
    import re

    mode = mode.replace('.', '').replace('.+', '')
    mode = mode.replace('?', '.').replace('*', '.+')
    mode = mode + '$'
    res = []

    for word in wordlist:
        if re.match(mode, word):
            res.append(word)

    return res


@njit
def ffill_3d_data(arr, init_val=0.):
    """ 给定一个三维np数组，如果数组中有nan值时，使用axis=1的前一个非Nan值填充Nan

    Parameters
    ----------
    arr: 3D ndarray
        一个含有Nan值的三维数组
    init_val: int, Default: 0.
        用于填充二维数组第一行Nan值的数字

    Returns
    -------
    ndarray, 填充后的ndarray
    """
    lv, row, col = arr.shape
    r0 = arr[:, 0, :]
    r0 = np.where(np.isnan(r0), init_val, r0)
    for i in range(row):
        if i == 0:
            arr[:, i, :] = r0
        r_c = arr[:, i, :]
        r_c = np.where(np.isnan(r_c), r0, r_c)
        r0 = r_c
        arr[:, i, :] = r_c
    return arr


@njit()
def ffill_2d_data(arr, init_val=0.):
    """ 给定一个二维np数组，如果数组中有nan值时，使用axis=0的前一个非Nan值填充Nan

    Parameters
    ----------
    arr: 2D ndarray
        一个含有Nan值的二维数组
    init_val: int, Default: 0.
        用于填充二维数组第一行Nan值的数字

    Returns
    -------
    ndarray, 填充后的ndarray
    """
    row, col = arr.shape
    r0 = arr[0, :]
    r0 = np.where(np.isnan(r0), init_val, r0)
    for i in range(row):
        if i == 0:
            arr[i, :] = r0
        r_c = arr[i, :]
        r_c = np.where(np.isnan(r_c), r0, r_c)
        r0 = r_c
        arr[i, :] = r_c
    return arr


@njit()
def fill_nan_data(arr, fill_val=0.):
    """ 给定一个ndarray，用fill_val来填充array中的nan值

    Parameters
    ----------
    arr: ndarray
        需要填充nan值的ndarray
    fill_val: float, Default: 0.
        需要填充的值

    Returns
    -------
    ndarray, 填充后的ndarray
    """
    return np.where(np.isnan(arr), fill_val, arr)


@njit()
def fill_inf_data(arr, fill_val=0.):
    """ 给定一个ndarray，用fill_val来填充array中的inf值

    Parameters
    ----------
    arr: ndarray
        需要填充inf值的ndarray
    fill_val: float, Default: 0.
        需要填充的值

    Returns
    -------
    ndarray, 填充后的ndarray
    """
    return np.where(np.isinf(arr), fill_val, arr)


def rolling_window(arr, window, axis=0):
    """ 给定一个ndarray，生成一个滑动窗口视图

    Parameters
    ----------
    arr: ndarray
        需要生成滑窗的矩阵，可以为1维或以上的数据
    window: int
        生成的滑动窗口的宽度
    axis: int, Default: 0
        生成滑窗的移动轴

    Returns
    -------
    ndarray_view
        输入数据的一个移动滑窗视图

    Examples
    --------
    >>> rolling_window(np.array([0,1,2,3,4,5]), 2)
    array([[0, 1, 2],
           [1, 2, 3],
           [2, 3, 4],
           [3, 4, 5]])
    >>> arr = np.random.randint(5, size=(5,4))
    array([[3, 0, 0, 0],
           [3, 2, 0, 2],
           [2, 3, 4, 1],
           [1, 2, 2, 3],
           [3, 2, 3, 0]])
    >>> rolling_window(arr, 3)
    array([[[3, 0, 0, 0],
            [3, 2, 0, 2],
            [2, 3, 4, 1]],

           [[3, 2, 0, 2],
            [2, 3, 4, 1],
            [1, 2, 2, 3]],

           [[2, 3, 4, 1],
            [1, 2, 2, 3],
            [3, 2, 3, 0]]])
    >>> rolling_window(arr, 3, 1)
    array([[[3, 0, 0],
            [3, 2, 0],
            [2, 3, 4],
            [1, 2, 2],
            [3, 2, 3]],

           [[0, 0, 0],
            [2, 0, 2],
            [3, 4, 1],
            [2, 2, 3],
            [2, 3, 0]]])

    Raises
    ------
    TypeError:
        当输入的参数类型不正确时
    ValueError:
        当输入的window或axis越界时
    """
    from numpy.lib.stride_tricks import as_strided
    if not isinstance(arr, np.ndarray):
        raise TypeError(f'arr should be an ndarray, got {type(arr)} instead.')
    if not isinstance(window, (int, np.int)):
        raise TypeError(f'window should be an integer, got {type(window)} instead.')
    if not isinstance(axis, int):
        raise TypeError(f'axis should be an integer, got {type(axis)} instead.')
    if window <= 0:
        raise ValueError(f'Invalid window({window}), can not be smaller than 0')
    if (axis < 0) or (axis >= arr.ndim):
        raise ValueError(f'Invalid axis({axis})')

    ndim = arr.ndim
    shape = list(arr.shape)
    strides = arr.strides
    axis_length = shape[axis]
    if window > axis_length:
        raise ValueError(f'window too long, should be less than or equal to axis_length ({axis_length})')
    window_count = axis_length - window + 1
    shape[axis] = window
    target_shape = (window_count, *shape)
    target_strides = (strides[axis], *strides)
    return as_strided(arr,
                      shape=target_shape,
                      strides=target_strides,
                      writeable=False)


def reindent(s, num_spaces=4):
    """ 给定一个（通常多行）的string，在每一行前面添加空格形成缩进效果

    Parameters
    ----------
    s: str
        待处理的字符串
    num_spaces: int, Default: 4
        需要添加的空格数量

    Returns
    -------
    str
    """
    if not isinstance(s, str):
        raise TypeError(f's should be a string, got {type(s)} instead')
    if not isinstance(num_spaces, int):
        raise TypeError(f'num_spaces should be an integer, got {type(num_spaces)} instead')
    if not 0 < num_spaces <= 50:
        raise ValueError(f'num_spaces should be larger than 0 and smaller or equal to 50, got {num_spaces}')
    s = s.split('\n')
    s = [(num_spaces * ' ') + line.lstrip() for line in s]
    s = '\n'.join(s)
    return s


def truncate_string(s, n, padder='.'):
    """ 如果字符串超过指定长度，则将字符串截短到制定的长度，并确保字符串的末尾有三个句点
        如果n<=4，则句点的数量相应减少
        如果n<0则报错

    Parameters
    ----------
    s: str
        字符串
    n: int
        需要保留的长度
    padder: str, Default: '.'
        作为省略号填充在字符串末尾的字符

    Returns
    -------
    str
    """
    if not isinstance(s, str):
        raise TypeError(f'the first argument should be a string, got {type(s)} instead')
    if not isinstance(n, int):
        raise TypeError(f'the second argument should be an integer, got {type(n)} instead')
    if not isinstance(padder, str):
        raise TypeError(f'the padder should be a character, got {type(padder)} instead')
    if not len(padder) == 1:
        raise ValueError(f'the padder should be a single character, got {len(padder)} characters')
    if n <= 1:
        raise ValueError(f'the expected length should be larger than 0, got {n}')
    if len(s) <= n:
        return s
    padder_count = 3
    if n < 3:
        padder_count = n
    return s[:n-padder_count] + padder * padder_count


