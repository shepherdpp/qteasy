# coding=utf-8
# blender.py

# ======================================
# This file contains a functions that are
# used for parsing and evaluating
# operator signal blending expressions.
# including expression parsing functions
# and basic signal operators, the atomic
# signal operation functions are defined
# in util functions
# ======================================

import numpy as np
import math
from .utilfuncs import unify, is_number_like, str_to_list


# 这里定义可用的交易信号混合函数
def argsum(*args):
    """sum of all arguments"""
    return sum(args)


def op_avg(*args):
    """

    :param args:
    :return:
    """
    raise NotImplementedError


def op_pos(*args):
    """

    :param args:
    :return:
    """
    raise NotImplementedError


def op_avg_pos(*args):
    """

    :param args:
    :return:
    """
    raise NotImplementedError


def op_str(*args):
    """

    :param args:
    :return:
    """
    raise NotImplementedError


def op_combo(*args):
    """

    :param args:
    :return:
    """
    raise NotImplementedError


_AVAILABLE_FUNCTIONS = {'abs(':     abs,
                        'acos(':    math.acos,
                        'asin(':    math.asin,
                        'atan(':    math.atan,
                        'atan2(':   math.atan2,
                        'ceil(':    math.ceil,
                        'cos(':     math.cos,
                        'cosh(':    math.cosh,
                        'degrees(': math.degrees,
                        'exp(':     math.exp,
                        'fabs(':    math.fabs,
                        'floor(':   math.floor,
                        'fmod(':    math.fmod,
                        'frexp(':   math.frexp,
                        'hypot(':   math.hypot,
                        'ldexp(':   math.ldexp,
                        'log(':     math.log,
                        'log10(':   math.log10,
                        'max(':     max,
                        'modf(':    math.modf,
                        'pow(':     math.pow,
                        'radians(': math.radians,
                        'sin(':     math.sin,
                        'sinh(':    math.sinh,
                        'sqrt(':    math.sqrt,
                        'tan(':     math.tan,
                        'tanh(':    math.tanh,
                        'sum(':     argsum
                        }


