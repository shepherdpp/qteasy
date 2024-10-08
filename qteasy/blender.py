# coding=utf-8
# ======================================
# File:     blender.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2021-08-29
# Desc:
#   Strategy blending functions and
#   blender string parsers.
# ======================================

import numpy as np
from numba import njit

from qteasy.utilfuncs import (
    is_number_like,
    BLENDER_STRATEGY_INDEX_IDENTIFIER,
)


# 这里定义可用的交易信号混合函数
@njit()  # 实测njit版本运行速度是python版本的2倍左右
def op_sum(*args):
    """ 在combo模式下，所有的信号被加总合并，这样每个所有的信号都会被保留,虽然并不是所有的信号都有效。

    在这种模式下，本意是原样保存所有单个输入
    多空模板产生的交易信号，但是由于正常多空模板在生成卖出信号的时候，会
    运用"比例机制"生成卖出证券占持有份额的比例。这种比例机制会在针对
    combo模式的信号组合进行计算的过程中产生问题。
    例如：在将两组信号A和B合并到一起之后，如果A在某一天产生了一个股票
    100%卖出的信号，紧接着B在接下来的一天又产生了一次股票100%卖出的信号，
    两个信号叠加的结果，就是产生超出持有股票总数的卖出数量。将导致信号问题
    因此combo后的数据需要用clip处理

    Parameters
    ----------
    args:

    Returns
    -------
    ndarray
    """
    # 计算所有交易信号之和
    signal_sum = np.zeros_like(args[0])
    for signal in args:
        signal_sum += signal
    return signal_sum


# 这个函数本身速度比较快，而且njit版本的运行速度没有任何提升
def op_avg(*args):
    """ 通常用于PT持仓目标信号。

    组合后的持仓取决于看多的蒙板的数量，看多蒙板越多，持仓越高，
    只有所有蒙板均看空时，最终结果才看空所有蒙板的权重相同，因此，如
    果一共五个蒙板三个看多两个看空时，持仓为60%。更简单的解释是，混
    合后的多空仓位是所有蒙版仓位的平均值.

    args: 以tuple形式传入的所有交易信号

    Returns
    -------
    ndarray
    """
    # 计算所有交易信号之和
    signal_sum = op_sum(*args)
    # 交易信号的个数
    signal_count = len(args)
    return signal_sum / signal_count


# 这个函数本身速度不快，但njit版本更慢，njit()后运行时间增加40%
def op_pos(n, t, *args):
    """ 择时策略混合器，将各个择时策略生成的多空蒙板按规则混合成一个蒙板

    最终的多空信号强度取决于蒙板集合中各个蒙板的信号值，只有满足N个以
    上的蒙板信号值为多(>0)或者为空(<0)时，最终蒙板的多空信号才为多或
    为空。某组信号看多/看空的判断依据是信号强度绝对值是否大于t。例如，
    当T为0.25的时候，0.35会被接受为多头，但是0.15不会被接受为多头，因
    此尽管有两个策略在这个时间点判断为多头，但是实际上只有一个策略会被
    接受.
    最终信号的强度始终为-1或1，如果希望最终信号强度为输入信号的
    平均值，应该使用avg_pos-N方式混合

    Parameters
    ---------
    n: int
    t: float
    args: ndarray

    Returns
    -------
    ndarray
    """
    signal_sign = np.zeros_like(args[0])
    for msk in args:
        signal_sign += np.sign(np.where(np.abs(msk) < t, 0, msk))
    res = np.where(np.abs(signal_sign) >= n, 1., 0)
    return res


