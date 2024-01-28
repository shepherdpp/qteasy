# coding=utf-8
# ======================================
# File:     trade_recording.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2023-04-04
# Desc:
#   functions that create, modify and
# read from system datatables that store
# trading data in live-trade mode.
# ======================================


import pandas as pd
import numpy as np

from qteasy.database import DataSource

# TODO: add TIMEZONE to qt config arguments
# TODO: move all secondary functions to trading_util.py
TIMEZONE = 'Asia/Shanghai'


# TODO: 创建一个模块级变量，用于存储交易信号的数据源，所有的交易信号都从这个数据源中读取
#  避免交易信号从不同的数据源中获取，导致交易信号的不一致性
# 9 foundational functions for account and position management
def new_account(user_name, cash_amount, data_source=None, **account_data):
    """ 创建一个新的账户

    Parameters
    ----------
    user_name: str
        用户名
    cash_amount: float
        账户的初始资金
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源
    account_data: dict
        账户的其他信息

    Returns
    -------
    int: 账户的id
    """
    # 输入数据检查在这里进行
    if cash_amount <= 0:
        raise ValueError('cash_amount must be positive!')

    import qteasy as qt
    if data_source is None:
        data_source = qt.QT_DATA_SOURCE
    if not isinstance(data_source, qt.DataSource):
        raise TypeError(f'data_source must be a DataSource instance, got {type(data_source)} instead')

    account_id = data_source.insert_sys_table_data(
            'sys_op_live_accounts',
            **{
                'user_name': user_name,
                'created_time': pd.to_datetime('today').strftime('%Y-%m-%d %H:%M:%S'),
                'cash_amount': cash_amount,
                'available_cash': cash_amount,
                'total_invest': cash_amount,
            },
            **account_data,
    )
    return account_id


def get_account(account_id, user_name=None, data_source=None):
    """ 根据account_id, 或者user_name获取账户的信息

    Parameters
    ----------
    account_id: int
        账户的id
    user_name: str, optional
        用户名, 默认为None, 表示使用account_id, 如果给出了user_name, 则忽略account_id
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源

    Returns
    -------
    dict: 账户的信息

    Raises
    ------
    KeyError: 如果账户不存在，则抛出异常
    """

    import qteasy as qt
    if data_source is None:
        data_source = qt.QT_DATA_SOURCE
    if not isinstance(data_source, qt.DataSource):
        raise TypeError(f'data_source must be a DataSource instance, got {type(data_source)} instead')
    if user_name is None:
        account = data_source.read_sys_table_data('sys_op_live_accounts', record_id=account_id)
        if account is None:
            raise KeyError(f'Account (id={account_id}) not found!')
        return account
    else:
        account = data_source.read_sys_table_data('sys_op_live_accounts', user_name=user_name)
        if account is None:
            raise KeyError(f'Account (user_name={user_name}) not found!')
        return account


def update_account(account_id, data_source=None, **account_data):
    """ 更新账户信息

    通用接口，用于更新账户的所有信息，除了账户的持仓和可用资金
    以外，还包括账户的其他状态变量

    Parameters
    ----------
    account_id: int
        账户的id
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源
    account_data: dict
        交易结果

    Returns
    -------
    None
    """

    import qteasy as qt
    if data_source is None:
        data_source = qt.QT_DATA_SOURCE
    if not isinstance(data_source, qt.DataSource):
        raise TypeError(f'data_source must be a DataSource instance, got {type(data_source)} instead')

    data_source.update_sys_table_data('sys_op_live_accounts', record_id=account_id, **account_data)


def update_account_balance(account_id, data_source=None, **cash_change):
    """ 更新账户的资金总额和可用资金, 为了避免误操作，仅允许修改现金总额、可用现金和总投资额，其他字段不可修改

    Parameters
    ----------
    account_id: int
        账户的id
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源
    cash_change: dict, optional {'cash_amount_change': float,
                                 'available_cash_change': float,
                                 'total_investment_change': float}
        可用资金的变化，其余字段不可用此函数修改

    Returns
    -------
    None
    """
    # TODO: refract this function, allow only one cash value as input argument for cash change, and
    #  change available cash and total investment according to two more input arguments:
    #  update_available_cash: bool default False and update_total_investment: bool default False

    import qteasy as qt
    if data_source is None:
        data_source = qt.QT_DATA_SOURCE
    if not isinstance(data_source, qt.DataSource):
        raise TypeError(f'data_source must be a DataSource instance, got {type(data_source)} instead')

    account_data = data_source.read_sys_table_data('sys_op_live_accounts', record_id=account_id)
    if account_data is None:
        raise RuntimeError(f'Account not found! account id: {account_id}')

    cash_amount_change = cash_change.get('cash_amount_change', 0.0)
    if not isinstance(cash_amount_change, (int, float, np.int64, np.float64)):
        raise TypeError(f'cash_amount_change must be a number, got {type(cash_amount_change)} instead')
    cash_amount = account_data['cash_amount'] + cash_amount_change

    available_cash_change = cash_change.get('available_cash_change', 0.0)
    if not isinstance(available_cash_change, (int, float, np.int64, np.float64)):
        raise TypeError(f'available_cash_change must be a number, got {type(available_cash_change)} instead')
    available_cash = account_data['available_cash'] + available_cash_change

    total_investment_change = cash_change.get('total_investment_change', 0.0)
    if not isinstance(total_investment_change, (int, float, np.int64, np.float64)):
        raise TypeError(f'total_investment_change must be a number, got {type(total_investment_change)} instead')
    total_investment = account_data['total_invest'] + total_investment_change

    # 如果可用现金超过现金总额，则报错
    if available_cash > cash_amount:
        raise RuntimeError(f'available_cash ({available_cash}) cannot be greater than cash_amount ({cash_amount})')
    # 如果可用现金小于0，则报错
    if available_cash < 0:
        raise RuntimeError(f'available_cash ({available_cash}) cannot be less than 0!')
    # 如果现金总额小于0，则报错
    if cash_amount < 0:
        raise RuntimeError(f'cash_amount cannot be less than 0!')

    # debug
    # print(f'[DEBUG]: update account balance for id: {account_id} \n'
    #       f'cash_amount: {account_data["cash_amount"]} -> {cash_amount}, \n'
    #       f'available_cash: {account_data["available_cash"]} -> {available_cash} \n'
    #       f'total_investment: {account_data["total_invest"]} -> {total_investment}')
    # 更新账户的资金总额和可用资金
    data_source.update_sys_table_data(
            'sys_op_live_accounts',
            record_id=account_id,
            cash_amount=cash_amount,
            available_cash=available_cash,
            total_invest=total_investment,
    )


