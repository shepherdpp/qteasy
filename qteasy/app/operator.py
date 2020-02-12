# coding=utf-8

class Operation():
    '交易操作生成类，通过简单工厂模式创建择时属性类和选股属性类，并根据这两个属性类的结果生成交易清单'
    '''
    交易操作生成类包含若干个选股对象组件，若干个择时对象组件，以及若干个风险控制组件，所有这些组件对象都能
    在同一组历史数据对象上进行相应的选股操作、择时操作并进行风控分析。不同的选股或择时对象工具独立地在历史数据
    对象上生成选股蒙版或多空蒙版，这些独立的选股蒙版及多空蒙版又由不同的方式混合起来（通过交易操作对象的蒙版
    混合属性确定，其中选股蒙版混合属性是一个逻辑表达式，根据这个逻辑表达式用户可以确定所有的蒙版的混合方式，
    例如“0 or （ 1 and （ 2 and 3 ） or 4 ）”；多空信号的生成方式是三个生成选项之一）。生成一个
    综合应用所有择时选股风控策略在目标历史数据上后生成的一个交易信号记录，交易信号经过合法性修改后成为
    一个最终输出的合法交易记录（信号）'''

    # 对象初始化时需要给定对象中包含的选股、择时、风控组件的类型列表
    def __init__(self, timing_types=['simple'],
                 selecting_types=['simple'],
                 ricon_types=['none']):
        # 根据输入的参数生成择时具体类:
        # 择时类的混合方式有：
        # pos-N：只有当大于等于N个策略看多时，输出为看多，否则为看空
        # chg-N：在某一个多空状态下，当第N个反转信号出现时，反转状态
        # cumulate：没有绝对的多空状态，给每个策略分配同样的权重，当所有策略看多时输出100%看多，否则
        # 输出的看多比例与看多的策略的权重之和相同，当多空状态发生变化时会生成相应仓位的交易信号
        # 对象属性：
        # 交易信号通用属性：
        self.__Tp0 = False  # 是否允许T+0交易，True时允许T+0交易，否则不允许
        # 交易策略属性：
        # 对象的timings属性和timing_types属性都是列表，包含若干策略而不是一个策略
        self.__timing_types = []
        self.__timing = []
        self.__timing_blender = 'pos-1'  # 默认的择时策略混合方式
        # print timing_types
        for timing_type in timing_types:
            # print timing_type.lower()
            # 通过字符串比较确认timing_type的输入参数来生成不同的具体择时策略对象，使用.lower()转化为全小写字母
            self.__timing_types.append(timing_type)
            if timing_type.lower() == 'cross_line':
                self.__timing.append(Timing_Crossline())
            elif timing_type.lower() == 'macd':
                self.__timing.append(Timing_MACD())
            elif timing_type.lower() == 'dma':
                self.__timing.append(Timing_DMA())
            elif timing_type.lower() == 'trix':
                self.__timing.append(Timing_TRIX())
            else:  # 默认情况下使用simple策略
                self.__timing.append(Timing_Simple())
                self.__timing_types.pop()
                self.__timing_types.append('simple')
                # print timing_type
        # 根据输入参数创建不同的具体选股策略对象。selecting_types及selectings属性与择时策略对象属性相似
        # 都是列表，包含若干相互独立的选股策略（至少一个）
        self.__selecting_type = []
        self.__selecting = []
        # 选股策略的混合方式使用以下字符串描述。简单来说，每个选股策略都独立地生成一个选股蒙版，每个蒙版与其他的
        # 蒙版的混合方式要么是OR（+）要么是AND（*），最终混合的结果取决于这些蒙版的混合方法和混合顺序而多个蒙版
        # 的混合方式就可以用一个类似于四则运算表达式的方式来描述，例如“（ 0 + 1 ） * （ 2 + 3 * 4 ）”
        # 在操作生成模块中，有一个表达式解析器，通过解析四则运算表达式来解算selecting_blender_string，并将混
        # 合的步骤以前缀表达式的方式存储在selecting_blender中，在混合时按照前缀表达式的描述混合所有蒙版。注意
        # 表达式中的数字代表selectings列表中各个策略的索引值
        cur_type = 0
        self.__selecting_blender_string = ''
        for selecting_type in selecting_types:
            self.__selecting_type.append(selecting_type)
            if cur_type == 0:
                self.__selecting_blender_string += str(cur_type)
            else:
                self.__selecting_blender_string += ' or ' + str(cur_type)
            cur_type += 1
            if selecting_type.lower() == 'trend':
                self.__selecting.append(Selecting_Trend())
            elif selecting_type.lower() == 'random':
                self.__selecting.append(Selecting_Random())
            elif selecting_type.lower() == 'ranking':
                self.__selecting.append(Selecting_Ranking())
            else:
                self.__selecting.append(Selecting_Simple())
                self.__selecting_type.pop()
                self.__selecting_type.append('simple')
            # create selecting blender by selecting blender string
            self.__selecting_blender = self.__exp_to_blender(self.__selecting_blender_string)

        # 根据输入参数生成不同的风险控制策略对象
        self.__ricon_type = []
        self.__ricon = []
        self.__ricon_blender = 'add'
        for ricon_type in ricon_types:
            self.__ricon_type.append(ricon_type)
            if ricon_type.lower() == 'none':
                self.__ricon.append(Ricon_None())
            elif ricon_type.lower() == 'urgent':
                self.__ricon.append(Ricon_Urgent())
            else:
                self.__ricon.append(Ricon_None())
                self.__ricon_type.append('none')

    @property
    def timing(self):
        return self.__timing

    @property
    def selecting(self):
        return self.__selecting

    @property
    def ricon(self):
        return self.__ricon

    @property
    def strategies(self):
        stg = []
        stg.extend(self.timing)
        stg.extend(self.selecting)
        stg.extend(self.ricon)
        return stg

    # Operation对象有两类属性需要设置：blender混合器属性、Parameters策略参数或属性
    # 这些属性参数的设置需要在OP模块设置一个统一的设置入口，同时，为了实现与Optimizer模块之间的接口
    # 还需要创建两个Opti接口函数，一个用来根据的值创建合适的Space初始化参数，另一个用于接受opt
    # 模块传递过来的参数，分配到合适的策略中去

    def set_blender(self, blender_type, *args, **kwargs):
        # 统一的blender混合器属性设置入口
        if type(blender_type) == str:
            if blender_type.lower() == 'selecting':
                self.__set_selecting_blender(*args, **kwargs)
            elif blender_type.lower() == 'timing':
                self.__set_timing_blender(*args, **kwargs)
            elif blender_type.lower() == 'ricon':
                self.__set_ricon_blender(*args, **kwargs)
            else:
                print('wrong input!')
                pass
        else:
            print('blender_type should be a string')
        pass

    def set_parameter(self, stg_id, pars=None, opt_tag=None, par_boes=None):
        '''# 统一的策略参数设置入口，stg_id标识接受参数的具体成员策略
        # stg_id的格式为'x-n'，其中x为's/t/r'中的一个字母，n为一个整数'''
        if type(stg_id) == str:
            l = stg_id.split('-')
            stg = l[0]
            num = int(l[1])
            if stg.lower() == 's':
                strategy = self.selecting[num]
            elif stg.lower() == 't':
                strategy = self.timing[num]
            elif stg.lower() == 'r':
                strategy = self.ricon[num]
            else:
                print('wrong input!')
                return
            if not pars is None:
                strategy.set_pars(pars)
            if not opt_tag is None:
                strategy.set_opt_tag(opt_tag)
            if not par_boes is None:
                strategy.set_par_boes(par_boes)

        else:
            print('blender_type should be a string')
        pass

    def set_opt_par(self, opt_par):
        # 将输入的opt参数切片后传入stg的参数中
        s = 0
        k = 0
        for stg in self.strategies:
            if stg.opt_tag == 0:
                pass
            elif stg.opt_tag == 1:
                k += stg.par_count
                stg.set_pars(opt_par[s:k])
                s = k
            elif stg.opt_tag == 2:
                k += 1
                stg.set_pars(opt_par[s:k])
                s = k

    def get_opt_space_par(self):
        ranges = []
        types = []
        for stg in self.strategies:
            if stg.opt_tag == 0:
                pass  # 策略优化方案关闭
            elif stg.opt_tag == 1:
                ranges.extend(stg.par_boes)
                types.extend(stg.par_types)
            elif stg.opt_tag == 2:
                ranges.append(stg.par_boes)
                types.extend(['enum'])
        return ranges, types
        pass

    # =================================================
    # 下面是Operation模块的公有方法：
    def info(self):
        '''# 打印出当前交易操作对象的信息，包括选股、择时策略的类型，策略混合方法、风险控制策略类型等等信息
        # 如果策略包含更多的信息，还会打印出策略的一些具体信息，如选股策略的信息等
        # 在这里调用了私有属性对象的私有属性，不应该直接调用，应该通过私有属性的公有方法打印相关信息
        # 首先打印Operation木块本身的信息'''
        print('OPERATION MODULE INFO:')
        print('=' * 25)
        print('Information of the Module')
        print('=' * 25)
        # 打印各个子模块的信息：
        # 首先打印Selecting模块的信息
        print ('Total count of Selecting strategies:', len(self.__selecting))
        print ('the blend type of selecting strategies is', self.__selecting_blender_string)
        print ('Parameters of Selecting Strategies:')
        for sel in self.selecting:
            sel.info()
        print('#' * 25)

        # 接着打印 timing模块的信息
        print ('Total count of timing strategies:', len(self.__timing))
        print ('The blend type of timing strategies is', self.__timing_blender)
        print ('Parameters of timing Strategies:')
        for tmg in self.timing:
            tmg.info()
        print('#' * 25)

        # 最后打印Ricon模块的信息
        print ('Total count of Risk Control strategies:', len(self.__ricon))
        print ('The blend type of Risk Control strategies is', self.__ricon_blender)
        for ric in self.ricon:
            ric.info()
        print('#' * 25)

    def create(self, hist_extract):
        """# 操作信号生成方法，在输入的历史数据上分别应用选股策略、择时策略和风险控制策略，生成初步交易信号后，
        # 对信号进行合法性处理，最终生成合法交易信号
        # 输入：
            # hist_extract：从数据仓库中导出的历史数据，包含多只股票在一定时期内特定频率的一组或多组数据
        # 输出：=====
            # lst：使用对象的策略在历史数据期间的一个子集上产生的所有合法交易信号，该信号可以输出到回测
            # 模块进行回测和评价分析，也可以输出到实盘操作模块触发交易操作
        #print( 'Time measurement: selection_mask creation')
        # 第一步，在历史数据上分别使用选股策略独立产生若干选股蒙板（sel_mask）
        # 选股策略的所有参数都通过对象属性设置，因此在这里不需要传递任何参数"""
        sel_masks = []
        assert type(hist_extract) is pd.DataFrame, 'Type Error: the extracted historical data is a Pandas DataFrame'
        shares = hist_extract.columns
        date_list = hist_extract.index
        h_v = hist_extract.values
        for sel in self.__selecting:  # 依次使用选股策略队列中的所有策略逐个生成选股蒙板
            # print('SPEED test OP create, Time of sel_mask creation')
            sel_masks.append(sel.generate(h_v, date_list, shares))  # 生成的选股蒙板添加到选股蒙板队列中
        # print('SPEED test OP create, Time of sel_mask blending')
        # %time (self.__selecting_blend(sel_masks))
        sel_mask = self.__selecting_blend(sel_masks)  # 根据蒙板混合前缀表达式混合所有蒙板
        # sel_mask.any(0) 生成一个行向量，每个元素对应sel_mask中的一列，如果某列全部为零，该元素为0，
        # 乘以hist_extract后，会把它对应列清零，因此不参与后续计算，降低了择时和风控计算的开销
        selected_shares = sel_mask.any(0)
        hist_selected = hist_extract * selected_shares
        # print ('Time measurement: ls_mask creation')
        # 第二步，使用择时策略在历史数据上独立产生若干多空蒙板(ls_mask)
        ls_masks = []
        for tmg in self.__timing:  # 依次使用择时策略队列中的所有策略逐个生成多空蒙板
            # 生成多空蒙板时忽略在整个历史考察期内从未被选中过的股票：
            # print('SPEED test OP create, Time of ls_mask creation')
            ls_masks.append(tmg.generate(h_v))
            # print(tmg.generate(h_v))
            # print('ls mask created: ', tmg.generate(hist_selected).iloc[980:1000])
        # print('SPEED test OP create, Time of ls_mask blending')
        # %time self.__timing_blend(ls_masks)
        ls_mask = self.__timing_blend(ls_masks)  # 混合所有多空蒙板生成最终的多空蒙板
        # print( '\n long/short mask: \n', ls_mask)
        # print 'Time measurement: risk-control_mask creation'
        # 第三步，风险控制交易信号矩阵生成（简称风控矩阵）
        ricon_mats = []
        for ricon in self.__ricon:  # 依次使用风控策略队列中的所有策略生成风险控制矩阵
            # print('SPEED test OP create, Time of ricon_mask creation')
            ricon_mats.append(ricon.generate(h_v))  # 所有风控矩阵添加到风控矩阵队列
        # print('SPEED test OP create, Time of ricon_mask blending')
        # %time self.__ricon_blend(ricon_mats)
        ricon_mat = self.__ricon_blend(ricon_mats)  # 混合所有风控矩阵后得到最终的风控策略
        # print ('risk control matrix \n', ricon_mat[980:1000])
        # print (ricon_mat)
        # print ('sel_mask * ls_mask: ', (ls_mask * sel_mask))
        # 使用mask_to_signal方法将多空蒙板及选股蒙板的乘积（持仓蒙板）转化为交易信号，再加上风控交易信号矩阵，并对交易信号进行合法化
        # print('SPEED test OP create, Time of operation mask creation')
        # %time self.__legalize(self.__mask_to_signal(ls_mask * sel_mask) + (ricon_mat))
        op_mat = self.__legalize(self.__mask_to_signal(ls_mask * sel_mask) + (ricon_mat))
        # print('SPEED test OP create, Time of converting op matrix into DataFrame')
        # pd.DataFrame(op_mat, index = date_list, columns = shares)
        lst = pd.DataFrame(op_mat, index=date_list, columns=shares)
        # print ('operation matrix: ', '\n', lst.loc[lst.any(axis = 1)]['2007-01-15': '2007-03-01'])
        # return lst[lst.any(1)]
        # 消除完全相同的行和数字全为0的行
        lst_out = lst[lst.any(1)]
        keep = (lst_out - lst_out.shift(1)).any(1)
        return lst_out[keep]

        ################################################################

    # 下面是Operation模块的私有方法

    def __set_timing_blender(self, timing_blender):
        '''设置择时策略混合方式，混合方式包括pos-N,chg-N，以及cumulate三种

        输入：
            参数 timing_blender，str，合法的输入包括：
                'chg-N': N为正整数，取值区间为1到len(timing)的值，表示多空状态在第N次信号反转时反转
                'pos-N': N为正整数，取值区间为1到len(timing)的值，表示在N个策略为多时状态为多，否则为空
                'cumulate': 在每个策略发生反转时都会产生交易信号，但是信号强度为1/len(timing)
        输出：=====
            无
        '''
        self.__timing_blender = timing_blender

    def __set_selecting_blender(self, selecting_blender_expression):
        # 设置选股策略的混合方式，混合方式通过选股策略混合表达式来表示
        # 给选股策略混合表达式赋值后，直接解析表达式，将选股策略混合表达式的前缀表达式存入选股策略混合器
        if not type(selecting_blender_expression) is str:  # 如果输入不是str类型
            self.__selecting_blender = self.__exp_to_blender('0')
            self.__selecting_blender_string = '0'
        else:
            self.__selecting_blender = self.__exp_to_blender(selecting_blender_expression)
            self.__selecting_blender_string = selecting_blender_expression

    def __set_ricon_blender(self, ricon_blender):
        self.__ricon_blender = ricon_blender

    def __timing_blend(self, ls_masks):
        '''# 择时策略混合器，将各个择时策略生成的多空蒙板按规则混合成一个蒙板
        # 输入：ls_masks：多空蒙板列表，包含至少一个多空蒙板
        # 输出：=====lm: 一个混合后的多空蒙板'''
        blndr = self.__timing_blender  # 从对象的属性中读取择时混合参数
        assert type(blndr) is str, 'Parmameter Type Error: the timing blender should be a text string!'
        # print 'timing blender is:', blndr
        if blndr[0:3] == 'chg':  # 出现N个状态变化信号时状态变化
            # TODO: ！！本混合方法暂未完成！！
            # chg-N方式下，持仓仅有两个位置，1或0，持仓位置与各个蒙板的状态变化有关，如果当前状态为空头，只要有N个或更多
            # 蒙板空转多，则结果转换为多头，反之亦然。这种方式与pos-N的区别在于，pos-N在多转空时往往滞后，因为要满足剩余
            # 的空头数量小于N后才会转空头，而chg-N则不然。例如，三个组合策略下pos-1要等至少两个策略多转空后才会转空，而
            # chg-1只要有一个策略多转空后，就会立即转空
            # 已经实现的chg-1方法由pandas实现，效率很低
            l_count = len(ls_masks)
            # print 'the first long/short mask is\n', ls_masks[-1]
            l_m = ls_masks.pop()  # 使用pop()弹出第一个蒙板
            while ls_masks != []:
                # print 'next ls mask:\n', ls_masks[-1]
                l_m += ls_masks.pop()  # 从队列中弹出下一个蒙板，累加到前一个
            return l_m.apply(self.__timing_blend_change, axis=1)
        else:  # 另外两种混合方式都需要用到蒙板累加，因此一同处理
            l_count = len(ls_masks)
            # print 'the first long/short mask is\n', ls_masks[-1]
            l_m = ls_masks.pop()  # 使用pop()弹出第一个蒙板
            while ls_masks != []:
                # print 'next ls mask:\n', ls_masks[-1]
                l_m += ls_masks.pop()  # 从队列中弹出下一个蒙板，累加到前一个
            if blndr == 'cumulate':
                # cumulate方式下，持仓取决于看多的蒙板的数量，看多蒙板越多，持仓越高，只有所有蒙板均看空时，最终结果才看空
                # 所有蒙板的权重相同，因此，如果一共五个蒙板三个看多两个看空时，持仓为60%
                # print 'long short masks are merged by', blndr, 'result as\n', l_m / l_count
                return l_m / l_count
            elif blndr[0:3] == 'pos':
                # pos-N方式下，持仓同样取决于看多的蒙板的数量，但是持仓只能为1或0，只有满足N个或更多蒙板看多时，最终结果
                # 看多，否则看空，如pos-2方式下，至少两个蒙板看多则最终看多，否则看空
                # print 'timing blender mode: ', blndr
                N = int(blndr[-1])
                # print 'long short masks are merged by', blndr, 'result as\n', l_m.clip(N - 1, N) - (N - 1)
                return l_m.clip(N - 1, N) - (N - 1)
            else:
                print('Blender text not recognized!')
        pass

    def __timing_blend_change(self, ser):
        # following method is based on Numpy thus is faster than the other two

        assert type(ser) is np.ndarray, 'type of ser should be pandas Series object'
        if ser[0] > 0:
            state = 1
        else:
            state = 0
        res = np.zeros_like(ser)
        prev = ser[0]
        for u, v in np.nditer([res, ser], op_flags=['readwrite']):
            if v < prev:
                state = 0
            elif v > prev:
                state = 1
            u[...] = state
            prev = v
        return res

        # following method is also SLOW, although slightly faster than the extremely SLOW version
        '''
        assert type(ser) is pd.Series, 'Parameter Type Error: the data should be a pandas Series object!'
        if ser[0]>0:
            state=1 
        else: 
            state=0 
        l = [] 
        prev = ser[0] 
        for i, v in ser.iteritems(): 
            if v<prev: 
                state = 0 
            elif v>prev: 
                state = 1 
            l.append(state) 
            prev = v 
        ser[:] = l 
        return ser'''

        # following method is extremely SLOW!!!
        '''
        assert type(ser) is pd.Series, 'Parameter Type Error: the data should be a pandas Series object!'
        chg = ser[(ser-ser.shift(1))!=0] 
        chg = chg - chg.shift(1) 
        chg[0] = ser[0] 
        chg.loc[chg<1] = 0 
        return chg.reindex(index=ser.index, method='pad').clip(0,1)'''

    def __selecting_blend(self, sel_masks):
        #
        exp = self.__selecting_blender[:]
        # print('expression in operation module', exp)
        s = []
        while exp != []:
            if exp[-1].isdigit():
                s.append(sel_masks[int(exp.pop())])
            else:
                s.append(self.__blend(s.pop(), s.pop(), exp.pop()))
        return self.__unify(s[0])

    def __ricon_blend(self, ricon_mats):
        if self.__ricon_blender == 'add':
            r_m = ricon_mats.pop()
            while ricon_mats != []:
                r_m += ricon_mats.pop()
            return r_m

    def __mask_to_signal(self, lst):
        '''将持仓蒙板转化为交易信号.

        转换的规则为比较前后两个交易时间点的持仓比率，如果持仓比率提高，
        则产生相应的补仓买入信号；如果持仓比率降低，则产生相应的卖出信号将仓位降低到目标水平。
        生成的信号范围在(-1, 1)之间，负数代表卖出，正数代表买入，且具体的买卖信号signal意义如下：
            signal > 0时，表示用总资产的 signal * 100% 买入该资产， 如0.35表示用当期总资产的35%买入该投资产品，如果
                现金总额不足，则按比例调降买入比率，直到用尽现金。
            signal < 0时，表示卖出本期持有的该资产的 signal * 100% 份额，如-0.75表示当期应卖出持有该资产的75%份额。
            signal = 0时，表示不进行任何操作

        输入：
            参数 lst，ndarray，持仓蒙板
        输出：=====
            op，ndarray，交易信号矩阵
        '''

        # 比较本期交易时间点和上期之间的持仓比率差额，差额大于0者可以直接作为补仓买入信号，如上期为0.35，
        # 本期0.7，买入信号为0.35，即使用总资金的35%买入该股，加仓到70%
        op = (lst - np.roll(lst, 1))
        # 差额小于0者需要计算差额与上期持仓数之比，作为卖出信号的强度，如上期为0.7，本期为0.35，差额为-0.35，则卖出信号强度
        # 为 (0.7 - 0.35) / 0.35 = 0.5即卖出50%的持仓数额，从70%仓位减仓到35%
        op = np.where(op < 0, (op / np.roll(lst, 1)), op)
        # 补齐因为计算差额导致的第一行数据为NaN值的问题
        op[0] = lst[0]
        return op

    def __legalize(self, lst):
        '''交易信号合法化，整理生成的交易信号，使交易信号符合规则.

        根据历史数据产生的交易信号不一定完全符合实际的交易规则，在必要时需要对交易信号进行
        修改，以确保最终的交易信号符合交易规则，这里的交易规则仅包含与交易时间相关的规则如T+1规则等，与交易
        成本或交易量相关的规则如费率、MOQ等都在回测模块中考虑'''

        # 最基本的操作规则是不允许出现大于1或者小于-1的交易信号
        return lst.clip(-1, 1)

    def __exp_to_blender(self, exp_list):
        '''# 选股策略混合表达式解析程序，将通常的中缀表达式解析为前缀运算队列，从而便于混合程序直接调用
        # 系统接受的合法表达式为包含 '*' 与 '+' 的中缀表达式，符合人类的思维习惯，使用括号来实现强制
        # 优先计算，如 '0 + (1 + 2) * 3'; 表达式中的数字0～3代表选股策略列表中的不同策略的索引号
        # 上述表达式虽然便于人类理解，但是不利于快速计算，因此需要转化为前缀表达式，其优势是没有括号
        # 按照顺序读取并直接计算，便于程序的运行。为了节省系统运行开销，在给出混合表达式的时候直接将它
        # 转化为前缀表达式的形式并直接存储在blender列表中，在混合时直接调用并计算即可
        # 输入： exp_list：输入的中缀混合计算表达式
        # 输出：===== s2: 前缀表达式

        # 以下算法来自简书
        # 定义两种可用操作符，并定义操作符的优先级，定义 or 的优先级低于 and'''
        prio = {'or': 0,
                'and': 1}
        # 定义两个队列作为操作堆栈
        s1 = []  # 运算符栈
        s2 = []  # 结果栈
        # 读取字符串并读取字符串中的各个元素（操作数和操作符），当前使用str对象的split()方法进行，要
        # 求字符串中个元素之间用空格或其他符号分割，应该考虑写一个self.__split()方法，不依赖空格对
        # 字符串进行分割
        # exp_list = self.__selecting_blender_string.split()
        exp_list = list(self.__selecting_blender_string)
        # 开始循环读取所有操作元素
        while exp_list != []:
            s = exp_list.pop()
            # 从右至左逐个读取表达式中的元素（数字或操作符）
            # 并按照以下算法处理
            if s.isdigit():
                # 1，如果元素是数字则压入结果栈
                s2.append(s)

            elif s == ')':
                # 2，如果元素是反括号则压入运算符栈
                s1.append(s)
            elif s == '(':
                # 3，扫描到（时，依次弹出所有运算符直到遇到），并把该）弹出
                while s1[-1] != ')':
                    s2.append(s1.pop())
                s1.pop()
            elif s in prio.keys():
                # 4，扫描到运算符时：
                if s1 == [] or s1[-1] == ')' or prio[s] >= prio[s1[-1]]:
                    # 如果这三种情况则直接入栈
                    s1.append(s)
                else:
                    # 否则就弹出s1中的符号压入s2，并将元素放回队列
                    s2.append(s1.pop())
                    exp_list.append(s)
        while s1 != []:
            s2.append(s1.pop())
        s2.reverse()  # 表达式解析完成，生成前缀表达式
        return s2

    def __blend(self, n1, n2, op):
        '''# 混合操作符函数，使用加法和乘法处理与和或的问题,可以研究逻辑运算和加法运算哪一个更快，使用更快的一个'''
        if op == 'or':
            # print 'blending two sel masks with method OR \n'
            # print 'first sel mask to blend\n', n1
            # print 'second sel mask to blendn', n2
            # print 'result after blending\n', n1 + n2
            return n1 + n2
        elif op == 'and':
            # print 'blending two sel masks with method AND \n'
            # print 'first sel mask to blend\n', n1
            # print 'second sel mask to blend\n', n2
            # print 'result after blending\n', n1 * n2
            return n1 * n2

    def __unify(self, arr):
        s = arr.sum(1)
        shape = (s.shape[0], 1)
        return arr / s.reshape(shape)