# 这个函数本身速度不快，但njit版本更慢，njit()后运行时间增加33%
def op_avg_pos(n, t, *args):
    """择时策略混合器，将各个择时策略生成的多空蒙板按规则混合成一个蒙板

    持仓目标取决于看多的蒙板的数量，只有满足N个或更多蒙板看多时，最终结果
    看多，否则看空，在看多/空情况下，最终的多空信号强度=平均多空信号强度
    。某组信号看多/看空的判断依据是信号强度绝对值是否大于t。例如，
    当T为0.25的时候，0.35会被接受为多头，但是0.15不会被接受为多头，因
    此尽管有两个策略在这个时间点判断为多头，但是实际上只有一个策略会被
    接受.
    当然，avg_pos-1与avg等价，如avg_pos-2方式下，至少两个蒙板看多
    则最终看多，否则看空

    Parameters
    ---------
    n: int
    t: float
    args: ndarray

    Returns
    -------
    ndarray
    """
    # 计算所有交易信号之和
    signal_sum = op_sum(*args)
    # 交易信号的个数
    signal_count = len(args)
    signal_sign = np.zeros_like(args[0])
    for msk in args:
        signal_sign += np.sign(np.where(np.abs(msk) < t, 0, msk))
    res = np.where(np.abs(signal_sign) >= n, signal_sum, 0) / signal_count
    return res


# 这个简单函数本身速度已经很快，不需要@njit()，njit()后运行时间增加25%
def op_str(t, *args):
    """ str-T模式下，持仓只能为0或+1，只有当所有多空模版的输出的总和大于
        某一个阈值T的时候，最终结果才会是多头，否则就是空头

    Parameters
    ----------
    t: float
    args: ndarray

    Returns
    -------
    ndarray
    """
    # 计算所有交易信号之和
    signal_sum = op_sum(*args)
    return np.where(np.abs(signal_sum) >= t, 1, 0) * np.sign(signal_sum)


# 这个简单函数本身速度已经很快，不需要@njit()，njit()后运行时间增加4倍
def op_clip(lbound, ubound, *args):
    """ 剪切掉信号中小于lbound，或大于ubound的值，替换为lbound或ubound

    Parameters
    ----------
    lbound: float
    ubound: float
    args: ndarray

    Returns
    -------
    ndarray

    Examples
    --------
    >>> op_clip(-0.5, 0.5, np.array([-0.6, -0.4, 0.4, 0.6]))
    array([-0.5, -0.4,  0.4,  0.5])
    """
    # 交易信号的个数
    signal_count = len(args)
    if signal_count > 1:
        raise ValueError(f'only one array of signals can be passed to blend function "clip", please check '
                         f'your input')
    signal_res = args[0]
    signal_res = np.where(signal_res < lbound, lbound, signal_res)
    signal_res = np.where(signal_res > ubound, ubound, signal_res)
    return signal_res


# 这个简单函数本身速度已经很快，不需要@njit()，njit()后运行时间增加90%
def op_unify(*args):
    """ 调整输入矩阵每一行的元素，通过等比例缩小（或放大）后使得所有元素的和为1
    用于调整

    Parameters
    ----------
    args: ndarray
    输入信号，只能输入一组信号作为输入

    Returns
    -------
    ndarray

    examples
    --------
    >>> op_unify([[3.0, 2.0, 5.0], [2.0, 3.0, 5.0]])
    [[0.3, 0.2, 0.5], [0.2, 0.3, 0.5]]
    """
    # 交易信号的个数
    signal_count = len(args)
    if signal_count > 1:
        raise ValueError(f'only one array of signals can be passed to blend function "unify", please check '
                         f'your input')
    signal_arr = args[0]
    if signal_arr.ndim == 1:
        # 如果输入的是一维数组，按一维数组处理
        s = signal_arr.sum()
        signal_res = signal_arr / s
    else:
        s = signal_arr.sum(1)
        shape = (s.shape[0], 1)
        signal_res = signal_arr / s.reshape(shape)
    # 如果原信号中有全0的情况，会导致NaN出现，下面将所有NaN填充为0
    signal_res = np.where(np.isnan(signal_res), 0., signal_res)
    return signal_res


# 这个简单函数本身速度已经很快，不需要@njit()，njit()后运行时间增加80%
def op_max(*args):
    """ 信号混合器，将各个择时策略生成的信号取最大值后生成新的交易信号

    生成的交易信号为所有交易信号中的最大值

    Parameters
    ----------
    args: ndarray
    交易信号，可以输入多组交易信号

    Returns
    -------
    ndarray

    Examples
    --------
    >>> op_max(np.array([0.1, 0.2, 0.5]), np.array([0.2, 0.3, 0.4]))
    array([0.2, 0.3, 0.5])
    """
    # 交易信号的个数
    signal_count = len(args)
    if signal_count < 1:
        return
    elif signal_count == 1:
        return args[0]
    elif signal_count == 2:
        return np.fmax(args[0], args[1])
    else:  # signal_count > 2
        signal_max = np.fmax(args[0], args[1])
        for signal in args[2:]:
            signal_max = np.fmax(signal_max, signal)
        return signal_max


