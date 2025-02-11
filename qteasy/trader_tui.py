# coding=utf-8
# ======================================
# File:     trader_tui.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2024-04-08
# Desc:
#   Terminal User Interface (TUI) for
# qteasy live trade system.
# ======================================

import sys
import time

from threading import Thread

from rich.text import Text
from textual.screen import ModalScreen

from textual import (
    work,
    on,
)
from textual.app import (
    App,
    ComposeResult,
)

from textual.containers import (
    Grid,
    Horizontal,
)

from textual.widgets import (
    Header,
    Footer,
    Button,
    Static,
    RichLog,
    DataTable,
    TabbedContent,
    Tree,
    Digits,
)

from textual.widgets import (
    TabPane,
    Label,
    Input,
)

from qteasy.utilfuncs import sec_to_duration


class SysLog(RichLog):
    """A widget to display system logs."""

    BINDINGS = [
        ("ctrl+p", "pause_trader", "Pause"),
        ("ctrl+r", "resume_trader", "Resume"),
    ]

    def write_with_timestamp(self, msg:str) -> None:
        """Write a message to the log, adding Time infor before the message."""
        from qteasy.utilfuncs import get_current_timezone_datetime
        datetime = get_current_timezone_datetime(time_zone='local').strftime("%Y-%m-%d %H:%M:%S")
        msg = f"[{datetime}] - {msg}"
        self.write(msg)

        return


class StrategyTree(Tree):
    """A widget to display the strategies."""

    BINDINGS = [
        ("shift+c", "change", "Change"),
    ]

    def action_change(self) -> None:
        """ Action to change the strategy."""
        return


class HoldingTable(DataTable):
    """A widget to display current holdings."""

    BINDINGS = [
        ("ctrl+b", "buy_stock", "Buy"),
        ("ctrl+s", "sell_stock", "Sell"),
        ("shift+c", "change", "Change"),
        ("ctrl+r", "refresh_table", "Refresh"),
    ]

    df_columns = ("name", "qty", "available_qty", "current_price", "cost",
                  "total_cost", "market_value", "profit", "profit_ratio")
    headers = ("Symbol",
               "Name", "Qty", "Available", "Price", "Cost",
               "Total Cost", "Value", "Profit", "Profit Ratio")

    def action_buy_stock(self) -> None:
        """ Action to buy a stock."""

        self.app.refresh_ui = False
        symbol, price, position = self.get_sel_symbol_price_and_position()
        if not symbol:
            return

        def on_input(input_string):
            # input the quantity to buy or sell
            if input_string == '':
                return
            try:
                quantity = float(input_string)
                self.app.submit_order(symbol, position, quantity, 0, 'buy')
            except Exception as e:
                self.app.trader.send_message(f'Error submitting order: {e}')
                return
            self.app.refresh_ui = True
            self.app.refresh_order()

        pop_str = f"Input qty for buying {symbol}({position[1].upper()}) @ market price:"
        self.app.push_screen(InputScreen(pop_str), on_input)

    def action_sell_stock(self) -> None:
        """ Action to sell a stock."""

        self.app.refresh_ui = False
        symbol, price, position = self.get_sel_symbol_price_and_position()
        if not symbol:
            return

        def on_input(input_string):
            # input the quantity to buy or sell
            if input_string == '':
                return
            try:
                quantity = float(input_string)
                self.app.submit_order(symbol, position, quantity, 0, 'sell')
            except Exception as e:
                self.app.trader.send_message(f'Error submitting order: {e}')
                return
            self.app.refresh_ui = True
            self.app.refresh_order()

        pop_str = f"Input qty for selling {symbol}({position[1].upper()}) @ market price:"
        self.app.push_screen(InputScreen(pop_str), on_input)

    def action_change(self) -> None:
        """ Action to change the strategy."""
        return

    def action_refresh_table(self) -> None:
        """ refresh table"""
        self.app.refresh_holdings()

    def get_sel_symbol_price_and_position(self):
        """ Get the selected symbol and price in the watch list."""
        sel_row = self.cursor_row
        if not sel_row:
            return None, None, None
        symbol = str(self.get_row_at(sel_row)[0])
        qty = str(self.get_row_at(sel_row)[2])
        price = str(self.get_row_at(sel_row)[4])
        try:
            qty = float(qty)
            price = float(price)
        except Exception:
            return None, None, None

        position = 'long' if qty > 0 else 'short'

        return symbol, price, position


