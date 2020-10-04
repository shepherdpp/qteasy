from qteasy.core import *
from qteasy.operator import *

if __name__ == '__main__':
    cont = Context(moq=0)
    cont.reference_asset = '000300.SH'
    cont.reference_asset_type = 'I'
    cont.share_pool = '000300.SH'
    cont.asset_type = 'I'
    cont.output_count = 30
    cont.invest_start = '20020101'
    cont.parallel = True
    cont.print_log = True
    cont.moq = 0

    op = Operator(timing_types=['dma'],
                  selecting_types=['all'], ricon_types=['urgent'])
    op.set_parameter('s-0', pars=(2,), sample_freq='y')
    op.set_parameter('t-0', opt_tag=1, par_boes=[(10, 250), (10, 250), (10, 250)])
    op.set_parameter('r-0', opt_tag=0, par_boes=[(5, 14), (-0.2, -0.01)])

    op.set_blender('ls', 'combo')
    op.set_parameter(stg_id='t-0', pars=(96, 111, 64))
    op.set_parameter('r-0', pars=(8, -0.1443033))
    # cont.mode = 1
    # run(op, cont)

    print(f'============SEARCHING FOR DMA PARAMS==============\n'
          f'==================================================')
    cont.mode = 2
    cont.opti_method = 1
    cont.opti_method_sample_size = 50000
    cont.opti_method_step_size = 32
    cont.opti_method_init_step_size = 16
    cont.opti_method_min_step_size = 1
    cont.opti_method_incre_ratio = 2
    perfs_dma, pars_dma = run(op, cont)

    # TODO: Following codes are new, but not running well, should find out why
    # find out best performers for strategy macd

    print(f'==================SEARCHING FOR MACD PARAMS===================\n'
          f'==============================================================')
    op = Operator(timing_types=['macd'],
                  selecting_types=['all'], ricon_types=['urgent'])
    op.set_parameter('s-0', pars=(2,), sample_freq='y')
    op.set_parameter('t-0', opt_tag=1, par_boes=[(10, 250), (10, 250), (10, 250)])
    op.set_parameter('r-0', opt_tag=0, par_boes=[(5, 14), (-0.2, -0.01)])

    op.set_blender('ls', 'combo')
    op.set_parameter(stg_id='t-0', pars=(96, 111, 64))
    op.set_parameter('r-0', pars=(8, -0.1443033))

    cont.mode = 2
    perfs_macd, pars_macd = run(op, cont)

    # find out best performers for strategy trix
    print(f'==================SEARCHING FOR TRIX PARAMS===================\n'
          f'==============================================================')
    op = Operator(timing_types=['trix'],
                  selecting_types=['all'], ricon_types=['urgent'])
    op.set_parameter('s-0', pars=(2,), sample_freq='y')
    op.set_parameter('t-0', opt_tag=1, par_boes=[(5, 50), (10, 150)])
    op.set_parameter('r-0', opt_tag=0, par_boes=[(5, 14), (-0.2, -0.01)])

    op.set_blender('ls', 'combo')
    op.set_parameter(stg_id='t-0', pars=(96, 111))
    op.set_parameter('r-0', pars=(8, -0.1443033))

    cont.mode = 2
    perfs_trix, pars_trix = run(op, cont)

    # find out best performers for strategy crossline
    print(f'===============SEARCHING FOR CROSSLINE PARAMS=================\n'
          f'==============================================================')
    op = Operator(timing_types=['crossline'],
                  selecting_types=['all'], ricon_types=['urgent'])
    op.set_parameter('s-0', pars=(2,), sample_freq='y')
    op.set_parameter('t-0', opt_tag=1, par_boes=[(10, 250), (10, 250), (0.0, 10.0), ('buy', 'sell', 'none')])
    op.set_parameter('r-0', opt_tag=0, par_boes=[(5, 14), (-0.2, -0.01)])

    op.set_blender('ls', 'combo')
    op.set_parameter(stg_id='t-0', pars=(97, 124, 3.8286731572085966, 'buy'))
    op.set_parameter('r-0', pars=(8, -0.1443033))

    cont.mode = 2
    perfs_cl, pars_cl = run(op, cont)

    # find out best performance with all four strategies combined:
    print(f'===============SEARCHING FOR COMBINED PARAMS==================\n'
          f'==============================================================\n'
          f'parameter enums:\n'
          f'dma: \n{pars_dma}\n'
          f'macd:\n{pars_macd}')
    op = Operator(timing_types=['dma', 'macd', 'trix', 'crossline'],
                  selecting_types=['all'], ricon_types=['urgent'])
    op.set_parameter('s-0', pars=(2,), sample_freq='y')
    op.set_parameter('t-0', opt_tag=2, par_boes=pars_dma, par_types='enum')
    op.set_parameter('t-1', opt_tag=2, par_boes=pars_macd, par_types='enum')
    op.set_parameter('t-2', opt_tag=2, par_boes=pars_trix, par_types='enum')
    op.set_parameter('t-3', opt_tag=2, par_boes=pars_cl, par_types='enum')
    op.set_parameter('r-0', opt_tag=0, par_boes=[(5, 14), (-0.2, -0.01)])

    op.set_blender('ls', 'combo')
    op.set_parameter(stg_id='t-0', pars=(96, 111, 64))
    op.set_parameter(stg_id='t-1', pars=(96, 111, 64))
    op.set_parameter(stg_id='t-2', pars=(96, 111))
    op.set_parameter(stg_id='t-3', pars=(97, 124, 3.8286731572085966, 'buy'))
    op.set_parameter('r-0', pars=(8, -0.1443033))
    print(f'=========================================\n'
          f'op object\'s opt space par is: {op.opt_space_par}\n'
          f'op object\'s par boes and par types are:\n')

    cont.mode = 2
    cont.opti_method = 1
    cont.opti_method_step_size = 1
    run(op, cont)