# 这个简单函数本身速度已经很快，不需要@njit()，njit()后运行时间增加50%
def op_min(*args):
    """ 信号混合器，将各个择时策略生成的信号取最小值后生成新的交易信号

    生成的交易信号为所有交易信号中的最小值

    Parameters
    ----------
    args: ndarray

    Returns
    -------
    ndarray

    Examples
    --------
    >>> op_min(np.array([0.1, 0.2, 0.5]), np.array([0.2, 0.3, 0.4]))
    array([0.1, 0.2, 0.4])
    """
    # 交易信号的个数
    signal_count = len(args)
    if signal_count < 1:
        raise KeyError('at least one signal array should be passed to min()')
    elif signal_count == 1:
        return args[0]
    elif signal_count == 2:
        return np.fmin(args[0], args[1])
    else:  # signal_count > 2
        signal_min = np.fmin(args[0], args[1])
        for signal in args[2:]:
            signal_min = np.fmin(signal_min, signal)
        return signal_min


# 这个函数本身速度不够快，但是njit版本的运行速度没有任何提升
def op_power(*args):
    """ ，逐个元素操作生成first的second次幂，功能等同于np.power

    np.power()函数可以接受第三个ndarray作为结果，这种操作方式
    是这里不需要的，因此创建op_power函数实现np.power的功能，但
    同时避免超过两个参数出现时导致的问题

    另外，在生成blender表达式的逆波兰式的时候，power函数的两个
    参数次序会颠倒，因此这里实际需要生成的是second的first次幂

    Parameters
    ----------
    args: ndarrays
    交易信号，接受只接受两组交易信号作为输入

    Returns
    -------
    ndarray

    Examples
    --------
    >>> op_power(np.array([1., 2., 3.]), np.array([2., 2., 2.]))
    array([1., 4., 9.])
    """
    # 交易信号的个数
    signal_count = len(args)
    if signal_count != 2:
        raise ValueError('only two signal arrays are allowed in power()/pow()')
        # return  # 本函数允许且仅允许两个参数传入

    # blender表达式的逆波兰式导致两个参数次序颠倒，这里再颠倒回来
    signal_res = np.power(args[1], args[0])
    return signal_res


@njit()  # 这个函数本身速度不够快，njit版本的运行速度稍快，实测大约快5%
def op_exp(*args):
    """ 逐个元素操作生成e的signal次幂，效果与np.exp()一致

    np.exp()函数可以接受一个ndarray作为结果，这种操作方式
    是这里不需要的，因此创建op_exp函数避免第二个参数被传入

    Parameters
    ----------
    args: args中有且只能有一个参数

    Returns
    -------
    ndarray

    Examples
    --------
    >>> op_exp(np.array([1., 2., 3.]))
    array([ 2.71828183,  7.3890561 , 20.08553692])
    """
    # 交易信号的个数
    signal_count = len(args)
    if signal_count != 1:
        raise ValueError('only one signal array is allowed in exp()')
        # return  # 本函数允许且仅允许一个参数传入

    signal_res = np.exp(args[0])
    return signal_res


# 这个函数本身速度不够快，但是njit版本的运行速度更慢，实测大约慢5%
def op_log(*args):
    """ ，逐个元素操作生成signal的自然对数，效果与np.log()一致

    np.log()函数可以接受一个ndarray作为结果，这种操作方式
    是这里不需要的，因此创建op_log函数避免第二个参数被传入

    Parameters
    ----------
    args: args中有且只能有一个参数

    Returns
    -------
    ndarray
    """
    # 交易信号的个数
    signal_count = len(args)
    if signal_count != 1:
        raise ValueError('only one signal array is allowed in log()')
        # return  # 本函数允许且仅允许一个参数传入

    signal_res = np.log(args[0])
    return signal_res