def get_position_by_id(pos_id, data_source=None):
    """ 通过pos_id获取持仓的信息

    Parameters
    ----------
    pos_id: int
        持仓的id
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源

    Returns
    -------
    持仓的信息
    dict: {'account_id': int,
           'symbol': str,
           'position': str,
           'qty': float,
           'available_qty': float,
           'cost': float,
           }

    Raises
    ------
    RuntimeError: 如果持仓不存在，则报错
    """

    import qteasy as qt
    if data_source is None:
        data_source = qt.QT_DATA_SOURCE
    if not isinstance(data_source, qt.DataSource):
        raise TypeError(f'data_source must be a DataSource instance, got {type(data_source)} instead')

    position = data_source.read_sys_table_data('sys_op_positions', record_id=pos_id)
    if position is None:
        raise RuntimeError('Position not found!')
    return position


def get_position_ids(account_id, symbol=None, position_type=None, data_source=None):
    """ 根据symbol和position_type获取账户的持仓id, 如果没有持仓，则返回空列表, 如果有多个持仓，则返回所有持仓的id

    Parameters
    ----------
    account_id: int
        账户的id
    symbol: str, optional
        交易标的的代码，一次只能提供一个symbol
    position_type: str, optional, {'long', 'short'}
        持仓类型, 'long' 表示多头持仓, 'short' 表示空头持仓
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源

    Returns
    -------
    position_ids: list of int: 持仓的id列表, 如果没有持仓, 则返回空列表
    """

    import qteasy as qt
    if data_source is None:
        data_source = qt.QT_DATA_SOURCE
    if not isinstance(data_source, qt.DataSource):
        raise TypeError(f'data_source must be a DataSource instance, got {type(data_source)} instead')

    # 获取账户的持仓
    position_filter = {'account_id': account_id}
    if symbol is not None:
        position_filter['symbol'] = str(symbol)
    if position_type is not None:
        position_filter['position'] = str(position_type)

    try:
        position = data_source.read_sys_table_data(
                table='sys_op_positions',
                record_id=None,
                **position_filter,
        )
    except Exception as e:
        print(f'Error occurred: {e}')
        return []
    if position is None:
        return []
    return position.index.tolist()


def get_or_create_position(account_id: int, symbol: str, position_type: str, data_source: DataSource = None):
    """ 获取账户的持仓, 如果持仓不存在，则创建一条新的持仓记录

    Parameters
    ----------
    account_id: int
        账户的id
    symbol: str
        交易标的的代码
    position_type: str, {'long', 'short'}
        持仓类型, 'long'表示多头持仓, 'short'表示空头持仓
    data_source: DataSource, optional
        数据源的名称, 默认为None, 表示使用默认的数据源

    Returns
    -------
    int: 返回持仓记录的id，如果匹配的持仓记录不存在，则创建一条新的空持仓记录，并返回新持仓记录的id
    """

    from qteasy import DataSource, QT_DATA_SOURCE
    if data_source is None:
        data_source = QT_DATA_SOURCE
    if not isinstance(data_source, DataSource):
        raise TypeError(f'data_source must be a DataSource instance, got {type(data_source)} instead')

    # 检查account_id是否存在，如果不存在，则报错，否则创建的持仓记录将无法关联到账户
    account = get_account(account_id, data_source=data_source)
    if account is None:
        raise RuntimeError(f'account_id {account_id} not found!')

    if not isinstance(symbol, str):
        raise TypeError(f'symbol must be a str, got {type(symbol)} instead')
    if not isinstance(position_type, str):
        raise TypeError(f'position_type must be a str, got {type(position_type)} instead')
    if position_type not in ('long', 'short'):
        raise ValueError(f'position_type must be "long" or "short", got {position_type} instead')
    # debug
    # print(f'[DEBUG]account_id: {account_id}, symbol: {symbol}, position_type: {position_type}')
    position = data_source.read_sys_table_data(
            table='sys_op_positions',
            record_id=None,
            **{
                'account_id': account_id,
                'symbol': symbol,
                'position': position_type,
            },
    )
    if position is None:
        return data_source.insert_sys_table_data(
                table='sys_op_positions',
                **{
                    'account_id':account_id,
                    'symbol': symbol,
                    'position': position_type,
                    'qty': 0,
                    'available_qty': 0,
                    'cost': 0,
                },
        )
    # position已存在，此时position中只能有一条记录，否则说明记录重复，报错
    if len(position) > 1:
        raise RuntimeError(f'position record is duplicated, got {len(position)} records: \n{position}')
    return position.index[0]


