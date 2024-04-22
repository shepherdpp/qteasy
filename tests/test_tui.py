# coding=utf-8
# ======================================
# File:     test_tui.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2024-04-09
# Desc:
#   Unittest for the TUI
# ======================================

import unittest
import time

import qteasy.trader
from qteasy.trader_tui import TraderApp


class TestTUI(unittest.TestCase):
    def test_action_toggle_dark(self):
        trader = qteasy.trader.Trader()
        app = TraderApp()
        app.action_toggle_dark()
        self.assertEqual(app.dark, False)
        app.action_toggle_dark()
        self.assertEqual(app.dark, True)


if __name__ == '__main__':
    # unittest.main()
    pass
