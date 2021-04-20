# coding=utf-8
# utilfuncs.py

# ======================================
# This file contains all functions that
# might be shared among different files
# in qteasy.
# ======================================

import numpy as np
import pandas as pd
import sys
import qteasy
from pandas import Timestamp
from datetime import datetime

TIME_FREQ_STRINGS = ['TICK',
                     'T',
                     'MIN',
                     'H',
                     'D', '5D', '10D', '20D',
                     'W',
                     'M',
                     'Q',
                     'Y']
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


def mask_to_signal(lst):
    """将持仓蒙板转化为交易信号.

        转换的规则为比较前后两个交易时间点的持仓比率，如果持仓比率提高，
        则产生相应的补仓买入信号；如果持仓比率降低，则产生相应的卖出信号将仓位降低到目标水平。
        生成的信号范围在(-1, 1)之间，负数代表卖出，正数代表买入，且具体的买卖信号signal意义如下：
        signal > 0时，表示用总资产的 signal * 100% 买入该资产， 如0.35表示用当期总资产的35%买入该投资产品，如果
            现金总额不足，则按比例调降买入比率，直到用尽现金。
        signal < 0时，表示卖出本期持有的该资产的 signal * 100% 份额，如-0.75表示当期应卖出持有该资产的75%份额。
        signal = 0时，表示不进行任何操作

    input:
        :param lst，ndarray，持仓蒙板
    return: =====
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

    example:
    unify([[3.0, 2.0, 5.0], [2.0, 3.0, 5.0]])
    =
    [[0.3, 0.2, 0.5], [0.2, 0.3, 0.5]]

    :param arr: type: np.ndarray
    :return: ndarray
    """
    assert isinstance(arr, np.ndarray), f'InputError: Input should be ndarray! got {type(arr)}'
    s = arr.sum(1)
    shape = (s.shape[0], 1)
    return arr / s.reshape(shape)


def time_str_format(t: float, estimation: bool = False, short_form: bool = False):
    """ 将int或float形式的时间(秒数)转化为便于打印的字符串格式

    :param t:  输入时间，单位为秒
    :param estimation:
    :param short_form: 时间输出形式，默认为False，输出格式为"XX hour XX day XX min XX sec", 为True时输出"XXD XXH XX'XX".XXX"
    :return:
    """
    assert isinstance(t, float), f'TypeError: t should be a float number, got {type(t)}'
    assert t >= 0, f'ValueError, t should be greater than 0, got minus number'
    # debug
    # print(f'time input is {t}')
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

    :param unknown_input: slice or int/str or list of int/string
    :param str_int_dict: a dictionary that contains strings as keys and integer as values
    :return:
        a list of slice/list that can be used to slice the Historical Data Object
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
    例如，列表target_list 中含有三个元素，分别是[100, 130, 170]
    现在输入一个label清单，作为列表中三个元素的标签，分别为：['first', 'second', 'third']
    使用labels_to_dict函数生成一个字典ID如下：
    ID:  {'first' : 0
          'second': 1
          'third' : 2}
    通过这个字典，可以容易且快速地使用标签访问target_list中的元素：
    target_list[ID['first']] == target_list[0] == 100

    本函数对输入的input_labels进行合法性检查，确保input_labels中没有重复的标签，且标签的数量与target_list相同
    :param input_labels: 输入标签，可以接受两种形式的输入：
                                    字符串形式: 如:     'first,second,third'
                                    列表形式，如:      ['first', 'second', 'third']
    :param target_list: 需要进行映射的目标列表
    :return:
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


def str_to_list(input_string, sep_char: str = ','):
    """将逗号或其他分割字符分隔的字符串序列去除多余的空格后分割成字符串列表，分割字符可自定义"""
    assert isinstance(input_string, str), f'InputError, input is not a string!, got {type(input_string)}'
    res = input_string.replace(' ', '').split(sep_char)
    return res