def update_position(position_id, data_source=None, **position_data):
    """ 更新账户的持仓，包括持仓的数量和可用数量，account_id, position和symbol不可修改

    Parameters
    ----------
    position_id: int
        持仓的id
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源
    position_data: dict, optional, {'qty_change': float, 'available_qty_change': float, 'cost': float}
        持仓的数据，只能修改qty, available_qty, cost 这三类数据中的任意一个或多个

    Returns
    -------
    None
    """
    # TODO: (maybe) refract this function, require only one change value as argument, change
    #       the available qty according to boolean argument 'change_available_qty', and change
    #       the cost automatically according to the average cost of increased qty

    import qteasy as qt
    if data_source is None:
        data_source = qt.QT_DATA_SOURCE
    if not isinstance(data_source, qt.DataSource):
        raise TypeError(f'data_source must be a DataSource instance, got {type(data_source)} instead')

    if not isinstance(position_id, (int, np.int64)):
        raise TypeError(f'position_id must be an int, got {type(position_id)} instead')

    # 从数据库中读取持仓数据，修改后再写入数据库
    position = data_source.read_sys_table_data('sys_op_positions', record_id=position_id)
    if position is None:
        raise RuntimeError(f'position_id {position_id} not found!')

    qty_change = position_data.get('qty_change', 0.0)
    if not isinstance(qty_change, (int, float, np.int64, np.float64)):
        raise TypeError(f'qty_change must be a int or float, got {type(qty_change)} instead')
    qty = position['qty'] + qty_change

    available_qty_change = position_data.get('available_qty_change', 0.0)
    if not isinstance(available_qty_change, (int, float, np.int64, np.float64)):
        raise TypeError(f'available_qty_change must be a int or float, got {type(available_qty_change)} instead')
    available_qty = position['available_qty'] + available_qty_change

    prev_cost = position['cost']
    cost = position_data.get('cost', prev_cost)
    if cost is not None:
        if not isinstance(cost, (int, float, np.int64, np.float64)):
            raise TypeError(f'cost must be a int or float, got {type(cost)} instead')

    # 如果可用数量超过持仓数量，则报错
    if available_qty > qty:
        raise RuntimeError(f'available_qty ({position["available_qty"]}) cannot be greater than '
                           f'qty ({position["qty"]})')
    # 如果可用数量小于0，则报错
    if available_qty < 0:
        raise RuntimeError(f'available_qty ({position["available_qty"]}) cannot be less than 0!')
    # 如果持仓数量小于0，则报错
    if qty < 0:
        raise RuntimeError(f'qty ({position["qty"]}) cannot be less than 0!')

    # debug
    # print(f'{pd.to_datetime("now")}[DEBUG]: update position for id: '
    #       f'{position_id} / {position["symbol"]} / {position["position"]}\n'
    #       f'qty: {position["qty"]} -> {qty}, \n'
    #       f'available_qty: {position["available_qty"]} -> {available_qty} \n'
    #       f'cost: {position["cost"]} -> {cost}')

    data_source.update_sys_table_data(
            'sys_op_positions',
            record_id=position_id,
            qty=qty,
            available_qty=available_qty,
            cost=cost,
    )


def get_account_positions(account_id, data_source=None):
    """ 根据account_id获取账户的所有持仓

    Parameters
    ----------
    account_id: int
        账户的id
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源

    Returns
    -------
    positions: pandas.DataFrame, columns=['account_id', 'symbol', 'position', 'qty', 'available_qty']
        账户的所有持仓
        account_id: int, 账户的id
        symbol: str, 股票代码
        position: str, 持仓类型，'long'表示多头持仓，'short'表示空头持仓
        qty: int, 持仓数量
        available_qty: int, 可用数量
    None: 如果账户不存在或持仓不存在，则返回None
    """

    import qteasy as qt
    if data_source is None:
        data_source = qt.QT_DATA_SOURCE
    if not isinstance(data_source, qt.DataSource):
        raise TypeError(f'data_source must be a DataSource instance, got {type(data_source)} instead')

    positions = data_source.read_sys_table_data(
            'sys_op_positions',
            record_id=None,
            **{'account_id': account_id},
    )
    if positions is None:
        return pd.DataFrame(columns=['account_id', 'symbol', 'position', 'qty', 'available_qty'])
    return positions


