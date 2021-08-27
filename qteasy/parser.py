# coding=utf-8
# parser.py

# ======================================
# This file contains a blender parser
# that can be used to parse user defined
# signal blender strings and execute
# their values, which are signals
# combined by all output signals from 
# all operator strategies
# ======================================

import math

_CONSTANTS = {
              'pi': math.pi,
              'e':  math.e,
              'phi': (1 + 5 ** .5) / 2
             }

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
    'tanh': math.tanh
}

