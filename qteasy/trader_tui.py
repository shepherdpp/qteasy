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

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import Header, Footer, Button, Static, RichLog, DataTable, TextArea, Tree, Digits


holding_columns = ("symbol", "qty", "available", "cost", "name", "price", "value", "profit", "profit_ratio", "last")


class ValueDisplay(Digits):
    """ A widget to display the value of a variable."""
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


class InfoPanel(TextArea):
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

    CSS_PATH = "tui_style.css"
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

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
        yield VerticalScroll(
            Container(
                Horizontal(
                    ValueDisplay("123456.78", id='cash'),
                    ValueDisplay("123456.78", id='value'),
                    InfoPanel(id='info'),
                ),
                Horizontal(
                    HoldingTable(id='holdings'),
                    StrategyTree(label='Strategies'),
                ),
                SysLog(id='log'),
            ),
            Container(
                    ControlPanel(id='control'),
            )
        )

    def on_mount(self) -> None:
        """Actions to perform after mounting the app."""
        # initialize widgets

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
        tree: Tree[dict] = self.query_one(StrategyTree)
        tree.root.expand()
        close = tree.root.add("Timing: close", expand=True)
        close.add_leaf("DMA")
        close.add_leaf("MACD")
        close.add_leaf("Custom")

        system_log = self.query_one(SysLog)
        system_log.write("System started.")
        system_log.write("System log initialized. this is a [bold red]new log.")

        # self.trader.run()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark


