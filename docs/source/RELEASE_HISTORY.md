# RELEASE HISTORY

## 2.2.3 (2026-03-21)
- **HistoryPanel static vs interactive chart parity (P1)**  
  OHLC summary headers are shown only when a candlestick panel is present: static charts use a dedicated top row for the **last** bar; interactive charts default the same and update the header when you click a bar (labels in English). Matplotlib and Plotly now share one logical theme with small adapter layers for font sizes and candlestick colors so the two backends look closer; the Plotly legend is inset at the upper-left (paper coordinates) to save horizontal space.
- **Unified layout spec (`HpVisualLayoutSpec`)**  
  Chart row heights, subplot indices, and related layout fields are computed in one place (`hp_visual_layout.py`) so matplotlib and Plotly stay aligned for stack/overlay group counts.
- **Matplotlib header and spacing**  
  Multi-group figures keep a **stable absolute header height** (no longer growing with figure height); a configurable **gap row** below the OHLC header separates header text from the first subplot title without shrinking the plot area (figure height grows by the same amount).
- **Plotly FigureWidget header position**  
  In Jupyter, when the figure is wrapped as a **FigureWidget**, the two header annotation lines use **paper** coordinates derived from `layout.height` and margins so the distance from the **top of the figure** stays consistent across layouts (defaults: ~6 mm / ~14.5 mm); the standalone HTML notebook path is unchanged.
- **`plotly_backend_app` on `HistoryPanel.plot()`**  
  With `interactive=True`, pass `plotly_backend_app='auto'` (default: try FigureWidget, fall back to HTML), `'FigureWidget'` (force widget or raise), or `'html'` (force HTML wrapper or raise).

## 2.2.2 (2026-03-20)
- **DataSource robustness and compatibility**
  Fixed a bug where `DataSource` could fail when optional file backends (e.g. `tables`/`pyarrow`) were missing; fallback to `csv` now guarantees the data directory is available, added `hdf5` alias for `hdf`, and improved fallback warnings for clearer diagnosis.

## 2.2.1 (2026-03-19)
- **NaN-price safe in Backtest**
  Fixed a problem that NaN prices will no longer pullut signal parsing and trade result calculation in Backtest result.

## 2.2.0 (2026-03-17)
- **Data visualization and charts**  
  Introduced a new charting pipeline that automatically builds candlestick, volume, MACD and line charts from your historical data, so you can mix multiple indicators and compare several symbols in one view without extra code.
- **Interactive K‑line experience**  
  Added interactive charts that support zooming, panning and hovering to inspect OHLCV and key indicators directly in the notebook, making it much easier to explore price action and drill into specific bars.
- **`qt.candle` behavior update**  
  Updated `qt.candle` to use the new visualization pipeline under the hood while keeping the existing API, so your existing scripts continue to work but immediately benefit from the new static and interactive charts; Renko plots are no longer supported and the old interactive widget is now considered legacy.
- **Logging and trade file maintenance**  
  Improved how log and trade report files are stored and rotated, so system and trade logs, as well as value‑curve CSV files, are kept in predictable locations and old files are cleaned up automatically to save disk space.
- **Backtest accuracy and time handling**  
  Refined how different signal types and intraday time grids are executed in backtests, so portfolio rebalancing and intraday schedules better match real‑world trading behavior and are easier to reason about.

## 2.1.4 (2026-03-10)
- **Evaluation fixes**  
  - Corrected the `oper_count` DataFrame in backtest.
  - Large backtests no longer trigger pandas `PerformanceWarning` in evaluation; the aggregation and concatenation logic has been refactored to be more efficient while keeping the same outputs.
- **Data type definitions and get_history_data**  
  - Fixed a few misdefined built-in data types.
  - Improved the resolution logic in `DataType` / `get_history_data` for `(dtype_name, freq, asset_type)` combinations: multiple definitions for the same logical name are merged safely instead of causing empty data or duplicate-column errors.

