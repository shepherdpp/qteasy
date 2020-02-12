# coding=utf-8

class Timing(Strategy):
    '择时策略的抽象基类，所有择时策略都继承自该抽象类，本类定义了generate抽象方法模版，供具体的择时类调用'
    __mataclass__ = ABCMeta
    # Strategy主类共有的属性
    _stg_type = 'timing'

    ###################
    # 以下是本类型strategy对象的公共方法和抽象方法

    @abstractmethod
    def _generate_one(self):
        '''抽象方法，在具体类中需要重写，是整个类的择时信号基本生成方法，针对单个个股的价格序列生成多空状态信号'''
        pass

    def generate(self, h_):
        '''基于_generate_one方法生成整个股票价格序列集合的多空状态矩阵.

        本方法基于numpy的ndarray计算
        输入：   hist_extract：DataFrame，历史价格数据，需要被转化为ndarray
        输出：=====
        '''
        assert type(h_) is np.ndarray, 'Type Error: input should be Ndarray'
        pars = self._pars

        # assert pars.keys() = hist_extract.columns
        if type(pars) is dict:
            # 调用_generate_one方法计算单个个股的多空状态，并组合起来
            # print('input Pars is dict type, different parameters shall be mapped within data')
            par_list = list(pars.values())
            # print('values of pars are listed:', par_list)
            res = np.array(list(map(self._generate_one, h_.T, par_list))).T
        else:
            # 当参数不是字典状态时，直接使用pars作为参数
            res = np.apply_along_axis(self._generate_one, 0, h_, pars)

        # 将完成的数据组合成DataFrame
        # print('generate result of np timing generate', res)
        return res

    def _ema(self, arr, span=None, alpha=None):
        '''基于numpy的高速指数移动平均值计算.

        输入：
            arr, 1-D ndarray, 输入数据，一维矩阵
            span, int, optional, 1 < span, 跨度
            alpha, float, optional, 0 < alpha < 1, 数据衰减系数
        输出：=====
            out
        '''
        if alpha is None:
            alpha = 2 / (span + 1.0)
        alpha_rev = 1 - alpha
        n = arr.shape[0]
        pows = alpha_rev ** (np.arange(n + 1))
        scale_arr = 1 / pows[:-1]
        offset = arr[0] * pows[1:]
        pw0 = alpha * alpha_rev ** (n - 1)
        mult = arr * pw0 * scale_arr
        cumsums = mult.cumsum()
        return offset + cumsums * scale_arr[::-1]

    def _ma(self, arr, window):
        '''基于numpy的高速移动平均值计算

        输入：
            arr, 1-D ndarray, 输入数据，一维矩阵
            window, int, optional, 1 < window, 时间滑动窗口
        输出：=====
            ndarray, 完成计算的移动平均序列
        '''
        arr_ = arr.cumsum()
        arr_r = np.roll(arr_, window)
        arr_r[:window - 1] = np.nan
        arr_r[window - 1] = 0
        return (arr_ - arr_r) / window