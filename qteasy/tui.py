# coding=utf-8
# ======================================
# File:     visual.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2024-04-08
# Desc:
#   Terminal User Interface (TUI) for
# qteasy live trade system.
# ======================================

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Static, RichLog, DataTable, TextArea, Tree


class ValueDisplay(Static):
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
        yield ValueDisplay("Total Value: 0")
        yield SysLog()
        yield StrategyTree(label='Strategies')
        yield HoldingTable()
        yield InfoPanel()
        yield ControlPanel()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