def blender_parser(blender_string):
    """选股策略混合表达式解析程序，将通常的中缀表达式解析为前缀运算队列，从而便于混合程序直接调用

    系统接受的合法表达式为包含 '*' 与 '+' 的中缀表达式，符合人类的思维习惯，使用括号来实现强制
    优先计算，如 '0 + (1 + 2) * 3'; 表达式中的数字0～3代表选股策略列表中的不同策略的索引号
    上述表达式虽然便于人类理解，但是不利于快速计算，因此需要转化为前缀表达式，其优势是没有括号
    按照顺序读取并直接计算，便于程序的运行。为了节省系统运行开销，在给出混合表达式的时候直接将它
    转化为前缀表达式的形式并直接存储在blender列表中，在混合时直接调用并计算即可
    input： =====
        no input parameter
    return：===== s2: 前缀表达式
        :rtype: list: 前缀表达式
    """
    # TODO: 将所有与表达式解析相关的函数移到新的parser模块中
    # TODO: 建立新的相关类，如表达式类、token类、function类、stack类等方便运算
    prio = {'|':   0,
            'or':  0,
            '&':   1,
            'and': 1,
            'not': 1,
            '+':   0,
            '-':   0,
            '*':   1,
            '/':   1,
            '^':   2}
    functions = {'sum(':  np.sum,
                 'abs(':  np.abs,
                 'sqrt(': np.sqrt,
                 'cos(':  np.cos,
                 'max(':  np.maximum}
    # 定义两个队列作为操作堆栈
    op_stack = []  # 运算符栈
    arg_count_stack = []  # 函数的参数个数栈
    output = []  # 结果队列
    exp_list = _exp_to_token(blender_string)[::-1]
    while exp_list:
        # print(f'step starts: output list is {output}, op_stack is {op_stack}\n'
        #       f'will pop token: {exp_list[-1]} from exp_list: {exp_list}')
        token = exp_list.pop()
        # 从右至左逐个读取表达式中的元素（数字或操作符）
        # 并按照以下算法处理
        if is_number_like(token):
            # 1，如果元素是数字则进入结果队列
            output.append(token)
            # print(f'got number token, put to output list')
        elif token == '(':
            # 2，如果元素是反括号则压入运算符栈
            op_stack.append(token)
            # print(f'got "(" token, put to op stack')
        elif token == ')':
            # 3，扫描到")"时，依次弹出所有运算符直到遇到"("或一个函数，并根据遇到的token类型（函数/右括号）来确定下一步
            while op_stack[-1][-1] != '(':
                try:
                    output.append(op_stack.pop())
                except:  # 如果右括号没有与之配对的左括号，则报错
                    raise ValueError(f'Invalid expression, missing opening parenthesis!')
            if op_stack[-1] == '(':  # 如果剩余右括号，则弹出右括号，并丢弃这对括号
                op_stack.pop()
            else:  # 如果剩余一个函数，则将函数的参数+1，并弹出函数，设置函数的参数个数
                arg_count = arg_count_stack.pop() + 1
                func = op_stack.pop() + str(arg_count) + ")"
                output.append(func)
                # print(f'there\'s function in op stack, poped function with argument count {arg_count}')
        elif token in prio.keys():
            # 4，扫描到运算符时
            # print(f'got op type token')
            if len(op_stack) > 0:
                if (op_stack[-1] in '+-*/&|^') and (prio[token] <= prio[op_stack[-1]]):
                    # print(f'op stack has op {op_stack[-1]}, which is higher than current token {s}, poped!\n'
                    #       f'current token {s} will be put back to exp for next try')
                    output.append(op_stack.pop())
                    exp_list.append(token)
                else:
                    op_stack.append(token)
            else:
                # 如果op栈为空，直接将token压入op栈
                op_stack.append(token)
        elif token in functions:
            # 5，扫描到函数时，将函数压入op栈，并将数字0压入arc_count栈
            op_stack.append(token)
            arg_count_stack.append(0)
        elif token == ',':
            # 6, 扫描到逗号时，说明函数有参数，该函数的参数数量+1，同时弹出op栈中所有非函数的op
            try:
                arg_count_stack[-1] += 1
            except:
                raise ValueError(f'Invalid expression: miss-placed comma!')
            while op_stack[-1][-1] != '(':  # 弹出所有的操作符，直到下一个函数或括号
                try:
                    output.append(op_stack.pop())
                except:
                    raise ValueError(f'Invalid expression, missing opening parenthesis!')

        else:  # 扫描到不合法输入
            raise ValueError(f'unidentified characters found in blender string: \'{token}\'')
    while op_stack:
        output.append(op_stack.pop())
    output.reverse()  # 表达式解析完成，生成前缀表达式
    return output


def signal_blend(op_signals, blender):
    """ 选股策略混合器，将各个选股策略生成的选股蒙板按规则混合成一个蒙板

    input:
        :param op_signals:
        :param blender:
    :return:
        ndarray, 混合完成的选股蒙板
    """
    exp = blender[:]
    s = []
    while exp:
        if exp[-1].isdigit():
            # 如果是数字则直接入栈
            s.append(op_signals[int(exp.pop())])
        elif exp[-1][-1] == ')':
            # 如果碰到函数，
            token = exp.pop()
            arg_count = int(token[-2])
            func = _AVAILABLE_FUNCTIONS.get(token[0:-2])
            if func is None:
                raise ValueError(
                        f'the function \'{token[0:-2]}\' -> {func.get(token[0:-2])} is not a valid function!')
            args = tuple(s.pop() for i in range(arg_count))
            try:
                s.append(func(*args))
            except:
                print(f'wrong output func(*args) with args = {args} => ')
        else:
            # 如果碰到运算符
            s.append(_operate(s.pop(), s.pop(), exp.pop()))
    # TODO: 是否真的需要把unify作为一个通用指标应用到所有信号上？我看没有这个必要
    return s[0]


