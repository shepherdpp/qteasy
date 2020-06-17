from qteasy.core import *
from qteasy.operator import *


class CustomRollingTiming(Rolling_Timing):
    """自定义celue"""

    def __init__(self, pars: tuple = None):
        """Crossline交叉线策略只有一个动态属性，其余属性均不可变"""
        super().__init__(pars=pars,
                         par_count=4,
                         par_types=['discr', 'discr', 'conti', 'enum'],
                         par_bounds_or_enums=[(10, 250), (10, 250), (0.0, 10.0), ('buy', 'sell', 'none')],
                         stg_name='CUSTOM ROLLING TIMING STRATEGY',
                         stg_text='Customized Rolling Timing Strategy for Testing',
                         data_types='close')
        print(f'=====================\n====================\n'
              f'custom strategy initialized, \npars: {self.pars}\npar_count:{self.par_count}\npar_types:'
              f'{self.par_types}')

    def _realize(self, hist_price, params):
        """crossline策略使用四个参数：
        s：短均线计算日期；l：长均线计算日期；m：均线边界宽度；hesitate：均线跨越类型"""
        s, l, m, hesitate = params
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可
        h = hist_price.T
        # 计算长短均线之间的距离
        diff = (sma(h[0], l) - sma(h[0], s))[-1]
        # 根据观望模式在不同的点位产生Long/short标记
        if hesitate == 'buy':
            m = -m
        elif hesitate == 'sell':
            pass
        else:  # hesitate == 'none'
            m = 0
        if diff < m:
            return 1
        else:
            return 0


if __name__ == '__main__':
    # TODO: TRIX 策略有问题
    custom_rolling = CustomRollingTiming()
    op = Operator(timing_types=['DMA', custom_rolling], selecting_types=['simple'], ricon_types=['urgent'])
    print('START TO SET SELECTING STRATEGY PARAMETERS\n=======================')
    op.set_parameter('s-0', pars=(2,), sample_freq='y')
    print('SET THE TIMING STRATEGY TO BE OPTIMIZABLE\n========================')
    op.set_parameter('t-0', opt_tag=1, par_boes=[(10, 250), (10, 250), (10, 250)])
    op.set_parameter('t-1', opt_tag=1, par_boes=[(10, 250), (10, 250), (0., 10.), ('buy', 'sell', 'none')])
    op.set_parameter('r-0', opt_tag=0, par_boes=[(5, 14), (-0.2, 0)])
    print('CREATE CONTEXT OBJECT\n=======================')
    cont = Context(moq=0)
    cont.reference_asset = '000300.SH'
    cont.reference_asset_type = 'I'
    # TODO: 当前tushare一次只能下载5000条数据，当股票的数量增加时，每只股票的历史数据就会减少，应该分批下载后再组合
    cont.share_pool = '000001.SZ'
    cont.asset_type = 'E'
    cont.output_count = 50
    cont.loop_period_start = '20040101'
    cont.moq = 1
    print(cont)
    print(f'TRANSACTION RATE OBJECT CREATED, RATE IS: \n==========================\n{cont.rate}')

    timing_pars1 = (128, 131, 36)
    timing_pars2 = {'000100': (77, 118, 144),
                    '000200': (75, 128, 138),
                    '000300': (73, 120, 143)}
    timing_pars3 = (98, 177, 158)
    timing_pars4 = (37, 44)
    timing_pars5 = (179, 166, 7.90, 'buy')
    print('START TO SET TIMING PARAMETERS TO STRATEGIES: \n===================')
    op.set_blender('timing', 'pos-1')
    op.set_parameter(stg_id='t-0', pars=timing_pars1)
    print(op.info())
    print('par_count is\n', op.timing[1].par_count)
    op.set_parameter(stg_id='t-1', pars=timing_pars5)
    # op.set_parameter(stg_id='t-2', pars=timing_pars4, opt_tag=1, par_boes=[(90, 100), (700, 100)])
    # op.set_parameter('t-3', pars=timing_pars1)
    print('START TO SET RICON PARAMETERS TO STRATEGIES:\n===================')
    op.set_parameter('r-0', pars=(6, -0.06))
    # op.info()
    # print('\nTime of creating operation list:')
    op.info()
    print(f'\n START QT RUNNING\n===========================\n')
    cont.parallel = True
    cont.mode = 1
    run(op, cont)
    cont.mode = 0
    run(op, cont)
    cont.mode = 2
    cont.opti_method = 1
    cont.opti_method_sample_size = 200
    cont.opti_method_step_size = 32
    cont.opti_method_init_step_size = 16
    cont.opti_method_min_step_size = 1
    cont.opti_method_incre_ratio = 2
    run(op, cont)
    # cont.mode = 3
    # run(op, cont)