class OrderTable(DataTable):
    """A widget to display current holdings."""

    BINDINGS = [
        ("ctrl+b", "buy_stock", "Buy"),
        ("ctrl+s", "sell_stock", "Sell"),
        ("ctrl+shift+c", "cancel_order", "Cancel"),
        ("ctrl+r", "refresh_table", "Refresh"),
    ]

    df_columns = ("symbol", "position", "direction", "order_type", "qty", "price_quoted",
                  "submitted_time", "status", "price_filled", "filled_qty", "canceled_qty", "transaction_fee",
                  "execution_time",  "delivery_status")

    headers = ("ID",
               "Symbol", "Position", "Side", "Type", "Qty", "Quote",
               "Submitted", "Status", "Filled Price", "Filled Qty", "Canceled Qty", "Fee",
               "Execution Time", "Delivery")

    def action_buy_stock(self) -> None:
        """ Action to buy a stock."""

        self.app.refresh_ui = False
        symbol, position = self.get_sel_symbol_and_position()
        if not symbol:
            return

        def on_input(input_string):
            # input the quantity to buy or sell
            if input_string == '':
                return
            try:
                quantity = float(input_string)
                self.app.submit_order(symbol, position, quantity, 0., 'buy')
            except Exception as e:
                self.app.trader.send_message(f'Error submitting order: {e}')
                return
            self.app.refresh_ui = True
            self.app.refresh_order()

        pop_str = f"Input qty for buying {symbol}({position[1].upper()}) @ market price:"
        self.app.push_screen(InputScreen(pop_str), on_input)

    def action_sell_stock(self) -> None:
        """ Action to sell a stock."""

        self.app.refresh_ui = False
        symbol, position = self.get_sel_symbol_and_position()
        if not symbol:
            return

        def on_input(input_string):
            # input the quantity to buy or sell
            if input_string == '':
                return

            try:
                quantity = float(input_string)
                self.app.submit_order(symbol, position, quantity, 0., 'sell')
            except Exception as e:
                self.app.trader.send_message(f'Error submitting order: {e}')
                return

            self.app.refresh_ui = True
            self.app.refresh_order()

        pop_str = f"Input qty for selling {symbol}({position}), please input quantity:"
        self.app.push_screen(InputScreen(pop_str), on_input)

    def action_cancel_order(self) -> None:
        """ Action to cancel an order."""
        def confirm_cancel(confirmed:bool) -> None:
            if confirmed:
                self.app.action_cancel_order()
            self.app.refresh_ui = True

        self.app.refresh_ui = False
        self.app.push_screen(QuitScreen(), confirm_cancel)

    def action_refresh_table(self) -> None:
        """ refresh table"""
        self.app.refresh_order()

    def get_sel_symbol_and_position(self):
        """ Get the selected symbol and price in the watch list."""
        sel_row = self.cursor_row
        if not sel_row:
            return None, None
        symbol = str(self.get_row_at(sel_row)[1])
        position = str(self.get_row_at(sel_row)[2])
        return symbol, position


