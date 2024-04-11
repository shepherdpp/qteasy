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

import time

from threading import Thread

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Header, Footer, Button, Static, RichLog, DataTable, TabbedContent, Tree, Digits
from textual.widgets import TabPane

from .utilfuncs import sec_to_duration


holding_columns = ("symbol", "qty", "available", "cost", "name", "price", "value", "profit", "profit_ratio", "last")
order_columns = ("symbol", "position", "qty", "price", "type", "status", "time", "8", "9", "10", "11", "12", "13", "14", "15")


class SysLog(RichLog):
    """A widget to display system logs."""
    pass


class StrategyTree(Tree):
    """A widget to display the strategies."""
    pass


class HoldingTable(DataTable):
    """A widget to display current holdings."""
    pass


class OrderTable(DataTable):
    """A widget to display current holdings."""
    pass


class Tables(TabbedContent):
    """A widget to display tables."""

    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane("Holdings"):
                yield HoldingTable(id='holdings')
            with TabPane("Orders"):
                yield OrderTable(id='orders')


class InfoPanel(TabbedContent):
    """A widget to display information."""

    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane("Info"):
                yield Static(id='info', name='info')
            with TabPane("Strategy"):
                yield StrategyTree(id='strategy', label='Information')


class DisplayPanel(Horizontal):
    """A widget to display the key information."""

    def compose(self) -> ComposeResult:
        yield Digits(id='total_value', name='Value', value='0.00')
        yield Digits(id='earning', name='Earning', value='0.00')
        yield Digits(id='cash', name='Cash', value='0.00')


class ControlPanel(Static):
    """A widget to display control buttons."""

    def compose(self) -> ComposeResult:
        yield Button("Start", id='start', name="start")
        yield Button("Stop", id='stop', name="stop")
        yield Button("Pause", id='pause', name="pause")
        yield Button("Resume", id='resume', name="resume")
        yield Button("Exit", id='exit', name="exit")