## 2.1.3 (2026-03-09)
- **Filenames**  
  Internal filename generation has been updated so that all generated file names (e.g. trade logs, system logs, data exports) comply with Windows, Linux, and macOS requirements. You no longer need to worry about invalid characters or path issues when using qteasy on different operating systems.
- **value_curve file when trade_log=True**  
  When `trade_log=True`, the full value curve is also saved as a CSV file (`value_curve_{name}_{datetime}.csv`) in the same directory as trade_log and trade_summary, and is rotated with them according to `trade_log_keep_days`, so you can keep or archive it with your other backtest logs.
- **Backtest result and reports**  
  Optimized backtest reports and added price information into backtest results in complete values, made backtest result analysis much easier.

## 2.1.2 (2026-03-08)
- **Backtest trade prices**  
  Asset pool passed as a comma-separated string is now handled correctly; trade price columns are aligned to the full pool so backtests work with back-adjusted prices or missing data for some symbols.
- **get_history_data**  
  Invalid type names now raise a `ValueError` listing unmatched names (and suggest `qt.define()` / DATA_TYPE_MAP) instead of being silently skipped; deprecated `htypes` only overrides `htype_names` when given explicitly.
- **Visualization chart titles**  
  Backtest result charts now show a title with the Operator name and backtest date-time, so you can match charts to the corresponding trade_log and trade_summary files.
- **Error messages**  
  Fixed typo and clarified message when a requested column is missing in DataType ("columu" → "column").

## 2.1.1 (2026-03-07)
- Fixed backtest report "Total operation fee" always showing zero when daily evaluation uses `evaluate_price_data`. Fees were aggregated by date but then reindexed against the daily index that carries a time-of-day (e.g. 15:00), so the index mismatch produced all NaNs and the subsequent fillna(0) zeroed the fee column. Alignment is now done on normalized dates so that `backtest_result['total_fee']` matches the sum of per-trade fees in trade_log.
- Added automatic rotation for trade_log and trade_summary files: old `trade_log_*.csv` and `trade_summary_*.csv` files are removed according to the configured retention period to avoid unbounded growth of the log directory, a new configure key `trade_log_keep_days` is now added to configure trade log rotation behavior.

## 2.1.0 (2026-03-06)
- **Process data (proc.\*) API**: Strategies can access runtime state (cash, positions, trade records, etc.) via `get_data('proc.own_cash')`, `get_data('proc.trade_records', lag=0)` and other `proc.*` fields in `realize()` without declaring them in `data_types`. Process data is injected by Backtester (backtest) and Trader (live) and respects no-look-ahead: at step k the strategy sees only results from steps 0..k-1 for trade data.
- **Dynamic backtest path selection**: If any strategy uses `proc.*` in its `realize()` source, backtest automatically uses the stepwise path (`_backtest_dynamic_operator`); otherwise the static path (batch signals + vectorized backtest) is used. Detection is via `_strategies_use_proc_data()` so no declaration is required.
- **Live trading process data**: When `operator.check_dynamic_data()` is True, Trader injects current account/position and price views into the operator so that `get_data('proc.xxx')` works in live mode with the same API as in backtest.
- **Removed legacy dynamic data types**: `TRADE_OPERATION_DATA_TYPES` and all `op_*` DataTypes (e.g. `op_cashes`, `op_trade_volumes`) have been removed from `qteasy.datatypes`. Creating `DataType('op_cashes')` etc. now raises `KeyError`. Process data must be accessed only via `get_data('proc.xxx')`. `Operator.prepare_dynamic_data_buffer` is now a no-op; `all_dynamic_dtypes` always returns an empty dict.
- **Tests**: Added `tests/test_process_data_api.py` for process data API, branch selection, static/dynamic equivalence, no-look-ahead, and dynamic strategy correctness. `TestDependentData` in operator tests was refactored to use `proc.*` instead of old `op_*` types.
- **Docs**: Design doc `docs/source/design/09-process-data-and-dynamic-backtest.md`; process data section in `03-data-in-strategies.md`; branch selection note in `06-backtest-live-optimization.md`.
- **Pandas frequency alias compatibility**: Fixed `pandas_freq_alias_version_conversion()` so that it normalizes both legacy (<2.2) and new (>=2.2) pandas frequency aliases (e.g. `M/ME`, `H/h`, `MIN/min`, `5MIN/5min`), avoiding mis-matched freq errors and warnings across different pandas versions.