class WatchTable(DataTable):
    """A widget to display current holdings."""

    BINDINGS = [
        ("ctrl+a", "add_symbol", "Add"),
        ("delete", "remove_symbol", "Remove"),
        ("ctrl+b", "buy_stock", "Buy"),
        ("ctrl+s", "sell_stock", "Sell"),
        ("ctrl+r", "refresh_table", "Refresh"),
    ]

    df_columns = ("name", "close", "pre_close", "open", "high",
                  "low", "vol", "amount", "change")

    headers = ("Symbol",
               "Name", "Price", "Last Close", "Open", "High",
               "Low", "Volume", "Amount", "Change")

    def action_add_symbol(self) -> None:
        """Action to add a symbol to watch list from a dialog."""
        def on_input(input_string):
            # received input string: input_string, add it to the watch list
            from .utilfuncs import is_complete_cn_stock_symbol_like, str_to_list
            symbols = str_to_list(input_string)

            for symbol in symbols:
                if is_complete_cn_stock_symbol_like(symbol):
                    self.app.trader.watch_list.append(symbol)

            self.app.refresh_ui = True
            self.app.refresh_watches()

        self.app.refresh_ui = False
        self.app.push_screen(InputScreen("Input symbols to add to watch list"), on_input)

    def action_remove_symbol(self) -> None:
        """Action to remove selected symbol, if no symbol selected, don't do anything."""
        watch_list = self.app.trader.watch_list
        self.app.refresh_ui = False
        symbol, price = self.get_sel_symbol_and_price()
        if not symbol:
            return

        try:
            watch_list.remove(symbol)
        except ValueError:
            return

        self.app.refresh_ui = True
        self.app.refresh_watches()

    def action_buy_stock(self) -> None:
        """ Action to buy a stock."""

        self.app.refresh_ui = False
        symbol, price = self.get_sel_symbol_and_price()
        if not symbol:
            return

        def on_input(input_string):
            # input the quantity to buy or sell
            if input_string == '':
                return
            try:
                quantity = float(input_string)
                self.app.submit_order(symbol, 'long', quantity, float(price), 'buy')
            except ValueError as e:
                self.app.trader.send_message(f'Error submitting order: {e}')
                return

            self.app.refresh_ui = True
            self.app.refresh_order()

        pop_str = f"Input qty for buying {symbol}(L) @ {price}:"
        self.app.push_screen(InputScreen(pop_str), on_input)

    def action_sell_stock(self) -> None:
        """ Action to sell a stock."""

        self.app.refresh_ui = False
        symbol, price = self.get_sel_symbol_and_price()
        if not symbol:
            return

        def on_input(input_string):
            # input the quantity to buy or sell
            if input_string == '':
                return

            try:
                quantity = float(input_string)
                self.app.submit_order(symbol, 'long', quantity, float(price), 'sell')
            except Exception as e:
                self.app.trader.send_message(f'Error submitting order: {e}')
                return

            self.app.refresh_ui = True
            self.app.refresh_order()

        pop_str = f"Input qty for selling {symbol}(L) @ {price}:"
        self.app.push_screen(InputScreen(pop_str), on_input)

    def action_refresh_table(self) -> None:
        """ refresh table"""
        self.app.refresh_watches()

    def get_sel_symbol_and_price(self):
        """ Get the selected symbol and price in the watch list."""
        sel_row = self.cursor_row
        if not sel_row:
            return None, None
        symbol = str(self.get_row_at(sel_row)[0])
        if symbol not in self.app.trader.asset_pool:
            # if the symbol is not in the asset pool, return None
            return None, None
        price = str(self.get_row_at(sel_row)[2])
        price = float(price)
        if price <= 0:
            return None, None
        return symbol, price


class TradeLogTable(DataTable):
    """A widget to display all trade logs."""

    BINDINGS = [
        ("ctrl+r", "refresh_table", "Refresh"),
    ]

    df_columns = ("datetime", "reason", "symbol", "name", "position_type",
                  "direction", "trade_qty", "price", "trade_cost", "qty",
                  "available_qty", "holding_cost", "cash", "available_cash")

    headers = ("ID",
               "Date", "Reason", "Symbol", "Name", "Position",
               "Direction", "Qty", "Price", "Trade fee", "Holding",
               "Available", "Holding cost", "Own cash", "Available cash")

    def action_refresh_table(self) -> None:
        """ refresh table"""
        self.app.refresh_trade_log()


