# coding=utf-8
# ======================================
# File:     qt_code.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2024-10-20
# Desc:
#   Definition of class QtCode, storing
# and managing different market symbols.
# ======================================


class QtCode(str):
    """ special string class for market symbols, with properties
    that can be used to identify market types, and easy access of
    stock symbols and asset types

    """

    def __init__(self, code: str, *, symbol=None, market=None, asset_type=None):
        self.code = code
        self._market = None
        self._asset_type = None
        self._symbol = None
        self._parse_code()

    def _parse_code(self):
        """ parse the code string into market, symbol and asset type

        """
        if self.code is not None:
            parts = self.code.split('.')
            if len(parts) == 2:
                self._market = parts[0]
                self._symbol = parts[1]
                self._asset_type = self.market
            elif len(parts) == 3:
                self._market = parts[0]
                self._symbol = parts[1]
                self._asset_type = parts[2]
            else:
                self._market = None
                self._symbol = None
                self._asset_type = None

    @property
    def market(self):
        return self._market

    @property
    def symbol(self):
        return self._symbol

    @property
    def asset_type(self):
        return self._asset_type
