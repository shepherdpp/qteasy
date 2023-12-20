# coding=utf-8
# ======================================
# File:     utilfuncs.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-02-21
# Desc:
#   Commonly used utility functions.
# ======================================

import argparse
import numpy as np
import pandas as pd
import sys
import re
import qteasy
import time
import warnings
from numba import njit
from functools import wraps, lru_cache

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
}  # TODO: 最好是将所有的frequency封装为一个类，确保字符串大小写正确，且引入复合频率的比较和处理
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
INTEGER_IDENTIFIER = re.compile(r'^-?(0|[1-9]\d*)$')
FLOAT_IDENTIFIER = re.compile(r'^-?(0|[1-9]\d*)?(\.\d+)?(?<=\d)$')
BLENDER_STRATEGY_INDEX_IDENTIFIER = re.compile(r's\d*\d$')
CN_STOCK_SYMBOL_IDENTIFIER = re.compile(r'^[0-9]{6}$')
# re identifier that matches string of 6 digits or 6 digits followed by a dot and "SZ" or "SH"
TS_CODE_IDENTIFIER_CN_STOCK = re.compile(r'^[0-9]{6}(\.SZ|\.SH|\.BJ)$')
TS_CODE_IDENTIFIER_CN_INDEX = re.compile(r'^[0-9]{6}(\.SH|\.SZ)$')
TS_CODE_IDENTIFIER_CN_FUND = re.compile(r'^[0-9]{6}(\.OF)$')
TS_CODE_IDENTIFIER_ALL = re.compile(r'^[0-9]{6}(\.SZ|\.SH|\.BJ|\.OF)$')
ALL_COST_PARAMETERS = ['buy_fix', 'sell_fix', 'buy_rate', 'sell_rate', 'buy_min', 'sell_min', 'slipage']

AVAILABLE_SIGNAL_TYPES = {'position target':   'pt',
                          'proportion signal': 'ps',
                          'volume signal':     'vs'}
AVAILABLE_OP_TYPES = ['batch', 'stepwise', 'step', 'st', 's', 'b']