# TODO: this function can be merged with str_to_list()y
def input_to_list(pars: [str, int, list], dim: int, padder=None):
    """将输入的参数转化为List，同时确保输出的List对象中元素的数量至少为dim，不足dim的用padder补足

    input:
        :param pars，需要转化为list对象的输出对象
        :param dim，需要生成的目标list的元素数量
        :param padder，当元素数量不足的时候用来补充的元素
    return: =====
        items, list 转化好的元素清单
    """
    if isinstance(pars, (str, int, np.int64)):  # 处理字符串类型的输入
        # print 'type of types', type(items)
        pars = [pars] * dim
    else:
        pars = list(pars)  # 正常处理，输入转化为列表类型
    par_dim = len(pars)
    # 当给出的两个输入参数长度不一致时，用padder补齐type输入，或者忽略多余的部分
    if par_dim < dim:
        pars.extend([padder] * (dim - par_dim))
    return pars


def regulate_date_format(date_str: [str, object]) -> str:
    """ tushare的财务报表函数只支持YYYYMMDD格式的日期，因此需要把YYYY-MM-DD及YYYY/MM/DD格式的日期转化为YYYYMMDD格式

    :param date_str:
    :return:
    """
    try:
        date_time = pd.to_datetime(date_str)
        return date_time.strftime('%Y%m%d')
    except:
        raise ValueError(f'Input string {date_str} can not be converted to a time format')


def list_to_str_format(str_list: [list, str]) -> str:
    """ tushare的财务报表函数只支持逗号分隔值的字符串形式作为ts_code或fields等字段的输入，如果输入是list[str]类型，则需要转换

    将list型数据转变为str类型，如
    ['close', 'open', 'high', 'low'] -> 'close, open, high, low'

    :param str_list: type: list[str]
    :return: string
    """
    assert isinstance(str_list, (list, str)), f'TypeError: expect list[str] or str type, got {type(str_list)} instead'
    if isinstance(str_list, str):
        str_list = str_list.split(' ')
    res = ''.join([item.replace(' ', '') + ',' for item in str_list if isinstance(item, str)])
    return res[0:-1]


def progress_bar(prog: int, total: int = 100, comments: str = '', short_form: bool = False):
    """根据输入的数字生成进度条字符串并刷新

    :param prog: 当前进度，用整数表示
    :param total:  总体进度，默认为100
    :param comments:  需要显示在进度条中的文字信息
    :param short_form:  显示
    """
    if total > 0:
        if prog > total:
            prog = total
        progress_str = f'\r \rProgress: [{PROGRESS_BAR[int(prog / total * 40)]}]' \
                       f' {prog}/{total}. {np.round(prog / total * 100, 1)}%  {comments}'
        sys.stdout.write(progress_str)
        sys.stdout.flush()


def maybe_trade_day(date):
    """ 判断一个日期是否交易日（或然判断，只剔除明显不是交易日的日期）
    准确率有限但是效率高

    :param date:
        :type date: obj datetime-like 可以转化为时间日期格式的字符串或其他类型对象

    :return:
    """
    # public_holidays 是一个含两个list的tuple，存储了闭市的公共假期，第一个list是代表月份的数字，第二个list是代表日期的数字
    public_holidays = ([1, 1, 1, 4, 4, 4, 5, 5, 5, 10, 10, 10, 10, 10, 10, 10],
                       [1, 2, 3, 3, 4, 5, 1, 2, 3, 1,  2,  3,  4,  5,  6,  7])
    try:
        date = pd.to_datetime(date)
    except:
        raise TypeError('date is not a valid date time format, cannot be converted to timestamp')
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
    else:
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
    else:
        d = pd.to_datetime(date)
        next = d + pd.Timedelta(1, 'd')
        while not maybe_trade_day(next):
            next = next + pd.Timedelta(1, 'd')
        return next


