# coding=utf-8

from .core import *
from .history import *
from .operator import *
from .strategy import *
from .visual import *
from .built_in import *
from .finance import *
import pandas as pd
import numpy as np

# TODO: 仅需要导入用户可能会用到的类或函数即可，不需要导入所有的函数

print(f'Module qteasy has been loaded successfully!, version: 0.1')
print('tushare version:', ts.__version__)


TUSHARE_TOKEN = '14f96621db7a937c954b1943a579f52c09bbd5022ed3f03510b77369'
ts.set_token(TUSHARE_TOKEN)

print('tushare token set!')