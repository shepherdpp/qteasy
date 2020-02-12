# coding=utf-8
class Looper:
    '''回测器类，获取历史数据以及历史交易信号数据，根据交易信号进行模拟交易并计算模拟交易历史记录，

    包括每次交易前后的现金持有额、投资产品持有额、交易费用及交易成本额等
    交易信号清单和资产价格清单是Looper类主要函数apply_loop()的主要输入参数，根据这两个输入参数
    apply_loop()函数返回模拟交易记录
    '''

    def __init__(self, superior, rate_fee=0.003, rate_slipery=0, rate_impact=0, MOQ=100):
        '''初始化回测器类,初始化回测器对象相关变量，主要包括计算交易费用的变量

        输入
            参数superior, object:上级模块，本模块在创建时必须作为上级模块的子模块创建，通过该参数可以访问上级模块
            参数rate_fee, float：交易费率，用于计算交易费用
            参数rate_slipery, float：滑点影响率，用于计算交易滑点成本
            参数rate_impact, float：冲击成本率，用于计算冲击成本
            参数MOQ, float：最小购买单位，表示购入金融产品时最低可购买的份额数量，
        输出：=====
            无
        '''
        self.__superior = superior  # 上层对象
        self.rate_fee = rate_fee  # 交易费用成本计算参数，固定交易费率
        self.rate_slipery = rate_slipery  # 交易滑点成本估算参数，对交易命令发出到实际交易完成之间价格变化导致的成本进行估算
        self.rate_impact = rate_impact  # 交易冲击成本估算参数，对交易本身对价格造成的影响带来的成本进行估算
        self.MOQ = MOQ  # 交易最小批量，设置为0表示可以买卖分数股

    @property
    def superior(self):
        '''返回Looper类的上层对象'''
        return self.__superior

    def info(self):
        '''打印Looper类的基本参数信息'''
        print (self.rate_fee)
        print (self.rate_slipery)
        print (self.rate_impact)
        print (self.MOQ)

    def rate(self, amount):
        return self.rate_fee + self.rate_slipery + self.rate_impact * amount

    def __loop_step(self, pre_cash, pre_amounts, op, prices):
        ''' 对单次交易进行处理，采用向量化计算以提升效率

        输入：=====
            参数 pre_cash, ndarray：本次交易开始前账户现金余额
            参数 pre_amounts, ndarray：list，交易开始前各个股票账户中的股份余额
            参数 op, ndarray：本次交易的个股交易清单
            参数 prices：List，本次交易发生时各个股票的价格
            参数 rate_in：买入成本——待改进，应根据三个成本费率动态估算
            参数 rate_out：卖出成本——待改进，应根据三个成本费率动态估算

        输出：=====元组，包含四个元素
            cash：交易后账户现金余额
            amounts：交易后每个个股账户中的股份余额
            fee：本次交易总费用
            value：本次交易后资产总额（按照交易后现金及股份余额以及交易时的价格计算）
        '''
        MOQ = self.MOQ
        # 计算交易前现金及股票余额在当前价格下的资产总额
        pre_value = pre_cash + (pre_amounts * prices).sum()
        # 计算按照交易清单出售资产后的资产余额以及获得的现金
        '''在这里出售的amount被使用np.rint()函数转化为int型，这里应该增加判断，如果MOQ不要求出售
        的投资产品份额为整数，可以省去rint处理'''
        if MOQ == 0:
            a_sold = np.where(prices != 0,
                              np.where(op < 0, pre_amounts * op, 0),
                              0)
        else:
            a_sold = np.where(prices != 0,
                              np.where(op < 0, np.rint(pre_amounts * op), 0),
                              0)
        rate_out = self.rate(a_sold * prices)
        cash_gained = np.where(a_sold < 0, -1 * a_sold * prices * (1 - rate_out), 0)
        # 本期出售资产后现金余额 = 期初现金余额 + 出售资产获得现金总额
        cash = pre_cash + cash_gained.sum()
        # 初步估算按照交易清单买入资产所需要的现金，如果超过持有现金，则按比例降低买入金额
        pur_values = pre_value * op.clip(0)  # 使用clip来代替np.where，速度更快,且op.clip(1)比np.clip(op, 0, 1)快很多
        if pur_values.sum() > cash:
            # 估算买入资产所需现金超过持有现金
            pur_values = pur_values / pre_value * cash
            # 按比例降低分配给每个拟买入资产的现金额度
        # 计算购入每项资产实际花费的现金以及实际买入资产数量，如果MOQ不为0，则需要取整并修改实际花费现金额
        rate_in = self.rate(pur_values)
        if MOQ == 0:  # MOQ为零时，可以购入的资产数量允许为小数
            a_purchased = np.where(prices != 0,
                                   np.where(op > 0,
                                            pur_values / (prices * (1 + rate_in)), 0), 0)
        else:  # 否则，使用整除方式确保购入的资产数量为MOQ的整数倍，MOQ非整数时仍然成立
            a_purchased = np.where(prices != 0,
                                   np.where(op > 0,
                                            pur_values // (prices * MOQ * (1 + rate_in)) * MOQ,
                                            0), 0)
        # 由于MOQ的存在，需要根据实际购入的资产数量确定花费的现金资产
        # 仅当a_purchased大于零时计算花费的现金额
        cash_spent = np.where(a_purchased > 0,
                              -1 * a_purchased * prices * (1 + rate_in), 0)

        # 计算购入资产产生的交易成本，买入资产和卖出资产的交易成本率可以不同，且每次交易动态计算
        fee = np.where(op == 0, 0,
                       np.where(op > 0, -1 * cash_spent * rate_in,
                                cash_gained * rate_out)).sum()
        # 持有资产总额 = 期初资产余额 + 本期买入资产总额 + 本期卖出资产总额（负值）
        amounts = pre_amounts + a_purchased + a_sold
        # 期末现金余额 = 本期出售资产后余额 + 本期购入资产花费现金总额（负值）
        cash += cash_spent.sum()
        # 期末资产总价值 = 期末资产总额 * 本期资产单价 + 期末现金余额
        value = (amounts * prices).sum() + cash
        return cash, amounts, fee, value

    def _get_complete_hist(self, values, history_list, with_price=False):
        '''完成历史交易回测后，填充完整的历史资产总价值清单

        输入：=====
            参数 values：完成历史交易回测后生成的历史资产总价值清单，只有在操作日才有记录，非操作日没有记录
            参数 history_list：完整的投资产品价格清单，包含所有投资产品在回测区间内每个交易日的价格
            参数 with_price：Bool，True时在返回的清单中包含历史价格，否则仅返回资产总价值
        输出：=====
            values，pandas.Series 或 pandas.DataFrame：重新填充的完整历史交易日资产总价值清单
        '''
        # 获取价格清单中的投资产品列表
        shares = history_list.columns
        # 使用价格清单的索引值对资产总价值清单进行重新索引，重新索引时向前填充每日持仓额、现金额，使得新的
        # 价值清单中新增的记录中的持仓额和现金额与最近的一个操作日保持一致，并消除nan值
        values = values.reindex(history_list.index, method='ffill').fillna(0)
        # 重新计算整个清单中的资产总价值，生成pandas.Series对象
        values = (history_list * values[shares]).sum(axis=1) + values['cash']
        if with_price:  # 如果需要同时返回价格，则生成pandas.DataFrame对象，包含所有历史价格
            values = pd.DataFrame(values.values, index=history_list.index, columns=['values'])
            values[shares] = history_list[shares]
        return values

    def apply_loop(self, op_list, history_list, visual=False, price_visual=False,
                   init_cash=100000, rate_fee=0.003, rate_slipery=0, rate_impact=0, MOQ=100):
        '''使用Numpy快速迭代器完成整个交易清单在历史数据表上的模拟交易，并输出每次交易后持仓、
            现金额及费用，输出的结果可选

        输入：=====
            参数 op_list: pd.DataFrame, 标准格式交易清单，描述一段时间内的交易详情，每次交易一行数据
            参数 history_list：完整历史价格清单，数据的频率由freq参数决定
            参数 visual：可选参数，默认False，仅在有交易行为的时间点上计算持仓、现金及费用，
                            # 为True时将数据填充到整个历史区间，并用图表输出
            参数 price_visual：选择是否在图表输出时同时输出相关资产价格变化，visual为False时无效
            参数 init_cash：初始资金额

        输出：=====
            Value_history：包含交易结果及资产总额的历史清单
        '''
        self.rate_fee = rate_fee
        self.rate_slipery = rate_slipery
        self.rate_impact = rate_impact
        self.MOQ = MOQ
        if op_list.empty: return op_list
        # 将交易清单和与之对应的价格清单转化为ndarray，确保内存存储方式为Fortune，
        # 以实现高速逐行循环批量操作
        # 根据最新的研究实验，在python3.6的环境下，nditer的速度显著地慢于普通的for-loop
        # 因此改回for-loop执行，知道找到更好的向量化执行方法
        op = op_list.values
        price = history_list.fillna(0).loc[op_list.index].values
        op_count = op.shape[0]  # 获取行数
        # 初始化计算结果列表
        cash = init_cash  # 持有现金总额，初始化为初始现金总额
        amounts = [0] * len(history_list.columns)  # 投资组合中各个资产的持有数量，初始值为全0向量
        cashes = []  # 中间变量用于记录各个资产买入卖出时消耗或获得的现金
        fees = []  # 交易费用，记录每个操作时点产生的交易费用
        values = []  # 资产总价值，记录每个操作时点的资产和现金价值总和
        amounts_matrix = []
        # 只有当交易的资产数量大于1时，才需要向量化逐行循环，否则使用默认的ndarray循环
        for i in range(op_count):
            # it = np.nditer([op, price], flags = ['external_loop'], order = 'C')
            if len(history_list.columns) > 1:
                # ndarray的内存存储方式和external loop的循环顺序不一致时，会产生逐行循环的效果，实现向量化计算

                cash, amounts, fee, value = self.__loop_step(pre_cash=cash,
                                                             pre_amounts=amounts,
                                                             op=op[i, :], prices=price[i, :])
            else:
                # it = np.nditer([op, price])
                # 将每一行交易信号代码和每一行价格使用迭代器送入_loop_step()函数计算结果
                cash, amounts, fee, value = self.__loop_step(pre_cash=cash,
                                                             pre_amounts=amounts,
                                                             op=op[i], prices=price[i])
            # 保存计算结果
            cashes.append(cash)
            fees.append(fee)
            values.append(value)
            amounts_matrix.append(amounts)
        # 将向量化计算结果转化回DataFrame格式
        value_history = pd.DataFrame(amounts_matrix, index=op_list.index,
                                     columns=op_list.columns)
        # 填充标量计算结果
        value_history['cash'] = cashes
        value_history['fee'] = fees
        value_history['value'] = values
        if visual:  # Visual参数为True时填充完整历史记录并
            complete_value = self._get_complete_hist(values=value_history,
                                                     history_list=history_list,
                                                     with_price=price_visual)
            # 输出相关资产价格
            if price_visual:  # 当Price_Visual参数为True时同时显示所有的成分股票的历史价格
                shares = history_list.columns
                share_prices = []
                complete_value.plot(grid=True, figsize=(15, 7), legend=True,
                                    secondary_y=shares)
            else:  # 否则，仅显示总资产的历史变化情况
                complete_value.plot(grid=True, figsize=(15, 7), legend=True)
        return value_history