# 这个函数本身速度不够快，但是njit版本的运行速度更慢，实测大约慢20%
def op_log10(*args):
    """ ，逐个元素操作生成signal的以10为底的对数，效果与np.log10()一致

    np.log10()函数可以接受一个ndarray作为结果，这种操作方式
    是这里不需要的，因此创建op_log10函数避免第二个参数被传入

    Parameters
    ----------
    args: args中有且只能有一个参数

    Returns
    -------
    ndarray
    """
    # 交易信号的个数
    signal_count = len(args)
    if signal_count != 1:
        raise ValueError('only one signal array is allowed in log10()')
        # return  # 本函数允许且仅允许一个参数传入

    signal_res = np.log10(args[0])
    return signal_res


@njit()  # 实测njit版本运行速度是python版本的10倍以上
def op_floor(*args):
    """ 逐个元素操作生成signal的floor，效果与np.floor()一致

    np.floor()函数可以接受一个ndarray作为结果，这种操作方式
    是这里不需要的，因此创建op_floor函数避免第二个参数被传入

    Parameters
    ----------
    args: args中有且只能有一个参数

    Returns
    -------
    ndarray
    """
    # 交易信号的个数
    signal_count = len(args)
    if signal_count != 1:
        raise ValueError('only one signal array is allowed in floor()')
        # return  # 本函数允许且仅允许一个参数传入

    signal_res = np.floor(args[0])
    return signal_res


@njit()  # 实测njit版本运行速度是python版本的10倍以上
def op_ceil(*args):
    """ 逐个元素操作生成signal的ceil，效果与np.cail()一致

    np.ceil()函数可以接受一个ndarray作为结果，这种操作方式
    是这里不需要的，因此创建op_ceil函数避免第二个参数被传入

    Parameters
    ----------
    args: args中有且只能有一个参数

    Returns
    -------
    ndarray
    """
    # 交易信号的个数
    signal_count = len(args)
    if signal_count != 1:
        raise ValueError('only one signal array is allowed in ceil()')
        # return  # 本函数允许且仅允许一个参数传入

    signal_res = np.ceil(args[0])
    return signal_res


# 这个简单函数本身速度已经很快，不需要@njit()，njit()后运行时间增倍（因为overhead）
def op_sqrt(*args):
    """ ，逐个元素操作生成signal的平方根，效果与np.sqrt()一致

    np.sqrt()函数可以接受一个ndarray作为结果，这种操作方式
    是这里不需要的，因此创建op_sqrt函数避免第二个参数被传入

    Parameters
    ----------
    args: args中有且只能有一个参数

    Returns
    -------
    ndarray
    """
    # 交易信号的个数
    signal_count = len(args)
    if signal_count != 1:
        raise ValueError('only one signal array is allowed in sqrt()')
        # return  # 本函数允许且仅允许一个参数传入

    signal_res = np.sqrt(args[0])
    return signal_res


# TODO: 增加下列函数支持：
#  product()
_AVAILABLE_FUNCTIONS = {'abs':      abs,
                        'avg':      op_avg,
                        'avgpos':   op_avg_pos,
                        'ceil':     op_ceil,
                        'clip':     op_clip,
                        'combo':    op_sum,
                        'exp':      op_exp,
                        'floor':    op_floor,
                        'log':      op_log,
                        'log10':    op_log10,
                        'max':      op_max,
                        'min':      op_min,
                        'pos':      op_pos,
                        'position': op_pos,
                        'pow':      op_power,
                        'power':    op_power,
                        'sqrt':     op_sqrt,
                        'strength': op_str,
                        'str':      op_str,
                        'sum':      op_sum,
                        'unify':    op_unify,
                        'uni':      op_unify
                        }


