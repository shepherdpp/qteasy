# coding=utf-8
class Ricon(Strategy):
    '风险控制抽象类，所有风险控制策略均继承该类'
    '''该策略仅仅生成卖出信号，无买入信号，因此作为止损点控制策略，仅与其他策略配合使用'''
    __metaclass__ = ABCMeta
    _stg_type = 'RiCon'
    @abstractmethod
    def generate(self, hist_price):
        pass