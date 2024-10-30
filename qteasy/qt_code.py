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


from .utilfuncs import AVAILABLE_ASSET_TYPES


def _is_valid_code(code: str) -> bool:
    """ check if the code is legal

    """
    if not isinstance(code, str):
        return False
    # no space or special characters
    if any([c in code for c in ' ~!@#$%^&*()_+={}[]|\\:;\"\'<>,?/']):
        return False

    # max two parts separated by a dot and length of each part is at least 1
    parts = code.split('.')
    if len(parts) > 2:
        return False
    if len(parts) == 1 and len(parts[0]) < 4:
        return False

    if not all([len(p) > 0 for p in parts]):
        return False
    # if both parts are longer than 2, then return False
    if len(parts) == 2 and all([len(p) > 2 for p in parts]):
        return False

    return True


def _infer_symbol_market(code):
    """ infer the symbol and market from the code as a tuple:

    Parameters
    ----------
    (code, market) : tuple
        tuple of code and market
    """
    # if the code splits into only one part, then it is the symbol
    parts = code.split('.')
    if len(parts) == 1:
        symbol = parts[0]
        # infer market according to symbol
        if len(symbol) == 5 and all(c.isdigit() for c in symbol):
            # symbols like '00001' are HK stocks
            return symbol, 'HK'
        elif len(symbol) == 8 and all(c.isdigit() for c in symbol):
            # symbols like '00000001' are SH options
            return symbol, 'SH'
        elif len(symbol) == 6 and all(c.isdigit() for c in symbol):
            # symbols like '000001' are SH stocks or SZ stocks depending on the first digit
            if symbol[0] in ['6', '9']:
                return symbol, 'SH'
            elif symbol[0] in ['0', '3']:
                return symbol, 'SZ'
            else:
                return symbol, 'SH'
        elif len(symbol) < 6 and all(c.isdigit() for c in symbol[-4:]) and all(c.isalpha() for c in symbol[:-4]):
            # symbols like 'A0001' or 'CU2310' are futures
            initials = ''.join([c for c in symbol if c.isalpha()])
            if initials in ['CU', 'AL', 'AL-C/P', 'PB', 'ZN', 'ZN-C/P', 'SN', 'NI', 'SS', 'AU',
                            'AG', 'RB', 'HC', 'BU', 'RU', 'FU', 'SP', 'RU-C/P', 'WR']:
                return symbol, 'SHF'
            elif initials in ['A', 'B', 'M', 'M-C/P', 'Y', 'P', 'I', 'J', 'JM', 'C', 'CS', 'L', 'V', 'PP', 'EG',
                              'RR', 'EB', 'I-C/P', 'PG', 'JD', 'FB', 'BB', 'LH']:
                return symbol, 'DCE'
            elif initials in ['RM', 'OI', 'CF', 'TA', 'SR', 'MA', 'FG', 'ZC', 'CY', 'SA', 'PF', 'JR', 'RS', 'PM',
                              'WH', 'RI', 'LR', 'SF', 'SM', 'AP', 'CJ', 'UR', 'PK', 'PX', 'SH']:
                return symbol, 'ZCE'
            elif initials in ['IF', 'IH', 'IC', 'TF', 'T', 'TS']:
                return symbol, 'CFX'
            elif initials in ['SC', 'NR', 'LU', 'BC']:
                return symbol, 'INE'
            elif initials in ['SI', 'LC']:
                return symbol, 'GFE'
        elif len(symbol) <= 6 and all(c.isalpha() for c in symbol):
            # symbols like 'MSFT' or 'AAPL' are US stocks
            return symbol, 'US'
        else:
            # the rest are temporarily considered as SH stocks
            return parts[0], 'SH'
    else:
        # if both parts are pure letters, then the longer one is the symbol
        if all([p.isalpha() for p in parts]):
            return max(parts, key=len), min(parts, key=len)
        # if one part is pure letters and the other is pure digits, then the digit part is the symbol
        elif parts[0].isalpha() and parts[1].isdigit():
            return parts[1], parts[0]
        elif parts[1].isalpha() and parts[0].isdigit():
            return parts[0], parts[1]
        # if both parts are digits, then the longer one is the symbol
        elif parts[0].isdigit() and parts[1].isdigit():
            return max(parts, key=len), min(parts, key=len)
        # if both parts are mixed, then the longer one is the symbol
        else:
            return max(parts, key=len), min(parts, key=len)