def run_blend_func(func_str, *args):
    """ 根据func_str（一个代表混合函数的字符串解析出正确的函，并返回正确结果

    Parameters
    ----------
    func_str: str
        交易信号混合函数名，额外的交易参数直接包含在函数名中
        含有此类附加参数的函数必须特殊解析后才能使用，即将函数名中的特殊参数
        分离出来后作为参数传入函数。
    args:
        作为函数func的参数传入的交易信号

    Returns
    -------
    res,函数的运行结果

    Raises
    ------
    TypeError: func_str不是字符串
    KeyError: func_str不是可用的函数名
    Exception: func执行时出现异常

    Examples
    --------
    >>> run_blend_func('avg_pos-3-0.5', args)
    avg_pos(3, 0.5, *args)
    """
    if not isinstance(func_str, str):
        raise TypeError(f'func_str should be a string, got {type(func_str)} instead')

    # 分离函数名和附加参数（附加参数的个数不限，受实际定义的函数限制）
    func_name_args = func_str.split('_')
    func_name, *additional_args = func_name_args
    func = _AVAILABLE_FUNCTIONS.get(func_name)
    if func is None:
        raise KeyError(f'function ({func_name}) is not available')
    # 将所有的附加参数处理为float类型，便于传入func处理
    additional_args = tuple(float(item) for item in additional_args)
    try:
        res = func(*additional_args, *args)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise Exception(f'Error raised while executing blending function {func_name}({additional_args}, {args}), '
                        f'error message: \n{e}')
    return res


def blender_parser(blender_string):
    """选股策略混合表达式解析程序，将通常的中缀表达式解析为前缀运算队列，从而便于混合程序直接调用

    系统接受的合法表达式为包含 '*' 与 '+' 的中缀表达式，符合人类的思维习惯，使用括号来实现强制
    优先计算，如 's0 + (s1 + s2) * s3'; 表达式中的数字0～3代表选股策略列表中的不同策略的索引号
    上述表达式虽然便于人类理解，但是不利于快速计算，因此需要转化为前缀表达式，其优势是没有括号
    按照顺序读取并直接计算，便于程序的运行。为了节省系统运行开销，在给出混合表达式的时候直接将它
    转化为前缀表达式的形式并直接存储在blender列表中，在混合时直接调用并计算即可

    Parameters
    ----------
    blender_string: str
        选股策略混合表达式，中缀表达式，如 's0 + (s1 + s2) * s3'

    Returns
    -------
    s2: list
    blender string的前缀表达式
    """

    prio = {'|':    0,
            'or':   0,
            '&':    1,
            'and':  1,
            '~':    1,
            'not':  1,
            '+':    0,
            '-':    0,
            '*':    1,
            '/':    1,
            '^':    2}

    # 定义两个队列作为操作堆栈
    op_stack = []  # 运算符栈
    arg_count_stack = []  # 函数的参数个数栈
    output = []  # 结果队列
    exp_list = _exp_to_token(blender_string)[::-1]
    while exp_list:
        token = exp_list.pop()
        # 从右至左逐个读取表达式中的元素（数字/操作符/函数/括号/逗号）
        # 并按照以下算法处理
        if is_number_like(token):
            # 1，如果元素是数字则进入结果队列
            output.append(token)
        elif token == '(':
            # 2，如果元素是反括号则压入运算符栈
            op_stack.append(token)
        elif token == ')':
            # 3，扫描到")"时，依次弹出所有运算符直到遇到"("或一个函数，并根据遇到的token类型（函数/右括号）来确定下一步
            if len(op_stack) == 0:
                raise ValueError(f'missing opening parenthesis!')
            while op_stack[-1][-1] != '(':
                try:
                    output.append(op_stack.pop())
                except:  # 如果右括号没有与之配对的左括号，则报错
                    raise ValueError(f'missing opening parenthesis!')
            if op_stack[-1] == '(':  # 如果剩余右括号，则弹出右括号，并丢弃这对括号
                op_stack.pop()
            else:  # 如果剩余一个函数，则将函数的参数+1，并弹出函数，设置函数的参数个数
                arg_count = arg_count_stack.pop() + 1
                func = op_stack.pop() + str(arg_count) + ")"
                output.append(func)
        elif token in prio.keys():
            # 4，扫描到运算符时
            if len(op_stack) > 0:
                if (op_stack[-1] in '+-*/&|^~andnotor') and (prio[token] <= prio[op_stack[-1]]):
                    output.append(op_stack.pop())
                    exp_list.append(token)
                else:
                    op_stack.append(token)
            else:
                # 如果op栈为空，直接将token压入op栈
                op_stack.append(token)
        elif token[0].isalpha and (token[-1] == '('):
            # 5，扫描到字母开头，且'('结尾的字符串时，说明扫描到函数，将函数压入op栈，并将数字0压入arc_count栈
            op_stack.append(token)
            arg_count_stack.append(0)
        elif token == ',':
            # 6, 扫描到逗号时，说明函数有参数，该函数的参数数量+1，同时弹出op栈中所有非函数的op
            try:
                arg_count_stack[-1] += 1
            except:
                raise ValueError(f'miss-placed comma!')
            if len(op_stack) == 0:
                raise ValueError(f'missing opening parenthesis!')
            while op_stack[-1][-1] != '(':  # 弹出所有的操作符，直到下一个函数或括号
                try:
                    output.append(op_stack.pop())
                except:
                    raise ValueError(f'missing opening parenthesis!')
        elif BLENDER_STRATEGY_INDEX_IDENTIFIER.match(token):
            # 7, 扫描到策略序号index时，将其送入结果队列
            output.append(token)

        else:  # 扫描到不合法输入
            raise ValueError(f'invalid token: "{token}"')

    while op_stack:
        output.append(op_stack.pop())

    # blender 质量检查：
    # 1，如果output中的所有token都不是策略序号，则报错
    if not any([BLENDER_STRATEGY_INDEX_IDENTIFIER.match(token) for token in output]):
        raise ValueError(f'no strategy index found in expression, use "s0"/"s1" to represent strategies, '
                         f'see document for details')
    # 2，如果output中策略序号大于blender中的最大序号，则报错
    # if max([int(token[1:]) for token in output if BLENDER_STRATEGY_INDEX_IDENTIFIER.match(token)]) >= len(blender):
    #     raise ValueError(f'strategy index out of range, count of strategies is {len(blender) - 1}')
    # 3，如果左右括号不匹配(生成的token中有左括号或右括号)，则报错
    if any([token in '()' for token in output]):
        raise ValueError(f'mismatched parenthesis!')
    output.reverse()  # 表达式解析完成，生成前缀表达式
    return output