def is_market_trade_day(date, exchange: str = 'SSE'):
    """ 根据交易所发布的交易日历判断一个日期是否是交易日，准确性高但需要读取网络数据，因此效率低

    :param date:
        :type date: obj datetime-like 可以转化为时间日期格式的字符串或其他类型对象

    :param exchange:
        :type exchange: str 交易所代码:
                            SSE:    上交所,
                            SZSE:   深交所,
                            CFFEX:  中金所,
                            SHFE:   上期所,
                            CZCE:   郑商所,
                            DCE:    大商所,
                            INE:    上能源,
                            IB:     银行间,
                            XHKG:   港交所

    :return:
    """
    try:
        _date = pd.to_datetime(date)
    except Exception as ex:
        ex.extra_info = f'{date} is not a valid date time format, cannot be converted to timestamp'
        raise
    assert _date is not None, f'{date} is not a valide date'
    if _date < pd.to_datetime('19910101') or _date > pd.to_datetime('20211231'):
        return False
    if not isinstance(exchange, str) and exchange in ['SSE',
                                                      'SZSE',
                                                      'CFFEX',
                                                      'SHFE',
                                                      'CZCE',
                                                      'DCE',
                                                      'INE',
                                                      'IB',
                                                      'XHKG']:
        raise TypeError(f'exchange \'{exchange}\' is not a valid input')
    non_trade_days = qteasy.tsfuncs.trade_calendar(exchange=exchange, is_open=0)
    return _date not in non_trade_days


def prev_market_trade_day(date, exchange='SSE'):
    """ 根据交易所发布的交易日历找到它的前一个交易日，准确性高但需要读取网络数据，因此效率较低

    :param date:
        :type date: obj datetime-like 可以转化为时间日期格式的字符串或其他类型对象

    :param exchange:
        :type exchange: str 交易所代码:
                            SSE:    上交所,
                            SZSE:   深交所,
                            CFFEX:  中金所,
                            SHFE:   上期所,
                            CZCE:   郑商所,
                            DCE:    大商所,
                            INE:    上能源,
                            IB:     银行间,
                            XHKG:   港交所

    :return:
    """
    try:
        _date = pd.to_datetime(date)
    except Exception as ex:
        ex.extra_info = f'{date} is not a valid date time format, cannot be converted to timestamp'
        raise
    assert _date is not None, f'{date} is not a valide date'
    if _date < pd.to_datetime('19910101') or _date > pd.to_datetime('20211231'):
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

    :param date:
        :type date: obj datetime-like 可以转化为时间日期格式的字符串或其他类型对象

    :param exchange:
        :type exchange: str 交易所代码:
                            SSE:    上交所,
                            SZSE:   深交所,
                            CFFEX:  中金所,
                            SHFE:   上期所,
                            CZCE:   郑商所,
                            DCE:    大商所,
                            INE:    上能源,
                            IB:     银行间,
                            XHKG:   港交所

    :return:
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

    :param weekday:
    :return:
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

    :param lst:
        list, 需要被切分的列表
    :param trunc_size:
        int, 列表中元素数量
    :return:
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


def function_debugger(func):
    """ a decorator that can be used to debug func during run time,
    print out extra information:

    name of function
    arguments of the function
    type of arguments of the function
    run-time of the function
    :param func:
    :return:
    """

    def func_debugger(*args, **kwargs):
        import time
        try:
            st = time.time()
            res = func(*args, **kwargs)
            run_time = time.time() - st
            print(f'Run time: {run_time * 1000:.5f} ms\nresult of {func.__name__}({args, kwargs}) is\n{res}')
            return res
        except Exception as ex:
            print(f'Error encountered during run time of function {func.__name__}({args, kwargs})\n'
                  f'types of arguments:')
            for arg in args:
                print(f'{arg}:    \n{type(arg)}')
            for arg in kwargs:
                print(f'{arg}:    \n{type(arg)}')
            raise

    return func_debugger