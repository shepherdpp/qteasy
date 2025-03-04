��    Q      �              ,  |   -  �   �  �   �  �   j  u     �   �  �   	  "   �	  %   
      A
     b
     �
  �   �
  �  f  �  &  �   �  J   �  �   �  �   �  �   �  D   _  �   �  Y   _     �  �   �  g   �     �  �        �  �   �  �   �  m   I  w   �  c   /  �   �  �        �  *   �  �     =   �  ]     Y   q    �  �   �  �   �  �   j   !   V!  t  x!     �"     �"  B   #     P#  J   _#  	   �#  �   �#  /   w$     �$     �$  %   �$  �   �$  '   �%  $  �%     �&  P   �&  i  E'  w   �(  r   ')     �)  �   �)     ?*  C   Q*  \   �*  *   �*     +  C   3+  %   w+  9  �+  �   �,  P   �-  L   �-  }  G.  �   �/  �   S0  �   S1  �   32  �   �2  �   y3  �   ,4  -   �4  5   �4      $5      E5     f5    5  Y  �6    �9  �   =  l   >  	  r>    |?  �   �@  D   �A  �   �A  q   �B     �B  �   C  s    D  "   tD  �   �D  $   vE    �E  �   �F  m   uG  }   �G  �   aH  �   �H  �   �I     SJ  ;   qJ  �   �J  5   �K  e   �K     L  T  �L  �   �M    �N    �O     Q  �  Q     �R     �R  W   �R     FS  D   VS     �S  �   �S  6   qT  %   �T     �T  6   �T  �   U  5   �U  [  V     cW  N   yW  �  �W  �   UY  �   �Y     �Z  �   �Z     G[  K   Y[  k   �[  *   \     <\  E   V\  -   �\    �\  �   �]  a   �^  <   )_   ![png](img/output_24_1.png)    将优化后的参数应用到策略中，并再次回测，可以看到结果明显提升： **`TraderApp`** (v1.2.0新增) 交互式图形界面，可以在图形界面中查看交易日志、查看持仓、查看账户资金变化等信息 ![png](examples/img/trader_app_light_theme.png)  ![png](examples/img/trader_app_2.png) **`TraderShell`** 交互式命令行界面，可以在命令行中输入命令，查看交易日志、查看持仓、查看账户资金变化等信息： ![png](img/output_27_1.png)   ![png](img/output_27_3.png) **`pyarrow`**, 用于操作`feather`文件，将本地数据存储为`feather`文件，`pyarrow`可以在安装`qteasy`时自动安装，也可以手动安装： **`pymysql`**, 从`v1.4`开始，`pymysql`以及`db-utils`已经成为`qteasy`的默认依赖包，无需额外安装 **`pytables`**, 用于操作`HDF`文件，将本地数据存储到`HDF`文件，`pytables`不能自动安装，需要使用`conda`手动安装`pytables`： **`ta-lib`**, 以便使用所有的内置交易策略，下面的方法可以安装`ta-lib API`，但它还依赖C语言的`TA-Lib`包，安装方法请参考[FAQ](https://qteasy.readthedocs.io/zh/latest/faq.html#id2) **使用内置交易策略组合** **通过策略类自行创建策略** *`python` version >= 3.6, <3.13* 10分钟了解qteasy的功能 QTEASY快速上手指南 `DMA`是一个内置的均线择时策略，它通过计算股票每日收盘价的快、慢两根移动均线的差值`DMA`与其移动平均值`AMA`之间的交叉情况来确定多空或买卖点。： `Qteasy`的实盘一旦启动，就会在`terminal`中启动一个单独的线程在后台运行，运行的时机也是跟真实的股票市场一致的，股票市场收市的时候不运行，交易日早上9点15分唤醒系统开始拉取实时股价，9点半开始运行交易策略，交易策略的运行时机和运行频率在策略的属性中设置。如果策略运行的结果产生交易信号，则根据交易信号模拟挂单，挂单成交后修改响应账户资金和股票持仓，交易费用按照设置中的费率扣除。如果资金不足或持仓不足会导致交易失败，当天买入的股票同真实市场一样T+1交割，第二个交易日开始前交割完毕。 `Qteasy`的实盘运行使用了“账户”的概念，就跟您在股票交易市场开户一样，一个账户可以有自己的持有资金，股票持仓，单独计算盈亏。运行过程中您可以随时终止程序，这时所有的交易记录都会保存下来，下次重新启动时，只要引用上一次运行使用的账户ID（account ID）就可以从上次中断的地方继续运行了，包括交易策略的参数等信息都会从上次停止的地方重新启动，因此启动时需要指定账户，如果不想继续上次的账户，可以新开一个账户运行，或者删除当前账户下的所有记录重新开始交易。 `qteasy`中的所有交易策略都是由`qteast.Operator`（交易员）对象来实现回测和运行的，`Operator`对象是一个策略容器，一个交易员可以同时 管理多个不同的交易策略。 `qteasy`可以使用历史数据回测策略表现并输出图表如下： `qteasy`可以通过`tushare`金融数据包来获取大量的金融数据，用户需要自行申请`API Token`，获取相应的权限和积分（详情参考：https://tushare.pro/document/2） `qteasy`将在同一段历史数据（优化区间）上反复回测，找到结果最好的30组参数，并把这30组参数在另一段历史数据（测试区间）上进行独立测试，并显 示独立测试的结果： `qteasy`所有必要的依赖包都可以在`pip`安装的同时安装好，但某些特殊情况下，您需要在安装时指定可选依赖包，以便在安装`qteasy`时同时安装，或者手动安装依赖包： `qteasy`提供了两种不同的用户界面以运行实盘交易： `qteasy`的K线图函数`candle`支持通过六位数股票/指数代码查询准确的证券代码，也支持通过股票、指数名称显示K线图 `qt.candle()`支持功能如下： `queasy`提供了两种方式创建交易策略，详细的说明请参见使用教程： python 版本 上面两种方式都可以在实盘运行时使用，根据`qteasy`的配置参数进入不同的交互界，关于更多实盘运行的介绍，请参见[`QTEASY`文档](https://qteasy.readthedocs.io) 上面的命令将启动一个实盘交易，使用账户ID为18，使用CLI界面监控实盘交易。 下载金融历史数据 为了使用`qteasy`，需要大量的金融历史数据，所有的历史数据都必须首先保存在本地，如果本地没有历史数据，那么`qteasy`的许多功能就无法执行。 交易策略的参数调优 交易策略的表现与参数有关，如果输入不同的参数，策略回报相差会非常大。`qteasy`可以用多种不同的优化算法，帮助搜索最优的策略参数， 使用`qt.built_ins()`函数可以查看`DMA`策略的详细解，使用`qt.built_ins()`函数可以获取或者筛选需要的内置交易策略，例如： 使用默认参数回测刚才建立的DMA策略在历史数据上的表现，可以使用`op.run(mode=1)`。 关于`DataSource`对象的更多详细介绍，请参见[qteasy教程](https://github.com/shepherdpp/qteasy/tutorials) 关于策略优化结果的更多解读、以及更多优化参数的介绍，请参见详细文档 关闭并保存好配置文件后，重新导入`qteasy`，就完成了数据源的配置，可以开始下载数据到本地了。 创建`Operator`对象时传入参数：`strategies='DMA'`，可以新建一个`DMA`双均线择时交易策略。 创建好`Operator`对象后，可以用`op.info()`来查看它的信息。 创建一个投资策略 回测并评价交易策略的性能表现 因此，在使用`qteasy`之前需要对本地数据源和`tushare`进行必要的配置。在`QT_ROOT_PATH/qteasy/`路径下打开配置文件`qteasy.cfg`，可以看到下面内容： 在K线图上双击鼠标，可以切换不同的均线类型 在K线图的指标区域双击，可以切换不同的指标类型：`MACD`，`RSI`，`DEMA` 在使用动态K线图时，用户可以用鼠标和键盘控制K线图的显示范围： 在启动实盘时可以通过`qteasy`的系统配置变量`live_trade_account_name`来指定使用的账户名，系统会自动创建一个新的账户并赋予账户ID；如果想要使用已有的账户，可以在启动时通过`live_trade_account_id`指定账户ID。 在这里，我们将使用一个内置的`DMA`均线择时策略来生成一个最简单的大盘择时交易系统。所有内置交易策略的清单和详细说明请参见文档。 在配置好`Operator`对象并设置好策略后，`qteasy`可以自动定期运行、自动盯盘、自动下载实时数据并根据策略结果生成交易指令，模拟交易过程并记录交易结果。 在默认情况下，策略由三个**可调参数**：`(12,26,9)`, 但我们可以给出任意大于2小于250的三个整数作为策略的参数，以适应不同交易活跃度的股票、或者适应 不同的策略运行周期。 基本的模块导入方法如下 如果您希望通过命令行方式在Terminal中启动`qteasy`并直接开始实盘交易，您可以创建一个脚本文件，并在Terminal中通过命令行启动交易。 `qteasy`提供了几个实盘交易脚本文件的示例，您可以在`qteasy`的安装目录下的`examples`文件夹中找到这些脚本文件，并使用下面的命令启动实盘交易： 安装依赖包 安装及依赖 完成上述设置后，使用下面的代码运行交易策略。 导入`qteasy` 将你获得的tushare API token添加到配置文件中，如下所示： 得到： 数据下载到本地后，可以使用`qt.get_history_data()`来获取数据，如果同时获取多个股票的历史数据，每个股票的历史数据会被分别保存到一个`dict`中。 显示不同移动均线以及MACD/KDJ等指标 显示分钟、 周或月K线 显示复权价格 显示股票、基金、期货的K线 现在可以看到`op`中有一个交易策略，ID是`dma`，我们在`Operator`层面设置或修改策略的参数 时，都需要引用这个`ID`。 生成一个DMA均线择时交易策略 生成的K线图可以是一个交互式动态K线图（请注意，K线图基于`matplotlib`绘制，在使用不同的终端时，显示功能有所区别，某些终端并不支持 动态图表，详情请参阅 [matplotlib文档](https://matplotlib.org/stable/users/explain/backends.html) 结果如下： 股票的数据下载后，使用`qt.candle()`可以显示股票数据K线图。 要下载金融价格数据，使用`qt.refill_data_source()`函数。下面的代码下载2021及2022两年内所有股票、所有指数的日K线数据，同时下载所有的股票和基金的基本信息数据。 （根据网络速度，下载数据可能需要十分钟左右的时间，如果存储为csv文件，将占用大约200MB的磁盘空间）： 要使用策略优化功能，需要设置交易策略的优化标记`opt_tag=1`，并配置环境变量`mode=2`即可: 详细的用法请参考文档，示例如下(请先使用`qt.refill_data_source()`下载相应的历史数据)： 输出结果如下： 运行上述代码会得到一个`Dict`对象，包含两个股票"000001.SZ"以及"000005.SZ"的K线数据（数据存储为`DataFrame`）： 通过`pip`安装 通过键盘上下键，可以缩小或放大K线图的显示范围 通过键盘左右方向键，可以移动K线图的显示范围显示更早或更晚的K线 部署并开始交易策略的实盘运行 配置`tushare token` 配置本地数据源 —— 用MySQL数据库作为本地数据源 配置本地数据源和tushare token 除了价格数据以外，`qteasy`还可以下载并管理包括财务报表、技术指标、基本面数据等在内的大量金融数据，详情请参见[QTEASY教程：金融数据下载及管理](https://github.com/shepherdpp/qteasy/blob/master/tutorials/Tutorial%2002%20-%20金融数据获取及管理.md) 默认情况下`qteasy`使用存储在`data/`路径下的`.csv`文件作为数据源，不需要特殊设置。 如果设置使用`mysql`数据库作为本地数据源，在配置文件中添加以下配置： 鼠标在图表上左右拖动：可以移动K线图显示更早或更晚的K线 鼠标滚轮在图表上滚动，可以缩小或放大K线图的显示范围 Project-Id-Version: qteasy 1.4