## 2.0.1 (2026-03-05)
- Improved documentation and docstrings, adding more explanations about the overall design and architecture of qteasy.
- Fixed the post-backtest performance evaluation so that all evaluation tables and plotted equity curves are consistently computed on daily frequency, independent of the strategy running frequency.
- Removed configuration keys `price_priority_OHLC` and `price_priority_quote`, which are no longer meaningful under the new pricing architecture.
- Fixed issues where trade prices could sometimes not be correctly fetched during backtests.
- Fixed incorrect inclusion of market opening time in strategy running schedules for high-frequency backtests such as hourly and minute-level runs.
- Unified the adjustment method for trading prices and evaluation prices so that both now use the same adjustment convention.
- Refined the semantics and execution behavior of PT / PS / VS signals: for PT signals, the backtest matching engine now reuses cash obtained from same-step sells as much as possible to reach the target portfolio; for PS and VS signals, the engine keeps naive order semantics and drops orders that cannot be filled due to resource limits.

## 2.0.0 (2026-02-27)
- Major update: qteasy 2.0 will be released with significant changes in the architecture and APIs, aiming to provide a more powerful and flexible framework for quantitative trading. Users are advised to check the migration guide in the documentation to smoothly upgrade to 2.0.
- Key changes in 2.0 include:
  - Major improvements in `Operator` / `Strategy` class:
    - Introduced `Parameter` class to represent strategy parameters, and `Operator` can now specify the parameters it needs with Parameter instances, and users can set the parameters with more flexible ways, including setting parameters with different values for different symbols.
    - Introduced `Group` class to represent strategy groups, and `Operator` now groups strategies into different groups, and each group can have its own running frequency and running timing and blender, thus strategies can be run with more flexible and powerful ways.
    - An improved operator running schedule is introduced in 2.0, now all strategies are running at a more granular level allowing more flexible running timing and more accurate backtesting results, and the running schedule is determined per strategy group, allowing different groups of strategies to be run with different frequencies and timings.
    - Improved how strategies utilizes historical data, now strategies are able to utilize data with different frequencies and window lengths in the same run, and the data are extracted and allocated to strategies in a more efficient way.
    - Improved efficiency of strategy backtesting and optimization, now the backtesting and optimization process is more efficient with better utilization of system resources, and the performance is improved significantly especially when running with multiprocessing.
    - Introduced Tracing mode in `Operator` to allow users to trace backtest results of each strategy group in more detail by defining tracing points in strategy realization, tracing results will be saved in trade logs.
    - Simplified definition of strategy realization, now users can acquire historical data and parameters with simpler APIs with user-defined names in more intuitive ways.
    - Introduced more strategy optimization algorithms, and users can set up different optimization algorithms for different strategy groups, and the optimization process is more efficient and more powerful with better utilization of system resources.
    - Improved backtest / optimization result evaluation processes with more comprehensive evaluation metrics and more intuitive result presentation.
  - `DataType` class now supports asset type "ANY" to represent any type of asset, and strategy can specify the asset type of its target symbols with "ANY" to be compatible with all types of assets.
  - Introduced `StgData` class in strategy definition as syntax suger for users to specify window length and other related properties of Data used in strategy
  - **Removed configuration keys**: `maximize_cash_usage`, `benchmark_asset_type`, `benchmark_dtype`. Logic is now inferred from execution flow and `benchmark_asset`. See [qteasy_2_migration_guide](qteasy_2_migration_guide.md) for migration.
  - Other bug fixes and improvements

