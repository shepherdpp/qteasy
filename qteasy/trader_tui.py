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
from textual.widgets import Header, Footer, Button, Static, RichLog, DataTable, TabbedContent, Tree, Digits
from textual.widgets import TabPane

from .utilfuncs import sec_to_duration


holding_columns = ("symbol", "qty", "available", "cost", "name", "price", "value", "profit", "profit_ratio", "last")


class ValueDisplay(Digits):
    """ A widget to display the total value."""
    pass


class EarningDisplay(Digits):
    """ A widget to display the value of a earnings."""
    pass


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


class InfoPanel(Static):
    """A widget to display information."""
    pass


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
        info = self.query_one(InfoPanel)

        self.status = 'running'

        system_log.write(f"System started, status: {self.status}")

        while True:

            # update current date and time
            current_time = self.trader.get_current_tz_datetime().strftime("%Y-%m-%d %H:%M:%S")

            next_task = self.trader.next_task
            count_down = sec_to_duration(self.trader.count_down_to_next_task, estimation=True)

            system_log.border_title = f"System Log - Next Task: {next_task} in {count_down}"

            # updated status
            trader_status = self.trader.status
            info.border_title = f"Information: {current_time}"
            info.update(f'Account: {self.trader.account_id}\n'
                        f'Status: {trader_status}\n'
                        f'UI Status: {self.status}')

            # check the message queue of the trader
            if not self.trader.message_queue.empty():
                msg = self.trader.message_queue.get()
                system_log.write(msg)

            # check the message queue of the broker
            if not self.trader.broker.broker_messages.empty():
                msg = self.trader.broker.broker_messages.get()
                system_log.write(msg)

            if self.status == 'stopped':
                break

            time.sleep(0.1)

        system_log.write(f"System stopped, status: {self.status}")

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
        yield ValueDisplay("123456.78", id='cash')
        yield EarningDisplay("456.78", id='earning')
        yield InfoPanel(id='info', classes='box')
        yield Tables(id='tables')
        yield StrategyTree(label='strategies')
        yield SysLog(id='log')
        yield ControlPanel(id='control')

    def on_mount(self) -> None:
        """Actions to perform after mounting the app."""
        # initialize widgets
        total_value = self.query_one(ValueDisplay)
        total_value.update("0.00")
        total_value.border_title = "Total Value"

        earning = self.query_one(EarningDisplay)
        earning.update("0.00")
        earning.border_title = "Earning"

        tables = self.query_one(Tables)
        tables.border_title = "Tables"

        # get the holdings from the trader
        holdings = self.query_one(HoldingTable)
        holdings.add_columns(*holding_columns)
        pos = self.trader.account_position_info
        if not pos.empty:
            import numpy as np
            pos.replace(np.nan, 0, inplace=True)
            list_tuples = list(pos.itertuples(name=None))
            holdings.add_row(*list_tuples[0])

        # get the strategies from the trader
        tree = self.query_one(StrategyTree)
        tree.border_title = "Strategies"
        tree.root.expand()
        close = tree.root.add("Timing: close", expand=True)
        close.add_leaf("DMA")
        close.add_leaf("MACD")
        close.add_leaf("Custom")

        system_log = self.query_one(SysLog)
        system_log.border_title = "System Log"
        system_log.write(f"System started, status: {self.status}")

        info = self.query_one(InfoPanel)
        info.border_title = "Information"
        account = self.trader.account_id
        trader_status = self.trader.status
        info.update(f'Account: {account}\nStatus: {trader_status}')

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


