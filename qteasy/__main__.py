from qteasy.core import *
from qteasy.operator import *

if __name__ == '__main__':
    # TODO: TRIX 策略有问题
    op = Operator(timing_types=['DMA', 'MACD'], selecting_types=['simple'], ricon_types=['urgent'])
    print('START TO SET SELECTING STRATEGY PARAMETERS\n=======================')
    op.set_parameter('s-0', pars=(2,), sample_freq='y')
    print('SET THE TIMING STRATEGY TO BE OPTIMIZABLE\n========================')
    op.set_parameter('t-0', opt_tag=0, par_boes=[(10, 100), (150, 200), (100, 150)])
    op.set_parameter('t-1', opt_tag=1, par_boes=[(10, 100), (150, 200), (100, 150)])
    op.set_parameter('r-0', opt_tag=0, par_boes=[(5, 14), (-0.2, 0)])
    print('CREATE CONTEXT OBJECT\n=======================')
    cont = Context(moq=0)
    cont.reference_asset='000300.SH'
    cont.reference_asset_type = 'I'
    cont.share_pool = '000300.SH'
    cont.asset_type = 'I'
    cont.opti_method = 1
    cont.output_count = 50
    cont.loop_period_start = '20040101'
    cont.moq = 1
    print(cont)
    print(f'TRANSACTION RATE OBJECT CREATED, RATE IS: \n==========================\n{cont.rate}')

    timing_pars1 = (24, 160, 124)
    timing_pars2 = {'000100': (77, 118, 144),
                    '000200': (75, 128, 138),
                    '000300': (73, 120, 143)}
    timing_pars3 = (93, 157, 107)
    timing_pars4 = (37, 44)
    timing_pars5 = (62, 132, 10, 'buy')
    print('START TO SET TIMING PARAMETERS TO STRATEGIES: \n===================')
    op.set_blender('timing', 'pos-1')
    op.set_parameter(stg_id='t-0', pars=timing_pars1)
    op.set_parameter(stg_id='t-1', pars=timing_pars3)
    # op.set_parameter(stg_id='t-2', pars=timing_pars4, opt_tag=1, par_boes=[(90, 100), (700, 100)])
    # op.set_parameter('t-3', pars=timing_pars1)
    print('START TO SET RICON PARAMETERS TO STRATEGIES:\n===================')
    op.set_parameter('r-0', pars=(8, -0.11))
    # op.info()
    # print('\nTime of creating operation list:')
    op.info()
    print(f'\n START QT RUNNING\n===========================\n')
    cont.mode = 1
    run(op, cont)
    cont.mode = 0
    run(op, cont)
    cont.mode = 2
    run(op, cont)
    # cont.mode = 3
    # run(op, cont)