def get_qt_argparser():
    """ 获取QT的命令行参数解析器

    生成的解析器包含以下参数：
    -a, --account: int, default None
        用于指定交易账户的ID，如果不指定，则使用默认账户
    -n, --new_account: str, default None
        用于指定新建账户的用户名，如果不指定，则使用默认账户
    -r, --restart: bool, default False
        用于指定是否清除所有账户数据并重新开始
    -d, --debug: bool, default False
        用于指定是否以debug模式启动交易程序
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--account', type=int, help='start trader with the given account id')
    parser.add_argument('-n', '--new_account', type=str, default=None,
                        help='if set, create a new account with the given user name')
    parser.add_argument('-r', '--restart', action='store_true', default=False,
                        help='if set, remove all record and restart account')
    parser.add_argument('-d', '--debug', action='store_true', help='if set, start trader in debug mode')

    return parser


def freq_dither(freq, freq_list):
    """ 频率抖动，将一个目标频率抖动到频率列表中的一个频率上，

    Parameters
    ----------
    freq: str
        目标频率
    freq_list: list of str
        频率列表

    Returns
    -------
    dithered_freq: str
        抖动后的频率

    Examples
    --------
    >>> freq_dither('M', ['Q', 'A'])
    'Q'
    >>> freq_dither('Q', ['M', 'A'])
    'M'
    >>> freq_dither('A', ['M', 'Q'])
    'M'
    >>> freq_dither('45min', ['5min', '15min', '30min', 'd', 'w', 'm'])
    '15MIN'
    """
    """抖动算法如下：
            0，从频率string中提取目标qty，目标主频、副频
            3，设定当前频率 = 目标主频，开始查找：
            # 4，将频率列表中的频率按level排序，并找到当前频率的插入位置，将列表分为高频列表与低频列表
            # 5，如果高频列表不为空，则从高频列表中取最低的主频，返回它
            # 6，否则从低频列表中取最高主频，返回它
            另一种方法
            4，逐次升高
    """

    qty, main_freq, sub_freq = parse_freq_string(freq)

    freq_list = [parse_freq_string(freq_string)[1] for freq_string in freq_list]
    level_list = np.array([get_main_freq_level(freq_string) for freq_string in freq_list])
    freq_level = get_main_freq_level(freq)

    level_list_sorter = level_list.argsort()
    insert_pos = level_list.searchsorted(freq_level, sorter=level_list_sorter)
    upper_level_arg_list = level_list_sorter[insert_pos:]
    lower_level_arg_list = level_list_sorter[:insert_pos]

    if len(upper_level_arg_list) > 0:
        # 在upper_list中位于第一位的可能是freq的同级频率，
        # 如果输出同级频率，需要确保该频率与freq一致，否则就需要跳过它
        maybe_found = freq_list[upper_level_arg_list[0]]
        if (get_main_freq_level(maybe_found) > freq_level) or (maybe_found == main_freq):
            return maybe_found
        # 查找下一个maybe_found
        return freq_list[upper_level_arg_list[1]]

    if len(lower_level_arg_list) > 0:
        return freq_list[lower_level_arg_list[-1]]
    return None


def parse_freq_string(freq, std_freq_only=False):
    """ 解析freqstring，找出其中的主频率、副频率，以及主频率的倍数

    Parameters
    ----------
    freq: str
        一个频率字符串
    std_freq_only: bool, default True
        是否使用复合频率，如果为True，则仅使用MIN/H等标准频率作为主频率，否则可使用5MIN/15MIN等复合频率作为主频率
        复合频率的定义TIME_FREQ_LEVELS

    Returns
    -------
    tuple: 包含三个元素(qty, main_freq, sub_freq)
    qty, int 主频率的倍数
    main_freq, str 主频率
    sub_freq, str 副频率

    Examples
    --------
    >>> parse_freq_string('25d')
    (25, 'D', '')
    >>> parse_freq_string('w-Fri')
    (1, 'W', 'Fri')
    >>> parse_freq_string('75min')
    (5, '15MIN', '')
    >>> parse_freq_string('90min')
    (3, '30MIN', '')
    >>> parse_freq_string('15min')
    (1, '15MIN', '')
    >>> parse_freq_string('15min', std_freq_only=True)
    (15, 'MIN', '')
    """

    import re

    freq_split = freq.split('-')
    qty = 1
    main_freq = freq_split[0].upper()
    sub_freq = ''
    if len(freq_split) >= 2:
        sub_freq = freq_split[1].upper()

    # 继续拆分main_freq与qty_part
    if len(main_freq) > 1:
        maybe_qty = ''.join(re.findall('\d+', main_freq))
        # 另外一种处理方法
        # qty_part = ''.join(list(filter(lambda x: x.isdigit(), main_freq)))
        qty_len = len(maybe_qty)
        if qty_len > 0:
            main_freq = main_freq[qty_len:]
            qty = int(maybe_qty)

    if main_freq not in TIME_FREQ_STRINGS:
        return None, None, None

    if (main_freq == 'MIN') and not std_freq_only:
        available_qty = [''.join(re.findall('\d+', freq_string)) for freq_string in TIME_FREQ_STRINGS]
        available_qty = [int(item) for item in available_qty if len(item) > 0]
        qty_fitness = [qty % item for item in available_qty]
        min_qty = available_qty[qty_fitness.index(0)]
        main_freq = str(min_qty) + main_freq
        qty = qty // min_qty

    return qty, main_freq, sub_freq


def get_main_freq_level(freq):
    """ 确定并返回freqency的级别

    :param freq:
    :return:
    """
    qty, main_freq, sub_freq = parse_freq_string(freq)
    if main_freq in TIME_FREQ_STRINGS:
        return TIME_FREQ_LEVELS[main_freq]
    else:
        return None


def next_main_freq(freq, direction='up'):
    """ 在可用freq清单中找到下一个可用的freq字符串

    :param freq: main_freq string
    :param direction: 'up' / 'down'
    :return:
    """
    freq = freq.upper()
    if freq not in TIME_FREQ_STRINGS:
        return None
    qty, main_freq, sub_freq = parse_freq_string(freq)
    level = get_main_freq_level(freq)
    freqs = list(TIME_FREQ_LEVELS.keys())
    target_pos = freqs.index(main_freq)
    while True:
        target_freq = freqs[target_pos]
        if direction == 'up':
            target_pos += 1
        elif direction == 'down':
            target_pos -= 1
        if get_main_freq_level(target_freq) != level:
            return target_freq


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
    lst: ndarray
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


def sec_to_duration(t: float, estimation: bool = False, short_form: bool = False):
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

    Examples
    --------
    >>> sec_to_duration(86400)
    '1 day '
    >>> sec_to_duration(86400, short_form=True)
    '1D'
    >>> sec_to_duration(86400, estimation=True)
    'about 1 day '
    >>> sec_to_duration(86399)
    '23 hour 59 min 59 sec'
    >>> sec_to_duration(86399, short_form=True)
    '23H 59'59".000"
    >>> sec_to_duration(86399, estimation=True)
    'about 1 day '
    >>> sec_to_duration(86399, estimation=True, short_form=True)
    '~ 1D'
    """

    # TODO: 此函数在estimation=True时，输出结果不准确，需要修正，例如，86399秒应该输出为1天，
    #  而不是23小时
    # TODO: 修正函数输出值的错，在estimation=True时，输出结果不正确）
    assert isinstance(t, (float, int)), f'TypeError: t should be a number, got {type(t)}'
    t = float(t)
    assert t >= 0, f'ValueError, t should be greater than 0, got minus number'

    milliseconds = t * 1000

    if estimation:
        # 大致估算时间，精确到最高时间单位，如天、小时、分钟、秒等
        seconds = round(milliseconds / 1000.0)
        if seconds <= 59:
            time_str = f'~{seconds:.0f}"' if short_form else f'about {seconds:.0f} sec'
            return time_str
        minutes = round(seconds / 60.0)
        if minutes <= 59:
            time_str = f'~{minutes:.0f}\'' if short_form else f'about {minutes:.0f} min'
            return time_str
        hours = round(seconds / 3600.0)
        if hours <= 23:
            time_str = f'~{hours:.0f}H' \
                if short_form \
                else f'about {hours:.0f} hour' \
                if hours == 1 \
                else f'about {hours:.0f} hours'
            return time_str
        days, hours = divmod(hours, 24)
        if short_form:
            return f'~{days:.0f}D' if hours == 0 else f'~{days:.0f}D{hours:.0f}H'
        else:
            return f'about {days:.0f} day' \
                    if hours == 0 \
                    else f'about {days:.0f} day {hours:.0f} hour' \
                    if days == 1 \
                    else f'about {days:.0f} days {hours:.0f} hours'
    else:  # estimation:
        seconds = int(milliseconds / 1000)
        milliseconds = milliseconds - seconds * 1000
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        if short_form:
            time_str = ""
            if days > 0:
                time_str += f"{days:.0f}D"
            if hours > 0:
                time_str += f"{hours:.0f}H"
            if minutes > 0:
                time_str += f"{minutes:.0f}'"
            if seconds > 0:
                time_str += f'{seconds:.0f}"'
            if milliseconds > 0 or not time_str:
                ms_str = f'{milliseconds:03.0f}' if time_str else f'0"{milliseconds:03.0f}'
                time_str += ms_str
            return time_str
        else:
            time_str = ""
            if days > 0:
                days_str = f"{days:.0f} days " if days > 1 else f"{days:.0f} day "
                time_str += days_str
            if hours > 0:
                hour_str = f"{hours:.0f} hours " if hours > 1 else f"{hours:.0f} hour "
                time_str += hour_str
            if minutes > 0:
                time_str += f"{minutes:.0f} min "
            if seconds > 0:
                time_str += f"{seconds:.0f} sec "
            if milliseconds > 0 or not time_str:
                time_str += f"{milliseconds:0.1f} ms"

        return time_str


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
    dict of {label: index}

    Examples
    --------
    例如，列表target_list 中含有三个元素，分别是[100, 130, 170]
    现在输入一个label清单，作为列表中三个元素的标签，分别为：['first', 'second', 'third']
    使用labels_to_dict函数生成一个字典如下：
    find_idx:  {'first' : 0
                'second': 1
                'third' : 2}
    通过这个字典，可以容易且快速地使用标签访问target_list中的元素：
    target_list[find_idx['first']] == target_list[0] == 100

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
    sep_char: str, default: ','
        字符串分隔符， 默认','
    case: str, Optional
        默认None, 是否改变大小写，upper输出全大写, lower输出全小写
    dim: int, Optional
        需要生成的目标list的元素数量
    padder: str, Optional
        当元素数量不足的时候用来补充的元素

    Returns
    -------
    list of str: 字符串分割后的列表

    Examples
    --------
    >>> str_to_list('a, b, c, d')
    ['a', 'b', 'c', 'd']
    >>> str_to_list('a, b, c, d', sep_char=' ')
    ['a,', 'b,', 'c,', 'd']
    >>> str_to_list('a, b, c, d', sep_char=' ', case='upper')
    ['A,', 'B,', 'C,', 'D']
    >>> str_to_list('a, b, c, d', sep_char=' ', case='lower')
    ['a,', 'b,', 'c,', 'd']
    >>> str_to_list('a, b, c, d', sep_char=' ', case='lower', dim=6)
    ['a,', 'b,', 'c,', 'd', None, None]
    >>> str_to_list('a, b, c, d', sep_char=' ', case='lower', dim=6, padder='e')
    ['a,', 'b,', 'c,', 'd', 'e', 'e']
    """
    assert isinstance(input_string, str), f'InputError, input is not a string!, got {type(input_string)}'
    if input_string == "":
        return list()
    input_string = input_string.strip()
    if sep_char != ' ':
        input_string = input_string.replace(' ', '')
    res = input_string.split(sep_char)
    res = [s for s in res if s != '']
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
    pars: str or int or list of int or list of str
        需要转化为list对象的输出对象
    dim: int
        需要生成的目标list的元素数量
    padder: Any
        当元素数量不足的时候用来补充的元素

    Returns
    -------
    items, list 转化好的元素清单

    Examples
    --------
    >>> input_to_list(1, 3)
    [1, 1, 1]
    >>> input_to_list([1, 2], 3)
    [1, 2, None]
    >>> input_to_list([1, 2], 3, padder=3)
    [1, 2, 3]
    >>> input_to_list('a', 3)
    ['a', 'a', 'a']
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
    """ 把YY-MM-DD或YYYY/MM/DD等各种格式的纯日期转化为YYYY-MM-DD格式
        将日期时间字符串转化为YYYY-MM-DD HH:MM:SS格式

    Parameters
    ----------
    date_str: str, date time like
        时间日期字符串

    Returns
    -------
    date_time: str
    格式为'%Y-%m-%d' 或 '%Y-%m-%d %H:%M:%S'

    Examples
    --------
    >>> regulate_date_format('2023/08/01')
    '2023-08-01'
    >>> regulate_date_format('2023-08-01')
    '2023-08-01'
    >>> regulate_date_format('2023-08-01 11:22:33')
    '2023-08-01 11:22:33'
    """
    try:
        date_time = pd.to_datetime(date_str)
    except Exception as e:
        raise ValueError(f'{e}: {date_str} is not a valid date-time')
    from datetime import time
    if date_time.time() == time.min:  # if datetime.time() == datetime.time(0, 0)
        str_format = '%Y-%m-%d'
    else:
        str_format = '%Y-%m-%d %H:%M:%S'
    return date_time.strftime(str_format)


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


def get_current_tz_datetime(self, time_zone='local'):
    """ 获取指定时区的当前时间，同时确保返回的时间是tz_naive的

    如果time_zone为'local', 获取当前时区的当前时间。
    如果指定time_zone的时间与本地时间相同，则直接返回当前时间

    Parameters
    ----------
    time_zone: str, default: 'local'
        符合标准的时区字符串
    """
    if time_zone == 'local':
        return pd.to_datetime('today')
    else:
        # create utc time and convert to time_zone time and remove time_zone information
        dt = pd.to_datetime('now', utc=True).tz_convert(self.time_zone)
        return pd.to_datetime(dt.tz_localize(None))


@lru_cache(maxsize=16)
def maybe_trade_day(date):
    """ 判断一个日期是否交易日（或然判断，只剔除明显不是交易日的日期）准确率有限但是效率高

    Parameters
    ----------
    date: datetime-like
        可以转化为时间日期格式的字符串或其他类型对象

    Raises
    ------
    ValueError, 当字符串无法被转化为datetime时

    Returns
    -------
    bool, True表示可能是交易日，False表示不是交易日

    Examples
    --------
    >>> maybe_trade_day('2019-01-01')
    False
    >>> maybe_trade_day('2019-01-02')
    False
    >>> maybe_trade_day('2023-04-11')
    True
    """
    # public_holidays 是一个含两个list的tuple，存储了闭市的公共假期，第一个list是代表月份的数字，第二个list是代表日期的数字
    public_holidays = ([1, 1, 1, 4, 4, 4, 5, 5, 5, 10, 10, 10, 10, 10, 10, 10],
                       [1, 2, 3, 3, 4, 5, 1, 2, 3, 1, 2, 3, 4, 5, 6, 7])
    try:
        date = pd.to_datetime(date).floor(freq='d')
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

    Parameters
    ----------
    date: datetime-like
        可以转化为时间日期格式的字符串或其他类型对象

    Returns
    -------
    prev: pd.Timestamp
        前一个或然交易日的时间戳

    Examples
    --------
    >>> prev_trade_day('2019-01-01')
    Timestamp('2018-12-28 00:00:00')
    """
    if maybe_trade_day(date):
        return date

    d = pd.to_datetime(date).floor(freq='d')
    prev = d - pd.Timedelta(1, 'd')
    while not maybe_trade_day(prev):
        prev = prev - pd.Timedelta(1, 'd')
    return prev