class Tables(TabbedContent):
    """A widget to display tables."""

    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane("Holdings"):
                yield HoldingTable(
                        id='holdings',
                        fixed_columns=1,
                        zebra_stripes=True,
                        cursor_type='row',
                )
            with TabPane("Orders"):
                yield OrderTable(
                        id='orders',
                        fixed_columns=4,
                        zebra_stripes=True,
                        cursor_type='row',
                )
            with TabPane("Watches"):
                yield WatchTable(
                        id='watches',
                        fixed_columns=3,
                        zebra_stripes=True,
                        cursor_type='row',
                )
            with TabPane("TradeLogs"):
                yield TradeLogTable(
                        id='tradelog',
                        fixed_columns=5,
                        zebra_stripes=True,
                        cursor_type='row',
                )


class InfoPanel(TabbedContent):
    """A widget to display information."""

    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane("System"):
                yield Static(id='system', name='system')
            with TabPane("Info"):
                yield Static(id='info', name='info')
            with TabPane("Strategy"):
                yield StrategyTree(id='operator', label='operator')


class DisplayPanel(Horizontal):
    """A widget to display the key information."""

    def compose(self) -> ComposeResult:
        yield Digits(id='total_value', name='Value', value='0.00')
        yield Digits(id='earning', name='Earning', value='0.00')
        yield Digits(id='cash', name='Cash', value='0.00')


class InputScreen(ModalScreen):
    """Screen that prints a prompt and takes input from user"""

    def __init__(self, question: str) -> None:
        self.question = question
        self.input_string = ''
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Grid(
            Input(placeholder=self.question, id="input_box", value=''),
            Button("OK", id="ok", variant="success"),
            Button("Cancel", id="cancel"),
            id="input_dialog",
        )

    @on(Input.Changed, "#input_box")
    def handle_input_changed(self, event: Input.Changed) -> None:
        self.input_string = event.value

    @on(Input.Submitted, "#input_box")
    def handle_input(self, event: Input.Submitted) -> None:
        self.dismiss(event.value)

    @on(Button.Pressed, "#ok")
    def handle_ok(self) -> None:
        self.dismiss(self.input_string)

    @on(Button.Pressed, "#cancel")
    def handle_cancel(self) -> None:
        self.dismiss('')