def signal_blend(op_signals, blender):
    """ 选股策略混合器，将各个选股策略生成的选股蒙板按规则混合成一个蒙板

    Parameters
    ----------
    op_signals:
    blender:

    Returns
    -------
    s: ndarray, 混合完成的选股蒙板
    """
    exp = blender[:]  # 混合表达式的逆波兰式，可以直接读取后计算
    s = []  # 信号栈，用来存储所有需要操作的交易信号
    while exp:
        token = exp[-1]
        if token[-1] == ')':
            # 如果碰到函数，解析函数的参数数量，并弹出信号栈内的适当个交易信号，应用函数得到结果，压入信号栈
            token = exp.pop()
            arg_count = int(token[-2])
            func_name = token[0:-3]
            args = tuple(s.pop() for i in range(arg_count))
            res = run_blend_func(func_name, *args)
            s.append(res)
        elif token in '~not':
            # 如果碰到一元运算符，弹出信号栈内的交易信号，得到结果，再压入信号栈
            s.append(_operate(s.pop(), None, exp.pop()))
        elif token in '+-*/^&|andor':
            # 如果碰到二元运算符，弹出信号栈内两个交易信号，得到结果，再压入信号栈
            s.append(_operate(s.pop(), s.pop(), exp.pop()))
        elif BLENDER_STRATEGY_INDEX_IDENTIFIER.match(token):
            # 如果是index，直接读取交易信号并压入信号栈
            sig_index = int(exp.pop()[1:])
            s.append(op_signals[sig_index])
        else:  # exp[-1].isnum():
            # 如果是数字，直接作为数字压入信号栈
            s.append(float(exp.pop()))

    return s[0]


