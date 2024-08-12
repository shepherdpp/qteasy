# RELEASE HISTORY

## 1.3.1 (2024-08-13)
- Fixed and improved watched prices in trader CLI
- Fixed a bug that may lead to failure displaying watched prices in trader CLI
- Corrected a font name issue in candle chart in Windows environment

## 1.3.0 (2024-08-09)
- New Feature:
  - Running example strategy files with parameter -r can now remove orders only for designated account, instead of all accounts
- Improvements and bug fixes:
  - Improved live trade log, Now delivery records for selling stocks are also displayed in a new line
  - Now delivery records are clearer shown
  - Fixed a bug that may cause wrong stock or cash change in trade logs
  - Fixed a bug that causes buying results not being delivered properly
  - Fixed a bug that sometimes empty data will be extracted even with valid data id from system datasource tables
  - Fixed a few bugs that will lead to error in CLI command `CHANGE`:
    - Prevented from acquiring latest price when only cash is to be changed
    - Ensured symbol be given when changing quantity of a stock

## 1.2.15 (2024-07-28)
- Added new built-in strategies: `ATR` and `OBV`, with docstrings

## 1.2.14 (2024-07-12)
- Updated Built-in Strategy AD and ADOSC, corrected mistakes, added docstring and optimized realization

## 1.2.13 (2024-06-19)
- Changed function qt.built_ins(), now it always return a dict of id and type of built-in strategies, and if incorrect strategy id is given as argument, it returns all fuzzy matched strategy ids
- Changed function qt.built_in_list() and qt.built_in_strategies(), now they return list of strategy ids and strategy types, respectively; and return fuzzy matched strategy ids for incorrect strategy id given as argument
- Added new function qt.built_in_doc(), to return the docstring of a built-in strategy

## 1.2.12 (2024-06-12)
- Fixed a bug, now cash gained by selling stocks can be delivered immediately to update available cash amount.
- Fixed a bug, now unfilled orders can be correctly canceled after each trading day
- Fixed a bug that might lead to failure of getting table information in Windows environment

## 1.2.11 (2024-06-09)
- Fall back to default data source type if mysql connection fails
- Fixed a bug in tui watch list management

## 1.2.10 (2024-06-07)
- Now symbols can be added to or removed from the watch list in the live trader TUI, with two added short cuts: ctrl+a to add and ctrl+r to remove
- Dialogs are now added to the live trader TUI to accept user inputs for adding symbols to the watch list, as well confirming to quit the App
- Slightly adjusted the appearance of live trader TUI

## 1.2.9 (2024-06-03)
- Added more help information and docstrings for user to initialize live trades

## 1.2.8 (2024-06-02)
- Changed argument "-u" in qt_argparser, now either "tui" or "cli" should be specified to choose ui type
- qt parameter "live_trade_account" is now renamed to "live_trade_account_name", and more help info is provided to guide users to set up live trade accounts in live trade mode
- Fixed a bug in qt.candle() that will fail to create candle charts when TA-lib is not installed

## 1.2.7 (2024-05-30)
- Fixed a bug in database that may cause data refill failure when trade calendar is not available in some cases

## 1.2.6 (2024-05-07)
- Fixed a bug in data source that causes failure of getting the last record id from system tables in some cases

## 1.2.5 (2024-05-06)
- Fixed a bug in HistoryPanel that causes recursive importing

## 1.2.4 (2024-05-05)
- Fixed bugs in built-in strategies: `MACDEXT`, `WILLR`, `AROONOSC`, and `SLPHT`
- Updated test cases for built-in strategies

## 1.2.3 (2024-04-30)
- Corrected a mistake in version 1.2,2: '1.2.1' will be displayed when running `qteasy.__version__`
- Fixed a bad information displayed with progress bar while downloading data from tushare with refill datasource

## 1.2.2 (2024-04-29)
- Fixed a bug that causes abnormally low speed in some cases if TA-LIB is not installed
- Fixed a bug that causes escaped failure in some cases when strategy is based on RuleIterator
- Now it is possible to view all live accounts with `qt.live_trade_accounts()`

## 1.2.1 (2024-04-25)
- Corrected a build mistake in version 1.2.0, which caused style files not being included in the package
- Added new qt level function: `live_trade_accounts()` to get detailed information of all accounts for live trading
- Corrected a mistake in trader CLI of wrong formatting of trade info
- Improved help information for live trade related configurations