# Four 2nd foundational functions for account and position availability check
def get_account_cash_availabilities(account_id, data_source=None):
    """ 根据账户id获取账户的可用资金和资金总额
    返回一个tuple，第一个元素是账户的可用资金，第二个元素是账户的资金总额

    Parameters
    ----------
    account_id: int
        账户的id
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源

    Returns
    -------
    cash_availabilities: tuple
        (cash_amount: float, 账户的可用资金
         available_cash: float, 账户的资金总额
         total_invest: float, 账户的总投入
        )
    """

    account = get_account(account_id=account_id, data_source=data_source)
    return account['cash_amount'], account['available_cash'], account['total_invest']


def get_account_position_availabilities(account_id, shares=None, data_source=None):
    """ 根据account_id读取账户的持仓，筛选出与shares相同的symbol的持仓，返回两个ndarray，分别为
    每一个share对应的持仓的数量和可用数量

    Parameters
    ----------
    account_id: int
        账户的id
    shares: list of str, optional
        需要输出的持仓的symbol列表, 如果不给出shares，则返回所有持仓的数量和可用数量
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源

    Returns
    -------
    (symbols, own_amounts, available_amounts, costs): tuple, (list, ndarray, ndarray, ndarray)
        symbols: 持仓share的symbol列表
        own_amounts: 每一个share对应的持仓的数量
        available_amounts: 每一个share对应的持仓的可用数量
        costs: 每一个share对应的持仓的成本
    """

    # 根据account_id读取账户的全部持仓
    positions = get_account_positions(account_id=account_id, data_source=data_source)

    if positions is None:
        return shares, np.zeros(len(shares)), np.zeros(len(shares))
    # 如果没有给出shares，则读取账户中所有持仓的symbol
    if shares is None:
        shares = positions['symbol'].unique()
    if isinstance(shares, str):
        from qteasy.utilfuncs import str_to_list
        shares = str_to_list(shares)
    if not isinstance(shares, (list, tuple, np.ndarray)):
        raise TypeError(f'shares must be a list, tuple or ndarray, got {type(shares)} instead')

    own_amounts = []
    available_amounts = []
    costs = []
    for share in shares:
        # 检查symbol为share的持仓是否存在
        position = positions[(positions['symbol'] == share) & (positions['qty'] > 0)]
        if position.empty:
            own_amounts.append(0.0)
            available_amounts.append(0.0)
            costs.append(0.0)
            continue
        # 如果同时存在多头和空头持仓，则报错
        if len(position) > 1:
            raise RuntimeError(f'position for {share} has more than one position!')
        position = position.iloc[0]
        # 如果存在多头持仓，则将多头持仓的数量和可用数量放入列表
        if position['position'] == 'long':
            own_amounts.append(position['qty'])
            available_amounts.append(position['available_qty'])
            costs.append(position['cost'])
            continue
        # 如果存在空头持仓，则将空头持仓的数量和可用数量乘以-1并放入列表
        if position['position'] == 'short':
            own_amounts.append(-1 * position['qty'])
            available_amounts.append(-1 * position['available_qty'])
            costs.append(position['cost'])
            continue
    # 如果列表长度与shares长度不相等，则报错
    if len(own_amounts) != len(shares):
        raise RuntimeError(f'own_amounts length ({len(own_amounts)}) is not equal to shares length ({len(shares)})')
    if len(available_amounts) != len(shares):
        raise RuntimeError(f'available_amounts length ({len(available_amounts)}) is not equal to '
                           f'shares length ({len(shares)})')
    if len(costs) != len(shares):
        raise RuntimeError(f'costs length ({len(costs)}) is not equal to shares length ({len(shares)})')
    # 将列表转换为ndarray并返回
    result = (
        shares,
        np.array(own_amounts).astype('float'),
        np.array(available_amounts).astype('float'),
        np.array(costs).astype('float')
    )

    return result


def get_account_position_details(account_id, shares=None, data_source=None):
    """ 根据account_id读取账户的持仓，筛选出与shares相同的symbol的持仓，返回一个DataFrame，包含
    每一个share对应的持仓的symbol，position，qty和可用数量。

    Parameters
    ----------
    account_id: int
        账户的id
    shares: list of str, optional
        需要输出的持仓的symbol列表, 如果不给出shares，则返回所有持仓的数量和可用数量
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源

    Returns
    -------
    positions: DataFrame, columns=['symbol', 'qty', 'available_qty'， 'cost']
        account持仓的symbol，qty, available_qty和cost, symbol与shares的顺序一致
    """

    # 根据account_id读取账户的全部持仓
    symbols, amounts, available_amounts, costs = get_account_position_availabilities(
            account_id=account_id,
            shares=shares,
            data_source=data_source
    )
    # 将symbol，position，qty和available_qty放入DataFrame并返回
    positions = pd.DataFrame(
            {
                'qty': amounts,
                'available_qty': available_amounts,
                'cost': costs,
            },
            index=symbols,
    ).T
    return positions