def next_trade_day(date):
    """ 返回一个日期的下一个或然交易日

    Parameters
    ----------
    date: datetime-like
        可以转化为时间日期格式的字符串或其他类型对象

    Returns
    -------
    next: pd.Timestamp
        下一个或然交易日的时间戳

    Examples
    --------
    >>> next_trade_day('2019-01-01')
    Timestamp('2019-01-04 00:00:00')
    """
    if maybe_trade_day(date):
        return date

    d = pd.to_datetime(date).floor(freq='d')
    next = d + pd.Timedelta(1, 'd')
    while not maybe_trade_day(next):
        next = next + pd.Timedelta(1, 'd')
    return next


@lru_cache(maxsize=16)
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

    Returns
    -------
    bool: True表示是交易日，False表示不是交易日

    Examples
    --------
    >>> is_market_trade_day('2019-01-01')
    False
    """
    try:
        _date = pd.to_datetime(date).floor(freq='d')
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
        warnings.warn('Trade Calendar is not available, will use maybe_trade_day instead to check trade day')
        return maybe_trade_day(_date)


@lru_cache(maxsize=4)
def last_known_market_trade_day(exchange: str = 'SSE'):
    """ 返回交易日列表中的最后一个已知交易日

    Parameters
    ----------
    exchange: str
        交易所代码:
            SSE:    上交所, SZSE:   深交所,
            CFFEX:  中金所, SHFE:   上期所,
            CZCE:   郑商所, DCE:    大商所,
            INE:    上能源, IB:     银行间,
            XHKG:   港交所

    Returns
    -------
    datetime-like
        最后一个已知交易日的日期
    """
    if not isinstance(exchange, str) and exchange in ['SSE', 'SZSE', 'CFFEX', 'SHFE', 'CZCE',
                                                      'DCE', 'INE', 'IB', 'XHKG']:
        raise TypeError(f'exchange \'{exchange}\' is not a valid input')
    if qteasy.QT_TRADE_CALENDAR is not None:
        try:
            exchange_trade_cal = qteasy.QT_TRADE_CALENDAR.loc[exchange]
        except KeyError as e:
            raise KeyError(f'Trade Calender for exchange: {e} was not properly downloaded, please refill data')
        return exchange_trade_cal[exchange_trade_cal.is_open == 1].index.max()
    else:
        raise RuntimeError('Trade Calendar is not available, please download basic data into DataSource, Use:\n'
                           'qteasy.refill_data_source(tables="basics")\n'
                           'see more details in qteasy docs')


@lru_cache(maxsize=16)
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

    Examples
    --------
    >>> prev_market_trade_day('2019-01-01')
    Timestamp('2018-12-28 00:00:00')
    >>> prev_market_trade_day('2020-12-24')
    Timestamp('2020-12-23 00:00:00')

    See Also
    --------
    is_market_trade_day()
    """
    try:
        _date = pd.to_datetime(date).floor(freq='d')
    except Exception as e:
        e.extra_info = f'{date} is not a valid date time format, cannot be converted to timestamp'
        raise e
    if qteasy.QT_TRADE_CALENDAR is not None:
        exchange_trade_cal = qteasy.QT_TRADE_CALENDAR.loc[exchange]
        pretrade_date = exchange_trade_cal.loc[_date].pretrade_date
        return pd.to_datetime(pretrade_date)
    else:
        raise RuntimeError('Trade Calendar is not available, please download basic data into DataSource, Use:\n'
                           'qteasy.refill_data_source(tables="basics")\n'
                           'see more details in qteasy docs')