def _exp_to_token(string):
    """ 将输入的blender-exp裁切成不同的元素(token)，包括数字、符号、函数等

    Parameters
    ----------
    string: str, blender-exp字符串

    Returns
    -------
    tokens: list, 元素为token的列表

    Examples
    --------
    >>> _exp_to_token('s0|s1')
    ['s0', '|', 's1']
    """
    if not isinstance(string, str):
        raise TypeError()
    function_like_operators = ['or',
                               'and',
                               'not']
    token_types = {
        'operator':          0,
        'number':            1,
        'function':          2,
        'open_parenthesis':  3,
        'close_parenthesis': 4,
        'comma':             5
    }
    tokens = []
    string = string.replace(' ', '')
    string = string.replace('\t', '')
    string = string.replace('\n', '')
    string = string.replace('\r', '')
    cur_token = ''
    next_token = False  # 如果需要强行分开两个相同类型的token，则将next_token设置为True
    prev_token_type = None
    cur_token_type = None
    # 逐个扫描字符，判断每个字符代表的token类型，当token类型发生变化时，将当前token压入tokens栈
    for ch in string:
        if ch in '+*/^&|~':
            cur_token_type = token_types['operator']
        elif ch in '-':
            # '-'号出现在function中作为参数存在时，应被识别为function的一部分，此时'-'前只能是'_'
            if (cur_token_type == token_types['function']) and (cur_token[-1] == '_'):
                cur_token_type = token_types['function']
            # '-'号在下面四种情况下应被识别为负号，成为数字的一部分：
            #   1，在表达式第一位
            #   2，紧接在左括号后面
            #   3，紧接在另一个符号后面
            #   4，紧接在一个完整结尾的function之后
            elif (prev_token_type == token_types['operator']) or \
                    (prev_token_type == token_types['open_parenthesis']) or \
                    (prev_token_type == token_types['function']) and (cur_token[-1] == '(') or \
                    (prev_token_type is None):

                cur_token_type = token_types['number']
            # 其余情况下被识别为一个操作符
            else:
                cur_token_type = token_types['operator']
        elif ch in '0123456789':
            if cur_token == '':
                cur_token_type = token_types['number']
            else:
                # 如果数字跟在function的后面，则被识别为字母（function）的一部分，否则被识别为数字
                # 但数字被识别为function一部分的前提是function还没有以左括号结尾
                # 以及前一个function不在"function_like_operator"中
                if (prev_token_type == token_types['function']) and \
                        (cur_token[-1] != '(') and \
                        (cur_token not in function_like_operators):
                    cur_token_type = token_types['function']
                else:
                    cur_token_type = token_types['number']
        elif ch in '.':
            # 小数点应被识别为数字，除非小数点是跟在一个function中的且function未结束（不以"("结尾）
            if (cur_token_type == token_types['function']) and (cur_token[-1] != '('):
                cur_token_type = token_types['function']
            # 其他情况下小数点应该被识别为数字（允许出现小数点打头的数字，如".15"
            else:
                cur_token_type = token_types['number']
        elif ch.upper() in '_ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            # 字母和下划线应被识别为变量或函数名,
            if cur_token == '':
                cur_token_type = token_types['function']
            else:
                # 如果当前token为function且已经完整，则强行分割token
                if (cur_token_type == token_types['function']) and (cur_token[-1] == '('):
                    next_token = True
                # 如果当前token为function，且属于function_like_operator，也强行分割token
                if (cur_token_type == token_types['function']) and (cur_token in function_like_operators):
                    next_token = True
                # 如果当前token为function，但发现当前token是index，以s打头且后接若干数，也强行分割token
                if (cur_token_type == token_types['function']) and \
                        (BLENDER_STRATEGY_INDEX_IDENTIFIER.match(cur_token)):
                    next_token = True
                cur_token_type = token_types['function']
        elif ch in '(':
            # 如果左括号是单独出现的，则应被识别为左括号
            if cur_token == '':
                cur_token_type = token_types['open_parenthesis']
            # 如果左括号出现在function的后面，且该function尚未以左括号结束，则应被识别为function
            # 的一部分，且被包含在function内作为function的结束符
            else:
                if (prev_token_type == token_types['function']) and (cur_token[-1] != '('):
                    cur_token_type = token_types['function']
                else:
                    cur_token_type = token_types['open_parenthesis']
        elif ch in ')':
            cur_token_type = token_types['close_parenthesis']
        elif ch in ',':
            # ','逗号被用来分割函数的参数，实际应被忽略
            cur_token_type = token_types['comma']
        else:
            # 某种没有预料到的字符出现在表达式中：
            raise TypeError(f'character in expression "{ch}" is not valid!')

        # 四种常规情况下判断当前token已经完整，将该token压入tokens栈，完成一个token的识别：
        # 1，当前字符被判定为新的token类型;
        # 2，当前token类型为左括号;
        # 3，当前token类型为右括号;
        # 4，出现强行分割token的标识next_token
        # 一种特殊情况下，将token压入tokens栈时，需要修改该token：
        # 1，当前token类型为数字，且token仅包含一个字符"-"时，将token改为'-1'，并压入一个额外token'*'
        # 此时重置token类型、重置当前token，将当前字符赋予当前token
        if cur_token_type != prev_token_type or \
                cur_token_type == token_types['open_parenthesis'] or \
                cur_token_type == token_types['close_parenthesis'] or \
                next_token:
            if cur_token != '':
                if (cur_token == '-') and (prev_token_type == token_types['number']):
                    tokens.append('-1')
                    tokens.append('*')
                else:
                    tokens.append(cur_token)
            prev_token_type = cur_token_type
            cur_token = ''
            next_token = False
        if cur_token_type is not None:
            cur_token += ch
    tokens.append(cur_token)
    return tokens