# 4 foundational functions for trade order
def record_trade_order(order, data_source=None):
    """ 将交易信号写入数据库

    Parameters
    ----------
    order: dict
        标准形式的交易订单，格式为
        {
            'pos_id': int,  # 持仓的id
            'direction': str,  # 交易方向，'buy'或'sell'
            'order_type': str,  # 订单类型，'market'或'limit'
            'qty': float,  # 交易数量
            'price': float,  # 交易价格
            'submitted_time': datetime.datetime,  # 交易信号提交时间
            'status': str,  # 交易信号状态
        }
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源

    Returns
    -------
    order_id: int
    写入数据库的交易信号的id
    """

    import qteasy as qt
    if data_source is None:
        data_source = qt.QT_DATA_SOURCE
    if not isinstance(data_source, qt.DataSource):
        raise TypeError(f'data_source must be a DataSource instance, got {type(data_source)} instead')

    # 检查交易信号的格式和数据合法性
    if not isinstance(order, dict):
        raise TypeError(f'signal must be a dict, got {type(order)} instead')
    if not isinstance(order['pos_id'], (int, np.int64)):
        raise TypeError(f'signal["pos_id"] must be an int, got {type(order["pos_id"])} instead')
    if not isinstance(order['direction'], str):
        raise TypeError(f'signal["direction"] must be a str, got {type(order["direction"])} instead')
    if not isinstance(order['order_type'], str):
        raise TypeError(f'signal["order_type"] must be a str, got {type(order["order_type"])} instead')
    if not isinstance(order['qty'], (float, int, np.float64, np.int64)):
        raise TypeError(f'signal["qty"] must be a float, got {type(order["qty"])} instead')
    if not isinstance(order['price'], (float, int, np.float64, np.int64)):
        raise TypeError(f'signal["price"] must be a float, got {type(order["price"])} instead')
    if order['qty'] <= 0:
        raise RuntimeError(f'signal["qty"] ({order["qty"]}) must be greater than 0!')
    if order['price'] <= 0:
        raise RuntimeError(f'signal["price"] ({order["price"]}) must be greater than 0!')

    return data_source.insert_sys_table_data('sys_op_trade_orders', **order)


def read_trade_order(order_id, data_source=None):
    """ 根据order_id从数据库中读取交易信号

    Parameters
    ----------
    order_id: int
        交易信号的id
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源

    Returns
    -------
    signal: dict
        交易信号
    """
    if not isinstance(order_id, (int, np.int64)):
        raise TypeError(f'order_id must be an int, got {type(order_id)} instead')

    import qteasy as qt
    if data_source is None:
        data_source = qt.QT_DATA_SOURCE
    if not isinstance(data_source, qt.DataSource):
        raise TypeError(f'data_source must be a DataSource instance, got {type(data_source)} instead')

    return data_source.read_sys_table_data('sys_op_trade_orders', record_id=order_id)


def update_trade_order(order_id, data_source=None, status=None, qty=None, raise_if_status_wrong=False):
    """ 更新数据库中trade_signal的状态或其他信，这里只操作trade_signal，不处理交易结果

    trade_order的所有字段中，可以更新字段只有status和qty(qty只能在submit的时候更改，一旦submit之后就不能再更改。
    status的更新遵循下列规律：
    1. 如果status为 'created'，则可以更新为 'submitted', 同时设置'submitted_time';
    2. 如果status为 'submitted'，则可以更新为 'canceled', 'partial-filled' 或 'filled';
    3. 如果status为 'partial-filled'，则可以更新为 'canceled' 或 'filled';
    4. 如果status为 'canceled' 或 'filled'，则不可以再更新.

    Parameters
    ----------
    order_id: int
        交易信号的id
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源
    status: str, optional
        交易信号的状态, 默认为None, 表示不更新状态
    qty: float, optional
        交易信号的数量, 默认为None, 表示不更新数量
    raise_if_status_wrong: bool, default False
        如果status不符合规则，则抛出RuntimeError, 默认为False, 表示不抛出异常

    Returns
    -------
    order_id: int, 如果更新成功，返回更新后的交易信号的id
    None, 如果更新失败，返回None

    Raises
    ------
    TypeError
        如果data_source不是DataSource的实例，则抛出TypeError
    RuntimeError
        如果trade_signal读取失败，则抛出RuntimeError
        如果status不符合规则，则抛出RuntimeError
    """

    if status is None:
        return None

    import qteasy as qt
    if data_source is None:
        data_source = qt.QT_DATA_SOURCE
    if not isinstance(data_source, qt.DataSource):
        raise TypeError(f'data_source must be a DataSource instance, got {type(data_source)} instead')
    if status is not None:
        if not isinstance(status, str):
            raise TypeError(f'status must be a str, got {type(status)} instead')
        if status not in ['created', 'submitted', 'canceled', 'partial-filled', 'filled']:
            raise RuntimeError(f'status ({status}) not in [created, submitted, canceled, partial-filled, filled]!')

    trade_signal = data_source.read_sys_table_data('sys_op_trade_orders', record_id=order_id)

    # 如果trade_signal读取失败，则报错
    if trade_signal is None:
        raise RuntimeError(f'Trade signal (order_id = {order_id}) not found!')

    # 如果trade_signal的状态为 'created'，则可以更新为 'submitted'
    if trade_signal['status'] == 'created' and status == 'submitted':
        if qty is not None:
            assert isinstance(qty, (float, int, np.float64, np.int64)), f'qty must be a float, got {type(qty)} instead'
            assert qty >= 0, f'qty ({qty}) must be greater than or equal to 0!'
        else:
            qty = trade_signal['qty']
        submit_time = pd.to_datetime('today').strftime('%Y-%m-%d %H:%M:%S')
        return data_source.update_sys_table_data(
                'sys_op_trade_orders',
                record_id=order_id,
                submitted_time=submit_time,
                status=status,
                qty=qty,
        )
    # 如果trade_signal的状态为 'submitted'，则可以更新为 'canceled', 'partial-filled' 或 'filled'
    if trade_signal['status'] == 'submitted' and status in ['canceled', 'partial-filled', 'filled']:
        return data_source.update_sys_table_data(
                'sys_op_trade_orders',
                order_id,
                status=status
        )
    # 如果trade_signal的状态为 'partial-filled'，则可以更新为 'canceled' 或 'filled'
    if trade_signal['status'] == 'partial-filled' and status in ['canceled', 'filled']:
        return data_source.update_sys_table_data(
                'sys_op_trade_orders',
                order_id,
                status=status
        )

    if raise_if_status_wrong:
        raise RuntimeError(f'Wrong status update: {trade_signal["status"]} -> {status}')

    return


