# coding=utf-8
class Optimizer():
    '参数优化器类，在指定的历史区间上使用多种算法，在指定的参数空间中搜索最佳参数组合，使得特定的评价函数值'
    '最大化，并对搜索到的最佳参数进行管理， Looper对象用于根据操作清单模拟交易并输出交易结果'
    # 类属性：
    # optization period 优化区间：指优化器尝试进行参数优化基于的历史区间，优化器可以利用优化区间内的历史数据
    # 优化参数，同时在测试区间对参数进行评价，以便对搜索到的参数进行独立验证
    # 优化区间类型：1: 参数优化区间与测试区间相同；2:优化区间与测试区间不同；3:重叠设置一系列优化区间与测试区间
    opt_period_type_dict = {1: 'simple', 2: 'standard', 3: 'convolutional'}
    # 目标函数：评价一组参数的效用的函数，定义使得该函数值最大化的一组参数为最优
    # 可以定义一系列不同的效用函数，1:投资终值；2:收益率；3:夏普率；4:Alpha比率。。。
    target_func_type_dict = {1: 'single', 2: 'compound'}
    target_func_dict = {1: 'FV', 2: 'RoI', 3: 'Sharp', 4: 'Alpha'}
    # 最佳参数存储在一个数据库结构或专用文件夹结构中，文件夹的位置定义在strategy_folder属性中
    strategy_folder = 'strategies/'

    def __init__(self, superior, operator=None, history=None):
        '''Optimizer对象包含三个子对象，分别是Looper、Operator和History对象

        输入：
            参数 superior：上层对象
            参数 Operator 对象用于应用策略生成买卖操作清单
            参数 History对象用于生成和保存历史价格数据
        输出：=====
            无
        '''
        import datetime
        # 对象属性初始化：
        self.__superior = superior  # 上层对象
        self.__looper = Looper(self)  # 回测器对象
        if operator is None:
            self.__operator = Operation()  # 一个operator对象
        else:
            self.__operator = operator
        if history is None:
            self.__history = History()  # 一个history对象
        else:
            self.__history = history
        today = datetime.datetime.today().date()
        self.shares = []  # 优化参数所针对的投资产品
        self.opt_period_start = today - datetime.timedelta(3650)  # 优化历史区间开始日
        self.opt_period_end = today - datetime.timedelta(365)  # 优化历史区间结束日
        self.opt_period_freq = 'd'  # 优化历史区间采样频率
        self.opt_period_interval = '1Y'  # 历史区间重复间隔（仅用于优化区间类型为3时）
        self.opt_period_cycles = 5  # 历史区间重复次数（仅用于优化区间类型为3时）
        self.test_period_start = today - datetime.timedelta(365)  # 测试区间开始日
        self.test_period_end = today  # 测试区间结束日（测试区间的采样频率与优化区间相同）
        self.opt_period_type = 2  # 'standard'
        self.t_func_type = 1  # 'single'
        self.t_func = 'FV'  # 评价函数
        self.compound_method_expr = '( FV + Sharp )'  # 复合评价函数表达式，使用表达式解析模块解析并计算
        self.cycle_convolution_type = 'average'  # 当使用重叠区间优化参数时，各个区间评价函数值的组合方法
        self.opti_method = 'standard'
        pass

    @property
    def superior(self):
        return self.__superior

    @property
    def looper(self):
        return self.__looper

    @property
    def operator(self):
        return self.__operator

    @property
    def history(self):
        return self.__history

    # 类方法:
    def info(self):
        '''打印Optimizer类的关键属性及其子对象的关键属性'''
        print ('Optimizer class information:')
        print ('operator object information: /n', self.operator.info())
        print ('shares:', self.shares)
        print ('optimizing period starts', self.opt_period_start, 'ends', self.opt_period_end)

    def start(self, how=0, output_count=50, keep_largest_perf=True, hist=None, *args, **kwargs):
        '''开始优化，Optimizer类的主要动作调用入口函数

           根据所需要优化的参数空间类型不同，所选择的优化算法不同，调用不同的优化函数完成优化并返回输出结果

        输入：
            参数 how, int，参数评价方法
            参数 output_count，int，优化器输出的结果数量
            参数 keep_largest_perf，bool，True表示寻找评价得分最高的参数，False表示寻找评价得分最低的参数
            其他参数
        输出：=====
            暂无，需完善
        '''
        # 确认所有的基本参数设置正确，否则打印错误信息，中止优化

        # 分析op对象，确定最大化的优化参数空间

        # 如果明确指定了参数空间：
        # 将给定的参数空间与最大化优化参数空间比较，对不需要优化的参数进行空间纬度压缩
        # 否则：
        # 使用最大化优化参数空间进行优化

        # 判断所选择的优化算法是否适用于参数空间，如否，打印错误信息并中止优化

        # 根据基本参数设置基本变量，如历史数据、op对象、lpr对象等
        shares = self.shares
        if hist is None:
            start = self.opt_period_start
            end = self.opt_period_end
            freq = self.opt_period_freq
            hist = self.history.extract(shares, price_type='close',
                                        start=start, end=end,
                                        interval=freq)
        else:  # TODO, operator start shall be improved!!
            assert type(hist) is pd.DataFrame, 'historical price DataFrame shall be passed as parameter!'
            start = hist.index[0]
            end = hist.index[-1]
            freq = 'd'
        op = self.operator
        lpr = self.looper
        # 以下是调试用代码
        print ('shares involved in optimization:', shares)
        print ('Historical period of optimization starts:', start)
        print ('Historical period of optimization endd:', end)
        print ('Historical data frequency:', freq)
        print ('Starts optimization')

        # 根据所选择的优化算法进行优化并输出结果
        # 优化方法可以做成一个简单工厂模式，此段代码应该重构并简化
        if how == 0:  # 穷举法

            pars, perfs = self.__search_exhaustive(hist=hist, op=op, lpr=lpr,
                                                   output_count=output_count, keep_largest_perf=True,
                                                   *args, **kwargs)
        elif how == 1:  # Montecarlo蒙特卡洛方法

            pars, perfs = self.__search_MonteCarlo(hist=hist, op=op, lpr=lpr,
                                                   output_count=output_count, keep_largest_perf=True,
                                                   *args, **kwargs)
        elif how == 2:  # 递进步长法

            pars, perfs = self.__search_Incremental(hist=hist, op=op, lpr=lpr,
                                                    output_count=output_count, keep_largest_perf=True,
                                                    *args, **kwargs)
        elif how == 3:  # 遗传算法
            pass
        pass

    # creation of historical data
    def __load_history(self):
        '''根据History子对象的属性，生成并调用History子对象的历史数据清单'''
        self.__hist = self.history.extract()
        pass

    # creation of spaces
    def __space_around_centre(self, space, centre, radius, ignore_enums=True):
        '在给定的参数空间中指定一个参数点，并且创建一个以该点为中心且包含于给定参数空间的子空间'
        '如果参数空间中包含枚举类型维度，可以予以忽略或其他操作'
        return space.from_point(point=centre, distance=radius, ignore_enums=ignore_enums)

    def __search_exhaustive(self, hist, op, lpr, output_count, keep_largest_perf, step_size=1):
        ''' 最优参数搜索算法1: 穷举法或间隔搜索法

            逐个遍历整个参数空间（仅当空间为离散空间时）的所有点并逐一测试，或者使用某个固定的
            “间隔”从空间中逐个取出所有的点（不管离散空间还是连续空间均适用）并逐一测试，
            寻找使得评价函数的值最大的一组或多组参数

        输入：
            参数 hist，object，历史数据，优化器的整个优化过程在历史数据上完成
            参数 op，object，交易信号生成器对象
            参数 lpr，object，交易信号回测器对象
            参数 output_count，int，输出数量，优化器寻找的最佳参数的数量
            参数 keep_largest_perf，bool，True寻找评价分数最高的参数，False寻找评价分数最低的参数
            参数 step_size，int或list，搜索参数，搜索步长，在参数空间中提取参数的间隔，如果是int型，则在空间的每一个轴上
                取同样的步长，如果是list型，则取list中的数字分别作为每个轴的步长
        输出：=====tuple对象，包含两个变量
            pool.pars 作为结果输出的参数组
            pool.perfs 输出的参数组的评价分数
        '''

        pool = Pool(output_count)  # 用于存储中间结果或最终结果的参数池对象
        s_range, s_type = op.get_opt_space_par()
        space = Space(s_range, s_type)  # 生成参数空间

        # 使用extract从参数空间中提取所有的点，并打包为iterator对象进行循环
        i = 0
        it, total = space.extract(step_size)
        # 调试代码
        print ('Result pool has been created, capacity of result pool: ', pool.capacity)
        print ('Searching Space has been created: ')
        space.info()
        print ('Number of points to be checked: ', total)
        print ('Searching Starts...')

        for par in it:
            op.set_opt_par(par)  # 设置Operator子对象的当前择时Timing参数
            # 调试代码
            # print('Optimization, created par for op:', par)
            # 使用Operator.create()生成交易清单，并传入Looper.apply_loop()生成模拟交易记录
            looped_val = lper.apply_loop(op_list=op.create(hist),
                                         history_list=hist, init_cash=100000,
                                         visual=False, price_visual=False)
            # 使用Optimizer的eval()函数对模拟交易记录进行评价并得到评价结果
            # 交易结果评价的方法由method参数指定，评价函数的输出为一个实数
            perf = self.__eval(looped_val, method='fv')
            # 将当前参数以及评价结果成对压入参数池中，并去掉最差的结果
            # 至于去掉的是评价函数最大值还是最小值，由keep_largest_perf参数确定
            # keep_largest_perf为True则去掉perf最小的参数组合，否则去掉最大的组合
            pool.in_pool(par, perf)
            # 调试代码
            i += 1.
            if i % 10 == 0:
                print('current result:', np.round(i / total * 100, 3), '%', end = '\r')

                pool.cut(keep_largest_perf)
                print ('Searching finished, best results:', pool.perfs)
                print ('best parameters:', pool.pars)
                return pool.pars, pool.perfs

            def __search_MonteCarlo(self, hist, op, lpr, output_count, keep_largest_perf, point_count=50):
                ''' 最优参数搜索算法2: 蒙特卡洛法

                从待搜索空间中随机抽取大量的均匀分布的参数点并逐个测试，寻找评价函数值最优的多个参数组合
                随机抽取的参数点的数量为point_count, 输出结果的数量为output_count

            输入：
                参数 hist，object，历史数据，优化器的整个优化过程在历史数据上完成
                参数 op，object，交易信号生成器对象
                参数 lpr，object，交易信号回测器对象
                参数 output_count，int，输出数量，优化器寻找的最佳参数的数量
                参数 keep_largest_perf，bool，True寻找评价分数最高的参数，False寻找评价分数最低的参数
                参数 point_count，int或list，搜索参数，提取数量，如果是int型，则在空间的每一个轴上
                    取同样多的随机值，如果是list型，则取list中的数字分别作为每个轴随机值提取数量目标
            输出：=====tuple对象，包含两个变量
                pool.pars 作为结果输出的参数组
                pool.perfs 输出的参数组的评价分数
            '''
                pool = Pool(output_count)  # 用于存储中间结果或最终结果的参数池对象
                s_range, s_type = op.get_opt_space_par()
                space = Space(s_range, s_type)  # 生成参数空间
                # 使用随机方法从参数空间中取出point_count个点，并打包为iterator对象，后面的操作与穷举法一致
                i = 0
                it, total = space.extract(point_count, how='rand')
                # 调试代码
                print ('Result pool has been created, capacity of result pool: ', pool.capacity)
                print ('Searching Space has been created: ')
                space.info()
                print ('Number of points to be checked:', total)
                print ('Searching Starts...')

                for par in it:
                    op.set_opt_par(par)  # 设置timing参数
                    # 生成交易清单并进行模拟交易生成交易记录
                    looped_val = lper.apply_loop(op_list=op.create(hist),
                                                 history_list=hist, init_cash=100000,
                                                 visual=False, price_visual=False)
                    # 使用评价函数计算该组参数模拟交易的评价值
                    perf = self.__eval(looped_val, method='fv')
                    # 将参数和评价值传入pool对象并过滤掉最差的结果
                    pool.in_pool(par, perf)
                    # 调试代码
                    i += 1.0
                    print ('current result:', np.round(i / total * 100, 3), '%', end = '\r')
                    pool.cut(keep_largest_perf)
                    print ('Searching finished, best results:', pool.perfs)
                    print ('best parameters:', pool.pars)
                    return pool.pars, pool.perfs

                def __search_Incremental(self, hist, op, lpr, output_count, keep_largest_perf, init_step=16,
                                         inc_step=2, min_step=1):
                    ''' 最优参数搜索算法3: 递进搜索法

                    该搜索方法的基础还是间隔搜索法，首先通过较大的搜索步长确定可能出现最优参数的区域，然后逐步
                    缩小步长并在可能出现最优参数的区域进行“精细搜索”，最终锁定可能的最优参数
                    与确定步长的搜索方法和蒙特卡洛方法相比，这种方法能够极大地提升搜索速度，缩短搜索时间，但是
                    可能无法找到全局最优参数。同时，这种方法需要参数的评价函数值大致连续

                输入：
                    参数 hist，object，历史数据，优化器的整个优化过程在历史数据上完成
                    参数 op，object，交易信号生成器对象
                    参数 lpr，object，交易信号回测器对象
                    参数 output_count，int，输出数量，优化器寻找的最佳参数的数量
                    参数 keep_largest_perf，bool，True寻找评价分数最高的参数，False寻找评价分数最低的参数
                    参数 init_step，int，初始步长，默认值为16
                    参数 inc_step，float，递进系数，每次重新搜索时，新的步长缩小的倍数
                    参数 min_step，int，终止步长，当搜索步长最小达到min_step时停止搜索
                输出：=====tuple对象，包含两个变量
                    pool.pars 作为结果输出的参数组
                    pool.perfs 输出的参数组的评价分数

                '''
                    pool = Pool(output_count)  # 用于存储中间结果或最终结果的参数池对象
                    s_range, s_type = op.get_opt_space_par()
                    spaces = []  # 子空间列表，用于存储中间结果邻域子空间，邻域子空间数量与pool中的元素个数相同
                    spaces.append(Space(s_range, s_type))  # 将整个空间作为第一个子空间对象存储起来
                    step_size = init_step  # 设定初始搜索步长
                    # 调试代码
                    print ('Result pool has been created, capacity of result pool: ', pool.capacity)
                    print ('Searching Space has been created: ', spaces)
                    print ('Searching Starts...')

                    while step_size >= min_step:  # 从初始搜索步长开始搜索，一回合后缩短步长，直到步长小于min_step参数
                        i = 0
                        while len(spaces) > 0:
                            space = spaces.pop()
                            # 逐个弹出子空间列表中的子空间，用当前步长在其中搜索最佳参数，所有子空间的最佳参数全部进入pool并筛选最佳参数集合
                            # 调试代码
                            it, total = space.extract(step_size, how='interval')
                            for par in it:
                                # 以下所有函数都是循环内函数，需要进行提速优化
                                # 以下所有函数在几种优化算法中是相同的，因此可以考虑简化
                                op.set_opt_par(par)  # 设置择时参数
                                # 声称交易清淡病进行模拟交易生成交易记录
                                looped_val = lper.apply_loop(op_list=op.create(hist),
                                                             history_list=hist, init_cash=100000,
                                                             visual=False, price_visual=False)
                                # 使用评价函数计算参数模拟交易的评价值
                                perf = self.__eval(looped_val, method='fv')
                                pool.in_pool(par, perf)
                                i += 1.
                                print (
                                'current result:', np.round(i / (total * output_count) * 100, 5), '%', end = '\r')
                                pool.cut(keep_largest_perf)
                                print ('Completed one round, creating new space set')
                                # 完成一轮搜索后，检查pool中留存的所有点，并生成由所有点的邻域组成的子空间集合
                                for item in pool.pars:
                                    spaces.append(space.from_point(point=item, distance=step_size))
                                # 刷新搜索步长
                                step_size = step_size // inc_step
                                print ('new spaces created, start next round with new step size', step_size)
                            print ('Searching finished, best results:', pool.perfs)
                            print ('best parameters:', pool.pars)
                            return pool.pars, pool.perfs

                        def __search_ga(self, hist, op, lpr, output_count, keep_largest_perf):
                            ''' 最优参数搜索算法4: 遗传算法
                        遗传算法适用于在超大的参数空间内搜索全局最优或近似全局最优解，而它的计算量又处于可接受的范围内

                        遗传算法借鉴了生物的遗传迭代过程，首先在参数空间中随机选取一定数量的参数点，将这批参数点称为
                        “种群”。随后在这一种群的基础上进行迭代计算。在每一次迭代（称为一次繁殖）前，根据种群中每个个体
                        的评价函数值，确定每个个体生存或死亡的几率，规律是若个体的评价函数值越接近最优值，则其生存的几率
                        越大，繁殖后代的几率也越大，反之则越小。确定生死及繁殖的几率后，根据生死几率选择一定数量的个体
                        让其死亡，而从剩下的（幸存）的个体中根据繁殖几率挑选几率最高的个体进行杂交并繁殖下一代个体，
                        同时在繁殖的过程中引入随机的基因变异生成新的个体。最终使种群的数量恢复到初始值。这样就完成
                        一次种群的迭代。重复上面过程数千乃至数万代直到种群中出现希望得到的最优或近似最优解为止

                    输入：
                        参数 hist，object，历史数据，优化器的整个优化过程在历史数据上完成
                        参数 op，object，交易信号生成器对象
                        参数 lpr，object，交易信号回测器对象
                        参数 output_count，int，输出数量，优化器寻找的最佳参数的数量
                        参数 keep_largest_perf，bool，True寻找评价分数最高的参数，False寻找评价分数最低的参数
                    输出：=====tuple对象，包含两个变量
                        pool.pars 作为结果输出的参数组
                        pool.perfs 输出的参数组的评价分数

                        '''
                            pool = Pool()
                            return pool.pars, pool.perfs

                        # 评价方法:
                        def __eval(self, looped_val, method):
                            '''评价函数，对回测器生成的交易模拟记录进行评价，包含不同的评价方法。

                    输入：
                        参数 looped_val，ndarray，回测器生成输出的交易模拟记录
                        参数 method，int，交易记录评价方法
                    输出：=====
                        调用不同评价函数的返回值
                    '''
                            if method.upper() == 'FV':
                                return self.__eval_FV(looped_val)
                            elif method.upper() == 'ROI':
                                return self.__eval_roi(looped_val)
                            elif method.upper() == 'SHARP':
                                return self.__eval_sharp(looped_val)
                            elif method.upper() == 'ALPHA':
                                return self.__eval_alpha(looped_val)

                        def __eval_FV(self, looped_val):
                            '''评价函数 Future Value 终值评价

                    '投资模拟期最后一个交易日的资产总值

                    输入：
                        参数 looped_val，ndarray，回测器生成输出的交易模拟记录
                    输出：=====
                        perf：float，应用该评价方法对回测模拟结果的评价分数

                    '''
                            if not looped_val.empty:
                                # 调试代码
                                # print looped_val.head()
                                perf = looped_val['value'][-1]
                                return perf
                            else:
                                return -np.inf

                        def __eval_roi(self, looped_val):
                            '''评价函数 RoI 收益率'

                    '投资模拟期间资产投资年化收益率

                    输入：
                        参数 looped_val，ndarray，回测器生成输出的交易模拟记录
                    输出：=====
                        perf：float，应用该评价方法对回测模拟结果的评价分数

                    '''
                            return perf

                        def __eval_sharp(self, looped_val):
                            return perf

                        def __eval_alpha(self, looped_val):
                            return perf

                    class Pool():
                        '''结果池类，用于保存限定数量的中间结果，当压入的结果数量超过最大值时，去掉perf最差的结果.

                '最初的算法是在每次新元素入池的时候都进行排序并去掉最差结果，这样要求每次都在结果池深度范围内进行排序'
                '第一步的改进是记录结果池中最差结果，新元素入池之前与最差结果比较，只有优于最差结果的才入池，避免了部分情况下的排序'
                '新算法在结果入池的循环内函数中避免了耗时的排序算法，将排序和修剪不合格数据的工作放到单独的cut函数中进行，这样只进行一次排序'
                '新算法将一百万次1000深度级别的排序简化为一次百万级别排序，实测能提速一半左右'
                '即使在结果池很小，总数据量很大的情况下，循环排序的速度也慢于单次排序修剪'''

                        # result pool operation:
                        def __init__(self, capacity):
                            'result pool stores all intermediate or final result of searching, the points'
                            self.__capacity = capacity  # 池中最多可以放入的结果数量
                            self.__pool = []  # 用于存放中间结果
                            self.__perfs = []  # 用于存放每个中间结果的评价分数，老算法仍然使用列表对象

                        @property
                        def pars(self):
                            return self.__pool  # 只读属性，所有池中参数

                        @property
                        def perfs(self):
                            return self.__perfs  # 只读属性，所有池中参数的评价分

                        @property
                        def capacity(self):
                            return self.__capacity

                        def in_pool(self, item, perf):
                            '''将新的结果压入池中

                    输入：
                        参数 item，object，需要放入结果池的参数对象
                        参数 perf，float，放入结果池的参数评价分数
                    输出：=====
                        无
                    '''
                            self.__pool.append(item)  # 新元素入池
                            self.__perfs.append(perf)  # 新元素评价分记录

                        def cut(self, keep_largest=True):
                            '''将pool内的结果排序并剪切到capacity要求的大小

                    直接对self对象进行操作，排序并删除不需要的结果

                    输入：
                        参数 keep_largest， bool，True保留评价分数最高的结果，False保留评价分数最低的结果
                    输出：=====
                        无
                    '''
                            poo = self.__pool  # 所有池中元素
                            per = self.__perfs  # 所有池中元素的评价分
                            cap = self.__capacity
                            if keep_largest:
                                arr = np.array(per).argsort()[-cap:]
                            else:
                                arr = np.array(per).argsort()[:cap]
                            poo2 = []
                            per2 = []
                            for i in arr:
                                poo2.append(poo[i])
                                per2.append(per[i])
                            self.__pool = poo2
                            self.__perfs = per2