def _exp_to_token(string):
    """ 将输入的blender-exp裁切成不同的元素(token)，包括数字、符号、函数等

    :return:
    """
    if not isinstance(string, str):
        raise TypeError()
    function_like_operators = ['or',
                               'and',
                               'not']
    token_types = {'operator':          0,
                   'number':            1,
                   'function':          2,
                   'open_parenthesis':  3,
                   'close_parenthesis': 4,
                   'comma':             5}
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
        if ch in '+*/^&|':
            cur_token_type = token_types['operator']
        elif ch in '-':
            # '-'号出现在左括号或另一个符号以后，应被识别为负号，成为数字的一部分
            if prev_token_type == token_types['operator'] or \
                    prev_token_type == token_types['open_parenthesis']:
                cur_token_type = token_types['number']
            else:
                # 否则被识别为一个操作符
                cur_token_type = token_types['operator']
        elif ch in '0123456789':
            if cur_token == '':
                cur_token_type = token_types['number']
            else:
                # 如果数字跟在function的后面，则被识别为字母（function）的一部分，否则被识别为数字
                # 但数字被识别为function一部分的前提是function还没有以左括号结尾
                # 以及前一个function不在"function_like_operator"中
                if prev_token_type == token_types['function'] and \
                        cur_token[-1] != '(' and \
                        cur_token not in function_like_operators:
                    cur_token_type = token_types['function']
                else:
                    cur_token_type = token_types['number']
        elif ch in '.':
            # 小数点应被识别为数字
            cur_token_type = token_types['number']
        elif ch.upper() in '_ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            # 字母和下划线应被识别为变量或函数名,
            if cur_token == '':
                cur_token_type = token_types['function']
            else:
                # 如果前一个token已经为function且已经完整，则强行分割token
                if cur_token_type == token_types['function'] and cur_token[-1] == '(':
                    next_token = True
                cur_token_type = token_types['function']
        elif ch in '(':
            if cur_token == '':
                cur_token_type = token_types['open_parenthesis']
            else:
                # 如果左括号出现在function的后面，则是function的一部分，否则被识别为左括号
                # 例外情况是前一个function已经以一个左括号结尾了，此时仍然应被识别为左括号
                if prev_token_type == token_types['function'] and cur_token[-1] != '(':
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
            raise TypeError(f'character in expression \'{ch}\' is not valid!')

        if cur_token_type != prev_token_type or \
                cur_token_type == token_types['open_parenthesis'] or \
                cur_token_type == token_types['close_parenthesis'] or \
                next_token:
            # 当发现当前字符被判定为新的token类型时，说明当前token已经完整，将该token压入tokens栈
            # 并重置token类型、重置当前token，将当前字符赋予当前token
            if cur_token != '':
                tokens.append(cur_token)
            prev_token_type = cur_token_type
            cur_token = ''
            next_token = False
        if cur_token_type is not None:
            cur_token += ch
    tokens.append(cur_token)
    return tokens


def _operate(n1, n2, op):
    """混合操作符函数，将两个选股、多空蒙板混合为一个

    input:
        :param n1: np.ndarray: 第一个输入矩阵
        :param n2: np.ndarray: 第二个输入矩阵
        :param op: np.ndarray: 运算符
    return:
        :return: np.ndarray

    """
    if op == '+':
        return n2 + n1
    elif op == 'and' or op == '&' or op == '*':
        return n2 * n1
    elif op == '-':
        return n2 - n1
    elif op == '/':
        return n2 / n1
    elif op == 'or' or op == '|':
        return 1 - (1 - n2) * (1 - n1)
    else:
        raise ValueError(f'ValueError, unknown operand, {op} is not an operand that can be recognized')


