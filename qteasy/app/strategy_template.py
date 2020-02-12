# coding=utf-8

class Strategy():
    '''量化投资策略的抽象基类，所有策略都继承自该抽象类，本类定义了generate抽象方法模版，供具体的择时类调用'''
    __mataclass__ = ABCMeta
    # Strategy主类共有的属性
    _stg_type = 'strategy type'
    _stg_name = 'strategy name'
    _stg_text = 'intro text of strategy'
    _par_count = 0
    _par_types = []
    _par_bounds_or_enums = []

    @property
    def stg_type(self):
        return self._stg_type

    @property
    def stg_name(self):
        return self._stg_name

    @property
    def stg_text(self):
        return self._stg_text

    @property
    def par_count(self):
        return self._par_count

    @property
    def par_types(self):
        return self._par_types

    @property
    def par_boes(self):
        return self._par_bounds_or_enums

    @property
    def opt_tag(self):
        return self._opt_tag

    @property
    def pars(self):
        return self._pars

    # 以下是所有Strategy对象的共有方法
    def __init__(self, pars=None, opt_tag=0):
        # 对象属性：
        self._pars = pars
        self._opt_tag = opt_tag

    def info(self):
        # 打印所有相关信息和主要属性
        print('Type of Strategy:', self.stg_type)
        print('Information of the strategy:\n', self.stg_name, self.stg_text)
        print('Optimization Tag and opti ranges:', self.opt_tag, self.par_boes)
        if not self._pars is None:
            print('Parameter Loaded：', type(self._pars), self._pars)
        else:
            print('Parameter NOT loaded!')
        pass

    def set_pars(self, pars):
        self._pars = pars
        return pars

    def set_opt_tag(self, opt_tag):
        self._opt_tag = opt_tag
        return opt_tag

    def set_par_boes(self, par_boes):
        self._par_bounds_or_enums = par_boes
        return par_boes

    @abstractmethod
    def generate(self):
        '''策略类的基本抽象方法，接受输入参数并输出操作清单'''
        pass