class Space():
    '''定义一个参数空间，一个参数空间包含一个或多个Axis对象，存储在axes列表中

    参数空间类用于生成并管理一个参数空间，从参数空间中根据一定的要求提取出一系列的参数点并组装成迭代器供优化器调用
    参数空间包含一个或多个轴，每个轴代表参数空间的一个维度，从每个轴上取出一个数值作为参数空间中某个点的坐标，而这个坐标
    就代表空间中的一个参数组合
    参数空间支持三种不同的轴，整数轴、浮点轴，这两种都是数值型的轴，还有另一种枚举轴，包含不同对象的枚举，同样可以作为参数
    空间的一个维度独立存在，与数值轴的操作方式相同
    数值轴的定义方式为上下界定义，枚举轴的定义方式为枚举定义，数值轴的取值范围为上下界之间的合法数值，而枚举轴的取值为枚举
    列表中的值
    '''

    def __init__(self, pars, types=[]):
        '''参数空间对象初始化，根据输入的参数生成一个空间

        输入：
            参数 pars，int、float或list,需要建立参数空间的初始信息，通常为一个数值轴的上下界，如果给出了types，按照
                types中的类型字符串创建不同的轴，如果没有给出types，系统根据不同的输入类型动态生成的空间类型分别如下：
                    pars为float，自动生成上下界为(0, pars)的浮点型数值轴，
                    pars为int，自动生成上下界为(0, pars)的整形数值轴
                    pars为list，根据list的元素种类和数量生成不同类型轴：
                        list元素只有两个且元素类型为int或float：生成上下界为(pars[0], pars[1])的浮点型数值
                        轴或整形数值轴
                        list元素不是两个，或list元素类型不是int或float：生成枚举轴，轴的元素包含par中的元素
            参数 types，list，默认为空，生成的空间每个轴的类型，如果给出types，应该包含每个轴的类型字符串：
                'discr': 生成整数型轴
                'conti': 生成浮点数值轴
                'enum': 生成枚举轴
        输出：=====
            无
        '''
        self.__axes = []
        # 处理输入，将输入处理为列表，并补齐与dim不足的部分
        pars = list(pars)
        par_dim = len(pars)
        types = self.__input_to_list(types, par_dim, [None])
        # 调试代码：
        # print('par dim:', par_dim)
        # print('pars and types:', pars, types)
        # 逐一生成Axis对象并放入axes列表中
        for i in range(par_dim):
            # print('appending', i+1, '-th par', pars[i],'in type:', types[i])
            self.__axes.append(Axis(pars[i], types[i]))

    @property
    def dim(self):  # 空间的维度
        return len(self.__axes)

    @property
    def types(self):  # List of types of axis of the space
        types = []
        if self.dim > 0:
            for i in range(self.dim):
                types.append(self.__axes[i].axis_type)
        return types

    @property
    def boes(self):  # List of bounds of axis of the space
        boes = []
        if self.dim > 0:
            for i in range(self.dim):
                boes.append(self.__axes[i].axis_boe)
        return boes

    @property
    def shape(self):
        # 输出空间的维度大小，输出形式为元组，每个元素代表对应维度的元素个数
        s = []
        for axis in self.__axes:
            s.append(axis.count)
        return tuple(s)

    @property
    def size(self):
        '''输出空间的尺度，输出每个维度的跨度之乘积'''
        s = []
        for axis in self.__axes:
            s.append(axis.size)
        return np.product(s)

    # Methods:
    def __input_to_list(self, pars, dim, padder):
        '''将输入的参数转化为List，同时确保输出的List对象中元素的数量至少为dim，不足dim的用padder补足

        输入：
            参数 pars，需要转化为list对象的输出对象
            参数 dim，需要生成的目标list的元素数量
            参数 padder，当元素数量不足的时候用来补充的元素
        输出：=====
            pars, list 转化好的元素清单
        '''
        if (type(pars) == str) or (type(pars) == int):  # 处理字符串类型的输入
            # print 'type of types', type(pars)
            pars = [pars] * dim
        else:
            pars = list(pars)  # 正常处理，输入转化为列表类型
        par_dim = len(pars)
        # 当给出的两个输入参数长度不一致时，用padder补齐type输入，或者忽略多余的部分
        if par_dim < dim: pars.extend(padder * (dim - par_dim))
        return pars

    def info(self):
        '''打印空间的各项信息'''
        if self.dim > 0:
            print ('Space is not empty!')
            print ('dimension:', self.dim)
            print ('types:', self.types)
            print ('the bounds or enums of space', self.boes)
            print ('shape of space:', self.shape)
            print ('size of space:', self.size)
        else:
            print ('Space is empty!')

    def extract(self, interval_or_qty=1, how='interval'):
        '''从空间中提取出一系列的点，并且把所有的点以迭代器对象的形式返回供迭代

        输入
            参数 interval_or_qty，int。从空间中每个轴上需要提取数据的步长或坐标数量
            参数 how, str, 有两个合法参数：
                'interval',以间隔步长的方式提取坐标，这时候interval_or_qty代表步长
                'rand', 以随机方式提取坐标，这时候interval_or_qty代表提取数量
        输出，tuple，包含两个数据
            iter，迭代器数据，打包好的所有需要被提取的点的集合
            total，int，迭代器输出的点的数量
        '''
        interval_or_qty = self.__input_to_list(pars=interval_or_qty,
                                               dim=self.dim,
                                               padder=[1])
        how = self.__input_to_list(pars=how, dim=self.dim, padder=['rand'])
        axis_ranges = []
        i = 0
        total = 1
        for axis in self.__axes:  # 分别从各个Axis中提取相应的坐标
            axis_ranges.append(axis.extract(interval_or_qty[i], how[i]))
            total *= len(axis_ranges[i])
            i += 1
        if how == 'interval':
            return itertools.product(*axis_ranges), total  # 使用迭代器工具将所有的坐标乘积打包为点集
        elif how == 'rand':
            return itertools.zip(*axis_ranges), total  # 使用迭代器工具将所有点组合打包为点集

    def from_point(self, point, distance, ignore_enums=True):
        '''在已知空间中以一个点为中心点生成一个字空间

        输入：
            参数 point，object，已知参数空间中的一个参数点
            参数 distance， int或float，需要生成的新的子空间的数轴半径
            参数 ignore_enums，bool，True忽略enum型轴，生成的子空间包含枚举型轴的全部元素，False生成的子空间
                包含enum轴的部分元素
        输出：=====

        '''
        if ignore_enums == True: pass
        assert self.dim > 0, 'original space should not be empty!'
        pars = []
        for i in range(self.dim):
            if self.types[i] != 'enum':
                space_lbound = self.boes[i][0]
                space_ubound = self.boes[i][1]
                lbound = max((point[i] - distance), space_lbound)
                ubound = min((point[i] + distance), space_ubound)
                pars.append((lbound, ubound))
            else:
                pars.append(self.boes[i])
        return Space(pars, self.types)

    def expand(self, bounds_or_enum, typ=None):
        # expand one more dimension of the space
        pass

    def squeez(self):
        # reduce one dimension of the space
        pass

