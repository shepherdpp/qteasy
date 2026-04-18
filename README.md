![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/docs/source/img/qteasy_logo_horizontal.png)

# `qteasy` -- 一个本地化、灵活易用的高效量化投资工具包

![PyPI](https://img.shields.io/pypi/v/qteasy)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/qteasy)
[![Build Status](https://app.travis-ci.com/shepherdpp/qteasy.svg?branch=master)](https://app.travis-ci.com/shepherdpp/qteasy)
[![Documentation Status](https://readthedocs.org/projects/qteasy/badge/?version=latest)](https://qteasy.readthedocs.io/zh-cn/latest/)
![GitHub](https://img.shields.io/github/license/shepherdpp/qteasy)
![GitHub repo size](https://img.shields.io/github/repo-size/shepherdpp/qteasy)
![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/shepherdpp/qteasy)
![GitHub top language](https://img.shields.io/github/languages/top/shepherdpp/qteasy)
![PyPI - Implementation](https://img.shields.io/pypi/implementation/qteasy)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/qteasy)
![GitHub branch checks state](https://img.shields.io/github/checks-status/shepherdpp/qteasy/master)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/shepherdpp/qteasy)
![GitHub issues](https://img.shields.io/github/issues/shepherdpp/qteasy)
![GitHub last commit](https://img.shields.io/github/last-commit/shepherdpp/qteasy)
![GitHub contributors](https://img.shields.io/github/contributors/shepherdpp/qteasy)
![PyPI - Downloads](https://img.shields.io/pypi/dm/qteasy)
![PyPI - Downloads](https://img.shields.io/pypi/dw/qteasy)
![GitHub Repo stars](https://img.shields.io/github/stars/shepherdpp/qteasy?style=social)
![GitHub forks](https://img.shields.io/github/forks/shepherdpp/qteasy?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/shepherdpp/qteasy?style=social)
![GitHub followers](https://img.shields.io/github/followers/shepherdpp?style=social)
![GitHub Sponsors](https://img.shields.io/github/sponsors/shepherdpp?style=social)


- [关于 qteasy](#关于qteasy)
- [为什么用 qteasy？——量化人关心的几点](#为什么用-qteasy量化人关心的几点)
- [qteasy 能做什么](#qteasy能做什么)
- [安装](#安装)
- [文档](#文档)
- [10分钟了解 qteasy 的功能](#10分钟了解-qteasy-的功能)
  - [初始配置——本地数据源](#配置本地数据源)
  - [下载股票价格并可视化](#下载金融历史数据)
  - [创建投资策略](#创建一个投资策略)
  - [投资策略的回测和评价](#回测并评价交易策略的性能表现)
  - [投资策略的优化](#交易策略的参数调优)
  - [投资策略的实盘运行](#部署并开始交易策略的实盘运行)

> Note:
> 
> `qteasy`已经升级到2.0版本，使得交易策略能更加灵活有效地使用历史数据、同时简化了交易策略的定义过程、提高了效率。
> 由于`qteasy`仍处于测试中，软件中不免存在一些漏洞和bug，如果大家使用中出现问题，欢迎[Issue-报告bug](https://github.com/shepherdpp/qteasy/issues/new?assignees=&labels=&projects=&template=bug-report---bug报告.md&title=)或者[提交新功能需求](https://github.com/shepherdpp/qteasy/issues/new?assignees=&labels=&projects=&template=feature-request---新功能需求.md&title=)给我，也可以进入[讨论区](https://github.com/shepherdpp/qteasy/discussions)参与讨论。也欢迎各位贡献代码！
>
> 我会尽快修复问题并回复大家的问题。

## 关于`qteasy`

- 作者: **Jackie PENG**
- email: *jackie_pengzhao@163.com*
- Created: 2019, July, 16
- Latest Version: `2.4.1`
- Document: [https://qteasy.readthedocs.io/zh-cn/latest/](https://qteasy.readthedocs.io/zh-cn/latest/)
- License: BSD 3-Clause License

`qteasy`是为量化交易人员开发的一套量化交易工具包，特点如下：

1. **全流程本地化**：数据、回测、优化、模拟均在本地，与云平台相比隐私与可控性更好，与多数开源框架比“数据→策略→回测→实盘”一体化程度高。
2. **回测可信与实盘一致**：严格“当时可见”数据注入、同一套策略逻辑用于回测与实盘，降低“回测漂亮、实盘走样”的风险。
3. **向量化 + 数据隔离**：以高速向量化回测为目标，但摒弃全时间轴一次性算指标，改用数据提前打包装配 + 按步注入数据窗口的方式——每步策略仅能访问该步对应的历史窗口，与实盘“当时能看到的数据”一致，从机制上避免未来函数；在保证正确性的前提下兼顾速度。
4. **精细交易与数据建模**：支持 T+1 交割、交易费用、MOQ、交割队列等；use_latest_data_cycle 显式控制「是否使用交易当时的最新数据」，该细节在长期回测中会对收益产生显著影响，qteasy 将其作为可配置项而非隐式假设。
5. **易用与灵活兼顾**：内置 70+ 策略、积木式多策略组合、参数可调与多优化算法；用户只需在 realize() 中 get_data() 取数并计算信号，窗口与时间对齐由框架负责，降低误用未来数据的可能。
6. **国内市场友好**：`Tushare`、A 股/指数/基金、计划 `QMT`，与 `Backtrader`/`Zipline` 等偏美股/国际的定位形成差异。

**设计理念**：qteasy 坚持本地化与可复现——你的数据在本地、策略逻辑统一用于回测与实盘、每个时点只用当时已可用的数据驱动决策，让回测结果更可信，从研究到实盘的过渡更顺畅。

## 为什么用 qteasy？——量化人关心的几点

- **回测结果可信，避免未来函数** 系统在回测时严格按「每个时点当时能看到的」历史数据驱动策略，策略无法触及未来数据，从机制上杜绝无意中的未来函数，回测结果更可信。
- **回测与实盘同一套逻辑** 你写的策略逻辑既用于历史回测，也用于实盘或模拟盘，不换引擎、不换数据接口，减少「回测很好、实盘走样」的常见落差。
- **多策略像搭积木，信号可配置合并** 可以把多个策略组合在一起，并选择如何把各策略的信号合并成最终交易信号（例如加权平均、取交集等），方便做多策略、多周期组合。
- **参数更灵活，不同标的可用不同参数** 同一套策略可以为不同股票或标的设置不同参数（例如不同股票用不同均线周期），并支持多种优化算法在历史数据上搜索更稳健的参数组合。
- **回测和优化效率极高** 回测核心以 NumPy + Numba 实现，标的维向量化、时间维顺序，支持多进程并行优化，回测和优化效率极高。
- **全流程本地、可复现** 数据获取与存储、回测、参数优化、实盘/模拟运行均在本地完成，配置清晰，便于复现结果和排查问题。

**高性能回测与设计特点**：回测与交易计算采用向量化 + Numba（`backtest_step`、`backtest_batch_steps`、`backtest_flash_steps` 等），时间维顺序以支持 T+1/交割等状态，标的维在单步内向量化；多组参数优化通过多进程并行。**防未来函数**由机制保证：每步仅向策略注入当时可见的数据窗口，策略在 `realize()` 中 `get_data()` 取到的仅是该步窗口，从根源上避免无意中使用未来数据。详见文档 [回测引擎与性能](https://qteasy.readthedocs.io/zh-cn/latest/back_testing/6.%20backtest_engine_and_performance.html)、[设计初衷与独特优势](https://qteasy.readthedocs.io/zh-cn/latest/design/08-design-rationale-and-advantages.html)。

| 对比项           | qteasy | Backtrader | VectorBT |
|------------------|--------|------------|----------|
| 回测引擎         | 时间顺序 + 标的向量化 + Numba | 事件驱动（逐 bar） | 全时间轴矩阵广播 |
| 防未来函数       | 内置（按步数据窗口注入） | 需自行保证 | 多简化资金/规则 |
| 国内数据/实盘    | Tushare、计划 QMT | 需自接；有 IB 等 | 无国内默认数据与实盘 |

### 2.0 版本亮点

2.0 在保持上述特性的基础上，进一步带来：更灵活的策略参数设置；多策略可按不同运行频率与运行时机组合；策略可同时使用多种时间周期与数据窗口；更多优化算法与更丰富的评估指标；支持追踪策略内部行为，便于排查与调试。更多变更说明见 [2.0 迁移指南](https://qteasy.readthedocs.io/zh-cn/latest/) 及文档中的「架构与设计」章节。

## `qteasy`能做什么？


### **获取并管理金融历史数据**: 

- 方便地从多渠道获取大量金融历史数据，进行数据清洗后以统一格式进行本地存储
- 通过`DataType`对象结构化管理金融数据中的可用信息，即便是复权价格、指数成份等复杂信息，也只需要一行代码即可获取
- 基于`HistoryPanel` 三维历史数据面板统一管理多标的 / 多数据类型，直接在其上完成统计、滚动窗口、收益 / 波动率、K 线技术指标与蜡烛形态识别等计算
- 基于`DataType` / `HistoryPanel` 的金融数据可视化、统计分析以及分析结果可视化
- 数据本地存储、按需取用，为回测与实盘提供一致的数据基础，便于复现

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/docs/source/img/output_5_2.png)

### **以简单、安全的方式创建交易策略**

- 通过`BaseStrategy`类，交易策略定义方法直观、逻辑清晰
- 内置超过70种策略开箱即用，独特的策略混合和组机制，复杂策略可以通过简单策略拼装而来，过程如同搭积木
- 交易策略的数据输入和使用方法完全封装且安全，完全避免无意中导致未来函数、数据泄露等问题，保证策略运行结果的真实性和可靠性
- 同一套策略逻辑既用于回测也用于实盘，减少「回测漂亮、实盘走样」的落差

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/docs/source/img/output_14_3.png)

### **交易策略的回测评价、优化和模拟自动化交易**

- 通过`Operator`交易员类管理策略运行，按照真实市场交易节奏回测策略，对交易结果进行多维度全方位评价，生成交易报告和结果图表
- 提供多种优化算法，包括模拟退火、遗传算法、贝叶斯优化等在大参数空间中优化策略性能
- 获取实时市场数据，运行策略模拟自动化交易，跟踪记录交易日志、股票持仓、账户资金变化等信息
- 回测、优化与实盘使用同一套运行机制，写一次策略即可全模式运行，配置清晰，便于复现与排查
- 未来将通过QMT接口接入券商提供的实盘交易接口，实现自动化交易

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/docs/source/examples/img/trader_app_1.png)  
![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/docs/source/examples/img/trader_app_2.png)  
![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/docs/source/examples/img/trader_app_light_theme.png) 

## 安装

```bash
$ pip install qteasy
```

## 文档

关于`QTEASY`系统的更多详细解释和使用方法，请参阅[QTEASY文档](https://qteasy.readthedocs.io/zh-cn/latest/)：


### python 版本
- *`python` version >= 3.9, < 3.13* 

### 安装可选依赖包

`qteasy`所有必要的依赖包都可以在`pip`安装的同时安装好，但某些特殊情况下，您需要在安装时指定可选依赖包，以便在安装`qteasy`时同时安装，或者手动安装依赖包：

- **`pymysql`**, 用于连接`MySQL`数据库,将本地数据存储到`MySQL`数据库 从1.4版本开始，`pymysql`和`db-utils`已经是qtesay的默认依赖包，不需要手动安装
- **`pyarrow`**, 用于操作`feather`文件，将本地数据存储为`feather`文件，`pyarrow`可以在安装`qteasy`时自动安装，也可以手动安装：
    ```bash
    $ pip install 'qteasy[feather]'  # 安装qteasy时自动安装pyarrow
    $ pip install pyarrow  # 手动安装pyarrow
    ```
- **`pytables`**, 用于操作`HDF`文件，将本地数据存储到`HDF`文件，`pytables`不能自动安装，需要使用`conda`手动安装`pytables`：
    ```bash
    $ conda install pytables  # 安装pytables
    ```
- **`ta-lib`**, 以便使用所有的内置交易策略，下面的方法可以安装`ta-lib API`，但它还依赖C语言的`TA-Lib`包，安装方法请参考[FAQ](https://qteasy.readthedocs.io/zh-cn/latest/faq.html#id2)
    ```bash
    $ pip install 'qteasy[talib]'  # 安装qteasy时自动安装ta-lib
    $ pip install ta-lib  # 手动安装ta-lib
    ```

## 10分钟了解 qteasy 的功能

下面通过一个约 10 分钟的教程，快速体验从数据到回测、优化与实盘的完整流程。

### 导入`qteasy`
基本的模块导入方法如下

```python
import qteasy as qt
qt.__version__
```

### 配置本地数据源

为了使用`qteasy`，需要大量的金融历史数据，所有的历史数据都必须首先保存在本地，如果本地没有历史数据，那么`qteasy`的许多功能就无法执行。

`qteasy`默认通过`tushare`金融数据包来获取金融数据，用户需要自行申请`API Token`，获取相应的权限和积分（详情参考：[Tushare 官网](https://tushare.pro/document/2)）

因此，在使用`qteasy`之前需要对`tushare`的`token`进行必要的配置。
最简单的方式是使用`qt.start_up_settings()`和`qt.update_start_up_setting()`方法：

```python
qt.update_start_up_setting(
        tushare_token='<你的tushare_token>',
        local_data_source='db',  # 可选项：设置本地数据源类型，db表示使用MySQL数据库，默认使用csv文件
        local_db_host = '<你的数据库主机名>',  # 可选项：如果使用MySQL数据库作为本地数据源，需要设置数据库的连接地址，默认localhost
        local_db_port = 3306,  # 可选项：如果使用MySQL数据库作为本地数据源，需要设置数据库的连接端口，默认3306
        local_db_user = '<user>',  # 可选项：如果使用MySQL数据库作为本地数据源，需要设置数据库的连接用户名，默认root
        local_db_password = '<password>',  # 可选项：如果使用MySQL数据库作为本地数据源，需要设置数据库的连接密码，默认password
)
# 设置完成后，可以使用qt.start_up_settings()来查看当前的配置
qt.start_up_settings()
```
这时可以看到当前的配置输出如下：

```text
Start up settings:
--------------------
tushare_token = <你的tushare token>
...
```
请检查打印出的配置文件内容是否正确，如果正确，就可以重新导入`qteasy`，并开始正常下载和使用金融数据了。

> qteasy默认情况下将所有的金融数据以csv文件的形式保存在磁盘中，详情参见[qteasy文档数据管理](https://qteasy.readthedocs.io/zh-cn/latest/manage_data/1.%20overview.html)，如果你想把数据保存在`MySQL`数据库中，可以在配置文件中设置`local_data_source='db'`，并设置相应的数据库连接参数，如下所示：
>
>```python
> qt.update_start_up_setting(
>         local_data_source='db',  # 可选项：设置本地数据源类型，db表示使用MySQL数据库，默认使用csv文件
>         local_db_host = '<你的数据库主机名>',  # 可选项：如果使用MySQL数据库作为本地数据源，需要设置数据库的连接地址，默认localhost
>         local_db_port = 3306,  # 可选项：如果使用MySQL数据库作为本地数据源，需要设置数据库的连接端口，默认3306
>         local_db_user = '<user>',  # 可选项：如果使用MySQL数据库作为本地数据源，需要设置数据库的连接用户名，默认root
>         local_db_password = '<password>',  # 可选项：如果使用MySQL数据库作为本地数据源，需要设置数据库的连接密码，默认password
> )
>```

### 下载金融历史数据 

要下载金融价格数据，使用`qt.refill_data_source()`函数。下面的代码下载2021及2022两年内所有股票、所有指数的日K线数据，同时下载所有的股票和基金的基本信息数据。
（根据网络速度，下载数据可能需要几十秒到几分钟的时间，如果存储为`csv`文件，将占用大约200MB的磁盘空间）：

```python
qt.refill_data_source(
        tables=['stock_daily',   # 股票的日线价格
                'index_daily',   # 指数的日线价格
                'basics'],       # 股票和基金的基本信息
        start_date='20210101',  # 下载数据的起止时间
        end_date='20221231',  
)
```

数据下载到本地后，可以使用`qt.get_history_data()`来获取数据，如果同时获取多个股票的历史数据，每个股票的历史数据会被分别保存到一个`dict`中。

```python
qt.get_history_data(htypes='open, high, low, close', 
                    shares='000001.SZ, 000300.SH',
                    start='20210101',
                    end='20210115')
```
运行上述代码会得到一个`Dict`对象，包含两个股票"000001.SZ"以及"000005.SZ"的K线数据（数据存储为`DataFrame`）：
```
{'000001.SZ':
              open   high    low  close
 2021-01-04  19.10  19.10  18.44  18.60
 2021-01-05  18.40  18.48  17.80  18.17
 2021-01-06  18.08  19.56  18.00  19.56
 ... 
 2021-01-13  21.00  21.01  20.40  20.70
 2021-01-14  20.68  20.89  19.95  20.17
 2021-01-15  21.00  21.95  20.82  21.00,
 
 '000300.SH':
                  open       high        low      close
 2021-01-04  5212.9313  5284.4343  5190.9372  5267.7181
 2021-01-05  5245.8355  5368.5049  5234.3775  5368.5049
 2021-01-06  5386.5144  5433.4694  5341.4304  5417.6677
 ...
 2021-01-13  5609.2637  5644.7195  5535.1435  5577.9711
 2021-01-14  5556.2125  5568.0179  5458.6818  5470.4563
 2021-01-15  5471.3910  5500.6348  5390.2737  5458.0812}
```
除了价格数据以外，`qteasy`还可以下载并管理包括财务报表、技术指标、基本面数据等在内的大量金融数据，详情请参见[qteasy文档](https://qteasy.readthedocs.io/zh-cn/latest/manage_data/1.%20overview.html)

股票的数据下载后，使用`qt.candle()`可以显示股票数据K线图，也可以直接使用 `HistoryPanel` 在代码中对历史数据做统计与因子计算。

```python
data = qt.candle('000300.SH', start='2021-06-01', end='2021-8-01', asset_type='IDX')
```

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/docs/source/img/output_5_2.png)
    
`qteasy`的K线图函数`candle`支持通过六位数股票/指数代码查询准确的证券代码，也支持通过股票、指数名称显示K线图
`qt.candle()`支持功能如下：
- 显示股票、基金、期货的K线
- 显示复权价格
- 显示分钟、 周或月K线 
- 显示不同移动均线以及MACD/KDJ等指标

详细的用法请参考文档，示例如下(请先使用`qt.refill_data_source()`下载相应的历史数据)：


```python
# 场内基金的小时K线图
qt.candle('159601', start = '20220121', freq='h')
# 沪深300指数的日K线图
qt.candle('000300', start = '20200121')
# 股票的30分钟K线，复权价格
qt.candle('中国电信', start = '20211021', freq='30min', adj='b')
# 期货K线，三条移动均线分别为9天、12天、26天
qt.candle('沪铜主力', start = '20211021', mav=[9, 12, 26])
# 场外基金净值曲线图，复权净值，不显示移动均线
qt.candle('000001.OF', start='20200101', asset_type='FD', adj='b', mav=[])
```

### 使用 HistoryPanel 操作历史数据

在掌握了基础取数之后，可以进一步使用 `HistoryPanel` 对历史数据做统计和因子计算，例如：

```python
import qteasy as qt

# 直接获取 HistoryPanel（三维数据：标的 × 时间 × 数据类型）
hp = qt.get_history_data(
        htypes='open, high, low, close, vol',
        shares='000300.SH',
        start='20230101',
        end='20231231',
        as_data_frame=False,    # 返回 HistoryPanel
)

# 计算简单收益率和 20 日波动率
ret = hp.returns(price_htype='close', method='simple')
vol = hp.volatility(window=20, price_htype='close', annualize=True)

# 叠加 20 日均线和 MACD 指标
hp_ma = hp.kline.sma(window=20, price_htype='close')
hp_ma_macd = hp_ma.kline.macd(price_htype='close')

# 识别蜡烛形态（如锤头线）
hammer = hp.candle_pattern('cdlhammer')
print(hammer[hammer['000300.SH'] != 0].head())
```

通过 `HistoryPanel`，可以在多标的、多指标维度上统一管理和计算历史数据，然后根据需要随时切换为 `DataFrame`，与 pandas / sklearn / statsmodels 等生态工具协同使用。

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/docs/source/img/output_3_1.png)

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/docs/source/img/output_7_2.png)

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/docs/source/img/output_8_3.png)

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/docs/source/img/output_3_4.png)

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/docs/source/img/output_3_5.png)
    

生成的K线图可以是一个交互式动态K线图（请注意，K线图基于`matplotlib`绘制，在使用不同的终端时，显示功能有所区别，某些终端并不支持
动态图表，详情请参阅 [matplotlib文档](https://matplotlib.org/stable/users/explain/backends.html)


在使用动态K线图时，用户可以用鼠标和键盘控制K线图的显示范围：

- 鼠标在图表上左右拖动：可以移动K线图显示更早或更晚的K线
- 鼠标滚轮在图表上滚动，可以缩小或放大K线图的显示范围
- 通过键盘左右方向键，可以移动K线图的显示范围显示更早或更晚的K线
- 通过键盘上下键，可以缩小或放大K线图的显示范围
- 在K线图上双击鼠标，可以切换不同的均线类型
- 在K线图的指标区域双击，可以切换不同的指标类型：MACD，RSI，DEMA

![gif](https://raw.githubusercontent.com/shepherdpp/qteasy/master/docs/source/img/output_dyna_plot.gif)

关于`DataSource`对象的更多详细介绍，请参见[qteasy文档](https://qteasy.readthedocs.io/zh-cn/latest/api/data_source.html)


###  创建一个投资策略并启动实盘自动化运行（模拟）

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/docs/source/examples/img/trader_app_2.png) 

`qteasy`中的所有交易策略都是由`qteast.Operator`（交易员）对象来实现回测和运行的，`Operator`对象是一个策略容器，一个交易员可以同时
管理多个不同的交易策略。

`qteasy`提供了两种方式创建交易策略，详细的说明请参见使用教程：

- **使用内置交易策略组合**
- **通过策略类自行创建策略**

#### 创建一个DMA均线择时交易策略
在这里，我们将使用一个内置的`DMA`均线择时策略来生成一个最简单的大盘择时交易系统。所有内置交易策略的清单和详细说明请参见文档。

创建`Operator`对象时传入参数：`strategies='DMA'`，可以新建一个`DMA`双均线择时交易策略。
创建好`Operator`对象后，可以用`op.info()`来查看它的信息。

```python
op = qt.Operator(strategies='dma')
```

现在可以看到`op`中有一个交易策略，ID是`dma`，我们在`Operator`层面设置或修改策略的参数
时，都需要引用这个`ID`。

`DMA`是一个内置的均线择时策略，它通过计算股票每日收盘价的快、慢两根移动均线的差值`DMA`与其移动平均值`AMA`之间的交叉情况来确定多空或买卖点。：

使用`qt.built_in_doc()`函数可以查看`DMA`策略的详细说明，使用`qt.built_ins()`函数可以获取或者筛选需要的内置交易策略，例如：
```python
qt.built_in_doc('dma')
```
得到：

```
 DMA择时策略
    策略参数:
        s, int, 短均线周期
        l, int, 长均线周期
        d, int, DMA周期
    信号类型:
        PS型: 百分比买卖交易信号
    信号规则:
        在下面情况下产生买入信号:
        1， DMA在AMA上方时，多头区间，即DMA线自下而上穿越AMA线后，输出为1
        2， DMA在AMA下方时，空头区间，即DMA线自上而下穿越AMA线后，输出为0
        3， DMA与股价发生背离时的交叉信号，可信度较高
    策略属性缺省值:
        默认参数: (12, 26, 9)
        数据类型: close 收盘价，单数据输入
        窗口长度: 270
        参数范围: [(10, 250), (10, 250), (8, 250)]
    策略不支持参考数据，不支持交易数据
```
在默认情况下，策略有三个**可调参数**：`(12,26,9)`, 但我们可以给出任意大于2小于250的三个整数作为策略的参数，以适应不同交易活跃度的股票、或者适应
不同的策略运行周期。

您可以使用`qt.built_in_list()`函数查看所有内置策略的清单，并使用`qt.built_ins()`或`qt.built_in_strategies()`函数查看特定策略的详细说明。



### 回测、评价并优化交易策略的性能表现

在`qteasy`中，交易策略中使用的任何变量都可以被定义为“可调参数”，例如dma策略中的短均线周期、长均线周期等等。

这些参数的调节范围和参数类型都是人为规定的，交易策略的性能表现受可调参数的影响。

因此，针对不同类型的股票，不同的交易风格、不同的交易周期，策略的参数可能需要被设为不同的值，同时，为了使策略性能最优化，我们也需要寻找最佳的参数组合。`qteasy`提供了策略回测功能，并多种优化算法，帮助搜索最优的策略参数，提高策略表现。

#### 交易策略的回测

`qteasy`可以使用历史数据回测策略表现并输出图表如下：
![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/docs/source/img/output_14_3.png)

使用默认参数回测刚才建立的DMA策略在历史数据上的表现，可以使用`qt.run()`。

```python
op = qt.Operator(strategies='dma')
qt.configure(
        asset_pool='000300.SH',         # 投资资产池
        asset_type='IDX',               # 投资资产类型
        invest_cash_amounts=[100000],   # 投资资金
        invest_start='20220501',        # 投资回测开始日期
             invest_end='20221231',          # 投资回测结束日期
        cost_rate_buy=0.0003,           # 买入费率
        cost_rate_sell=0.0001,          # 卖出费率
        visual=True,                    # 打印可视化回测图表
        trade_log=True,                 # 打印交易日志
)
res = qt.run(op, mode=1)  # 历史回测模式
```
输出结果如下：
```
     ====================================
     |                                  |
     |       BACK TESTING RESULT        |
     |                                  |
     ====================================

qteasy running mode: 1 - History back testing
time consumption for operate signal creation: 4.4 ms
time consumption for operation back looping:  82.5 ms

investment starts on      2022-05-05 00:00:00
ends on                   2022-12-30 00:00:00
Total looped periods:     0.7 years.

-------------operation summary:------------
Only non-empty shares are displayed, call 
"loop_result["oper_count"]" for complete operation summary

          Sell Cnt Buy Cnt Total Long pct Short pct Empty pct
000300.SH    6        6      12   56.4%      0.0%     43.6%   

Total operation fee:     ¥      257.15
total investment amount: ¥  100,000.00
final value:              ¥  105,773.09
Total return:                     5.77% 
Avg Yearly return:                8.95%
Skewness:                          0.58
Kurtosis:                          3.54
Benchmark return:                -3.46% 
Benchmark Yearly return:         -5.23%

------strategy loop_results indicators------ 
alpha:                            0.142
Beta:                             1.003
Sharp ratio:                      0.637
Info ratio:                       0.132
250 day volatility:               0.138
Max drawdown:                    11.92% 
    peak / valley:        2022-08-17 / 2022-10-31
    recovered on:         Not recovered!

===========END OF REPORT=============
```
![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/docs/source/img/output_21_1.png)

#### 交易策略的参数调优

交易策略的表现与参数有关，如果输入不同的参数，策略回报相差会非常大。`qteasy`可以用多种不同的优化算法，帮助搜索最优的策略参数，

要使用策略优化功能，需要设置交易策略的优化标记`opt_tag=1`，并配置环境变量`mode=2`即可:

```python
import qteasy as qt

op = qt.Operator(strategies='dma')
qt.configure(
             opti_start='20220501',     # 优化区间开始日期
             opti_end='20221231',       # 优化区间结束日期
             test_start='20220501',     # 测试区间开始日期
             test_end='20221231',       # 测试区间结束日期
             opti_sample_count=1000,    # 优化样本数量
             visual=True,               # 打印优化结果图表
             parallel=False             # 不使用并行计算
)
op.set_parameter('dma', opt_tag=1)
res = qt.run(op, mode=2)  # 策略优化模式
```

`qteasy`将在同一段历史数据（优化区间）上反复回测，找到结果最好的30组参数，并把这30组参数在另一段历史数据（测试区间）上进行独立测试，并显
示独立测试的结果：
```commandline
==================================== 
|                                  |
|       OPTIMIZATION RESULT        |
|                                  |
====================================

qteasy running mode: 2 - Strategy Parameter Optimization

... # 省略部分输出

# 以下是30组优化的策略参数及其结果（部分结果省略）
    Strategy items Sell-outs Buy-ins ttl-fee     FV      ROI  Benchmark rtn MDD 
0     (35, 69, 60)     1.0      2.0    71.45 106,828.20  6.8%     -3.5%     9.5%
1   (124, 104, 18)     3.0      2.0   124.86 106,900.59  6.9%     -3.5%     7.4%
2   (126, 120, 56)     1.0      1.0    72.38 107,465.86  7.5%     -3.5%     7.5%
...
27   (103, 84, 70)     1.0      1.0    74.84 114,731.44 14.7%     -3.5%     8.8%
28  (143, 103, 49)     1.0      1.0    74.33 116,453.26 16.5%     -3.5%     4.3%
29   (129, 92, 56)     1.0      1.0    74.55 118,811.58 18.8%     -3.5%     4.3%

===========END OF REPORT=============
```

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/docs/source/img/output_24_1.png)   
将优化后的参数应用到策略中，并再次回测，可以看到结果明显提升：

```python
op.set_parameter('dma', par_values=(143, 99, 32))
res = qt.run(op, mode=1)  # 历史回测模式
```
结果如下：

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/docs/source/img/output_26_1.png)   


关于策略优化结果的更多解读、以及更多优化参数的介绍，请参见详细文档

### 启动交易策略的实盘自动化模拟运行

在配置好`Operator`对象并设置好策略后，`qteasy`可以自动定期运行、自动盯盘、自动下载实时数据并根据策略结果生成交易指令，模拟交易过程并记录交易结果。

`Qteasy`的实盘一旦启动，就会在`terminal`中启动一个单独的线程在后台运行，运行的时机也是跟真实的股票市场一致的，股票市场收市的时候不运行，交易日早上9点15分唤醒系统开始拉取实时股价，9点半开始运行交易策略，交易策略的运行时机和运行频率在策略的属性中设置。如果策略运行的结果产生交易信号，则根据交易信号模拟挂单，挂单成交后修改响应账户资金和股票持仓，交易费用按照设置中的费率扣除。如果资金不足或持仓不足会导致交易失败，当天买入的股票同真实市场一样T+1交割，第二个交易日开始前交割完毕。

```python
# 创建一个交易策略alpha
alpha = qt.get_built_in_strategy('ndayrate')  # 创建一个N日股价涨幅交易策略

# 设置策略的运行参数
alpha.window_length = 20  # 数据窗口长度
alpha.sort_ascending = False  # 优先选择涨幅最大的股票
alpha.condition = 'greater'  # 筛选出涨幅大于某一个值的股票
alpha.ubound = 0.005  # 筛选出涨幅大于0.5%的股票
alpha.sel_count = 7  # 每次选出7支股票

# 创建一个交易员对象，运行alpha策略
op = qt.Operator(alpha)

# 设置策略运行参数
# 交易股票池包括所有的银行股和家用电器股
asset_pool = qt.filter_stock_codes(industry='银行, 家用电器', exchange='SSE, SZSE')

qt.configure(
        asset_type='E',  # 交易的标的类型为股票
        asset_pool=asset_pool,  # 交易股票池为所有银行股和家用电器股
        trade_batch_size=100,  # 交易批量为100股的整数倍
        sell_batch_size=1,  # 卖出数量为1股的整数倍
        live_trade_account_id=None,  # 不指定实盘交易账户，给出账户名称并创建一个新的账户
        live_trade_account_name='new_account',
        # 如果想要使用已有的账户，应该指定账户ID同时不给出account_name：
        live_trade_account_id=1
        live_trade_account_name=None
        live_trade_ui_type='tui',  # 使用TUI界面监控实盘交易，默认使用CLI界面
)
```
完成上述设置后，使用下面的代码运行交易策略，运行交易策略时指定模式0，代表实盘交易:

```python
qt.run(op, mode=0)  # 交易模式为实盘运行
```

`Qteasy`的实盘运行有一个“账户”的概念，就跟您在股票交易市场开户一样，一个账户可以有自己的持有资金，股票持仓，单独计算盈亏。运行过程中您可以随时终止程序，这时所有的交易记录都会保存下来，下次重新启动时，只要引用上一次运行使用的账户ID（account ID）就可以从上次中断的地方继续运行了，因此启动时需要指定账户，如果不想继续上次的账户，可以新开一个账户运行。

在启动实盘时可以通过`qteasy`的系统配置变量`live_trade_account_name`来指定使用的账户名，系统会自动创建一个新的账户并赋予账户ID；如果想要使用已有的账户，可以在启动时通过`live_trade_account_id`指定账户ID。

#### 实盘自动化交易的控制界面

为了对策略运行过程进行监控，同时与`qteasy`进行互动，`qteasy`提供了两种不同的交互界面：

#### 命令行用户界面 CLI

- **`TraderShell`** 交互式命令行界面CLI，可以在命令行中输入命令，查看交易日志、查看持仓、查看账户资金变化等信息：
   
   在命令行界面中，启动后默认显示的是交易策略的dashboard(状态页)，在该屏幕上会滚动显示交易策略运行日志，打印产生的交易信号、交易结果、当前最新股票价格等信息。
   
   ![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/docs/source/img/output_27_1.png)  
   在策略运行过程中，用户可以通过键入"Ctrl+C"进入主菜单，按1键进入交互模式，这时用户可以通过键盘输入命令来查看持仓、查看账户资金变化、查看交易日志等信息，也可以通过命令来控制交易策略的运行，例如暂停、继续、终止交易策略的运行。

   ![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/docs/source/img/output_27_3.png) 


   
   CLI界面目前支持的交互命令较多，包括：
  - 暂停、恢复、终止交易策略的运行
  - 查看持仓、账户资金、交易订单、交易历史等信息
  - 手动调整持仓数量、资金数量、手动调整交易配置
  - 手动下单，手动撤单
  - 设置实时价格监控的股票代码



#### Terminal图形用户界面 TUI

- **`TraderApp`** (v1.2.0新增) 交互式图形界面TUI，可以在图形界面中查看交易日志、查看持仓、查看账户资金变化等信息：

   在TUI图形界面中，用户的Terminal会被划分为多个区域，显示策略运行过程中的所有关键信息，例如在顶部显示当前资产总额、浮动盈亏，在画面中部以图表显示当前持仓、交易订单历史记录、实时股票价格、以及策略运行参数等信息，在画面底部显示交易日志。

   ![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/docs/source/examples/img/trader_app_light_theme.png)


   用户可以在TUI界面中以快捷键或者鼠标按钮点击的方式与qteasy的自动化交易程序互动，目前支持的功能较少，包括：
  - 设置或调整实时价格监控的股票代码
  - 更多的功能正在逐步添加中

上面两种方式都可以在实盘运行时使用，根据`qteasy`的配置参数进入不同的交互界，关于更多实盘运行的介绍，请参见[`QTEASY`文档](https://qteasy.readthedocs.io/zh-cn/latest/tutorials/1-get-started.html)