## 1.2.0 (2024-04-25)
- New feature added: Now qteasy has a new Terminal UI for live trading, thus users can choose from one of the two UIs for live trading: the Trader Shell or the TUI
  - A new configure key `qt.config['live_trade_ui_type']` is added to allow users to choose between the two UIs for live trading
  - The new TUI has built in light mode and dark mode themes, and is more user-friendly for users who are not familiar with command line interfaces
  - The new TUI displays live status of the account, on hand stocks, historical order, and live operation logs
  - Use Ctrl=P and Ctrl+R to pause and resume the live trading process

## 1.1.11 (2024-04-20)
- Improved function `refill_data_source`, allowed data being downloaded in batches that are adjust-able in size and intervals in between
- Improved error messages raised by qt when wrong values are set to configuration keys, providing better guidance for users

## 1.1.10 (2024-04-19)
- Fixed a bug that causes not taking effect the configuration that are related to automatic retries in data acquiring from tushare

## 1.1.9 (2024-04-09)
- Fixed a bug that might cause error extracting minute level data from local data source
- Improved compatibilities

## 1.1.8 (2024-04-05)
- Improved compatibility for higher versions of `python` from 3.9 up to 3.12
- Improved compatibility for higher versions of `pandas` (v2.2.1), `numpy` (1.26.4), and `numba` (v0.59.1)
- Fixed a bug that will cause failure of strategy optimizations in python 3.10 and above
- Corrected and improved a few error messages

## 1.1.7 (2024-04-03)
- Now qteasy can be installed in higher versions of `python` from 3.9 up to 3.12

## 1.1.4 (2024-03-30)
- Updated version restrictions on dependencies, to solve the version conflicts between `numba` and `numpy`.
- Slightly improved warning information when loading qteasy for the first time.
- Fixed a few bugs that will cause compatibility issue with `pandas` > 2.0
- Added performance warnings for strategy optimization method 2 when some `numpy` and `numba` versions will cause performance degrade in multiprocessing

## 1.1.3 (2024-03-25)
- now trade_log, trade_records, full_histories are added to the results returned from backtest run, and can be accessed by `res['trade_log']`, `res['trade_records']`, and `res['full_histories']`

## 1.1.2 (2024-03-18)
- New parameter `--rewind` is now added to command `dashboard`, to allow users to view previously saved logs when switched to dashboard mode.
- Added more information print-outs for command `buy` and `sell`, to show if orders are submitted successfully.

## 1.1.1 (2024-03-16)
- corrected system log for live trade, now different live trade instances will log to different files
- added capability of reading info from live trade log files and system log files

## 1.1.0 (2024-03-08)
- New feature: The QTEASY shell is now parsing command arguments in a better and more intuitive way:
  - Now all commands support `--parameter` / `-p` style parameters, same way as all other CLI tools
  - All commands now support `--help` and `-h` to show help messages, are now fully documented in the shell help message
  - All commands now have better error handling and usage messages when wrong arguments are given
  - All commands are now thoroughly tested and debugged
  - Arguments of some commands are now re-designed and re-organized to be more intuitive and easier to use:
    - `watch` command now supports `--remove` / `-r` to remove symbols from watch list, and `--clear` / `-c` to clear the list
    - `buy` and `sell` commands now uses `--price` / `-p` to specify price, and `--side` / `-s` to specify position side
    - `info` and `overview` commands now support new argument `--system` to show system info, and `verbose` will be replaced by `detail` in future versions
    - `history` command now accepts explicit argument `all` to show all history
    - `orders` command now accepts order filter arguments with optional tags `--status`, `--time`, `--side`, and `--type`
    - `config` command now support `--set` / `-s` to set configurations, and set view levels with count of `--level` / `-l`
    - `strategies` command now supports `--set-par` to set strategy optimizable parameters, and to be implemented: possible to set blenders with `--blender` and `--timing`
    - `run` command now supports running tasks with arguments given with optional flag `--args` / `-a`
    - `orders` command now works with new optional arguments for time, type, side and status in more logical way
    
## 1.0.27 (2024-3-5)
- Removed dependency on pandas to load dataframes from database, which will arouse UserWarnings in higher versions of pandas, requesting users to install sqlalchemy

## 1.0.26 (2024-2-29)
- Now live trade logs are kept in system log files, live logs are saved in the same file, with different account number as prefix
- Fixed bugs

## 1.0.25 (2024-2-28)
- Now trade logs are saved in a file in live trade mode, the file is saved in the same directory as set in `qt.config['trade_log_file_path']`
- Fixed a few bugs in live trade mode, and added information print-outs on errors

## 1.0.24 (2024-02-18)
- Corrected a mistake introduced since version 1.0.18, with wrongly merged incomplete and untested features in broker. this bug will cause failure of execution orders in live trade mode.

## 1.0.23 (2024-02-15)
- Fixed a bug that will cause wrong type conversion when filtering stocks with `qt.filter_stocks()` and creating candle charts with `qt.candle()`