def query_trade_orders(account_id,
                       symbol=None,
                       position=None,
                       direction=None,
                       order_type=None,
                       status=None,
                       data_source=None):
    """ 根据symbol、direction、status 从数据库中查询交易信号并批量返回结果

    Parameters
    ----------
    account_id: int
        账户的id
    symbol: str, optional
        交易标的
    position: str, optional, {'long', 'short'}
        持仓方向, 默认为None, 表示不限制, 'long' 表示多头, 'short' 表示空头
    direction: str, optional, {'buy', 'sell'}
        交易方向, 默认为None, 表示不限制, 'buy' 表示买入, 'sell' 表示卖出
    order_type: str, optional, {'market', 'limit', 'stop', 'stop_limit'}
        交易类型, 默认为None, 表示不限制, 'market' 表示市价单, 'limit' 表示限价单, 'stop' 表示止损单, 'stop_limit' 表示止损限价单
    status: str, optional, {'created', 'submitted', 'canceled', 'partial-filled', 'filled'}
        交易信号状态
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源

    Returns
    -------
    pd.DataFrame, columns = ['pos_id', 'direction', 'order_type', 'qty', 'price', 'submitted_time', 'status']
        交易订单列表，包含所有符合查询条件的订单的DataFrame
    """

    # TODO: move this function to trading_util.py
    # TODO: allow list of str as input for symbol, position, direction, order_type, status

    import qteasy as qt
    if data_source is None:
        data_source = qt.QT_DATA_SOURCE
    if not isinstance(data_source, qt.DataSource):
        raise TypeError(f'data_source must be a DataSource instance, got {type(data_source)} instead')

    # 从数据库中读取position的id
    pos_ids = get_position_ids(account_id, symbol, position, data_source=data_source)
    if pos_ids is None:
        return pd.DataFrame(columns=['pos_id', 'direction', 'order_type', 'qty', 'price', 'submitted_time', 'status'])

    data_filter = {}
    if direction is not None:
        data_filter['direction'] = direction
    if order_type is not None:
        data_filter['order_type'] = order_type
    if status is not None:
        data_filter['status'] = status

    res = []
    for pos_id in pos_ids:
        res.append(
                data_source.read_sys_table_data(
                        'sys_op_trade_orders',
                        pos_id=pos_id,
                        **data_filter,
                )
        )
    if all(r is None for r in res):
        return pd.DataFrame(columns=['pos_id', 'direction', 'order_type', 'qty', 'price', 'submitted_time', 'status'])

    return pd.concat(res)


# 2 2nd level functions for trade signal
def read_trade_order_detail(order_id, data_source=None):
    """ 从数据库中读取交易信号的详细信息，包括从关联表中读取symbol和position的信息

    Parameters
    ----------
    order_id: int
        交易信号的id
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源

    Returns
    -------
    trade_signal_detail: dict
        包含symbol和position信息的交易信号明细:
        {
            'account_id': int,
            'pos_id': int,
            'symbol': str,
            'position': str,
            'direction': str,
            'order_type': str,
            'qty': float,
            'price': float,
            'status': str,
            'submitted_time': str,
        }
    """

    import qteasy as qt
    if data_source is None:
        data_source = qt.QT_DATA_SOURCE
    if not isinstance(data_source, qt.DataSource):
        raise TypeError(f'data_source must be a DataSource instance, got {type(data_source)} instead')

    trade_signal_detail = read_trade_order(order_id, data_source=data_source)
    if trade_signal_detail is None:
        return None
    pos_id = trade_signal_detail['pos_id']
    position = get_position_by_id(pos_id, data_source=data_source)
    if position is None:
        raise RuntimeError(f'Position (position_id = {pos_id}) not found!')
    # 从关联表中读取symbol和position的信，添加到trade_signal_detail中
    trade_signal_detail['account_id'] = position['account_id']
    trade_signal_detail['symbol'] = position['symbol']
    trade_signal_detail['position'] = position['position']
    return trade_signal_detail


def save_parsed_trade_orders(account_id, symbols, positions, directions, quantities, prices, data_source=None):
    """ 根据parse_trade_signal的结果，将交易订单要素组装成完整的交易订单dict，并将交易信号保存到数据库

    Parameters
    ----------
    account_id: int
        账户ID
    symbols: list of str
        交易信号对应的股票代码
    positions: list of str
        交易信号对应的持仓类型
    directions: list of str
        交易信号对应的交易方向
    quantities: list of float
        交易信号对应的交易数量
    prices: list of float
        交易信号对应的股票价格
    data_source: str, optional
        交易信号对应的数据源, 默认为None, 使用默认数据源

    Returns
    -------
    order_ids: list of int
        生成的交易订单的id
    """

    if len(symbols) == 0:
        return []

    if len(symbols) != len(positions) or \
            len(symbols) != len(directions) or \
            len(symbols) != len(quantities) or \
            len(symbols) != len(prices):
        raise ValueError('Length of symbols, positions, directions, quantities and prices must be the same')

    order_ids = []
    # 逐个处理所有的交易信号要素
    for sym, pos, dirc, qty, price in zip(symbols, positions, directions, quantities, prices):
        # 获取pos_id, 如果pos_id不存在，则新建一个posiiton
        pos_id = get_or_create_position(account_id, sym, pos, data_source=data_source)
        # 生成交易信号dict
        trade_order = {
            'pos_id': pos_id,
            'direction': dirc,
            'order_type': 'market',  # TODO: 交易信号的order_type应该是可配置的，增加其他配置选项
            'qty': qty,
            'price': price,
            'submitted_time': None,
            'status': 'created'
        }
        sig_id = record_trade_order(trade_order, data_source=data_source)
        order_ids.append(sig_id)

    return order_ids


# 5 foundational functions for trade result
def write_trade_result(trade_result, data_source=None):
    """ 将交易结果写入数据库, 并返回交易结果的id

    Parameters
    ----------
    trade_result: dict
        交易结果
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源

    Returns
    -------
    result_id: int
        交易结果的id
    """

    if not isinstance(trade_result, dict):
        raise TypeError('trade_results must be a dict')

    if not isinstance(trade_result['order_id'], (int, np.int64)):
        raise TypeError(f'order_id of trade_result must be an int, got {type(trade_result["order_id"])} instead')
    if not isinstance(trade_result['filled_qty'], (int, float, np.int64, np.float64)):
        raise TypeError(f'filled_qty of trade_result must be a number, got {type(trade_result["filled_qty"])} instead')
    if not isinstance(trade_result['price'], (int, float, np.int64, np.float64)):
        raise TypeError(f'price of trade_result must be a number, got {type(trade_result["price"])} instead')
    if not isinstance(trade_result['transaction_fee'], (int, float, np.int64, np.float64)):
        raise TypeError(f'transaction_fee of trade_result must be a number, got '
                        f'{type(trade_result["transaction_fee"])} instead')
    if isinstance(trade_result['execution_time'], str):
        try:
            execution_time = pd.to_datetime(trade_result['execution_time']).strftime('%Y-%m-%d %H:%M:%S')
            trade_result['execution_time'] = execution_time
        except Exception as e:
            raise RuntimeError(f'{e}, Invalid execution_time {trade_result["execution_time"]}, '
                               f'can not be converted to datetime format')
    if not isinstance(trade_result['canceled_qty'], (int, float, np.int64, np.float64)):
        raise TypeError(f'canceled_qty of trade_result must be a number, got '
                        f'{type(trade_result["canceled_qty"])} instead')
    if not isinstance(trade_result['delivery_status'], str):
        raise TypeError(f'delivery_status of trade_result must be a str, '
                        f'got {type(trade_result["delivery_status"])} instead')
    if not isinstance(trade_result['delivery_amount'], (int, float, np.int64, np.float64)):
        raise TypeError(f'delivery_amount of trade_result must be a number, got '
                        f'{type(trade_result["delivery_amount"])} instead')
    if trade_result['order_id'] <= 0:
        raise ValueError('order_id can not be less than or equal to 0')
    if trade_result['filled_qty'] < 0:
        raise ValueError('filled_qty can not be less than 0')
    if trade_result['price'] < 0:
        raise ValueError('price can not be less than 0')
    if trade_result['transaction_fee'] < 0:
        raise ValueError('transaction_fee can not be less than 0')
    if trade_result['canceled_qty'] < 0:
        raise ValueError('canceled_qty can not be less than 0')
    if trade_result['delivery_amount'] < 0:
        # raise ValueError('delivery_amount can not be less than 0')
        pass
    if trade_result['delivery_status'] not in ['ND', 'DL']:
        raise ValueError(f'delivery_status can only be ND or DL, got {trade_result["delivery_status"]} instead')

    import qteasy as qt
    if data_source is None:
        data_source = qt.QT_DATA_SOURCE
    if not isinstance(data_source, qt.DataSource):
        raise TypeError(f'data_source must be a DataSource instance, got {type(data_source)} instead')

    result_id = data_source.insert_sys_table_data('sys_op_trade_results', **trade_result)
    return result_id