## 1.4.11 (2026-02-14)
- Added FutureWarning for APIs that will be removed or changed in qteasy 2.0. Users are advised to migrate to the recommended alternatives so as to upgrade smoothly to 2.0.
- Affected APIs:
  - `get_history_data(htypes=..., adj=...)`: use `htype_names` and htype suffixes (e.g. `close:b`) instead.
  - Config keys `print_trade_log` / `print_backtest_log`: use `trade_log` instead.
  - `get_table_map()`: use `get_table_master()` instead.
  - Broker name `random`: use `simulator` instead.
  - Trader method `info(verbose=...)`: use `detail` instead.
  - `Operator.op_type`: run mode will be determined per strategy group in 2.0.
  - `Operator.op_data_freq`: use strategy-level data type and frequency information in 2.0.
  - `Operator.get_share_idx()`: will be removed in 2.0.

## 1.4.10 (2025-12-19)
Bug fixes:
- Fixed a bug that will lead to low performance in optimization algorithm 2 when running with multiprocessing in some systems

## 1.4.9 (2025-03-11)
Bug fixes:
- Fixed problem in trader logger that causes duplicated logs in live trade mode
- Fixed a bug in trader: when two trade results are generated at nearly the same time for the same position, the results will be wrongly recorded in the database due to data recording conflicts
- Fixed a bug in trader that very occasionally price data with wrong timestamp will be returned and may cause NaN values output from strategies for some symbols.
- Fixed a bug that strategy will not get enough extracted data to run in live trade mode in some cases on Monday morning due to not mis-calculation of date offset due to weekends.
- Corrected automatic datasource refill timing for weekly data refilling, now it will refill data every Friday evening

## 1.4.8 (2025-03-01)
New features:
- Added a new CLI command in trader CLI: `refill`, to manually refill datasource tables in trader CLI
- Allowed users to manually refill datasource table with trader CLI command `run` with parameter `--task refill`
Bug fixes:
- Fixed a bug that will lead to failure of automatic datasource refilling in trader

## 1.4.7 (2025-02-26)
New features:
- Added configuration settings: `live_trade_daily_refill_tables`, `live_trade_weekly_refill_tables`, `live_trade_monthly_refill_tables`, to allow users to set up tables to be refilled in live trade mode
Fixed bugs:
- Sometimes the configure settings might be overwritten unexpectedly in trading mode
- `DataSource.all_basic_tables` will not return correct tables in some cases
- CLI command `schedule` fails to print out current scheduled tasks in trader shell

## 1.4.6 (2025-02-19)
- Improved function `qt.refill_data_source()`, now it will skip the tables that are not available from current channel and provide a warning message
- Fixed a bug that will sometimes result in duplicated data being refilled from channels while running `qt.refill_data_source()`

## 1.4.5 (2025-02-18)
- Fixed a bug that may cause incorrect k-line data being stored in the datasource when running in live trade mode
- Added APIs to get minute level and daily candle bar price data for funds from channel 'eastmoney'

## 1.4.4 (2025-02-12)
- Fixed bugs: 
  - Simulator broker and Trader module in live trade mode might fail to fetch real time price data in some cases
  - Sometimes the historical data extracted from datasource are not re-indexed to exactly matching the stock market open time.
  - Corrected the data formats and errors downloaded from channel `eastmoney`, improved error handling and stability

## 1.4.3 (2025-02-11)
- Fixed a bug: Trader might fail to acquire live prices from correct channel and may fail to save the prices to datasource due to channel updates
- Improved `refill_data_source()`: added an optional parameter: `refill_dependent_tabes: bool = True`, to give user control if dependent tables are downloaded

## 1.4.2 (2025-02-07)
- Added `dbutil` as mandatory dependency, and moved `pymysql` also as mandatory, removed optional dependencies as database
- Fixed a bug: warnings showing missing of some dependencies are not properly displayed.

## 1.4.1 (2025-02-06)
- Fixed bugs:
  - sometimes the back-adjusted prices are not properly get from data source
  - sometimes data types with parameters will not set correct parameter into the kwargs, and will cause problem
  - sometimes the realtime kline data will have no valid trade time in index
- Improvement:
  - Improved function refill_data_source, made parameters "channel" and "data_source" optional and provided type and validity check