class TraderApp(App):
    """A Textual app to manage stopwatches."""

    CSS_PATH = "tui_style.tcss"
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def __init__(self, trader, *args, **kwargs):
        """ Initialize the app with a trader.

        Parameters
        ----------
        trader : Trader
            A trader object to manage the trades.
        """
        super().__init__(*args, **kwargs)
        self.dark = True
        self.trader = trader
        self.status = 'init'

    def trader_event_loop(self):
        """ Event loop for the trader. continually check message queue of trader and broker,
        and update the UI accordingly.

        this event loop should be running in a separate thread.

        """
        Thread(target=self.trader.run).start()
        Thread(target=self.trader.broker.run).start()

        system_log = self.query_one(SysLog)
        info = self.query_one('#info')
        display = self.query_one(DisplayPanel)

        self.status = 'running'

        system_log.write(f"System started, status: {self.status}")

        while True:

            # update current date and time
            current_time = self.trader.get_current_tz_datetime().strftime("%Y-%m-%d %H:%M:%S")

            next_task = self.trader.next_task
            count_down = sec_to_duration(self.trader.count_down_to_next_task, estimation=True)

            system_log.border_title = f"System Log - Next Task: {next_task} in {count_down}"
            display.border_title = f"{self.status}: {current_time}"

            # check the message queue of the trader
            if not self.trader.message_queue.empty():
                msg = self.trader.message_queue.get()
                system_log.write(msg)

                if any(words in msg for words in ['RAN STRATEGY', 'RESULT']):
                    # if ran strategy or got result from broker, refresh UI
                    self.refresh_order()
                    self.refresh_holdings()

                    trader_info = self.trader.info(detail=True)
                    self.refresh_values(trader_info)
                    self.refresh_info_panel(trader_info)

            # check the message queue of the broker
            if not self.trader.broker.broker_messages.empty():
                msg = self.trader.broker.broker_messages.get()
                system_log.write(msg)

            if self.status == 'stopped':
                break

            time.sleep(0.1)

        system_log.write(f"System stopped, status: {self.status}")

    def refresh_holdings(self):
        """Refresh the holdings table."""
        # get the holdings from the trader
        holdings = self.query_one(HoldingTable)
        holdings.add_columns(*holding_columns)
        pos = self.trader.account_position_info
        holdings.clear()
        if not pos.empty:
            # import numpy as np
            # pos.replace(np.nan, 0, inplace=True)
            list_tuples = list(pos.itertuples(name=None))
            holdings.add_row(*list_tuples[0])

    def refresh_order(self):
        """Refresh the order table."""
        orders = self.query_one(OrderTable)
        orders.add_columns(*order_columns)
        orders.clear()
        order_list = self.trader.history_orders(with_trade_results=True)
        if not order_list.empty:
            list_tuples = list(order_list.itertuples(name=None))
            orders.add_row(*list_tuples[0])

    def refresh_info_panel(self, trader_info):
        """Refresh the information panel"""
        info = self.query_one('#info')

        account = trader_info['Account ID']
        user_name = trader_info['User Name']
        created_on = trader_info['Created on']
        started_on = trader_info['Started on']

        total_investment = trader_info['Total Investment']
        total_stock_value = trader_info['Total Stock Value']

        trader_status = self.trader.status
        info.update(f'Account:          {account}\n'
                    f'Username:         {user_name}\n'
                    f'Created On:       {created_on}\n'
                    f'Started On:       {started_on}\n'
                    f'Status:           {trader_status}\n'
                    f'Total Investment: {total_investment:.2f}\n'
                    f'Total Stock Value:{total_stock_value:.2f}')

    def refresh_values(self, trader_info):
        """Refresh the total value, earning and cash."""

        total_value = trader_info['Total Value']
        total_return_of_investment = trader_info['Total ROI']
        total_roi_rate = trader_info['Total ROI Rate']
        own_cash = trader_info['Total Cash']
        total_market_value = trader_info['Total Stock Value']

        value = self.query_one('#total_value')
        value.border_title = "Total Value / Market Value"
        value.update(f"{total_value:.2f} / {total_market_value:.2%}")

        earning = self.query_one('#earning')
        earning.border_title = "Total Return"
        earning.update(f"{total_return_of_investment:.2f} / {total_roi_rate:.2%}")

        cash = self.query_one('#cash')
        cash.border_title = "Own Cash"
        cash.update(f"{own_cash:.2f}")

    def refresh_tree(self):
        """Refresh the tree."""
        tree = self.query_one(StrategyTree)
        tree.clear()
        tree.root.expand()
        close = tree.root.add("Timing: close", expand=True)
        close.add_leaf("DMA")
        close.add_leaf("MACD")
        close.add_leaf("Custom")

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
        yield DisplayPanel(id='display')
        yield Tables(id='tables')
        yield InfoPanel(id='info_panel')
        yield SysLog(id='log')
        yield ControlPanel(id='control')

    def on_mount(self) -> None:
        """Actions to perform after mounting the app."""

        # updated status
        trader_info = self.trader.info(detail=True)
        self.refresh_values(trader_info)
        self.refresh_info_panel(trader_info)

        # initialize widgets
        tables = self.query_one(Tables)
        tables.border_title = "Tables"

        # get the strategies from the trader
        info = self.query_one(InfoPanel)
        info.border_title = "Information"

        # refresh the holdings table and order tables
        self.refresh_holdings()
        self.refresh_order()

        system_log = self.query_one(SysLog)
        system_log.border_title = "System Log"
        system_log.write(f"System started, status: {self.status}")

        # start the trader, broker and the trader event loop all in separate threads
        Thread(target=self.trader_event_loop).start()
        # self.run_worker(self.trader_event_loop())

        return

    def _on_exit_app(self) -> None:
        """Actions to perform before exiting the app.
        confirms the exit action.
        """
        # stop the trader, broker and the trader event loop
        self.trader.status = 'stopped'
        time.sleep(0.1)
        self.trader.broker.status = 'stopped'
        time.sleep(0.1)

        self.status = 'stopped'
        time.sleep(0.1)

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark


