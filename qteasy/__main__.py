from qteasy.core import *
from qteasy.operator import *

if __name__ == '__main__':
    op = Operator(timing_types=['dma', 'macd', 'trix', 'crossline'],
                  selecting_types=['all'], ricon_types=['urgent'])
    print('START TO SET SELECTING STRATEGY PARAMETERS\n=======================')
    op.set_parameter('s-0', pars=(2,), sample_freq='y')
    # print('SET THE TIMING STRATEGY TO BE OPTIMIZABLE\n========================')
    # print('strategy count of operation object is:===================', op.strategy_count)
    op.set_parameter('t-0', opt_tag=1, par_boes=[(10, 250), (10, 250), (10, 250)])
    op.set_parameter('t-1', opt_tag=1, par_boes=[(10, 250), (10, 250), (10, 250)])
    op.set_parameter('t-2', opt_tag=1, par_boes=[(2, 50), (3, 150)])
    op.set_parameter('t-3', opt_tag=1, par_boes=[(10, 250), (10, 250), (0.0, 10.0), ('buy', 'sell', 'none')])
    op.set_parameter('r-0', opt_tag=1, par_boes=[(5, 14), (-0.2, -0.01)])
    # print('CREATE CONTEXT OBJECT\n=======================')
    cont = Context(moq=0)
    cont.reference_asset = '000300.SH'
    cont.reference_asset_type = 'I'
    cont.share_pool = '000300.SH'  # '000001.SZ, 000002.SZ, 000005.SZ, 000651.SZ, 601398.SH'
    cont.asset_type = 'I'
    cont.output_count = 100
    cont.invest_start = '20020101'
    cont.moq = 1
    # print(cont)
    # print(f'TRANSACTION RATE OBJECT CREATED, RATE IS: \n==========================\n{cont.rate}')

    timing_pars1 = (155, 108, 66)
    timing_pars2 = (162, 88, 137)
    timing_pars3 = (162, 88, 137)
    timing_pars4 = (10, 21)
    timing_pars5 = (44, 17, 3.00015022958923, 'buy')
    timing_par_dict = {'000100': (77, 118, 144),
                       '000200': (75, 128, 138),
                       '000300': (73, 120, 143)}
    print('START TO SET TIMING PARAMETERS TO STRATEGIES: \n===================')
    op.set_blender('ls', 'combo')
    op.set_parameter(stg_id='t-0', pars=timing_pars1)
    op.set_parameter(stg_id='t-1', pars=timing_pars3)
    op.set_parameter(stg_id='t-2', pars=timing_pars4)
    op.set_parameter(stg_id='t-3', pars=timing_pars5)
    print('START TO SET RICON PARAMETERS TO STRATEGIES:\n===================')
    op.set_parameter('r-0', pars=(14, -0.07630337840174323))
    print(f'\n START QT RUNNING\n===========================\n')
    cont.parallel = True
    cont.print_log = True
    cont.moq = 0
    cont.mode = 1
    run(op, cont)
    cont.mode = 0
    run(op, cont)
    cont.mode = 2
    cont.opti_method = 1
    cont.opti_method_sample_size = 300
    cont.opti_method_step_size = 32
    cont.opti_method_init_step_size = 16
    cont.opti_method_min_step_size = 1
    cont.opti_method_incre_ratio = 2
    run(op, cont)
    cont.visual = True
    cont.mode = 1
    run(op, cont)
    # cont.mode = 3
    # run(op, cont)