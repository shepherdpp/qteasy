# `qteasy`教程2 - 获取并管理金融数据

`qteasy`是一个完全本地化部署和运行的量化交易分析工具包，具备以下功能：

- 金融数据的获取、清洗、存储以及处理、可视化、使用
- 量化交易策略的创建，并提供大量内置基本交易策略
- 向量化的高速交易策略回测及交易结果评价
- 交易策略参数的优化以及评价
- 交易策略的部署、实盘运行

通过本系列教程，您将会通过一系列的实际示例，充分了解`qteasy`的主要功能以及使用方法。

## 开始前的准备工作

在开始本教程前，请完成以下工作：

- 完成`qteasy`的安装并升级到最新版本
- 注册`tushare pro`账户并确保有一定的积分（大多数高级数据需要较多积分才能下载）
- 完成`qteasy.cfg`文件的配置，将`tushare_token`写入配置文件
- 完成`mysql`数据库的配置，并将数据库配置写入`qteasy.cfg·`(***可选项***)
- 完成`ta-lib`的安装 (***可选项***)

在[上一篇教程](https://blog.csdn.net/Shepherdppz/article/details/136075222?spm=1001.2014.3001.5501)中，我介绍了如何新建一个虚拟环境，并在新的虚拟环境中安装并初始化`qteasy`，如果还没有完成这一步的朋友，请移步前一篇教程完成`qteasy`的安装和基础配置。

另外，为了方便后续图表等功能的使用，建议使用`jupyter notebook`来进行开发，您可以在新建的虚拟环境中运行以下命令安装`jupyter notebook`：

```
pip install notebook
```
安装完成后，可以使用下面命令启动`jupyter notebook`：

```
jupyter notebook
```

启动后，就可以在浏览器中的一个交互式开发环境中运行代码了，如下图所示：

![在这里插入图片描述](img/jupyter_notebook.png)

如果不使用`jupyter notebook`，也可以使用`ipython`：
```
pip install ipython
```
ipython 运行在terminal中，但是对图表的支持没有那么好


## 获取基础数据以及价格数据

如上一篇教程介绍，刚刚初始化的qteasy是无法调用任何历史数据的，所有历史数据都必须首先下载到本地，保存到一个称为Datasource的数据仓库之后，才能完成后续所有需要数据的工作，例如调用历史数据，进行策略的回测和优化等等。

qteasy需要使用的数据种类很多，所有的数据都是保存在一些预定义的数据表中，Datasource就是一系列数据表的集合。其中最基础的数据表包括：

- trade_calendar - 交易日历数据，包括不同交易所的开市、闭市日期计划，每年底更新下一年的交易日历
- stock_basics - 股票基础信息，包括沪深股市所有股票的基本信息，包括代码、名称、全称、上市日期、分类等等基础信息
- index_basics - 指数基础信息，包括沪深股市所有指数的基本信息，包括代码、名称、全称等等信息

在配置好tushare_token以后，第一次导入qteasy时，如果系统未找到交易日历数据，会显示以下提示信息：

```python
import qteasy as qt
UserWarning: trade calendar is not loaded, some utility functions may not work properly, to download trade calendar, run 
"qt.refill_data_source(tables='trade_calendar')"
  warnings.warn(f'trade calendar is not loaded, some utility functions may not work '
```
qteasy提供了一个函数get_table_overview()来显示本地存储的数据信息，运行这个函数，可以打印出本地保存的数据表的清单，存储的数据量、占用的磁盘空间大小、以及数据范围等等。


```python
import qteasy as qt
qt.get_table_overivew()
[Out]:
Analyzing local data source tables... depending on size of tables, it may take a few minutes
[########################################]62/62-100.0%  Analyzing completed!or>>>>>ht>or>>
file://csv@qt_root/data/
Following tables contain local data, to view complete list, print returned DataFrame
Empty DataFrame
Columns: [has_data, size, records, min2, max2]
Index: []
```

如果本地数据源中没有数据，将会显示上面的内容。此时需要下载数据到本地数据源。
### 下载交易日历和基础数据

我们可以调用`refill_data_source`函数下载交易日历和基础数据。这个函数是`qteasy`的标准数据下载接口函数，所有的历史数据类型均可以通过此接口下载。这个函数的基本参数是tables，传入数据表的名称即可下载相应的数据到本地存储了。使用`refill_data_source`下载交易数据时，`qteasy`会自动进行数据清洗，排除重复数据，去除错误数据，发生错误自动重试，并将下载的数据合并到本地数据表中。目前`qteasy`仅支持通过`tushare`下载金融数据，未来还会增加其他的金融数据接口，丰富用户选择。

要下载前面提到的交易日历、股票和指数的基本信息，只需要运行下面的代码：

```python
qt.refill_data_source(tables='trade_calendar, stock_basic, index_basic')
[out]:
Filling data source file://csv@qt_root/data/ ...
[########################################]9/9-100.0%  <trade_calendar:SSE-XHKG>74804wrtn in ~9't
[########################################]3/3-100.0%  <stock_basic:SSE-BSE>5365wrtn in ~1't
[########################################]7/7-100.0%  <index_basic:SSE-OTH>10365wrtn in ~1't
```
数据下载过程中会显示一个进度条，下载完成后，再次运行`qt.get_table_overview()`函数，可以看到数据已经成功下载到本地：

```python
qt.get_table_overivew()
[Out]:
Analyzing local data source tables... depending on size of tables, it may take a few minutes
[########################################]62/62-100.0%  Analyzing completed!or>>>>>ht>or>>
file://csv@qt_root/data/
Following tables contain local data, to view complete list, print returned DataFrame
               Has_data Size_on_disk Record_count Record_start Record_end
table                                                                    
trade_calendar   True       1.9MB         75K       19901012    20241231 
stock_basic      True       355KB          2K           None        None 
index_basic      True       3.4MB         10K           None        None 
```

可以看到，三张数据表已经被下载到本地数据源，数据源的类型为`"file://csv@qt_root/data/"`类型（即数据以`csv`文件形式存储在qt根路径的`/data/`路径下），包含三张数据表，其中交易日历的范围涵盖到2024年年底。

### 查看股票和指数的基础数据

上面的基础数据下载好之后，建议重新启动IDE，重新导入`qteasy`。这时，我们就可以使用`qteasy`筛选和查找股票/指数了。

查找股票/指数详细信息可以使用`get_stock_info()`或者`get_basic_info()`函数，两个函数功能相同，都可以根据输入的证券代码、名称或者关键字查找证券的信息，支持通配符或者模糊查找；如果同一个代码对应不同的`qt_code`，例如股票`000001`代表平安银行，对应`qt_code: 000001.SZ`，而指数`000001`代表上证指数，`qt_code: 000001.SZ`，`qteasy`会罗列出所有的证券信息：

```python
import qteasy as qt

# 通过完整的qt_code获取信息
qt.get_basic_info('000001.SZ')
[Out]:
found 1 matches, matched codes are {'E': {'000001.SZ': '平安银行'}, 'count': 1}
More information for asset type E:
------------------------------------------
ts_code       000001.SZ
name               平安银行
area                 深圳
industry             银行
fullname     平安银行股份有限公司
list_status           L
list_date    1991-04-03
-------------------------------------------

# 如果不知道完整的qt_code，可以通过六位数字证券代码获取所有相关的证券信息，并列出他们的qt_code
qt.get_basic_info('000001')
found 4 matches, matched codes are {'E': {'000001.SZ': '平安银行'}, 'IDX': {'000001.CZC': '农期指数', '000001.SH': '上证指数'}, 'count': 3}
More information for asset type E:
------------------------------------------
ts_code       000001.SZ
name               平安银行
area                 深圳
industry             银行
fullname     平安银行股份有限公司
list_status           L
list_date    1991-04-03
-------------------------------------------
More information for asset type IDX:
------------------------------------------
ts_code   000001.CZC   000001.SH
name            农期指数        上证指数
fullname        农期指数      上证综合指数
publisher    郑州商品交易所        中证公司
category        商品指数        综合指数
list_date       None  1991-07-15
-------------------------------------------

# 通过中文名称关键字搜索相关证券代码
qt.get_basic_info('平安银行')
found 4 matches, matched codes are {'E': {'000001.SZ': '平安银行', '600928.SH': '西安银行'}, 'IDX': {'802613.SI': '平安银行养老新兴投资指数'}, 'count': 3}
More information for asset type E:
------------------------------------------
ts_code       000001.SZ   600928.SH
name               平安银行        西安银行
area                 深圳          陕西
industry             银行          银行
fullname     平安银行股份有限公司  西安银行股份有限公司
list_status           L           L
list_date    1991-04-03  2019-03-01
-------------------------------------------
More information for asset type IDX:
------------------------------------------
ts_code       802613.SI
name       平安银行养老新兴投资指数
fullname   平安银行养老新兴投资指数
publisher          申万研究
category           价值指数
list_date    2017-01-03
-------------------------------------------

# 有时候精确匹配证券名称无法找到结果
qt.get_basic_info('贵州钢绳')
No match found! To get better result, you can
- pass "match_full_name=True" to match full names of stocks and funds

# 此时可以指定搜索全名，从而找到相关的证券
qt.get_basic_info('贵州钢绳', match_full_name=True)
found 1 matches, matched codes are {'E': {'600992.SH': '贵绳股份'}, 'count': 1}
More information for asset type E:
------------------------------------------
ts_code       600992.SH
name               贵绳股份
area                 贵州
industry            钢加工
fullname     贵州钢绳股份有限公司
list_status           L
list_date    2004-05-14
-------------------------------------------
```

![在这里插入图片描述](img/get_stock_info.png)

在上面的例子中，系统只找到了类型为股票和指数的证券，如果还需要查找基金、期货等更多的证券信息，用同样的方法下载更多的基础数据表即可：

- **fund_basic**: 基金基础数据
- **future_basic**: 期货基础数据

除了查找股票或证券的基本信息以外，我们还能用qt.filter_stock()函数来筛选股票：
```python
qt.filter_stocks(date='20240212', industry='银行', area='上海')
[Out]:
           name area industry market  list_date exchange
qt_code                                                 
600000.SH  浦发银行   上海       银行     主板 1999-11-10      SSE
601229.SH  上海银行   上海       银行     主板 2016-11-16      SSE
601328.SH  交通银行   上海       银行     主板 2007-05-15      SSE
601825.SH  沪农商行   上海       银行     主板 2021-08-19      SSE
```
### 下载沪市股票数据

金融数据中最重要的数据类型非量价数据莫属。接下来，我们就来下载历史价格数据。

qteasy的历史数据全都是以K线数据的形式存储在数据表中的，目前支持的K线数据包括：

- 分钟K线 - 1分钟/5分钟/15分钟/30分钟/60分钟K线
- 日K线
- 周K线
- 月K线

我们同样使用qt.refill_data_source()函数下载股票数据。最常用的股票日K线数据保存在stock_daily表中。不过由于数据量较大，我们最好在下载数据时限定数据的范围，通过start_date/end_date参数，指定下载数据的起始日期，分批下载历史数据，否则，下载的过程将会非常漫长：

```python
qt.refill_data_source(tables='stock_daily', start_date='20230101', end_date='20231231')
[Out]:
Filling data source file://csv@qt_root/data/ ...
[########################################]247/247-100.0%  <stock_daily:20230104-20231229>97486200wrtn in ~49"
```
上面的代码下载了2023年全年所有已上市股票的日K线数据，同样，下面的代码可以用来下载常用指数（上证指数和沪深300指数）的日K线数据：

```python
qt.refill_data_source(tables='index_daily', symbols='000001, 000300', start_date='20231231', end_date='20240208')
[Out]:
Filling data source file://csv@qt_root/data/ ...
[########################################]7/7-100.0%  <index_basic:SSE-OTH>10365wrtn in ~1't
[########################################]2/2-100.0%  <index_daily:000001.SH-000300.SH>97050wrtn in ~2"
```
### 从本地获取股价数据
当股价数据保存在本地之后，就可以随时提取出来使用了。

我们可以使用`qt.get_history_data()`函数来获取股票的量价数据。这个函数时`qteasy`的一个通用接口，可以用来获取各种类型的数据。在函数的参数中指定数据的类型（通过数据类型ID）、股票的代码以及其他参数，就可以获取相应的数据了。如果要获取刚刚下载的K线价格，需要设置数据类型为`"open, high, low, close, vol"`以获取开盘价、最高价、最低价、收盘价和交易量：

```python
qt.get_history_data(htypes='open, high, low, close, vol', shares='000001.SZ', start='20230101', end='20230201')
[Out]:
{'000001.SZ':
              open   high    low  close         vol
 2023-01-04  13.71  14.42  13.63  14.32  2189682.53
 2023-01-05  14.40  14.74  14.37  14.48  1665425.18
 2023-01-06  14.50  14.72  14.48  14.62  1195744.71
 2023-01-09  14.75  14.88  14.52  14.80  1057659.11
 2023-01-10  14.76  14.89  14.39  14.44  1269423.39
 2023-01-11  14.45  14.78  14.39  14.67   830566.12
 2023-01-12  14.77  14.77  14.53  14.67   625694.84
 2023-01-13  14.67  14.95  14.55  14.95   949085.83
 2023-01-16  14.95  15.28  14.85  15.08  1560039.89
 2023-01-17  15.13  15.18  14.77  14.97   935834.54
 2023-01-18  14.95  15.18  14.91  15.11   718434.03
 2023-01-19  15.13  15.25  14.87  15.09   641875.20
 2023-01-20  15.16  15.24  15.00  15.13   608590.08
 2023-01-30  15.60  15.74  14.89  15.15  1374317.50
 2023-01-31  15.24  15.51  14.96  14.99  1030497.84
 2023-02-01  15.03  15.08  14.51  14.70  1653421.48}
```

上面函数的输出是一个字典，字典的键为shares参数指定的所有股票的代码，而值为一个DataFrame，包含该股票在指定期间的历史数据，这里我们指定了数据类型为K线量价数据。当然，我们也可以指定其他的数据类型，只要这些数据已经下载到了本地，就可以直接读取。

例如，指定数据类型htypes='pe, pb, total_mv'可以获取股票的市盈率、市净率和总市值等三项财务指标。如果某些指标存在缺失值的时候，可以定义填充方式填充缺失值，还可以对数据进行重新采样，将每日的数据变为每周或每小时数据。

关于get_history_data函数参数的详细解释，请参见[qteasy文档](https://qteasy.readthedocs.io)

### 生成K线图
使用量价数据，更加方便易读的方法是将数据显示为K线图。

qteasy提供了qt.candle()函数，用于显示专业K线图，只要数据下载到本地后，就可以立即显示K线图：

```python
qt.candle('600004.SH', start='20230101', end='20230301')
```
![在这里插入图片描述](img/candle-600004.png)

下载复权因子数据到本地后，就可以显示复权价格了：

```python
qt.refill_data_source(tables='adj', start_date='20230101', end_date='20230601')
[Out]:
Filling data source file://csv@qt_root/data/ ...
[########################################]99/99-100.0%  <stock_adj_factor:20230103-20230601>508575wrtn in ~56"
[########################################]99/99-100.0%  <fund_adj_factor:20230103-20230601>121647wrtn in ~4"
qt.candle('600004.SH', start='20230101', end='20230301', adj='b')
```

![在这里插入图片描述](img/candle-600004-b.png)


`qt.candle()`函数支持传入K线图的开始日期、结束日期、K线频率、复权方式以显示不同区间和频率的K线图，也支持传入移动均线的时长和macd的不同参数显示不同的均线，`qt.candle()`函数还支持通过股票名称显示K线图，如果输入是股票名称，会自动模糊查找，并且支持通配符。

下面是更多的K线图例子，展示了股票、基金、指数等不同的资产类别，不同的数据频率，不同的均线设定、不同的图表类型等，为了显示下面示例中的K线图，您需要下载相应的数据。
```python
import qteasy as qt
df = qt.candle('159601', start='20210420', freq='d')
df = qt.candle('000001.SH', start = '20211221', asset_type='IDX', plot_type='c')
df = qt.candle('000300.SH', start = '20220331', asset_type='IDX', mav=[], plot_type='c')
df = qt.candle('000300.SH', start = '20221021', asset_type='IDX', mav=[], plot_type='c', 
               freq='30min')
df = qt.candle('601728', freq='30min', adj='b', plot_type='c')
df = qt.candle('沪镍主力', start = '20211130', mav=[5, 12, 36])
df = qt.candle('510300', start='20200101', asset_type='FD', adj='b', mav=[])
df = qt.candle('格力电器', start='20220101', asset_type='E', adj='f', mav=[5, 10, 20, 30])
df = qt.candle('513100', asset_type='FD', adj='f', mav=[])
df = qt.candle('110025', asset_type='FD', adj='f', mav=[9, 28])
df = qt.candle('001104', asset_type='FD', adj='f', mav=[12, 26])
```

![png](img/output_18_1.png)
    

![png](img/output_18_2.png)
    

![png](img/output_18_3_copy.png)
    

![png](img/output_18_4.png)
    

![png](img/output_18_5.png)


![png](img/output_18_6.png)
    

![png](img/output_18_7.png)
    

![png](img/output_18_8.png)
    

![png](img/output_18_9.png)
    

![png](img/output_18_10.png)
    

![png](img/output_18_11.png)
    
## 数据类型的查找
前面提到过，`qteasy`中的所有数据类型均有一个唯一的ID，通过这个ID，可以提取数据，在交易策略中引用该数据类型，完成`qteasy`中所需的工作。

为了更加了解`qteasy`中的数据类型，我们可以用`qt.find_history_data()`函数来查询所需的数据类型。`qteasy`中定义的数据类型是与数据频率、资产类型挂钩的，也就是说，不同资产的收盘价是不同的数据类型，不同频率的收盘价也是不同的。

`qt.find_history_data()`函数可以根据输入查找相关的数据类型，并且显示它们的ID，数据表、说明等相关信息，例如，搜索`‘close’`（收盘价）可以找到所有相关的数据类型：

```python
qt.find_history_data('close')
[Out]:
matched following history data, 
use "qt.get_history_data()" to load these historical data by its data_id:
------------------------------------------------------------------------
          freq asset           table            desc
data_id                                             
close        d     E     stock_daily     股票日K线 - 收盘价
close        w     E    stock_weekly     股票周K线 - 收盘价
close        m     E   stock_monthly     股票月K线 - 收盘价
close     1min     E      stock_1min   股票60秒K线 - 收盘价
close     5min     E      stock_5min   股票5分钟K线 - 收盘价
close    15min     E     stock_15min  股票15分钟K线 - 收盘价
close    30min     E     stock_30min  股票30分钟K线 - 收盘价
close        h     E    stock_hourly    股票小时K线 - 收盘价
close        d   IDX     index_daily     指数日K线 - 收盘价
close        w   IDX    index_weekly     指数周K线 - 收盘价
close        m   IDX   index_monthly     指数月K线 - 收盘价
close     1min   IDX      index_1min   指数60秒K线 - 收盘价
close     5min   IDX      index_5min   指数5分钟K线 - 收盘价
close    15min   IDX     index_15min  指数15分钟K线 - 收盘价
close    30min   IDX     index_30min  指数30分钟K线 - 收盘价
close        h   IDX    index_hourly    指数小时K线 - 收盘价
close        d    FT    future_daily     期货日K线 - 收盘价
close     1min    FT     future_1min   期货60秒K线 - 收盘价
close     5min    FT     future_5min   期货5分钟K线 - 收盘价
close    15min    FT    future_15min  期货15分钟K线 - 收盘价
close    30min    FT    future_30min  期货30分钟K线 - 收盘价
close        h    FT   future_hourly    期货小时K线 - 收盘价
close        d   OPT   options_daily     期权日K线 - 收盘价
close     1min   OPT    options_1min   期权60秒K线 - 收盘价
close     5min   OPT    options_5min   期权5分钟K线 - 收盘价
close    15min   OPT   options_15min  期权15分钟K线 - 收盘价
close    30min   OPT   options_30min  期权30分钟K线 - 收盘价
close        h   OPT  options_hourly    期权小时K线 - 收盘价
close        d    FD      fund_daily     基金日K线 - 收盘价
close     1min    FD       fund_1min   基金60秒K线 - 收盘价
close     5min    FD       fund_5min   基金5分钟K线 - 收盘价
close    15min    FD      fund_15min  基金15分钟K线 - 收盘价
close    30min    FD      fund_30min  基金30分钟K线 - 收盘价
close        h    FD     fund_hourly    基金小时K线 - 收盘价
close        d   Any        top_list  融资融券交易明细 - 收盘价
========================================================================
```
再例如，搜索市盈率pe，可以得到：

```python
qt.find_history_data('pe')
[Out]:
matched following history data, 
use "qt.get_history_data()" to load these historical data by its data_id:
------------------------------------------------------------------------
           freq asset             table                            desc
data_id                                                                
initial_pe    d     E         new_share                  新股上市信息 - 发行市盈率
pe            d   IDX   index_indicator                    指数技术指标 - 市盈率
pe            d     E   stock_indicator  股票技术指标 - 市盈率（总市值/净利润， 亏损的PE为空）
pe_2          d     E  stock_indicator2                  股票技术指标 - 动态市盈率
========================================================================
```
查找到相应的数据之后，只需要查看该数据所属的数据表，将该数据表下载到本地数据源中(`refill_data_source(tables, ...)`)，即可使用这些数据(`qt.get_history_data(htype, shares, ...)`)了。

## 回顾总结

至此，我们已经初步了解了`qteasy`中对数据的管理方式，了解了数据下载的方法。下载了基本数据以及一些量价数据。我们学会了如何提取数据、如何显示K线图。最后，我们还学会了查询数据的方法，如果需要某种数据，知道如何查询，如何下载和调用这些数据。

在下一篇教程中，我们将进一步加深对qteasy的了解，我们将学会如何创建交易策略，如何运行并回测交易策略。

关于qteasy的更多介绍，请参见[qteasy文档](https://qteasy.readthedocs.io)