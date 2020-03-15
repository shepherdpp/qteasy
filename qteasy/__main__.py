# coding = utf-8
# __main__.py

from qteasy.core import *
import qteasy.history as hs
from qteasy.operator import *
import pandas as pd

if __name__ == '__main__':

    op = Operator(timing_types=['simple'], selecting_types=['finance'], ricon_types=['urgent'])
    d = pd.read_csv('000300_I_N.txt', index_col='date')
    d.index = pd.to_datetime(d.index, format='%Y-%m-%d')
    d.drop(labels=['volume', 'amount'], axis=1, inplace=True)
    '''d.drop(labels=['open', 'high', 'low', 'volume', 'amount'], axis=1, inplace=True)
    d.columns = ['000300-I']'''
    d = d[::-1]
    v3D=np.zeros((3, *d.values.shape)) # 创建一个空的三维矩阵，包含三层，行数和列数与d.values相同
    v3D[0] = d.values
    v3D[1] = d.values + 20 # 填入模拟数据
    v3D[2] = d.values - 20 # 填入模拟数据
    h = hs.HistoryPanel(v3D, ['000300', '000301', '000302'], d.index.values, ['open', 'high', 'low', 'close'])
    print('INFORMATION OF CREATED HISTORY PANEL: h \n============================')
    h.info() # 模拟3维数据，三支个股，四种类型


    v3D=np.zeros((4, len(d.index), 1)) # 创建一个空的三维矩阵，包含四层，行数与d.values相同，共一列
    v3D[0, :, 0] = d.values.T[0]
    v3D[1, :, 0] = d.values.T[1] # 填入模拟数据
    v3D[2, :, 0] = d.values.T[2] # 填入模拟数据
    v3D[3, :, 0] = d.values.T[3] # 填入模拟数据
    h2 = hs.HistoryPanel(v3D, ['000300', '000301', '000302', '000303'], d.index.values, ['close'])
    print('INFORMATION OF CREATED HISTORY PANEL: h2\n==========================')
    h2.info() # 模拟三维数据，四只个股，一种数据类型
    print('START TO SET SELECTING STRATEGY PARAMETERS\n=======================')
    sel_param = ('y', 1)
    sel_param2 = (True, 'proportion', 0, 0.75)
    op.set_parameter('s-0', pars=sel_param2, data_types=['close'])
    #op.set_parameter('s-1', pars=('Q', 0.5))
    print('SET THE TIMING STRATEGY TO BE OPTIMIZABLE\n========================')
    op.set_parameter('t-0', opt_tag=1)

    shares = ['600037', '600547', '000726', '600111', '600600', '600549', '000001',
              '000002', '000005', '000004', '000006', '000007', '000008']
    # share_pool = ['600037', '000005']
    # print('Historical data has been extracted')
    # %time d = h.extract(share_pool, start='2005-01-15', end = '2019-10-15', interval = 'd')
    print('CREATE CONTEXT OBJECT\n=======================')
    cont = Context()
    cont.share_pool = shares
    cont.share_pool = h2.shares
    cont.history_data = h2
    # print ('Optimization Period:', opt.opt_period_start, opt.opt_period_end,opt.opt_period_freq)
    print(f'TRANSACTION RATE OBJECT CREATED, RATE IS: \n==========================\n{cont.rate}')

    timing_pars1 = (86, 198, 58)
    timing_pars2 = {'600037': (177, 248, 244),
                    '000005': (86, 198, 58)}
    timing_pars3 = (72, 130, 133)
    timing_pars4 = (31, 17)
    timing_pars5 = (62, 132, 10, 'buy')
    print('START TO SET TIMING PARAMETERS TO STRATEGIES: \n===================')
    op.set_blender('timing', 'pos-1')
    op.set_parameter('t-0', pars = timing_pars3)
    # op.set_parameter('t-1', pars = timing_pars3)
    # op.set_parameter('t-2', pars = timing_pars4)
    # op.set_parameter('t-3', pars = timing_pars1)
    print('START TO SET RICON PARAMETERS TO STRATEGIES:\n===================')
    op.set_parameter('r-0', pars=(8, -0.1312))
    # op.info()
    # print('\nTime of creating operation list:')
    op.info()
    print(f'\n START QT RUNNING\n===========================\n')
    run(op, cont, mode=1, history_data=cont.history_data)
