# RELEASE HISTORY

## 1.0.24 (2024-02-18)
- Corrected a mistake introduced since version 1.0.18, with wrongly merged incomplete and untested features in broker. this bug will cause failure of executiong orders in live trade mode.

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
- Improved trader shell live messages: now order execution results are better displayed with more info regarding change of stock qty and cash amounts
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

## 1.1.0 (2023-)

## 1.0.13 (2023-12-21)
- Improvements in Trader Shell
  - Now users can scroll to previous commands with up and down keys in Command mode
  - Created new command `buy` / `sell` to allow users to manually submit orders to broker
  - Optimized shell tasks and let live price acquisition to run in back ground threads
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
- Implemented "--perameter" / "-p" style parameter in Trader Shell, the old style will be deprecated in later versions
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
- Improved Strategy class, added Strategy.use_latest_data_cycle property to allow use latest prices to create trade signals
- now stock names are displayed in qt shell
- Added shell command `watch`, to watch stock price in realtime
- Implemented live price acquiring channel eastmoney
- Improvements in text display effects and bug fixes

## 1.0.6 (2023-10-19)
- Added shell command `config`
- Supported using FUND as investment type

## 1.0.0 (2023-09-19)
- First release of working version on PyPI.