def update_trade_result(result_id, delivery_status, data_source=None):
    """ 更新交易结果的delivery_status

    Parameters
    ----------
    result_id: int
        交易结果的id
    delivery_status: str
        交易结果的delivery_status
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源
    """
    if not isinstance(result_id, (int, np.int64)):
        raise TypeError('result_id must be an int')
    if not isinstance(delivery_status, str):
        raise TypeError('delivery_status must be a str')
    if delivery_status not in ['ND', 'DL']:
        raise ValueError(f'delivery_status can only be ND or DL, got {delivery_status} instead')

    import qteasy as qt
    if data_source is None:
        data_source = qt.QT_DATA_SOURCE
    if not isinstance(data_source, qt.DataSource):
        raise TypeError(f'data_source must be a DataSource instance, got {type(data_source)} instead')

    data_source.update_sys_table_data(
            'sys_op_trade_results',
            result_id,
            **{'delivery_status': delivery_status},
    )


def read_trade_result_by_id(result_id, data_source=None):
    """ 根据result_id从数据库中读取一条交易结果, 并返回交易结果的dict形式

    Parameters
    ----------
    result_id: int
        交易结果的id
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源

    Returns
    -------
    trade_result: dict 交易结果
        {'order_id': int,  # 交易结果对应的order_id
        'filled_qty': float,  # 交易结果的成交数量
        'price': float,  # 交易结果的成交价格
        'transaction_fee': float,  # 交易结果的交易费用
        'execution_time': str,  # 交易结果的成交时间
        'canceled_qty': float,  # 交易结果的撤单数量
        'delivery_amount': float,  # 交易结果的交割数量
        'delivery_status': str}  # 交易结果的交割状态
    """
    if not isinstance(result_id, (int, np.int64)):
        raise TypeError('result_id must be an int')

    import qteasy as qt
    if data_source is None:
        data_source = qt.QT_DATA_SOURCE
    if not isinstance(data_source, qt.DataSource):
        raise TypeError(f'data_source must be a DataSource instance, got {type(data_source)} instead')

    trade_result = data_source.read_sys_table_data('sys_op_trade_results', result_id)
    return trade_result


def read_trade_results_by_order_id(order_id, data_source=None):
    """ 根据order_id从数据库中读取所有与signal相关的交易结果，以DataFrame的形式返回

    Parameters
    ----------
    order_id: int, list of int
        交易信号的id, 可以是一个int, 也可以是一个int的list, 表示多个交易信号的id
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源

    Returns
    -------
    trade_results: pd.DataFrame, columns=['order_id', 'filled_qty', 'price', 'transaction_fee', 'execution_time',
                        'canceled_qty', 'delivery_amount', 'delivery_status']
    交易结果:
    order_id: int 交易信号的id
    filled_qty: int 成交数量
    price: float 成交价格
    transaction_fee: float 交易费用
    execution_time: datetime.datetime 成交时间
    canceled_qty: int 撤单数量
    delivery_amount: float 交割金额
    delivery_status: str 交割状态
    """
    if not isinstance(order_id, (int, np.int64, np.ndarray, list, )):
        raise TypeError(f'order_id must be an integer, a list of integers or a numpy array of integers, '
                        f'got {type(order_id)} instead')
    if isinstance(order_id, np.ndarray):
        order_id = order_id.tolist()
    if isinstance(order_id, list):
        if not all([isinstance(i, (int, np.int64)) for i in order_id]):
            raise TypeError('order_id must be an int or a list of int')

    import qteasy as qt
    if data_source is None:
        data_source = qt.QT_DATA_SOURCE
    if not isinstance(data_source, qt.DataSource):
        raise TypeError(f'data_source must be a DataSource instance, got {type(data_source)} instead')

    if isinstance(order_id, (int, np.int64)):
        trade_results = data_source.read_sys_table_data(
                'sys_op_trade_results',
                **{'order_id': order_id},
        )
    else:  # order_id is a list
        trade_results = data_source.read_sys_table_data(
            'sys_op_trade_results',
        )
    if trade_results is None:
        return pd.DataFrame(columns=['order_id', 'filled_qty', 'price', 'transaction_fee', 'execution_time',
                                     'canceled_qty', 'delivery_amount', 'delivery_status'])
    if isinstance(order_id, list):
        trade_results = trade_results[trade_results['order_id'].isin(order_id)]

    return trade_results


def read_trade_results_by_delivery_status(delivery_status, data_source=None):
    """ 根据delivery_status从数据库中读取所有与signal相关的交易结果，以DataFrame的形式返回

    Parameters
    ----------
    delivery_status: str
        交易结果的交割状态
    data_source: str, optional
        数据源的名称, 默认为None, 表示使用默认的数据源

    Returns
    -------
    trade_results: pd.DataFrame
        交易结果
    """
    if not isinstance(delivery_status, str):
        raise TypeError('delivery_status must be a str')
    if not delivery_status in ['ND', 'DL']:
        raise ValueError(f'delivery_status can only be ND or DL, got {delivery_status} instead')

    import qteasy as qt
    if data_source is None:
        data_source = qt.QT_DATA_SOURCE
    if not isinstance(data_source, qt.DataSource):
        raise TypeError(f'data_source must be a DataSource instance, got {type(data_source)} instead')

    trade_results = data_source.read_sys_table_data(
            'sys_op_trade_results',
            **{'delivery_status': delivery_status},
    )
    return trade_results
