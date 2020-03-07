from qteasy.core import *
import qteasy.history as hs
from qteasy.operator import *
import pandas as pd

if __name__ == '__main__':

    op = Operator(timing_types=['CDL'], selecting_types=['simple'], ricon_types=['urgent'])


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
    h.info() # 模拟3维数据，一支个股，四种类型
    v3D=np.zeros((4, len(d.index), 1)) # 创建一个空的三维矩阵，包含三层，行数和列数与d.values相同
    v3D[0, :, 0] = d.values.T[0]
    v3D[1, :, 0] = d.values.T[1] # 填入模拟数据
    v3D[2, :, 0] = d.values.T[2] # 填入模拟数据
    v3D[3, :, 0] = d.values.T[3] # 填入模拟数据
    h2 = hs.HistoryPanel(v3D, ['000300', '000301', '000302', '000303'], d.index.values, ['close'])
    h2.info()

    op.set_parameter('s-0', pars=('Y', 1))
    op.set_parameter('t-0', opt_tag=1)

    shares = ['600037', '600547', '000726', '600111', '600600', '600549', '000001',
              '000002', '000005', '000004', '000006', '000007', '000008']
    # shares = ['600037', '000005']
    print('Historical data has been extracted')
    # %time d = h.extract(shares, start='2005-01-15', end = '2019-10-15', interval = 'd')
    cont = Context()
    cont.shares = shares
    cont.shares = h.shares
    cont.history_data = h
    # print ('Optimization Period:', opt.opt_period_start, opt.opt_period_end,opt.opt_period_freq)
    print('transaction rate object created, rate is', cont.rate)

    timing_pars1 = (86, 198, 58)
    timing_pars2 = {'600037': (177, 248, 244),
                    '000005': (86, 198, 58)}
    timing_pars3 = (72, 130, 133)
    timing_pars4 = (31, 17)
    timing_pars5 = (62, 132, 10, 'buy')
    op.set_blender('timing', 'pos-1')
    op.set_parameter('t-0', pars = timing_pars5)
    # op.set_parameter('t-1', pars = timing_pars3)
    # op.set_parameter('t-2', pars = timing_pars4)
    # op.set_parameter('t-3', pars = timing_pars1)
    op.set_parameter('r-0', pars=(8, -0.1312))
    # op.info()
    # print('\nTime of creating operation list:')
    op.info()
    run(op, cont, mode=1, history_data=cont.history_data)
