from qteasy.core import *
import qteasy.history as hs
from qteasy.operator import *
import pandas as pd

if __name__ == '__main__':
    # TODO: bug: rand类型的选股模型在timing策略为simple的时候似乎不起作用，需要检查
    op = Operator(timing_types=['DMA'], selecting_types=['rand'], ricon_types=['none'])
    d = pd.read_csv('000300_I_N.txt', index_col='date')
    d.index = pd.to_datetime(d.index, format='%Y-%m-%d')
    d.drop(labels=['volume', 'amount'], axis=1, inplace=True)
    d = d[::-1]
    hp = hs.dataframe_to_hp(d,column_type='htype', shares='000300')
    # hp = hs.stack_dataframes([d, d, d], stack_along='shares', shares=['000100', '000200', '000300'])
    print('INFORMATION OF CREATED HISTORY PANEL: \n==========================')
    hp.info()
    print('START TO SET SELECTING STRATEGY PARAMETERS\n=======================')
    op.set_parameter('s-0', pars=(2, ), sample_freq='q')
    print('SET THE TIMING STRATEGY TO BE OPTIMIZABLE\n========================')
    op.set_parameter('t-0', opt_tag=1)
    print('CREATE CONTEXT OBJECT\n=======================')
    cont = Context(investment_amounts=[20000],
                   investment_dates=['2014-07-01'],
                   reference_data='000300',
                   moq=0)
    cont.share_pool = hp.shares
    cont.history_data = hp
    print(f'TRANSACTION RATE OBJECT CREATED, RATE IS: \n==========================\n{cont.rate}')

    timing_pars1 = (96, 144, 50)
    timing_pars2 = {'600037': (177, 248, 244),
                    '000005': (86, 198, 58)}
    timing_pars3 = (73, 120, 143)
    timing_pars4 = (37, 44)
    timing_pars5 = (62, 132, 10, 'buy')
    print('START TO SET TIMING PARAMETERS TO STRATEGIES: \n===================')
    op.set_blender('timing', 'pos-1')
    op.set_parameter('t-0', pars = timing_pars1)
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