@lru_cache(maxsize=16)
def nearest_market_trade_day(date, exchange='SSE'):
    """ 根据交易所发布的交易日历找到某一日的最近交易日，需要提前准备QT_TRADE_CALENDAR数据

    - 如果date是交易日，返回date当日，如2020-12-24日是交易日，返回2020-12-24
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

    Examples:
    ---------
    >>> nearest_market_trade_day('2019-01-01')
    Timestamp('2018-12-28 00:00:00')
    >>> nearest_market_trade_day('2020-12-24')
    Timestamp('2020-12-24 00:00:00')

    See Also
    --------
    is_market_trade_day()
    """
    try:
        _date = pd.to_datetime(date).floor(freq='d')
    except Exception as e:
        e.extra_info = f'{date} is not a valid date time format, cannot be converted to timestamp'
        raise e
    last_known_trade_day = last_known_market_trade_day(exchange)
    if _date < pd.to_datetime('19910101') or _date > last_known_trade_day:
        return None
    if is_market_trade_day(_date, exchange):
        return _date
    else:
        prev = _date - pd.Timedelta(1, 'd')
        while not is_market_trade_day(prev):
            prev = prev - pd.Timedelta(1, 'd')
        return prev


@lru_cache(maxsize=16)
def next_market_trade_day(date, exchange='SSE', nearest_only=True):
    """ 根据交易所发布的交易日历找到它的后一个交易日，准确性高但需要提前准备QT_TRADE_CALENDAR数据

    - 如果date是一个交易日，则返回date当日(若nearst_only=True)或者返回date的下一个交易日(若nearest_only=False)
    - 如果date不是一个交易日，则返回date的下一个交易日，如2020-12-25不是交易日，但它的下一个交易日是2020-12-28，因此返回2020-12-28

    Parameters
    ----------
    date: str datetime like
        可以转化为时间日期格式的字符串或其他类型对象
    exchange: str
        交易所代码
    nearest_only: bool, default: True
        是否只返回最近的交易日，如果为True，则返回最近的交易日，如果为False，则返回下一个交易日

    Returns
    -------
    pd.TimeStamp

    Raises
    ------
    NotImplementedError: 要求在本地DataSource中必须存在'trade_calendar'表，否则报错

    Examples
    --------
    >>> next_market_trade_day('2019-01-01')
    Timestamp('2019-01-02 00:00:00')
    >>> next_market_trade_day('2020-12-24')
    Timestamp('2020-12-24 00:00:00')
    >>> next_market_trade_day('2020-12-24', nearest_only=False)
    Timestamp('2020-12-25 00:00:00')

    See Also
    --------
    is_market_trade_day()
    """
    try:
        _date = pd.to_datetime(date).floor(freq='d')
    except Exception as e:
        e.extra_info = f'{date} is not a valid date time format, cannot be converted to timestamp'
        raise e
    last_known_trade_day = last_known_market_trade_day(exchange)
    if _date < pd.to_datetime('19910101') or _date > last_known_trade_day:
        return None
    if is_market_trade_day(_date, exchange) and nearest_only:
        return _date
    else:
        next_date = _date + pd.Timedelta(1, 'd')
        while not is_market_trade_day(next_date):
            next_date = next_date + pd.Timedelta(1, 'd')
        return next_date


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
    # a different implementation:
    # return [lst[i:i+trunc_size] for i in range(0, len(lst), trunc_size)]
    # or a more pythonic way:
    # return list(map(lambda i: lst[i:i+trunc_size], range(0, len(lst), trunc_size)))
    # or return a generator:
    # return (lst[i:i+trunc_size] for i in range(0, len(lst), trunc_size))
    # or create a generator with yield from:
    # yield from (lst[i:i+trunc_size] for i in range(0, len(lst), trunc_size))


