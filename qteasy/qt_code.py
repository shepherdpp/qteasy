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


def _is_valid_code(code):
    """ check if the code is legal

    """
    if code is not None:
        parts = code.split('.')
        if len(parts) == 2:
            return True
        elif len(parts) == 3:
            return True
        else:
            return False
    else:
        return False


def _infer_market(code):
    """ infer the market from the code

    """
    if code is not None:
        parts = code.split('.')
        if len(parts) == 2:
            return parts[0]
        elif len(parts) == 3:
            return parts[0]
        else:
            return None
    else:
        return None


def _infer_asset_type(code):
    """ infer the asset type from the code

    """
    if code is not None:
        parts = code.split('.')
        if len(parts) == 2:
            return None
        elif len(parts) == 3:
            return parts[2]
        else:
            return None
    else:
        return None


class QtCode(str):
    """ special string class for market symbols, with properties
    that can be used to identify market types, and easy access of
    stock symbols and asset types

    """

    market_names = {
        'SZ': 'Shenzhen',
        'SH': 'Shanghai',
        'HK': 'Hong Kong',
        'US': 'United States',
        'BJ': 'Beijing',
    }

    def __init__(self, code: str, *, symbol=None, market=None, asset_type=None):
        self._market = None
        self._asset_type = None
        self._symbol = None
        if _is_valid_code(code):
            self.code = self._parse_code(code, symbol, market, asset_type)
        else:
            raise ValueError('Invalid code format: ' + code)

    def _parse_code(self, code, symbol, market, asset_type):
        """ parse the code string into market, symbol and asset type

        """
        if code is not None:
            parts = code.split('.')
            if len(parts) == 2:
                self._market = parts[0]
                self._symbol = parts[1]
                self._asset_type = asset_type
            elif len(parts) == 3:
                self._market = parts[0]
                self._symbol = parts[1]
                self._asset_type = parts[2]
            else:
                self._market = None
                self._symbol = None
                self._asset_type = None

            return self._symbol + '.' + self._market

        else:
            return ''

    @property
    def market(self):
        return self._market

    @property
    def market_name(self):
        return self.market_names.get(self._market, None)

    @property
    def symbol(self):
        return self._symbol

    @property
    def asset_type(self):
        return self._asset_type

    def __str__(self):
        return self.code

    def __repr__(self):
        return self.code

    def __eq__(self, other):
        return self.code == other

    def __hash__(self):
        return hash(self.code)

    def __ne__(self, other):
        return self.code != other

    def __lt__(self, other):
        return self.code < other

    def __le__(self, other):
        return self.code <= other

    def __gt__(self, other):
        return self.code > other

    def __ge__(self, other):
        return self.code >= other

    def __add__(self, other):
        return self.code + other

    def __radd__(self, other):
        return other + self.code

    def __mul__(self, other):
        return self.code * other

    def __rmul__(self, other):
        return other * self.code

    def __contains__(self, item):
        return item in self.code

    def __getitem__(self, item):
        return self.code[item]

    def __len__(self):
        return len(self.code)

    def __iter__(self):
        return iter(self.code)

    def __reversed__(self):
        return reversed(self.code)
