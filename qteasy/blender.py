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


def argsum(*args):
    """sum of all arguments"""
    return sum(args)


_FUNCTIONS = {
    'abs': abs,
    'acos': math.acos,
    'asin': math.asin,
    'atan': math.atan,
    'atan2': math.atan2,
    'ceil': math.ceil,
    'cos': math.cos,
    'cosh': math.cosh,
    'degrees': math.degrees,
    'exp': math.exp,
    'fabs': math.fabs,
    'floor': math.floor,
    'fmod': math.fmod,
    'frexp': math.frexp,
    'hypot': math.hypot,
    'ldexp': math.ldexp,
    'log': math.log,
    'log10': math.log10,
    'max': max,
    'modf': math.modf,
    'pow': math.pow,
    'radians': math.radians,
    'sin': math.sin,
    'sinh': math.sinh,
    'sqrt': math.sqrt,
    'tan': math.tan,
    'tanh': math.tanh,
    'sum': argsum
}


@property
def _exp_to_blender():
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
    exp_list = self._exp_to_token(self._selecting_blender_string)[::-1]
    while exp_list:
        # print(f'step starts: output list is {output}, op_stack is {op_stack}\n'
        #       f'will pop token: {exp_list[-1]} from exp_list: {exp_list}')
        token = exp_list.pop()
        # 从右至左逐个读取表达式中的元素（数字或操作符）
        # 并按照以下算法处理
        if is_number(token):
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
        # print(f'step ends: output list is {output}, op_stack is {op_stack}')
    while op_stack:
        output.append(op_stack.pop())
    output.reverse()  # 表达式解析完成，生成前缀表达式
    return output


def _exp_to_token(string):
    """ 将输入的blender-exp裁切成不同的元素(token)，包括数字、符号、函数等

    :return:
    """
    if not isinstance(string, str):
        raise TypeError()
    token_types = {'operation':         0,
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
            cur_token_type = token_types['operation']
        elif ch in '-':
            # '-'号出现在左括号或另一个符号以后，应被识别为负号，成为数字的一部分
            if prev_token_type == token_types['operation'] or \
                    prev_token_type == token_types['open_parenthesis']:
                cur_token_type = token_types['number']
            else:
                # 否则被识别为一个操作符
                cur_token_type = token_types['operation']
        elif ch in '0123456789':
            if cur_token == '':
                cur_token_type = token_types['number']
            else:
                # 如果数字跟在function的后面，则被识别为字母（function）的一部分，否则被识别为数字
                # 但数字被识别为function一部分的前提是function还没有以左括号结尾
                if prev_token_type == token_types['function'] and cur_token[-1] != '(':
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
            else:  # 如果前一个token已经为function且已经完整，则强行分割token
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


def _selecting_blend(self, sel_masks):
    """ 选股策略混合器，将各个选股策略生成的选股蒙板按规则混合成一个蒙板

    input:
        :param sel_masks:
    :return:
        ndarray, 混合完成的选股蒙板
    """
    functions = {'sum(':  np.sum,
                 'abs(':  np.abs,
                 'sqrt(': np.sqrt,
                 'cos(':  np.cos,
                 'max(':  max}
    exp = self._selecting_blender[:]
    s = []
    while exp:  # 等同于但是更好: while exp != []
        if exp[-1].isdigit():
            # 如果是数字则直接入栈
            s.append(sel_masks[int(exp.pop())])
        elif exp[-1][-1] == ')':
            # 如果碰到函数，
            token = exp.pop()
            arg_count = int(token[-2])
            func = functions.get(token[0:-2])
            if func is None:
                raise ValueError(
                    f'the function \'{token[0:-2]}\' -> {functions.get(token[0:-2])} is not a valid function!')
            args = tuple([s.pop() for i in range(arg_count)])
            try:
                s.append(func(*args))
            except:
                print(f'wrong output func(*args) with args = {args} => ')
        else:
            # print(f'calculating: taking {s[-1]} and {s[-2]} and eval {s[-2]} {exp[-1]} {s[-1]}')
            s.append(self._blend(s.pop(), s.pop(), exp.pop()))
    return unify(s[0])


def _blend(self, n1, n2, op):
    """混合操作符函数，将两个选股、多空蒙板混合为一个

    input:
        :param n1: np.ndarray: 第一个输入矩阵
        :param n2: np.ndarray: 第二个输入矩阵
        :param op: np.ndarray: 运算符
    return:
        :return: np.ndarray

    """
    # import pdb; pdb.set_trace()
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