Report-Msgid-Bugs-To: 
POT-Creation-Date: 2025-03-03 20:50+0800
PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE
Last-Translator: FULL NAME <EMAIL@ADDRESS>
Language: en
Language-Team: en <LL@li.org>
Plural-Forms: nplurals=2; plural=(n != 1);
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8
Content-Transfer-Encoding: 8bit
Generated-By: Babel 2.15.0
 ![png](img/output_24_1.png)    Apply the optimized parameters to the strategy and backtest again, the results will be significantly improved: **`TraderApp`** (added in v1.2.0) Interactive graphical interface, you can view trading logs, view positions, view account fund changes, etc. in the graphical interface ![png](examples/img/trader_app_light_theme.png)  ![png](examples/img/trader_app_2.png) **`TraderShell`** Interactive command line interface, you can enter commands in the command line, view trading logs, view positions, view account fund changes, etc.: ![png](img/output_27_1.png)   ![png](img/output_27_3.png) **`pyarrow`**, used to operate `feather` files, store local data as `feather` files, `pyarrow` can be automatically installed when installing `qteasy`, or manually installed: **`pymysql`**, Starting from `v1.4`, `pymysql` and `db-utils` have become the default dependencies of `qteasy`, no additional installation is required **`pytables`**, used to operate `HDF` files, store local data to `HDF` files, `pytables` cannot be automatically installed, you need to manually install `pytables` using `conda`: **`ta-lib`**, to use all built-in trading strategies, the following method can install the `ta-lib API`, but it also depends on the C language `TA- **Use built-in trading strategy combination** **Create custom strategies through strategy classes** *`python` version >= 3.6, <3.13* Get to know qteasy in 10 minutes QTEASY Quick Start Guide `DMA` is a built-in moving average timing strategy. It determines the long or short or buy/sell points by calculating the difference between the fast and slow moving averages of the daily closing price of the stock `DMA` and the cross situation between its moving average `AMA`. When started, `qteasy` will run the strategy in the background in a separate thread in the `terminal`. The timing of the run is consistent with the real stock market. The system will not run when the stock market closes. The system will wake up at 9:15 am to start pulling real-time stock prices, and start running the trading strategy at 9:30 am. The timing and frequency of the trading strategy are set in the strategy attributes. If the running result of the strategy generates a trading signal, simulate the order according to the trading signal, modify the corresponding account funds and stock holdings after the order is executed, and deduct the trading fee according to the rate set. If the funds are insufficient or the position is insufficient, the transaction will fail. Stocks purchased on the same day will be settled on the second trading day. In `Qteasy`, an "account" is needed for each trader instance, just like opening an account in the stock trading market. An account can have its own holding funds, stock holdings, and calculate profits and losses separately. You can terminate the program at any time during the operation. All transaction records will be saved. When you restart the program, you can continue from the last interrupted place as long as you refer to the account ID used in the last operation (account ID). All information, including the parameters of the trading strategy, will be restarted from the last stop. Therefore, you need to specify the account when starting. If you do not want to continue the last account, you can start a new account, or delete all records under the current account and start trading again. All trading strategies in `qteasy` are implemented by `qteasy.Operator` (trader) objects for backtesting and running. The `Operator` object is a strategy container, and a trader can manage multiple different trading strategies at the same time. `qteasy` can backtest the performance of the strategy using historical data and output the chart as follows: `qteasy` can obtain a large amount of financial data through the `tushare` financial data package. Users need to apply for an `API Token` by themselves to obtain the corresponding permissions and points (for details, please refer to: https://tushare.pro/document/2) `qteasy` will repeatedly backtest on the same historical data (optimization interval) to find the best 30 sets of parameters, and test these 30 sets of parameters independently on another historical data (test interval), and display the results of the independent test: All necessary dependencies for `qteasy` can be installed at the same time as `pip`, but in some special cases, you need to specify optional dependencies at installation time to install them at the same time as `qteasy`, or install them manually: `qteasy` provides two different user interfaces to run real trading: The function `candle` is able to query the accurate security code through the six-digit stock/index code, and also display the K-line chart by stock/index name. such as following examples: `qteasy` provides two ways to create trading strategies, for detailed instructions, please refer to the tutorial: python version Both methods can be used during real trading. Enter different interactive interfaces according to the configuration parameters of `qteasy`. For more information about real trading, please refer to [`QTEASY` documentation](https://qteasy.readthedocs.io) Above command will start a real trading, using account ID 18, and monitor the real trading using the CLI interface. Download financial historical data In order to use `qteasy`, a large amount of financial historical data is required, and all historical data must be saved locally first. If there is no historical data locally, many functions of `qteasy` cannot be executed. Optimize trading strategy parameters The performance of the trading strategy is related to the parameters. If different parameters are input, the difference in strategy returns will be very large. `qteasy` can use a variety of different optimization algorithms to help search for the optimal strategy parameters. Check the detailed explanation of the `DMA` strategy with the `qt.built_ins()` function. Use the `qt.built_ins()` function to obtain or filter the required built-in trading strategies, for example: Back test to evaluate the strategy with historical data with default parameters, we can use `op.run(mode=1)`. For more detailed introductions about `DataSource` object, please refer to [qteasy tutorial](qteasy.readthedocs.io/en/latest) Please refer to the detailed documentation for more interpretation of the optimization results and more introduction of optimization parameters Close and save the configuration file, re-import `qteasy`, and the data source configuration is complete, you can start downloading data to the local. Pass `strategies='DMA'` when creating the `Operator` object to create a new `DMA` dual moving average timing trading strategy. View its information with `op.info()` after creating the `Operator` object. Create an investment strategy Backtest and evaluate the performance of trading strategies Therefore, before using `qteasy`, it is necessary to configure the local data source and `tushare`. Open the configuration file `qteasy.cfg` in the `QT_ROOT_PATH/qteasy/` path, you can see the following content: Double-click to switch different moving average types Double-click in the indicator area to switch between different indicator types: `MACD`, `RSI`, `DEMA` With the dynamic candle stick chart, users can control the display range of the candle stick chart with the mouse and keyboard: You can specify the account name to be used by `qteasy`'s system configuration variable `live_trade_account_name` when starting the real trading. The system will automatically create a new account and assign an account ID. If you want to use an existing account, you can specify the account ID when starting through `live_trade_account_id`. Now, we will use a built-in `DMA` moving average timing strategy to generate the simplest market timing trading system. For a list and detailed description of all built-in trading strategies, please refer to the documentation. Configured the `Operator` object and set the strategy, `qteasy` can automatically run regularly, monitor the market, automatically download real-time data, generate trading instructions according to the strategy results, simulate the trading process, and record the trading results. By default, the strategy has three **adjustable parameters**: `(12,26,9)`, but we can provide any three integers greater than 2 and less than 250 as the parameters of the strategy to adapt to stocks with different trading activity, or to adapt to different strategy operation cycles. Import the module: If you want to start `qteasy` and start real trading directly in the Terminal through the command line, you can create a script file and start trading through the command line in the Terminal. `qteasy` provides several examples of real trading script files. You can find these script files in the `examples` folder under the installation directory of `qteasy`, and start real trading with the following command: Install dependencies Installation and Dependencies Start the trading strategy with the following code after completing the above settings. Import `qteasy` Add your tushare API token to the configuration file as shown below: We will see: Acquire downloaded data with function `qt.get_history_data()`. If you get historical data for multiple stocks at the same time, the historical data for each stock will be saved separately to a `dict`. View different moving averages and MACD/KDJ indicators View minute, weekly or monthly charts View adjusted prices View candle stick chart for stocks, funds, and futures Now we can see that there is a trading strategy in `op`, the ID is `dma`, when we set or modify the parameters of the strategy at the `Operator` level, we need to refer to this `ID`. Generate a DMA moving average timing trading strategy The candle stick chart is interactive and dynamic (please note that the candle stick chart is drawn based on `matplotlib`, and the display function varies when using different terminals. Some terminals do not support dynamic charts. For details, please refer to [matplotlib documentation](https://matplotlib.org/stable/users/explain/backends.html) Result is as follows: A candle stick chart can be displayed using `qt.candle()` after data download. Download financial price data with `qt.refill_data_source()` function. The following code downloads daily K-line data for all stocks and all indexes within 2021 and 2022, and downloads basic information data for all stocks and funds at the same time. (Depending on the network speed, downloading data may take about ten minutes. If stored as a csv file, it will occupy about 200MB of disk space): To optimize the strategy, you need to set the optimization flag of the trading strategy `opt_tag=1`, and configure the environment variable `mode=2`. More detailed introductions can be found in the documentation, examples are as follows (please use `qt.refill_data_source()` to download the corresponding historical data first): Following result will pop up: Above snippet will return a `Dict` object, containing K-line data for two stocks "000001.SZ" and "000005.SZ" (data stored as `DataFrame`): Install via `pip` Press `up` or `down` arrow keys to zoom in or out of the candle stick chart Press `left` or `right` arrow keys to move the candle stick chart to display earlier or later candle sticks Deploy and start the real trading strategy Configure `tushare token` Configure local data source - use MySQL database as local data source Configure local data source and tushare token Apart from stock prices, `qteasy` can also download and manage a large amount of financial data including financial statements, technical indicators, fundamental data, etc. For details, please refer to [QTEASY Tutorial: Financial Data Download and Management]( By default, `qteasy` uses `.csv` files stored in the `data/` path as the data source, and no special settings are required. If you set to use the `mysql` database as the local data source, add the following configuration to the configuration file: Drag and drop horizontally: move the candle stick chart to display earlier or later candle sticks Scroll the mouse to zoom in or out of the candle stick chart 