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

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Header, Footer, Button, Static, RichLog, DataTable, TabbedContent, Tree, Digits
from textual.widgets import TabPane
from textual.worker import Worker

from .utilfuncs import sec_to_duration


holding_columns = ("symbol", "qty", "available", "cost", "name",
                   "price", "total cost", "value", "profit", "profit_ratio")
order_columns = ("ID", "symbol", "position", "side", "type", "qty", "price", "submitted time",
                 "result", "status", "cost", "filled qty", "canceled qty", "execution time", "delivery")


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
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("ctrl+p", "pause_trader", "Pause the trader"),
        ("ctrl+r", "resume_trader", "Resume the trader"),
    ]

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
        display = self.query_one(DisplayPanel)

        self.status = 'running'

        system_log.write(f"System started, status: {self.status}")

        cum_time_counter = 0

        while True:

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
                system_log.write(msg)

                if any(words in msg for words in ['RAN STRATEGY', 'RESULT', 'delivery']):
                    # if ran strategy or got result from broker, refresh UI
                    self.refresh_order()
                    self.refresh_holdings()

            # check the message queue of the broker
            if not self.trader.broker.broker_messages.empty():
                msg = self.trader.broker.broker_messages.get()
                system_log.write(msg)

            cum_time_counter += 1
            if cum_time_counter % 100 == 0:
                # refresh the tree every 10 seconds
                trader_info = self.trader.info(detail=True)
                self.refresh_values(trader_info)
                self.refresh_info_panels(trader_info)
                self.refresh_tree()
                cum_time_counter = 0
            time.sleep(0.1)

        system_log.write(f"System stopped, status: {self.status}")

    @work(exclusive=True, thread=True)
    def refresh_holdings(self):
        """Refresh the holdings table."""
        # get the holdings from the trader
        holdings = self.query_one(HoldingTable)
        holdings.clear()
        pos = self.trader.account_position_info
        if not pos.empty:
            import numpy as np
            pos.replace(np.nan, 0, inplace=True)
            list_tuples = list(pos.itertuples(name=None))
            holdings.add_rows(list_tuples)

        # sys_log = self.query_one(SysLog)
        # sys_log.write(f"Refreshed holdings table: {pos}")

    @work(exclusive=True, thread=True)
    def refresh_order(self):
        """Refresh the order table."""
        orders = self.query_one(OrderTable)
        orders.clear()
        order_list = self.trader.history_orders(with_trade_results=True)
        if not order_list.empty:
            list_tuples = list(order_list.itertuples(name=None))
            orders.add_rows(list_tuples)

    @work(exclusive=True, thread=True)
    def refresh_info_panels(self, trader_info):
        """Refresh the information panel"""
        info = self.query_one('#info')
        system = self.query_one('#system')

        account = trader_info['Account ID']
        user_name = trader_info['User Name']
        created_on = trader_info['Created on']
        started_on = trader_info['Started on']
        broker_name = trader_info['Broker Name']
        broker_status = trader_info['Broker Status']

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
                f'[b]Account:[/b]            {account}\n'
                f'[b]Username:[/b]           {user_name}\n'
                f'[b]Created On:[/b]         {created_on}\n'
                f'[b]Started On:[/b]         {started_on}\n'
                f'[b]Status:[/b]             {trader_status}\n'
                f'[b]Broker:[/b]             {broker_name}\n'
                f'[b]Broker Status:[/b]      {broker_status}'
        )

    @work(exclusive=True, thread=True)
    def refresh_values(self, trader_info):
        """Refresh the total value, earning and cash."""

        total_value = trader_info['Total Value']
        total_return_of_investment = trader_info['Total ROI']
        total_roi_rate = trader_info['Total ROI Rate']
        own_cash = trader_info['Total Cash']
        total_market_value = trader_info['Total Stock Value']

        value = self.query_one('#total_value')
        value.border_title = "Total Value / Market Value"
        value.update(f"{total_value:.2f}")

        earning = self.query_one('#earning')
        earning.border_title = "Total Return"
        earning.update(f"{total_return_of_investment:.2f} / {total_roi_rate:.2%}")

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
    def refresh_tree(self):
        """Refresh the operator tree.
        The operator tree has 3 layers of nodes:
        1. Timing: strategy timings
        2. Strategy: strategies
        3. Properties: strategy properties
        """
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
        trader_info = self.trader.info(detail=True)
        self.refresh_values(trader_info)
        self.refresh_info_panels(trader_info)
        self.refresh_tree()

        # initialize widgets
        tables = self.query_one(Tables)
        tables.border_title = "Tables"

        # get the strategies from the trader
        info_pad = self.query_one(InfoPanel)
        info_pad.border_title = "Information"

        # refresh the holdings table and order tables
        holdings = self.query_one(HoldingTable)
        holdings.add_columns(*holding_columns)
        self.refresh_holdings()
        orders = self.query_one(OrderTable)
        orders.add_columns(*order_columns)
        self.refresh_order()

        system_log = self.query_one(SysLog)
        system_log.border_title = "System Log"

        # start the trader, broker and the trader event loop all in separate threads
        Thread(target=self.trader_event_loop).start()

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

    def action_pause_trader(self) -> None:
        """ Parse the trader"""
        syslog = self.query_one(SysLog)
        syslog.write(f"ctrl-p pressed, Pausing the trader")
        self.trader.add_task('pause')

    def action_resume_trader(self) -> None:
        """ Resume the trader"""
        syslog = self.query_one(SysLog)
        syslog.write(f"ctrl-r pressed, Resuming the trader")
        self.trader.add_task('resume')