class Axis():
    '数轴对象，空间对象的一个组成部分，代表空间对象的一个维度'

    def __init__(self, bounds_or_enum, typ=None):
        import numpy as np
        self.__type = None  # 数轴类型
        self.__lbound = None  # 空间在数轴上的下界
        self.__ubound = None  # 空间在数轴上的上届
        self.__enum_val = None  # 当数轴类型为“枚举”型时，储存改数轴上所有可用值
        # 将输入的上下界或枚举转化为列表，当输入类型为一个元素时，生成一个空列表并添加该元素
        boe = list(bounds_or_enum)
        length = len(boe)  # 列表元素个数
        # 调试代码
        # print('in Axis: boe recieved, and its length:', boe, length, 'type of boe:', typ)
        if typ is None:
            # 当typ为空时，需要根据输入数据的类型猜测typ
            if length <= 2:  # list长度小于等于2，根据数据类型取上下界，int产生离散，float产生连续
                if type(boe[0]) == int:
                    typ = 'discr'
                elif type(boe[0]) == float:
                    typ = 'conti'
                else:  # 输入数据类型不是数字时，处理为枚举类型
                    typ = 'enum'
            else:  # list长度为其余值时，全部处理为enum数据
                typ = 'enum'
        elif typ != 'enum' and typ != 'discr' and typ != 'conti':
            typ = 'enum'  # 当发现typ为异常字符串时，修改typ为enum类型
        # 调试代码
        # print('in Axis, after infering typ, the typ is:', typ)
        # 开始根据typ的值生成具体的Axis
        if typ == 'enum':  # 创建一个枚举数轴
            return self.__new_enumerate_axis(boe)
        elif typ == 'discr':  # 创建一个离散型数轴
            if length == 1:
                self.__new_discrete_axis(0, boe[0])
            else:
                self.__new_discrete_axis(boe[0], boe[1])
        else:  # 创建一个连续型数轴
            if length == 1:
                self.__new_continuous_axis(0, boe[0])
            else:
                self.__new_continuous_axis(boe[0], boe[1])

    @property
    def count(self):  # 输出数轴中元素的个数，若数轴为连续型，输出为inf
        self_type = self.__type
        if self_type == 'conti':
            return np.inf
        elif self_type == 'discr':
            return self.__ubound - self.__lbound
        else:
            return len(self.__enum_val)

    @property
    def size(self):  # 输出数轴的跨度，或长度，对连续型数轴来说，定义为上界减去下界
        self_type = self.__type
        if self_type == 'conti':
            return self.__ubound - self.__lbound
        else:
            return self.count

    @property
    def axis_type(self):
        return self.__type

    @property
    def axis_boe(self):
        if self.__type == 'enum':
            return tuple(self.__enum_val)
        else:
            return (self.__lbound, self.__ubound)

    def extract(self, interval_or_qty=1, how='interval'):
        if how == 'interval':
            if self.axis_type == 'enum':
                return self.__extract_enum_interval(interval_or_qty)
            else:
                return self.__extract_bounding_interval(interval_or_qty)
        else:
            if self.axis_type == 'enum':
                return self.__extract_enum_random(interval_or_qty)
            else:
                return self.__extract_bounding_random(interval_or_qty)

    def __set_bounds(self, lbound, ubound):
        self.__lbound = lbound
        self.__ubound = ubound
        self.__enum = None

    def __set_enum_val(self, enum):
        self.__lbound = None
        self.__ubound = None
        self.__enum_val = np.array(enum, subok=True)

    def __new_discrete_axis(self, lbound, ubound):
        self.__type = 'discr'
        self.__set_bounds(int(lbound), int(ubound))

    def __new_continuous_axis(self, lbound, ubound):
        self.__type = 'conti'
        self.__set_bounds(float(lbound), float(ubound))

    def __new_enumerate_axis(self, enum):
        self.__type = 'enum'
        self.__set_enum_val(enum)

    def __extract_bounding_interval(self, interval):
        return np.arange(self.__lbound, self.__ubound, interval)

    def __extract_bounding_random(self, qty):
        if self.__type == 'discr':
            result = np.random.randint(self.__lbound, self.__ubound + 1, size=(qty))
        else:
            result = self.__lbound + np.random.random(size=(qty)) * (self.__ubound - self.__lbound)
        return result

    def __extract_enum_interval(self, interval):
        count = self.count
        return self.__enum_val[np.arange(0, count, interval)]

    def __extract_enum_random(self, qty):
        count = self.count
        return self.__enum_val[np.random.choice(count, size=(qty))]


