import unittest
import numpy as np

from qteasy.strategy import (
    BaseStrategy,
    GeneralStg,
    RuleIterator,
    FactorSorter,
)

from qteasy.datatypes import DataType
from qteasy.parameter import Parameter


param1 = Parameter(
        name='param1',
        par_type='int',
        par_range=(1, 100),
        value=50,
)

param2 = Parameter(
        name='param2',
        par_type='float',
        par_range=(0.0, 1.0),
        value=0.5,
)

param3 = Parameter(
        name='param3',
        par_type='enum',
        par_range=('option1', 'option2', 'option3'),
        value='option1',
)

param4 = Parameter(
        name='param4',
        par_type='array[3,]',
        par_range=(1.0, 5.0),
        value=np.array([1.0, 2.0, 3.0]),
)


# 创建三个测试交易策略类，用于测试
class GenStg(GeneralStg):
    """第一个测试交易策略类，继承自GeneralStg

    包含两个可调参数: `param1` 和 `param2`，用于测试参数传递和使用。
    使用三种不同的数据类型: 'price@5minx30', 'volume@hx10', 'indicator@dx5'，用于测试数据类型的处理。
    """
    def __init__(self, pars=None, data_types=None):
        super().__init__(
                name='test_gen',
                description='test general strategy',
                run_freq='d',
                run_timing='close',
                pars=pars,
                stg_type='general',
                data_types=data_types,

        )

    def realize(self):
        print("GeneralStg realized")


class FactorSorterStg(FactorSorter):
    def __init__(self):
        pass

    def realize(self):
        print("FactorSorter realized")


class RuleIteratorStg(RuleIterator):
    def __init__(self):
        pass

    def realize(self):
        print("RuleIterator realized")


class TestStrategy(unittest.TestCase):
    def test_creation(self):
        """ test creation of strategy objects"""
        stg = BaseStrategy(
                name='TestStrategy',
        )
        self.assertIsInstance(stg, BaseStrategy)
        self.assertEqual(stg.name, 'TestStrategy')
        self.assertEqual(stg.run_freq, '1d')

    def test_properties(self):
        self.assertEqual(True, False)

    def test_parameters(self):
        self.assertEqual(True, False)

    def test_general_stg(self):
        self.assertEqual(True, False)


if __name__ == '__main__':
    unittest.main()