class QuitScreen(ModalScreen):
    """Screen with a dialog to quit."""

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("Are you sure you want to quit?", id="question"),
            Button("Quit", variant="error", id="quit"),
            Button("Cancel", variant="primary", id="cancel"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.dismiss(True)
        else:
            self.dismiss(False)


class TraderApp(App):
    """A Textual app to manage stopwatches."""

    CSS_PATH = "tui_style.tcss"
    BINDINGS = [
        ("d", "toggle_dark", "Dark mode"),
        ("ctrl+q", "request_quit", "Quit app"),
    ]

    def __init__(self, trader, *args, **kwargs):
        """ Initialize the app with a trader.

        Parameters
        ----------
        trader : Trader
            A trader object to manage the trades.
        """
        super().__init__(*args, **kwargs)
        self.dark:bool = True
        self.trader = trader
        self.status:str = 'init'
        self.refresh_ui = True

    def trader_event_loop(self):
        """ Event loop for the trader. continually check message queue of trader and broker,
        and update the UI accordingly.

        this event loop should be running in a separate thread.

        """
        Thread(target=self.trader.run).start()
        Thread(target=self.trader.broker.run).start()

        system_log = self.query_one(SysLog)
        display = self.query_one(DisplayPanel)

        self.status = 'running'

        system_log.write_with_timestamp(f"System started, status: {self.status}")

        trader_info = self.trader.info(detail=True, system=True)
        self.refresh_values(trader_info)
        self.refresh_info_panels(trader_info)
        self.refresh_operator_tree()

        cum_time_counter = 0

        while True:
            time.sleep(0.1)

            if self.status == 'stopped':
                break

            # update current date and time
            current_time = self.trader.get_current_tz_datetime().strftime("%Y-%m-%d %H:%M:%S")

            next_task = self.trader.next_task
            count_down = sec_to_duration(self.trader.count_down_to_next_task, estimation=True)

            system_log.border_title = f"System Log - Next Task: {next_task} in {count_down}"
            display.border_title = f"{self.status}: {current_time}"

            # check the message queue of the trader
            if not self.trader.message_queue.empty():
                msg = self.trader.message_queue.get()
                system_log.write_with_timestamp(msg)

                if any(words in msg for words in ['RAN STRATEGY', 'RESULT', 'DELIVERY']):
                    # if ran strategy or got result from broker, refresh UI
                    self.refresh_order()
                    self.refresh_holdings()
                    self.refresh_trade_log()

            # check the message queue of the broker
            if not self.trader.broker.broker_messages.empty():
                msg = self.trader.broker.broker_messages.get()
                system_log.write_with_timestamp(msg)

            if self.trader.status not in ['running', 'paused']:
                info_refresh_interval = 600  # every 1 minutes
            else:
                info_refresh_interval = 50  # every 5 seconds while running

            # refresh the operator tree every interval
            cum_time_counter += 1
            if cum_time_counter % info_refresh_interval == 0:

                trader_info = self.trader.info(detail=True, system=True)
                self.refresh_values(trader_info)
                self.refresh_info_panels(trader_info)
                self.refresh_operator_tree()
                self.refresh_holdings()
                self.refresh_watches()
                self.refresh_trade_log()
                cum_time_counter = 0

            if self.trader.status not in ['running', 'paused']:
                continue

        system_log.write_with_timestamp(f"System stopped, status: {self.status}")

    @work(exclusive=True, thread=True)
    def refresh_holdings(self):
        """Refresh the holdings table."""
        if not self.refresh_ui:
            return
        # get the holdings from the trader
        holdings = self.query_one(HoldingTable)
        holdings.clear()
        pos = self.trader.account_position_info
        if pos.empty:
            return
        pos = pos.reindex(columns=holdings.df_columns)
        list_tuples = list(pos.itertuples(name=None))

        for row in list_tuples:
            row = list(row)
            earning_rate = row[9]
            row[2] = f'{row[2]:.2f}'
            row[3] = f'{row[3]:.2f}'
            row[4] = f'{row[4]:.2f}'
            row[5] = f'{row[5]:.2f}'
            row[6] = f'{row[6]:.2f}'
            row[7] = f'{row[7]:.2f}'
            row[8] = f'{row[8]:.2f}'
            row[9] = f"{earning_rate:.2%}"

            if earning_rate > 0:
                row_color = 'red'
            elif earning_rate < 0:
                row_color = 'green'
            else:
                row_color = ''
            styled_row = [
                Text(str(cell), style=f"bold {row_color}") for cell in row
            ]
            holdings.add_row(*styled_row)

    @work(exclusive=True, thread=True)
    def refresh_order(self):
        """Refresh the order table."""
        if not self.refresh_ui:
            return
        orders = self.query_one(OrderTable)
        orders.clear()
        order_list = self.trader.history_orders(with_trade_results=True)
        if order_list.empty:
            return
        order_list = order_list.reindex(columns=orders.df_columns)
        list_tuples = list(order_list.itertuples(name=None))
        for row in list_tuples:
            row = list(row)
            row[5] = f'{row[5]:.2f}'
            
            if row[8] == 'canceled':
                row_color = 'gray'
            elif row[3] == 'sell':
                row_color = 'green'
            elif row[3] == 'buy':
                row_color = 'red'
            else:
                row_color = 'yellow'

            styled_row = row[:4]
            styled_row += [
                Text(str(cell), style=f"bold {row_color}") for cell in row[4:]
            ]
            orders.add_row(*styled_row)

    @work(exclusive=True, thread=True)
    def refresh_watches(self):
        """Refresh the watch list."""
        if not self.refresh_ui:
            return
        watches = self.query_one(WatchTable)
        watched_prices = self.trader.update_watched_prices()
        watched_prices = watched_prices.reindex(columns=watches.df_columns)
        watches.clear()
        if watched_prices.empty:
            return

        list_tuples = list(watched_prices.itertuples(name=None))
        for row in list_tuples:
            row = list(row)
            change = row[9]
            row[9] = f"{change:.2%}"
            if change > 0:
                row_color = 'red'
            elif change < 0:
                row_color = 'green'
            else:
                row_color = ''

            styled_row = row[:2]
            styled_row += [
                Text(str(cell), style=f"bold {row_color}") for cell in row[2:]
            ]
            watches.add_row(*styled_row)

    @work(exclusive=True, thread=True)
    def refresh_trade_log(self):
        """Refresh the trade log table."""
        if not self.refresh_ui:
            return
        trade_log = self.query_one(TradeLogTable)
        t_log = self.trader.read_trade_log()
        trade_log.clear()

        if t_log.empty:
            return
        t_log = t_log.reindex(columns=trade_log.df_columns)
        t_log.fillna('', inplace=True)
        list_tuples = list(t_log.itertuples(name=None))
        for row in list_tuples:

            row = list(row)
            reason = row[2]
            direction = row[6]
            if reason == 'manual':
                row_color = 'yellow'
            elif reason == 'delivery':
                row_color = 'blue'
            elif direction == 'sell':
                row_color = 'bold green'
            elif direction == 'buy':
                row_color = 'bold red'
            else:
                row_color = ''

            styled_row = [
                Text(str(cell), style=row_color) for cell in row
            ]

            trade_log.add_row(*styled_row)

    @work(exclusive=True, thread=True)
    def refresh_info_panels(self, trader_info):
        """Refresh the information panel"""

        if not self.refresh_ui:
            return

        info = self.query_one(InfoPanel)
        system = self.query_one(SysLog)

        account = trader_info['Account ID']
        user_name = trader_info['User Name']
        created_on = trader_info['Created on']
        started_on = trader_info['Started on']
        broker_name = trader_info['Broker Name']
        broker_status = trader_info['Broker Status']
        asset_pool = trader_info['Asset Pool']
        asset_pool_size = trader_info['Asset in Pool']

        total_investment = trader_info['Total Investment']
        total_value = trader_info['Total Value']
        total_roi = trader_info['Total ROI']
        total_roi_rate = trader_info['Total ROI Rate']
        total_cash = trader_info['Total Cash']
        available_cash = trader_info['Available Cash']
        cash_percent = trader_info['Cash Percent']
        total_stock_value = trader_info['Total Stock Value']
        total_stock_profit = trader_info['Total Stock Profit']

        trader_status = self.trader.status
        investment_info = ''

        investment_info += f'[b]Total Investment:[/b]   {total_investment:.2f}\n'
        if total_value < total_investment:
            investment_info += f'[b]Total Value:[/b]        [b green]{total_value:.2f}[/b green]\n'
            investment_info += f'[b]Total ROI:[/b]          [b green]{total_roi:.2f}[/b green]\n'
            investment_info += f'[b]Total ROI Rate:[/b]     [b green]{total_roi_rate:.2%}[/b green]\n'
        else:
            investment_info += f'[b]Total Value:[/b]        [b red]{total_value:.2f}[/b red]\n'
            investment_info += f'[b]Total ROI:[/b]          [b red]{total_roi:.2f}[/b red]\n'
            investment_info += f'[b]Total ROI Rate:[/b]     [b red]{total_roi_rate:.2%}[/b red]\n'
        investment_info += f'[b]Total Cash:[/b]         {total_cash:.2f} / {cash_percent:.1%}\n'
        investment_info += f'[b]Available Cash:[/b]     {available_cash:.2f}\n'
        if total_stock_profit > 0:
            investment_info += f'[b]Total Stock Value:[/b]  [b red]{total_stock_value:.2f}[/b red]\n'
            investment_info += f'[b]Total Stock Profit:[/b] [b red]{total_stock_profit:.2f}[/b red]\n'
        else:
            investment_info += f'[b]Total Stock Value:[/b]  [b green]{total_stock_value:.2f}[/b green]\n'
            investment_info += f'[b]Total Stock Profit:[/b] [b green]{total_stock_profit:.2f}[/b green]\n'

        info.update(
                investment_info
        )

        system.update(
                f'[b]Python:[/b]             {trader_info["python"]}\n'
                f'[b]qteasy:[/b]             {trader_info["qteasy"]}\n'
                f'[b]Tushare:[/b]            {trader_info["tushare"]}\n'
                f'[b]Ta-lib:[/b]             {trader_info["ta-lib"]}\n'
                f'[b]Local Datasource:[/b]   {trader_info["Local DataSource"]}\n'
                f'[b]Account:[/b]            {account}\n'
                f'[b]Username:[/b]           {user_name}\n'
                f'[b]Created On:[/b]         {created_on}\n'
                f'[b]Started On:[/b]         {started_on}\n'
                f'[b]Status:[/b]             {trader_status}\n'
                f'[b]Broker:[/b]             {broker_name}\n'
                f'[b]Broker Status:[/b]      {broker_status}\n'
                f'[b]Asset Pool({asset_pool_size}):[/b]\n{asset_pool}'
        )

    @work(exclusive=True, thread=True)
    def refresh_values(self, trader_info):
        """Refresh the total value, earning and cash."""
        if not self.refresh_ui:
            return

        total_value = trader_info['Total Value']
        total_return_of_investment = trader_info['Total ROI']
        # total_roi_rate = trader_info['Total ROI Rate']
        own_cash = trader_info['Total Cash']
        # total_market_value = trader_info['Total Stock Value']

        value = self.query_one('#total_value')
        value.border_title = "Total Value"
        value.update(f"{total_value:.2f}")

        earning = self.query_one('#earning')
        earning.border_title = "Total Return"
        earning.update(f"{total_return_of_investment:.2f}")

        # set text colors of value and earning based on the value
        if total_return_of_investment > 0:
            value.styles.color = 'red'
            earning.styles.color = 'red'
        else:
            value.styles.color = 'green'
            earning.styles.color = 'green'

        cash = self.query_one('#cash')
        cash.border_title = "Own Cash"
        cash.update(f"{own_cash:.2f}")

    @work(exclusive=True, thread=True)
    def refresh_operator_tree(self):
        """Refresh the operator tree.
        The operator tree has 3 layers of nodes:
        1. Timing: strategy timings
        2. Strategy: strategies
        3. Properties: strategy properties
        """
        if not self.refresh_ui:
            return
        tree = self.query_one(StrategyTree)
        tree.clear()

        op = self.trader.operator
        tree.root.expand()

        # add first level nodes per timing
        for timing in op.strategy_timings:
            timing_node = tree.root.add(f"Timing: {timing}", expand=True)
            for strategy in op.get_strategies_by_run_timing(timing):
                strategy_node = timing_node.add(f"Strategy: {strategy.name}", expand=True)
                strategy_node.add_leaf(f"Run freq: {strategy.strategy_run_freq}")
                strategy_node.add_leaf(f"Parameters: {strategy.pars}")
                strategy_node.add_leaf(f"Par Types: {strategy.par_types}")
                strategy_node.add_leaf(f"Data Types: {strategy.data_types}")

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield DisplayPanel(id='display')
        yield Tables(id='tables')
        yield InfoPanel(id='info_panel')
        yield SysLog(id='log')
        yield Footer()

    def on_mount(self) -> None:
        """Actions to perform after mounting the app."""

        # updated status
        trader_info = self.trader.info(detail=True, system=True)
        self.refresh_values(trader_info)
        self.refresh_info_panels(trader_info)
        self.refresh_operator_tree()

        # initialize widgets
        tables = self.query_one(Tables)
        tables.border_title = "Tables"

        # get the strategies from the trader
        info_pad = self.query_one(InfoPanel)
        info_pad.border_title = "Information"

        # refresh all the data tables, adding columns and refreshing the data
        holdings = self.query_one("#holdings")
        holdings.add_columns(*holdings.headers)
        self.refresh_holdings()
        orders = self.query_one("#orders")
        orders.add_columns(*orders.headers)
        self.refresh_order()
        watches = self.query_one("#watches")
        watches.add_columns(*watches.headers)
        self.refresh_watches()
        trade_log = self.query_one("#tradelog")
        trade_log.add_columns(*trade_log.headers)
        self.refresh_trade_log()

        system_log = self.query_one(SysLog)
        system_log.border_title = "System Log"
        # start the trader, broker and the trader event loop all in separate threads
        Thread(target=self.trader_event_loop).start()

        return

    def _on_exit_app(self) -> None:
        """Actions to perform before exiting the app.
        """
        # stop the trader, broker and the trader event loop
        self.trader.run_task('stop')
        time.sleep(0.1)

        self.status = 'stopped'

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    def action_pause_trader(self) -> None:
        """ Parse the trader"""
        syslog = self.query_one(SysLog)
        syslog.write_with_timestamp(f"ctrl-p pressed, Pausing the trader")
        self.trader.add_task('pause')

    def action_resume_trader(self) -> None:
        """ Resume the trader"""
        syslog = self.query_one(SysLog)
        syslog.write_with_timestamp(f"ctrl-r pressed, Resuming the trader")
        self.trader.add_task('resume')

    def submit_order(self, symbol, position, qty, price, direction) -> None:
        """ Action to buy a stock.

        Parameters
        ----------
        symbol : str
            The symbol of the stock to buy.
        position : str
            The position of the stock to buy.
        qty : float
            The quantity of the stock to buy.
        price : float
            The price of the stock to buy.
        direction : str
            The direction of the order, 'buy' or 'sell'.

        Returns
        -------
        None
        """

        syslog = self.query_one(SysLog)

        trade_order = self.trader.submit_trade_order(
                symbol=symbol,
                qty=qty,
                price=price,
                position=position,
                direction=direction,
                order_type='market',
        )
        if trade_order:
            self.trader.broker.order_queue.put(trade_order)
            order_id = trade_order['order_id']
            syslog.write_with_timestamp(
                    f'Order <{order_id}> has been submitted to broker: '
                    f'{trade_order["direction"]} {trade_order["qty"]:.1f} of {symbol} '
                    f'at price {trade_order["price"]:.2f}'
            )

        if not self.trader.is_market_open:
            syslog.write_with_timestamp(
                    f'Market is not open, order might not be executed immediately'
            )

        return

    def action_cancel_order(self) -> None:
        """ Action to cancel an order."""
        # def confirm_cancel(confirmed:bool) -> None:
        #     if confirmed:
        #         self.trader.add_task('cancel')
        #     self.refresh_ui = True
        #
        # self.refresh_ui = False
        # self.push_screen(QuitScreen(), confirm_cancel)
        raise NotImplementedError

    def action_request_quit(self) -> None:
        """Action to display the quit dialog."""
        def confirm_exit(confirmed:bool) -> None:
            if confirmed:
                self.exit()
            self.refresh_ui = True

        self.refresh_ui = False
        self.push_screen(QuitScreen(), confirm_exit)

