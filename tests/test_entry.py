# coding=utf-8
# ======================================
# File:     test_visual.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-02-12
# Desc:
#   Unittest for all qteasy visual
#   effects.
# ======================================
import unittest
import qteasy as qt


class TestEntry(unittest.TestCase):
    """ 测试queasy的所有入口函数

    """
    def test_qt_version(self):
        print(f'test qteasy version')
        print(f'qteasy version: {qt.__version__}')
        print(f'qteasy version info: {qt.version_info}')

    def test_qt_root_path(self):
        print(f'test qteasy root path')
        print(f'qteasy root path: {qt.QT_ROOT_PATH}')

    def test_qt_local_configs(self):
        print(f'test qteasy local configs')
        print(f'qteasy local configs: {qt._qt_local_configs}')

    def test_qt_config_file_intro(self):
        print(f'test qteasy config file intro')
        from qteasy.configure import QT_START_UP_FILE_INTRO
        print(f'qteasy config file intro: {QT_START_UP_FILE_INTRO}')

    def test_qt_start_up_settings(self):
        """ test accessing and modifying start up settings"""
        print(f'test qteasy start up settings')
        config_lines = qt.start_up_settings()
        self.assertIsNone(config_lines)

        config_lines = qt.get_start_up_settings()
        print(f'qteasy start up settings: {config_lines}')
        self.assertIsInstance(config_lines, dict)
        self.assertTrue(len(config_lines) > 0)
        for k, v in config_lines.items():
            self.assertIsInstance(k, str)

        # test modify start up settings
        qt.update_start_up_setting(test_key='test_value')
        config_lines = qt.get_start_up_settings()
        print(f'qteasy start up settings after update: {config_lines}')
        self.assertEqual(config_lines['test_key'], 'test_value')

        # test special values in start up settings
        qt.update_start_up_setting(test_key='test_value',
                                   test_key2=123,
                                   test_key3=0.123,
                                   test_key4=True,
                                   test_key5=False,
                                   test_key6=None,
                                   test_key7='None',
                                   test_key8='False',
                                   test_key9='3.14',
                                   test_key10='3',
        )
        config_lines = qt.get_start_up_settings()
        print(f'qteasy start up settings after update: {config_lines}')
        self.assertEqual(config_lines['test_key'], 'test_value')
        self.assertEqual(config_lines['test_key2'], 123)
        self.assertEqual(config_lines['test_key3'], 0.123)
        self.assertEqual(config_lines['test_key4'], True)
        self.assertEqual(config_lines['test_key5'], False)
        self.assertEqual(config_lines['test_key6'], None)
        self.assertEqual(config_lines['test_key7'], 'None')
        self.assertEqual(config_lines['test_key8'], 'False')
        self.assertEqual(config_lines['test_key9'], '3.14')
        self.assertEqual(config_lines['test_key10'], '3')

        # test remove start up settings
        qt.remove_start_up_setting('test_key')
        config_lines = qt.get_start_up_settings()
        print(f'qteasy start up settings after remove: {config_lines}')
        self.assertEqual(config_lines.get('test_key'), None)

        # remove other test keys
        qt.remove_start_up_setting('test_key2', 'test_key3', 'test_key4', 'test_key5', 'test_key6',
                                   'test_key7', 'test_key8', 'test_key9', 'test_key10')
        config_lines = qt.get_start_up_settings()
        print(f'qteasy start up settings after remove: {config_lines}')
        self.assertEqual(config_lines.get('test_key2'), None)
        self.assertEqual(config_lines.get('test_key3'), None)
        self.assertEqual(config_lines.get('test_key4'), None)
        self.assertEqual(config_lines.get('test_key5'), None)
        self.assertEqual(config_lines.get('test_key6'), None)
        self.assertEqual(config_lines.get('test_key7'), None)
        self.assertEqual(config_lines.get('test_key8'), None)
        self.assertEqual(config_lines.get('test_key9'), None)
        self.assertEqual(config_lines.get('test_key10'), None)

        # test updated invalid system settings
        with self.assertRaises(ValueError):
            qt.update_start_up_setting(test_key='test_value', mode='invalid_mode')

    def test_qt_built_ins(self):
        """ test functions built_ins, built_in_list, built_in_strategies, get_built_in_strategy, built_in_doc"""
        print(f'test qteasy built-ins')
        print(f'qteasy built-ins: {qt.built_ins}')
        self.assertIsInstance(qt.built_ins(), dict)
        self.assertTrue(len(qt.built_ins()) > 0)

        res = qt.built_ins('macd')
        self.assertIsInstance(res, dict)
        self.assertEqual(list(res.keys()), ['macd'])
        self.assertIsInstance(res['macd'](), qt.BaseStrategy)

        res = qt.built_ins('macde')
        self.assertIsInstance(res, dict)
        self.assertEqual(list(res.keys()), ['macd', 'macdext'])
        self.assertIsInstance(res['macd'](), qt.BaseStrategy)
        self.assertIsInstance(res['macdext'](), qt.BaseStrategy)

        with self.assertRaises(TypeError):
            qt.built_ins(123)

        print(f'qteasy built-in list: {qt.built_in_list}')
        res = qt.built_in_list()
        self.assertIsInstance(res, list)
        res = qt.built_in_list('macd')
        self.assertIsInstance(res, list)
        self.assertEqual(res, ['macd'])
        res = qt.built_in_list('macde')
        self.assertIsInstance(res, list)
        self.assertEqual(res, ['macd', 'macdext'])

        with self.assertRaises(TypeError):
            qt.built_in_list(123)

        print(f'qteasy built-in strategies: {qt.built_in_strategies}')
        macd = qt.built_in.MACD
        macdext = qt.built_in.MACDEXT
        res = qt.built_in_strategies()
        self.assertIsInstance(res, list)
        self.assertTrue(len(res) > 0)
        res = qt.built_in_strategies('macd')
        self.assertIsInstance(res, list)
        self.assertEqual(res, [macd])
        res = qt.built_in_strategies('macde')
        self.assertIsInstance(res, list)
        self.assertEqual(res, [macd, macdext])

        with self.assertRaises(TypeError):
            qt.built_in_strategies(123)

        print(f'qteasy built-in doc: {qt.built_in_doc}')
        res = qt.built_in_doc('macd')
        self.assertIsInstance(res, str)
        self.assertTrue(len(res) > 0)

        with self.assertRaises(TypeError):
            qt.built_in_doc(123)
        with self.assertRaises(ValueError):
            qt.built_in_doc('macde')

        print(f'qteasy get built-in strategy: {qt.get_built_in_strategy}')
        res = qt.get_built_in_strategy('macd')
        self.assertIsInstance(res, qt.BaseStrategy)
        self.assertIsInstance(res, macd)
        res = qt.get_built_in_strategy('mACD')
        self.assertIsInstance(res, qt.BaseStrategy)
        self.assertIsInstance(res, macd)

        with self.assertRaises(ValueError):
            qt.get_built_in_strategy('macde')
        with self.assertRaises(TypeError):
            qt.get_built_in_strategy(123)


if __name__ == '__main__':
    unittest.main()