# 这个简单函数本身速度已经很快，不需要@njit()，njit()后运行时间大大增加（因为overhead）
def _operate(n1, n2, op):
    """混合操作符函数，将两个选股、多空蒙板混合为一个

    Parameters
    ----------
    n1: np.ndarray: 第一个输入矩阵
    n2: np.ndarray: 第二个输入矩阵
    op: np.ndarray: 运算符

    Returns
    -------
        np.ndarray

    """
    if op == '+':
        return n2 + n1
    elif op in ['and', '&', '*']:
        return n2 * n1
    elif op == '-':
        return n2 - n1
    elif op == '/':
        return n2 / n1
    elif op in ['or', '|']:
        return 1 - (1 - n2) * (1 - n1)
    elif op in ['not', '~']:
        return -1 * n1
    else:
        raise ValueError(f'Unknown operand: ({op})!')


def human_blender(blender_str: str, strategy_ids: list) -> str:
    """ 将blender字符串转化为可读的字符串，将s0等策略代码替换为策略ID，将blender string的各个token识别出来并添加空格分隔

    Parameters
    ----------
    blender_str: str
        blender字符串，例如's0+s1*s2'
    strategy_ids: list of str
        策略ID列表，例如['MACD', 'DMA', 'TRIX'], 策略的数量必须与blender_str中的策略数量一致或大于blender_str中的策略数量

    Returns
    -------
    blender_str: str
        可读的blender字符串，例如'MACD + DMA * TREND'
    """

    if blender_str is None:
        return ''

    if not isinstance(blender_str, str):
        raise TypeError(f'blender_str must be a string, got {type(blender_str)}')
    if not isinstance(strategy_ids, list):
        raise TypeError(f'strategy_ids must be a list, got {type(strategy_ids)}')

    tokens = _exp_to_token(blender_str)

    # 将tokens中的策略序号替换为策略ID
    human_tokens = []
    for token in tokens:
        if BLENDER_STRATEGY_INDEX_IDENTIFIER.match(token):
            try:
                strategy_id = strategy_ids[int(token[1:])]
            except IndexError:
                raise IndexError(f'index {token[1:]} out of range, while there are only '
                                 f'{len(strategy_ids)} strategies in the list')
            human_tokens.append(str(strategy_id))
        elif token in ['+', '-', '*', '/', '^', '&', '|', 'and', 'or', 'not', '~']:
            human_tokens.append(f' {token} ')
        elif token in [',']:
            human_tokens.append(f'{token} ')
        else:
            human_tokens.append(token)

    return ''.join(human_tokens)