def _infer_asset_type(symbol, market):
    """ infer the asset type according to symbol and market

    """
    # rules are different from market to market
    if market == 'SH':
        if len(symbol) > 6 and all(c.isdigit() for c in symbol):
            return 'OPT'
        elif symbol[0:3] in ['600', '601', '603', '900']:
            return 'E'
        elif symbol[0:3] in ['000']:
            return 'IDX'
        elif (symbol[0:3] > '100') and (symbol < '270'):
            return 'BOND'
        elif symbol[0] == '5':
            return 'FD'
        else:
            return 'E'
    elif market == 'SZ':
        if symbol[0:2] in ['00', '03', '07', '08', '09']:
            return 'E'
        elif symbol[0:2] in ['10', '11', '12', '13']:
            return 'BOND'
        elif symbol[0:2] in ['17', '18']:
            return 'FD'
        elif symbol[0:2] in ['39']:
            return 'IDX'
        else:
            return 'E'
    elif market == 'BJ':
        return 'E'
    elif market == 'OF':
        return 'FD'
    elif market in ['DCE', 'ZCE', 'CFX', 'INE', 'GFE', 'SHF']:
        return 'FT'

    elif market == 'HK':
        if symbol[0:1] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
            return 'E'
        else:
            return 'IDX'

    elif market == 'US':
        return 'E'

    else:
        return 'E'


class QtCode:
    """ special string class for market symbols, with properties
    that can be used to identify market types, and easy access of
    stock symbols and asset types

    """

    market_names = {
        'SZ': 'Shenzhen',
        'SH': 'Shanghai',
        'BJ': 'Beijing',
        'OF': 'Out market Fund',
        'DCE': 'Dalian Commodity Exchange',
        'ZCE': 'Zhengzhou Commodity Exchange',
        'CFX': 'China Financial Exchange',
        'INE': 'International Exchange',
        'GFE': 'Guangzhou Futures Exchange',
        'SHF': 'Shanghai Futures Exchange',
        'HK': 'Hong Kong',
        'US': 'United States',
    }

    def __init__(self, code_or_symbol=None, *, market=None, asset_type=None):
        """ initialize the QtCode object

        Parameters
        ----------
        code_or_symbol : str
            the market symbol or complete code with market separated by a dot
        market : str
            the market of the symbol
        asset_type : str
            the asset type of the symbol
        """
        self._symbol = None
        self._market = None
        self._asset_type = None
        self._code = None

        if _is_valid_code(code_or_symbol):
            if market is None:
                symbol, market = _infer_symbol_market(code_or_symbol)
            else:
                symbol, _ = _infer_symbol_market(code_or_symbol)

            if asset_type is None:
                asset_type = _infer_asset_type(symbol, market)

            self._parse_code(symbol, market, asset_type)
        else:
            raise ValueError(f'Invalid code: {code_or_symbol}')

    def _parse_code(self, symbol, market, asset_type) -> None:
        """ check if symbol matches market and asset type
        if so, return the code, otherwise raise ValueError
        """
        if asset_type not in AVAILABLE_ASSET_TYPES:
            raise ValueError(f'Invalid asset type: {asset_type}')

        if market not in self.market_names:
            raise ValueError(f'Invalid market: {market}')

        self._symbol = symbol
        self._market = market
        self._asset_type = asset_type
        self._code = f'{symbol}.{market}'

        return None

    @property
    def code(self):
        return self._code

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

    def upper(self):
        return self.code.upper()

    def lower(self):
        return self.code.lower()

    def title(self):
        return self.code.title()

    def __get__(self, instance, owner):
        return self.code

    def __iter__(self):
        return iter(self.code)

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

    def __setitem__(self, key, value):
        self.code[key] = value

    def __delitem__(self, key):
        del self.code[key]

    def __len__(self):
        return len(self.code)

    def __iter__(self):
        return iter(self.code)

    def __reversed__(self):
        return reversed(self.code)

    def __contains__(self, item: object) -> object:
        return item in self.code

    def find(self, sub, start=None, end=None):
        return self.code.find(sub, start, end)

    def rfind(self, sub, start=None, end=None):
        return self.code.rfind(sub, start, end)

    def index(self, sub, start=None, end=None):
        return self.code.index(sub, start, end)

    def rindex(self, sub, start=None, end=None):
        return self.code.rindex(sub, start, end)

    def count(self, sub, start=None, end=None):
        return self.code.count(sub, start, end)
