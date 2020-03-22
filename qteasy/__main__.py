from qteasy.core import *
import qteasy.history as hs
from qteasy.operator import *
import pandas as pd

if __name__ == '__main__':

    op = Operator(timing_types=['DMA'], selecting_types=['simple', 'rand'], ricon_types=['urgent'])
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
    h.info() # 模拟3维数据，一支个股，四种类型
    v3D=np.zeros((4, len(d.index), 1)) # 创建一个空的三维矩阵，包含三层，行数和列数与d.values相同
    v3D[0, :, 0] = d.values.T[0]
    v3D[1, :, 0] = d.values.T[1] # 填入模拟数据
    v3D[2, :, 0] = d.values.T[2] # 填入模拟数据
    v3D[3, :, 0] = d.values.T[3] # 填入模拟数据
    h2 = hs.HistoryPanel(v3D, ['000300', '000301', '000302', '000303'], d.index.values, ['close'])
    print('INFORMATION OF CREATED HISTORY PANEL: h2\n==========================')
    h2.info()
    print('START TO SET SELECTING STRATEGY PARAMETERS\n=======================')
    op.set_parameter('s-0', pars=(0.5,))
    op.set_parameter('s-1', pars=(0.5,))
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

    print('start testing HistoryPanel')
    data = np.random.randint(10, size=(10, 5))
    index = pd.date_range(start='20200101', freq='d', periods=10)
    shares = '000100,000101,000102,000103,000104'
    dtypes = 'close'
    df = pd.DataFrame(data)
    print('=========================\nTesting HistoryPanel creation from DataFrame')
    hp = hs.from_dataframe(df=df, shares=shares, dtypes=dtypes)
    hp.info()
    hp = hs.from_dataframe(df=df, shares='000100', dtypes='close, open, high, low, middle', column_type='dtypes')
    hp.info()

    print('=========================\nTesting HistoryPanel creation from initialization')
    data = np.random.randint(10, size=(5, 10, 4)).astype('float')
    index = pd.date_range(start='20200101', freq='d', periods=10)
    shares = '000100,000101,000102,000103,000104'
    dtypes = 'close, open, high,low'
    data[0,[5,6,9], [0,1,3]] = np.nan
    data[1:4, [4,7,6,2], [1,1,3,0]] = np.nan
    data[4:5, [2, 9, 1, 2], [0, 3, 2, 1]] = np.nan
    hp = hs.HistoryPanel(data, levels=shares, columns=dtypes, rows=index)
    hp.info()
    print('==========================\n输出close类型的所有历史数据\n',hp['close', :, :])
    print(f'==========================\n输出close和open类型的所有历史数据\n{hp[[0,1], :, :]}')
    print(f'==========================\n输出第一只股票的所有类型历史数据\n: {hp[:,[0], :]}')
    print('==========================\n输出第0、1、2个htype对应的所有股票全部历史数据\n', hp[[0, 1, 2],:,:])
    print('==========================\n输出close、high两个类型的所有历史数据\n', hp[['close', 'high']])
    print('==========================\n输出0、1两个htype的所有历史数据\n', hp[[0,1]])
    print('==========================\n输出close、high两个类型的所有历史数据\n', hp['close,high'])
    print('==========================\n输出close起到high止的三个类型的所有历史数据\n', hp['close:high'])
    print('==========================\n输出0、1、3三个股票的全部历史数据\n', hp[:, [0, 1, 3]] )
    print('==========================\n输出000100、000102两只股票的所有历史数据\n', hp[:, ['000100', '000102']])
    print('==========================\n输出0、1、2三个股票的历史数据\n', hp[:, 0: 3])
    print('==========================\n输出000100、000102两只股票的所有历史数据\n', hp[:, '000100, 000102'])
    print('==========================\n输出所有股票的0-7日历史数据\n', hp[:, :, 0:8])
    print('==========================\n输出000100股票的0-7日历史数据\n', hp[:, '000100', 0:8])
    print('==========================\nstart testing multy axis slicing of HistoryPanel object')
    print('==========================\n输出000100、000120两只股票的close、open两组历史数据\n',
          hp['close,open', ['000100', '000102']])
    print('==========================\n输出000100、000120两只股票的close到open三组历史数据\n',
          hp['close,open', '000100, 000102'])
    print(f'historyPanel: hp:\n{hp}')
    print(f'data is:\n{data}')
    hp.htypes = 'open,high,low,close'
    hp.info()
    hp.shares = ['000300', '600227', '600222', '000123', '000432']
    hp.info()