## 1.0.22 (2024-02-14)
- Fixed a mistake in qt.get_config and qt.candle() that interprets wrong list dates in basic data
- Improved progress bar: trim the text to screen width
- Allows qt.get_stock_info() to run without all basic tables being downloaded

## 1.0.21 (2024-02-11)
- Fixed bugs

## 1.0.20 (2024-02-08)
- Fixed mistakes in ta-lib compatible functions `EMA()`, `MACD()`, `TRIX()`, and `DEMA()`, now they can be used without `ta-lib` installed, although the results are slightly different from their talib versions

## 1.0.19 (2024-02-07)
- Removed dependency on `ta-lib` package for ta functions `RSI()`, `MA()`, and `BBANDS()`, thus candle charts can be created without `ta-lib` installed
- Updated dependencies, made package more use-able for beginners with no `ta-lib` and only basic `tushare` credits

## 1.0.18 (2024-02-05)
- Improved Trader Shell live messages: now order execution results are better displayed with more info regarding change of stock qty and cash amounts
- Command INFO and OVERVIEW in trader shell now will not print out system information in default.
- Updated version requirements for numpy
- Bug fixes

## 1.0.17 (2024-01-29)
- improved trader shell command "run", now it can run a strategy in main thread, making it easier to debug
- fixed a bug that will cause error acquiring live price in live trade mode if running freq is lower than 1 hour

## 1.0.16 (2024-01-27)
- Added feature: if a valid trade signal can not be converted to an order due to lack of available cash/stock, a message will be posted in live mode
- Fixed a bug in live trade mode that will cause trade results being processed and delivered for more than one time, thus leads to wrong available qty or available cash recorded
- Fixed a mistake that will cause wrong cost being calculated during live trade
- Fixed a mistake in live trade shell with command history, that wrong stock cost is calculated when history of multiple stocks are listed
- Fixed bug in issue #85 where data are extracted and filled unexpectedly in non-trading days
- Fixed other bugs

## 1.0.15 (2023-12-29)
- Now live prices of Index and ETFs can also be watched in live running mode
- ETF and Index are now supported in live trading mode as trading targets
- Fixed bugs

## 1.0.14 (2023-12-22)
- Removed optional dependency sqlalchemy
- Added retry in broker to stop order execution after max retries

## 1.0.13 (2023-12-21)
- Improvements in Trader Shell
  - Now users can scroll to previous commands with up and down keys in Command mode
  - Created new command `buy` / `sell` to allow users to manually submit orders to broker
  - Optimized shell tasks and let live price acquisition to run in background threads
- In Broker:
  - Optimized behavior of Simulator Broker, to return execution result according to live prices
  - Fixed bugs: order execution will not block each other

## 1.0.12 (2023-12-07)
- improved visual effects
- now live prices are acquired in background threads, not causing lags in the main loop
- mistake corrections that allow live prices to be displayed when time zone is not local
- watched price refresh interval is now configurable

*in next release:*

- two new commands will be added to Shell: `buy` and `sell` 

## 1.0.11 (2023-12-03)
- Implemented "--parameter" / "-p" style parameter in Trader Shell, the old style will be deprecated in later versions
- Allowed users to set up live trade broker parameters with QT configurations
- Allowed users to set up live trade running time zone
- Made dependency ta-lib as optional, kept a few critical built in strategies usable without `ta-lib`

## 1.0.10 (2023-11-25)
- Corrected a mistake left out in version 1.0.9, which caused error when reference data is None in strategy
- Changed default value of qteasy parameter `backtest_price_adj` to `none`

## 1.0.9 (2023-11-24)
- Corrected a mistake in reference data generation and allocation to strategies, making reference data available to strategies
- Improved documentations

## 1.0.8 (2023-11-22)
- Improved trader shell visual effects, added color coding for different types of messages, with dependency on `rich` package
- Published `Qteasy` Docs to https://qteasy.readthedocs.io/zh/latest/, added more supportive documents including api reference, examples, tutorials, etc.
- Added parameter `qteasy.__version__`
- Fixed bugs

## 1.0.7 (2023-11-11)
- Improved Strategy class, added Strategy.use_latest_data_cycle property to allow use the latest prices to create trade signals
- now stock names are displayed in qt shell
- Added shell command `watch`, to watch stock price in realtime
- Implemented live price acquiring channel eastmoney
- Improvements in text display effects and bug fixes

## 1.0.6 (2023-10-19)
- Added shell command `config`
- Supported using FUND as investment type

## 1.0.0 (2023-09-19)
- First release of working version on PyPI.