# TODO: 将ls_blend中的函数写入blender.py的第一部分函数定义中
def _ls_blend(ls_masks):
    """ 择时策略混合器，将各个择时策略生成的多空蒙板按规则混合成一个蒙板
        这些多空模板的混合方式由混合字符串来定义。
        混合字符串是满足以下任意一种类型的字符串：

        1，  'none'
            模式表示输入的蒙板不会被混合，所有的蒙板会被转化为一个
            三维的ndarray返回,不做任何混合，在后续计算中采用特殊计算方式
            # 分别计算每一个多空蒙板的交易信号，然后再将交易信号混合起来.

        2,  'avg':
            avg方式下，持仓取决于看多的蒙板的数量，看多蒙板越多，持仓越高，
            只有所有蒙板均看空时，最终结果才看空所有蒙板的权重相同，因此，如
            果一共五个蒙板三个看多两个看空时，持仓为60%。更简单的解释是，混
            合后的多空仓位是所有蒙版仓位的平均值.

        3,  '[pos]/[avg-pos](-N)(-T)'
            格式为满足以上正则表达式的字符串，其混合规则如下：
            在pos-N方式下，
            最终的多空信号强度取决于蒙板集合中各个蒙板的信号值，只有满足N个以
            上的蒙板信号值为多(>0)或者为空(<0)时，最终蒙板的多空信号才为多或
            为空。最终信号的强度始终为-1或1，如果希望最终信号强度为输入信号的
            平均值，应该使用avg_pos-N方式混合

            pos-N还有一种变体，即pos-N-T模式，在这种模式下，N参数仍然代表看
            多的参数个数阈值，但是并不是所有判断持仓为正的数据都会被判断为正
            只有绝对值大于T的数据才会被接受，例如，当T为0.25的时候，0.35会
            被接受为多头，但是0.15不会被接受为多头，因此尽管有两个策略在这个
            时间点判断为多头，但是实际上只有一个策略会被接受.

            avg_pos-N方式下，
            持仓同样取决于看多的蒙板的数量，只有满足N个或更多蒙板看多时，最终结果
            看多，否则看空，在看多/空情况下，最终的多空信号强度=平均多空信号强度
            。当然，avg_pos-1与avg等价，如avg_pos-2方式下，至少两个蒙板看多
            则最终看多，否则看空

            avg_pos-N还有一种变体，即avg_pos-N-T模式，在通常的模式下加
            入了一个阈值Threshold参数T，用来判断何种情况下输入的多空蒙板信号
            可以被保留，当T大于0时，只有输入信号绝对值大于T的时候才会被接受为有
            意义的信号否则就会被忽略。使用avg_pos-N-T模式，并把T设置为一个较
            小的浮点数能够过滤掉一些非常微弱的多空信号.

        4，  'str-T':
            str-T模式下，持仓只能为0或+1，只有当所有多空模版的输出的总和大于
            某一个阈值T的时候，最终结果才会是多头，否则就是空头

        5,  'combo':
            在combo模式下，所有的信号被加总合并，这样每个所有的信号都会被保留，
            虽然并不是所有的信号都有效。在这种模式下，本意是原样保存所有单个输入
            多空模板产生的交易信号，但是由于正常多空模板在生成卖出信号的时候，会
            运用"比例机制"生成卖出证券占持有份额的比例。这种比例机制会在针对
            combo模式的信号组合进行计算的过程中产生问题。
            例如：在将两组信号A和B合并到一起之后，如果A在某一天产生了一个股票
            100%卖出的信号，紧接着B在接下来的一天又产生了一次股票100%卖出的信号，
            两个信号叠加的结果，就是产生超出持有股票总数的卖出数量。将导致信号问题

    input：=====
        :type: ls_masks：object ndarray, 多空蒙板列表，包含至少一个多空蒙板
    return：=====
        :rtype: object: 一个混合后的多空蒙板
    """
    try:
        blndr = str_to_list(self._stg_blender, '-')  # 从对象的属性中读取择时混合参数
    except:
        raise TypeError(f'the timing blender converted successfully!')
    assert isinstance(blndr[0], str) and blndr[0] in self.AVAILABLE_LS_BLENDER_TYPES, \
        f'extracted blender \'{blndr[0]}\' can not be recognized, make sure ' \
        f'your input is like "str-T", "avg_pos-N-T", "pos-N-T", "combo", "none" or "avg"'
    l_m = ls_masks
    l_m_sum = np.sum(l_m, 0)  # 计算所有多空模版的和
    l_count = ls_masks.shape[0]
    # 根据多空蒙板混合字符串对多空模板进行混合
    if blndr[0] == 'none':
        return l_m
    if blndr[0] == 'avg':
        return l_m_sum / l_count
    if blndr[0] == 'pos' or blndr[0] == 'avg_pos':
        l_m_sign = 0.
        n = int(blndr[1])
        if len(blndr) == 3:
            threshold = float(blndr[2])
            for msk in ls_masks:
                l_m_sign += np.sign(np.where(np.abs(msk) < threshold, 0, msk))
        else:
            for msk in ls_masks:
                l_m_sign += np.sign(msk)
        if blndr[0] == 'pos':
            res = np.where(np.abs(l_m_sign) >= n, l_m_sign, 0)
            return res.clip(-1, 1)
        if blndr[0] == 'avg_pos':
            res = np.where(np.abs(l_m_sign) >= n, l_m_sum, 0) / l_count
            return res.clip(-1, 1)
    if blndr[0] == 'str':
        threshold = float(blndr[1])
        return np.where(np.abs(l_m_sum) >= threshold, 1, 0) * np.sign(l_m_sum)
    if blndr[0] == 'combo':
        return l_m_sum
    raise ValueError(f'Blender text \'({blndr})\' not recognized!')