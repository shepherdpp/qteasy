from qteasy.core import *
from qteasy.operator import *

if __name__ == '__main__':
    cont = Context(moq=0)
    cont.reference_asset = '000300.SH'
    cont.reference_asset_type = 'I'
    cont.share_pool = '000300.SH'
    cont.asset_type = 'I'
    cont.output_count = 100
    cont.invest_start = '20020101'

    op = Operator(timing_types=['dma'],
                  selecting_types=['all'], ricon_types=['urgent'])
    print('START TO SET SELECTING STRATEGY PARAMETERS\n=======================')
    op.set_parameter('s-0', pars=(2,), sample_freq='y')
    op.set_parameter('t-0', opt_tag=1, par_boes=[(10, 250), (10, 250), (10, 250)])
    op.set_parameter('r-0', opt_tag=0, par_boes=[(5, 14), (-0.2, -0.01)])


    op.set_blender('ls', 'combo')
    op.set_parameter(stg_id='t-0', pars=(155, 108, 66))
    op.set_parameter('r-0', pars=(8, -0.1443033))
    print(f'\n START QT RUNNING\n===========================\n')
    cont.parallel = True
    cont.print_log = True
    cont.moq = 0
    cont.mode = 1
    run(op, cont)
    cont.mode = 2
    cont.opti_method = 1
    cont.opti_method_sample_size = 30000
    cont.opti_method_step_size = 32
    cont.opti_method_init_step_size = 16
    cont.opti_method_min_step_size = 1
    cont.opti_method_incre_ratio = 2
    run(op, cont)

    # TODO: Following codes are new, but not running well, should find out why
    #
    # cont = Context(moq=0)
    # cont.reference_asset = '000300.SH'
    # cont.reference_asset_type = 'I'
    # cont.share_pool = '000300.SH'  # '000001.SZ, 000002.SZ, 000005.SZ, 000651.SZ, 601398.SH'
    # cont.asset_type = 'I'
    # cont.output_count = 100
    # cont.invest_start = '20020101'
    # cont.moq = 0
    # cont.parallel = True
    # cont.print_log = True
    #
    # # find out best performers for strategy dma
    # op = Operator(timing_types=['dma'], selecting_types=['all'], ricon_types=['urgent'])
    # op.set_blender('ls', 'combo')
    # op.set_parameter('s-0', pars=(2,), sample_freq='y')
    # op.set_parameter('r-0', opt_tag=1, pars=(2, -0.3), par_boes=[(5, 14), (-0.2, -0.01)])
    # op.set_parameter('t-0', opt_tag=1, par_boes=[(10, 250), (10, 250), (10, 150)], pars=(142, 184, 18))
    #
    # print(op.info())
    # cont.mode = 1
    # run(op, cont)
    # cont.mode = 2
    # run(op, cont)

    # find out best performers for strategy macd
    # op = Operator(timing_types=['macd'], selecting_types=['all'], ricon_types=['urgent'])
    # op.set_blender('ls', 'combo')
    # op.set_parameter('s-0', opt_tag=0, pars=(2,), sample_freq='y')
    # op.set_parameter('r-0', opt_tag=0, pars=(2, -0.3))
    # op.set_parameter('t-0', opt_tag=1, par_boes=[(10, 250), (10, 250), (10, 250)], pars=(111, 175, 59))
    #
    # cont.mode = 2
    # cont.opti_method = 1
    # cont.opti_method_sample_size = 300
    # cont.opti_method_step_size = 32
    # cont.opti_method_init_step_size = 16
    # cont.opti_method_min_step_size = 1
    # cont.opti_method_incre_ratio = 2
    # pars_macd, perfs_macd = run(op, cont)
    #
    # # find out best performance for strategy trix
    # op = Operator(timing_types=['trix'], selecting_types=['all'], ricon_types=['ricon_none'])
    # op.set_parameter('t-0', opt_tag=1, par_boes=[(2, 50), (10, 150)], pars=(45, 143))
    #
    # cont.mode = 2
    # pars_trix, perfs_trix = run(op, cont)
    #
    # # find out best performance for strategy crossline
    # op = Operator(timing_types=['crossline'], selecting_types=['all'], ricon_types=['ricon_none'])
    # op.set_parameter('t-0', opt_tag=1, par_boes=[(2, 50), (10, 150)], pars=(97, 124, 3.8286731572085966, 'buy'))
    #
    # cont.mode = 2
    # pars_crossline, perfs_crossline = run(op, cont)
    #
    # # find out best performance with all four strategies combined:
    # op = Operator(timing_types=['dma', 'macd', 'trix','crossline'],
    #               selecting_types=['all'], ricon_types=['urgeng'])
    # op.set_parameter('t-0', opt_tag=1, par_boes=pars_dma, pars=(142, 184, 18))
    # op.set_parameter('t-1', opt_tag=1, par_boes=pars_macd, pars=(111, 175, 59))
    # op.set_parameter('t-2', opt_tag=1, par_boes=pars_trix, pars=(45, 143))
    # op.set_parameter('t-3', opt_tag=1, par_boes=pars_macd, pars=(97, 124, 3.8286731572085966, 'buy'))
    #
    # cont.mode = 2
    # pars_combo, perfs_combo = run(op, cont)
    #
    # # set the best parameter for ricon strategy
    # op.set_parameter('t-0', opt_tag=0, par_boes=pars_dma, pars=pars_dma[-1])
    # op.set_parameter('t-1', opt_tag=0, par_boes=pars_macd, pars=pars_macd[-1])
    # op.set_parameter('t-2', opt_tag=0, par_boes=pars_trix, pars=pars_trix[-1])
    # op.set_parameter('t-3', opt_tag=0, par_boes=pars_macd, pars=pars_crossline[-1])
    # op.set_parameter('r-0', opt_tag=1, par_boes=[(2, 20), (-0.3, -0.001)], pars=(2, -0.3))
    #
    # cont.mode = 2
    # pars_ricon, perfs_ricon = run(op, cont)
    #
    # cont.mode = 1
    # run(op, cont)
