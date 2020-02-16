# coding=utf-8

import time
import pandas as pd
import tushare as ts
import numpy as np
from datetime import datetime
import datetime as dt
from abc import abstractmethod, abstractproperty, ABCMeta
import matplotlib.pyplot as plt
import itertools
from multiprocessing import Pool
import numba as nb

print ('pandas version:', pd.__version__)
print ('numpy version:', np.__version__)
print ('tushare version:', ts.__version__)