## 1.4.0 (2025-02-05)
- New features:
  - A new DataType class has been introduced, making it much easier and more flexible to utilize historical data stored in local datasources
  - Now datatypes can be defined with parameters followed by a "|" in its name, like "close|b" represents "back adjusted close price".
  - A new data_channel module has been defined for qteasy, allowing users to download data from different online sources
  - More data tables are defined to store more types of financial historical data.
  - Enhanced real-time price data acquisition APIs, allowing real-time data been downloaded from different sources
  - More introduction to above new features can be found in qteasy documents.
- Deprecated
  - The old way of extracting adjusted price data with parameter "adj" is deprecated, although still supported, now adjusted prices can be acquired with datatypes with parameter like "close|b" or "open|f"
  - The old way of getting composition data, "wt_000300.SH" is deprecated and replaced by datatype with parameter: "wt_idx|%" where % is any index code
  - More introductions to the new datatypes can be found in qteasy documents.

## 1.3.12 (2024-12-18)
- Improved Log information and print outs in trader TUI and CLI:
  - excessive digits of amount changes are now truncated to 2 or 3 digits in trader CLI for RESULT DELIVERY
  - added timestamp before all system logs on the system log pane
  - added system environment information in TUI system info panel

## 1.3.11 (2024-11-03)
- fixed a bug: pure digit strings are not properly parsed from start up configuration file

## 1.3.10 (2024-09-03)
- removed deprecated pandas syntax from database.py and updated version requirements
- added qt level configure keys for Chinese font names in candle chart for different Operating systems respectively:
  - `ZH_font_name_MAC` / `ZH_font_name_WIN` / `ZH_font_name_LINUX`
- added qt function and attributes:
  - `get_start_up_settings()`
  - `start_up_config`
- corrected help messages for live trader users

## 1.3.9 (2024-09-01)
- Added setting key validation in `qt.update_start_up_setting()` to prevent from invalid values if the key is in qt_config_kwargs
- improved print outs and return values of `qt.start_up_settings()`
- improved the way the start up setting file is written to always keep intro messages

## 1.3.8 (2024-09-01)
- Added new features: now qteasy has multiple functions to access and modify start up setting file:
  - Added new function `qt.start_up_settings()`, to access and print contents of start up settings file
  - Added new function `qt.update_start_up_setting()`, to modify start up settings file
  - Added new function `qt.remove_start_up_setting()`, to remove settings from the file
- Fixed bugs in trader TUI buy and sell orders, added error handling for wrong inputs

## 1.3.7 (2024-08-31)
- Added features in trader TUI:
  - Added commands and short-cuts to manually place buy and sell orders
  - Added commands and short-cuts to cancel submitted orders
  - Added a new data table to display trade logs

## 1.3.6 (2024-08-25)
- Fixed bugs in command `orders` in trader CLI:
  - now `orders` command selects symbols correctly
  - now parameter `--time` works with value 'all' or 'a'
- Added new command `summary` that displays trading operations in given period in human readable way

## 1.3.5 (2024-08-22)
- Added new feature: now trader will save the latest operation status on the dist while exit, and will restore the status when re-enter
- Improved delete_account() function, now it will delete all account related files, including trade logs, trade records, and trader break points
- Other bug fixes and optimizations in trader

## 1.3.4 (2024-08-17)
- Improved Live trade broker, added retry count before canceling submitted orders when live price is not available, reduced chance of order filling failure
- Corrected a mistake in grid trading example files, nan prices are now not written to strategy parameters

## 1.3.3 (2024-08-16)
- Fixed a bug that will cause buying stock with 0 price when live prices are not available
- Added freq alias support for pandas version >= 2.2.0, to prevent from FutureWarning raised by pandas

## 1.3.2 (2024-08-13)
- Corrected Font name in candle chart in Windows environment

## 1.3.1 (2024-08-13)
- Added trader CLI command `debug`, to set or toggle debug mode while trader is running
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
- Published `Qteasy` Docs to https://qteasy.readthedocs.io/zh-cn/latest/, added more supportive documents including api reference, examples, tutorials, etc.
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