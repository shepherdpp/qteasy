from core import *
import pandas as pd

if __name__ == '__main__':

    l1 = np.array([[3, 2, 5], [5, 3, 2]])
    res = unify(l1)
    target = np.array([[0.3, 0.2, 0.5], [0.5, 0.3, 0.2]])
    print('test result of unify:',l1, res)
    assert np.allclose(res, target), 'there\'s something wrong with unfiy function'

    h = History()
    op = Operator(timing_types=['DMA', 'MACD'], selecting_types=['simple'], ricon_types=['urgent'])
    op.info()

    d = pd.read_csv('000300_I_N.txt', index_col='date')
    d.index = pd.to_datetime(d.index, format='%Y-%m-%d')
    d.drop(labels=['open', 'high', 'low', 'volume', 'amount'], axis=1, inplace=True)
    d.columns = ['000300-I']
    d = d[::-1]
    d.head()

    op.set_parameter('s-0', pars=('Y', 1))
    op.set_parameter('t-0', opt_tag=1)

    shares = ['600037', '600547', '000726', '600111', '600600', '600549', '000001',
              '000002', '000005', '000004', '000006', '000007', '000008']
    # shares = ['600037', '000005']
    print('Historical data has been extracted')
    # %time d = h.extract(shares, start='2005-01-15', end = '2019-10-15', interval = 'd')
    cont = Context()
    cont.shares = shares
    cont.shares = ['000300-I']
    cont.history_data=d
    # print ('Optimization Period:', opt.opt_period_start, opt.opt_period_end,opt.opt_period_freq)
    print('transaction rate object created, rate is', cont.rate)

    timing_pars1 = (86, 198, 58)
    timing_pars2 = {'600037': (177, 248, 244),
                    '000005': (86, 198, 58)}
    timing_pars3 = (72, 130, 133)
    timing_pars4 = (131, 27)
    op.set_blender('timing', 'pos-1')
    op.set_parameter('t-0', pars=timing_pars1)
    op.set_parameter('t-1', pars=timing_pars3)
    # op.set_parameter('t-2', pars = timing_pars4)
    # op.set_parameter('t-3', pars = timing_pars1)
    op.set_parameter('r-0', pars=(8, -0.1312))
    # op.info()
    # print('\nTime of creating operation list:')
    run(op, cont, mode=1, history_data=cont.history_data)