def is_number_like(key: [str, int, float]) -> bool:
    """ 判断一个字符串是否是一个合法的数字

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


def is_integer_like(key: [str, int]) -> bool:
    """ 判断一个字符串是否是一个合法的整数

    Parameters
    ----------
    key: [str, int], 需要检查的输入

    Returns
    -------
    bool
    """
    if isinstance(key, int):
        return True
    if not isinstance(key, str):
        return False
    if INTEGER_IDENTIFIER.match(key):
        return True
    return False


def is_float_like(key: [str, int, float]) -> bool:
    """ 判断一个字符串是否是一个合法的浮点数

    Parameters
    ----------
    key: [str, int, float], 需要检查的输入

    Returns
    -------
    bool

    Examples
    --------
    >>> is_number_like('123')
    >>> True
    >>> is_number_like('123.456')
    >>> True
    >>> is_number_like('123.456.789')
    >>> False
    """
    if isinstance(key, (float, int)):
        return True
    if not isinstance(key, str):
        return False
    if FLOAT_IDENTIFIER.match(key):
        return True
    return False


def is_cn_stock_symbol_like(key: str) -> bool:
    """ 判断一个字符串是否是一个合法的A股股票代码，不含市场标识符

    Parameters
    ----------
    key: str, 需要检查的输入

    Returns
    -------
    bool
    """
    # TODO: test this function
    if not isinstance(key, str):
        return False
    if CN_STOCK_SYMBOL_IDENTIFIER.match(key):
        return True
    return False


def is_complete_cn_stock_symbol_like(key: str) -> bool:
    """ 判断一个字符串是否是一个合法的A股股票代码, 必须包含市场标识符如SH或SZ

    Parameters
    ----------
    key: str, 需要检查的输入

    Returns
    -------
    bool
    """
    # TODO: test this function
    if not isinstance(key, str):
        return False
    if TS_CODE_IDENTIFIER_CN_STOCK.match(key):
        return True
    return False


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

    Parameters
    ----------
    file_size: int
        表示文件大小的数字，单位为字节

    Returns
    -------
    str, 代表文件大小的字符串

    Examples
    --------
    >>> human_file_size(1024)
    '1KB'
    >>> human_file_size(1024 * 1024)
    '1.0MB'
    >>> human_file_size(1024 * 1024 * 1024)
    '1.00GB'
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

    Examples
    --------
    >>> human_units(1000)
    '1K'
    >>> human_units(1000, short_form=False)
    '1 thousand'
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

    Examples
    --------
    >>> _lev_ratio('abc', 'abc')
    1.0
    >>> _lev_ratio('abc', 'ab')
    0.6666666666666666
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

    Examples
    --------
    >>> _partial_lev_ratio('abc', 'abc')
    1.0
    >>> _partial_lev_ratio('abc', 'ab')
    1.0
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

    用"?"匹配任意单个字符，用"*"匹配任意多个字符

    Parameters
    ----------
    mode: str
        带通配符wildcard的字符串
    wordlist: iterable
        一个列表、元组、生成器或任何可循环的对象，包含一系列需要匹配的字符串

    Returns
    -------
    list: 匹配成功的字符串

    Examples
    --------
    >>> _wildcard_match('a*b', ['abc', 'aabb', 'ab', 'a'])
    ['abc', 'aabb', 'ab']
    >>> _wildcard_match('a?c', ('abc', 'aabb', 'ab', 'a'))
    ['abc']
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

    Examples
    --------
    >>> arr = np.array([[[1, 2, 3], [np.nan, np.nan, np.nan], [4, 5, 6]],
    ...                 [[1, 3, 5], [np.nan, np.nan, np.nan], [4, 5, 6]]])
    >>> ffill_3d_data(arr)
    array([[[1., 2., 3.],
            [1., 2., 3.],
            [4., 5., 6.]],

           [[1., 3., 5.],
            [1., 3., 5.],
            [4., 5., 6.]]])

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

    Examples
    --------
    >>> arr = np.array([[1, 2, 3], [np.nan, np.nan, np.nan], [4, 5, 6]])
    >>> ffill_2d_data(arr)
    array([[1., 2., 3.],
           [1., 2., 3.],
           [4., 5., 6.]])
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

    Examples
    --------
    >>> arr = np.array([[1, 2, 3], [np.nan, np.nan, np.nan], [4, 5, 6]])
    >>> fill_nan_data(arr)
    array([[1., 2., 3.],
           [0., 0., 0.],
           [4., 5., 6.]])
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
    if not isinstance(window, int):
        raise TypeError(f'window should be an integer, got {type(window)} instead.')
    if not isinstance(axis, int):
        raise TypeError(f'axis should be an integer, got {type(axis)} instead.')
    if window <= 0:
        raise ValueError(f'Invalid window({window}), can not be smaller than 0')
    if (axis < 0) or (axis >= arr.ndim):
        raise ValueError(f'Invalid axis({axis})')

    shape = list(arr.shape)
    strides = arr.strides
    axis_length = shape[axis]
    if window > axis_length:
        raise ValueError(f'window too long ({window}), should be <= axis_length ({axis_length}), array shape ({shape})')
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

    Examples
    --------
    >>> s = 'hello\\nworld'
    >>> reindent(s)
    '    hello\\n    world'
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


def truncate_string(s, n, padder='.'):  # to be deprecated
    """ to be deprecated, 调整字符串为指定长度，为了保证兼容性，暂时保留此函数
    以后使用adjust_string_length代替

    Parameters
    ----------
    s: str
        字符串
    n: int
        需要保留的长度
    padder: str, Default: '...'
        填充在截短的字符串后用于表示省略号的字符，默认为'.'

    Returns
    -------
    str

    Examples
    --------
    >>> truncate_string('hello world', 5)
    'he...'
    >>> truncate_string('hello world', 5, padder='*')
    'he***'
    >>> truncate_string('hello world', 3)
    'h..'
    """
    warnings.warn('truncate_string will be deprecated, use adjust_string_length instead', DeprecationWarning)
    return adjust_string_length(s, n, ellipsis=padder)


def adjust_string_length(s, n, ellipsis='.', padder=' ', hans_aware=False, padding='right', format_tags=False):
    """ 调整字符串为指定长度，如果字符串过长则将其截短，并在末尾添加省略号提示，
        如果字符串过短则在末尾添加空格补齐长度

    默认情况下，认为汉字的长度为2，英文字符的长度为1，可以通过hans_aware参数设置是否考虑汉字的长度
    如果字符串中含有格式标签，如[bold]或[red]，则需要将format_tags参数设置为True，此时会先将格式标签去除，
    然后调整字符串长度，调整完成后再将格式标签添加回去

    Parameters
    ----------
    s: str
        字符串
    n: int
        需要保留的长度
    ellipsis: str, Default: '.'
        填充在截短的字符串后用于表示省略号的字符，默认为'.'
    padder: str, Default: ' '
        填充在字符串末尾补充长度的字符，默认为空格
    hans_aware: bool, Default: False
        是否考虑汉字的长度，如果为True，则汉字的长度为2，否则为1
    padding: str, Default: 'right'
        填充的位置，可以为'left'或'right'，默认为'right'
    format_tags: bool, Default: False
        是否考虑字符串中的格式标签，如果为True，则首先去除字符串中的格式标签后再调整长度，调整完成后再将格式标签添加回去

    Returns
    -------
    str

    Examples
    --------
    >>> adjust_string_length('hello world', 8)
    'hell...d'
    >>> adjust_string_length('hello world', 15, padder='*')
    'hello world****'
    >>> adjust_string_length('hello world', 9, ellipsis='_')
    'hell___ld'
    >>> adjust_string_length('中文字符占据2个位置', 9, hans_aware=False)
    '中文字符...位置'
    >>> adjust_string_length('中文字符占据2个位置', 9, hans_aware=True)
    '中文...置'
    >>> adjust_string_length('hello [bold red]world[/bold red]', 9, format_tags=True)
    'hell[bold red]...ld[/bold red]'
    """

    if format_tags:
        format_tags, format_tags_positions, s = _extract_format_tags(s)
    else:
        format_tags = []
        format_tags_positions = []

    cut_off_proportion = 0.7

    if not isinstance(s, str):
        raise TypeError(f'the first argument should be a string, got {type(s)} instead')
    if not isinstance(n, int):
        raise TypeError(f'the second argument should be an integer, got {type(n)} instead')
    if not isinstance(ellipsis, str):
        raise TypeError(f'the padder should be a character, got {type(ellipsis)} instead')
    if not len(ellipsis) == 1:
        raise ValueError(f'the padder should be a single character, got {len(ellipsis)} characters')
    if not isinstance(padder, str):
        raise TypeError(f'the padder should be a character, got {type(padder)} instead')
    if n < 1:
        raise ValueError(f'the expected length should be larger than 0, got {n}')

    length = len(s)
    if hans_aware:
        length += _count_hans(s)

    if (length <= n) and (padding == 'right'):
        res_str = s + padder * (n - length)
        if format_tags:
            res_str = _put_back_format_tags(res_str, format_tags, format_tags_positions)
        return res_str

    if (length <= n) and (padding == 'left'):
        res_str = padder * (n - length) + s
        if format_tags:
            res_str = _put_back_format_tags(res_str, format_tags, format_tags_positions)
        return res_str

    if n == 3:
        elipsis_count = 2
        front_length = 1
    elif n < 3:
        elipsis_count = n
        front_length = 0
    else:
        elipsis_count = 3
        front_length = round((n - elipsis_count) * cut_off_proportion)

    # count from beginning of the string
    front_part = []
    front_print_width = 0
    if front_length > 0:
        for char in s:  # build up front part of the string
            if hans_aware and ('\u4e00' <= char <= '\u9fff'):
                front_print_width += 2
            else:
                front_print_width += 1
            front_part.append(char)
            if front_print_width - front_length == 2:
                front_part.pop()  # 如果刚好多增加了一个中文字符，则需要将最后一个字符去掉
                front_print_width -=2
                break
            if front_print_width - front_length >= 0:
                break

    # count from back of the string
    remainder_part = []
    remainder_print_width = 0
    remainder_length = n - front_length - elipsis_count
    if (n >= 5) and (remainder_length == 0):
        remainder_length = 1  # there must be a character in the remainder part if n >= 5
    if remainder_length > 0:
        for char in s[::-1]:  # build up ellipsis part of the string
            if hans_aware and ('\u4e00' <= char <= '\u9fff'):
                remainder_print_width += 2
            else:
                remainder_print_width += 1

            remainder_part.append(char)
            if remainder_print_width >= remainder_length:
                break

    if (front_print_width + remainder_print_width + elipsis_count > n) and (n >= 3):
        # 此时前面的字符数和后面的字符数加上省略号的字符数比n多，需要将省略号的字符数减少
        elipsis_count -= front_print_width + remainder_print_width + elipsis_count - n

    combined_string = ''.join(front_part) + ellipsis * elipsis_count + ''.join(remainder_part[::-1])
    if format_tags:
        cut_off_position = len(front_part) + elipsis_count
        removed_count = len(s) - len(combined_string)
        adjusted_format_tags_positions = []
        # adjust the format tags positions because the string is now shorter
        for item in format_tags_positions:
            item = item if item < cut_off_position else max(cut_off_position, item - removed_count)
            adjusted_format_tags_positions.append(item)
        # put all format tags back on the positions as the format_tags_positions
        combined_string = _put_back_format_tags(
                combined_string,
                format_tags,
                adjusted_format_tags_positions,
        )

        return combined_string

    else:
        return combined_string


def _extract_format_tags(s):
    """ 从字符串中提取格式标签，生成一个标签列表，并生成标签的位置列表，同时返回不含标签的字符串

    注意生成的标签位置列表是每一个标签在不含标签的字符串中的位置列表，而不是在原字符串中的位置列表

    Parameters
    ----------
    s: str
        字符串

    Returns
    -------
    list: 格式标签列表
    list: 标签位置列表
    str: 不含标签的字符串

    Examples
    --------
    >>> _extract_format_tags('hello [bold]world[/bold]')
    ['[bold]', '[/bold]']], [6, 11], 'hello world'
    >>> _extract_format_tags('hello [bold]world[/bold] [red]!')
    ['[bold]', '[/bold]', '[red]'], [6, 11, 12], 'hello world !'
    """
    import re
    pattern = re.compile(r'\[.*?\]')
    tags = pattern.findall(s)
    tag_positions = []
    prev_end = 0
    prev_pos = 0
    for match in pattern.finditer(s):
        prev_pos += match.start() - prev_end
        tag_positions.append(prev_pos)
        prev_end = match.end()
    s = re.sub(r'\[.*?\]', '', s)
    return tags, tag_positions, s


def _put_back_format_tags(s, tags, tag_positions):
    """ 将格式标签放回字符串中, 标签的位置由tag_positions指定

    Parameters
    ----------
    s: str
        字符串
    tags: list of str
        格式标签列表
    tag_positions: list of int
        标签位置列表

    Returns
    -------
    str: 含有格式标签的字符串
    """
    res_str = ''
    for pos, char in enumerate(s):
        while pos in tag_positions:
            res_str += tags.pop(0)
            tag_positions.pop(0)
        res_str += char
    while tag_positions:
        res_str += tags.pop(0)
        tag_positions.pop(0)

    return res_str


def _count_hans(s: str):
    """ 统计字符串中汉字的数量 (unicode 4E00-9FFF)

    Parameters
    ----------
    s: str
        字符串

    Returns
    -------
    int, 汉字的数量

    Examples
    --------
    >>> _count_hans('hello world')
    0
    >>> _count_hans('你好，世界')
    4
    """
    # for loop is faster than list comprehension and regex
    if not isinstance(s, str):
        raise TypeError(f'the argument should be a string, got {type(s)} instead')
    hans_total = 0
    for char in s:
        if '\u4e00' <= char <= '\u9fff':
            hans_total += 1
    return hans_total

