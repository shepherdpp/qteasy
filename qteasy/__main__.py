from core import *
import pandas as pd

if __name__ == '__main__':

    l1 = np.array([[3, 2, 5], [5, 3, 2]])
    res = unify(l1)
    target = np.array([[0.3, 0.2, 0.5], [0.5, 0.3, 0.2]])
    print('test result of unify:',l1, res)
    assert np.allclose(res, target), 'there\'s something wrong with unfiy function'

    h = History()
    h.work_days()
    op = Operator(timing_types=['DMA', 'MACD'], selecting_types=['simple'], ricon_types=['urgent'])
    worker = Qteasy(operator=op, history=h)
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
    print('Time of historical data extraction:')
    # %time d = h.extract(shares, start='2005-01-15', end = '2019-10-15', interval = 'd')
    opt = worker.optimizer
    opt.shares = shares
    opt.shares = ['000300-I']
    # print ('Optimization Period:', opt.opt_period_start, opt.opt_period_end,opt.opt_period_freq)

    if not d.empty:
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
        op_list = op.create(hist_extract=d)
    else:
        print('historical data is empty')

    # print(op_list.head())
    lper = opt.looper
    ic = 1000
    print('\nTime of looping operational list without visual:')
    lper.apply_loop(op_list, d.fillna(0), init_cash=ic, moq=0)
    looped_values = lper.apply_loop(op_list, d.fillna(0), init_cash=ic, moq=0)
    # print('\nTime of looping operational list with visual')
    looped_values_2 = lper.apply_loop(op_list, d.fillna(0), init_cash=ic, moq=0, visual=True, price_visual=True)
    # print(looped_values.head())
    ret = looped_values.value[-1] / looped_values.value[0]

    years = (looped_values.index[-1] - looped_values.index[0]).days / 365.
    print('\nTotal investment years:', np.round(years, 1), np.round(ret * 100 - 100, 3), '%, final value:',
          np.round(ret * ic, 2))
    print('Average Yearly return rate: ', np.round((ret ** (1 / years) - 1) * 100, 3), '%')