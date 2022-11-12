# QTEASY基本使用教程——02，金融数据下载及管理

本示例展示了如何使用qteasy模块下载、管理及提取本地存储的金融数据
QTEASY提供了一套比较完善的金融数据下载及管理工具，可以通过tushare服务器下载相当广泛的金融数据，将数据存储在本地，并在需要的时候自动从本地提取数据用于策略的回测或策略运行。

## 本地数据源对象`DataSource`

在`qteasy`中定义了一个`DataSource`对象，这个对象定义了一个本地金融数据源，并提供了一系列内置的本地金融数据表和数据类型，用户可以直接通过各种数据类型的ID来直接读取相应的金融数据（前提是这些金融数据已经从网上下载并保存到了本地数据源中）。

大量常用的金融数据，例如'close' 'pe'都是预先定义并内置在`qteasy`中的，这些数据涵盖了相当广泛的范围，包括：

- 量价数据，如开盘价open、收盘价close、最高价high，交易量vol等等
- 财务指标数据，如市盈率pe，市净率pb
- 财务报表数据，如ebidta、ebit等等
- 公司基本信息数据，如管理层姓名、公司行业信息

上面的数据都是以“数据表”的形式内置并定义在系统中的，如果需要使用这些数据，必须首先下载数据至本地。`DataSource`对象定义了数据存储的方式和位置。`qteasy`定义了一个默认的数据源对象`QT_DATA_SOURCE`，在不特殊指明的情况下，`qteasy`所操作及使用的数据都在这个数据源中。

`DataSource`对象可以将数据保存为文件格式（csv、fth等），也可以将数据保存在mysql数据库中，鉴于金融数据的体量，建议将数据保存在数据库中。数据存储方式及存储位置可以在`qteasy`的`configuration`中设置。


```python
import qteasy as qt
```


使用`qt.configuration`可以查看当前的配置变量，使用`qt.QT_DATA_SOURCE`可以查看当前数据源的类型和参数


```python
qt.configuration(config='local_data_source, local_data_file_type, local_data_file_path', default=False)
qt.QT_DATA_SOURCE
```

    No. Config-Key            Cur Val        
    -----------------------------------------
    1   local_data_source     database
    2   local_data_file_type  csv
    3   local_data_file_path  qteasy/data/




    DataSource('db', 'localhost', 3306)



## 检查本地数据源的数据
使用qt.get_table_overview()可以查看当前数据源中已经下载的数据量
当数据量较大时，需要花费几分钟时间分析所有的数据，并打印本地数据源中数据表的数据量、占用磁盘空间以及数据范围

本地数据存储在若干张数据表中，也可以通过qt.get_table_info()来获取某一张数据表的详细信息
包括数据表的主键类型和取值范围以外，还包括各数据列的名称、含义和数据类型

### `qt.get_table_info(table_name, data_source=None, verbose=True)`

获取一张数据表的信息，包括数据量（数据行数），占用磁盘空间大小、数据主键的名称及数据范围
如果设置`verbose=True`，还可以查看数据表中的数据列完整信息，包括列名、数据类型和说明

### `qt.get_table_overview(data_source=None)`

统计数据源中所有数据表的数据量并打印总览


```python
qt.get_table_overview()
```

    Analyzing local data source tables... depending on size of tables, it may take a few minutes
    [########################################]62/62-100.0%  Analyzing completed!or>>>>>ht>or>>
    db:mysql://localhost@3306/ts_db
    Following tables contain local data, to view complete list, print returned DataFrame
                     Has_data Size_on_disk Record_count Record_start  Record_end
    table                                                                       
    trade_calendar     True        2.5MB         76K     1990-10-12   2022-12-31
    stock_basic        True        1.5MB          5K           None         None
    stock_names        True        2.4MB         13K     1990-12-10   2022-03-21
    index_basic        True        4.5MB         11K           None         None
    fund_basic         True        8.3MB         17K           None         None
    future_basic       True        2.5MB          7K           None         None
    opt_basic          True        4.5MB         10K           None         None
    stock_15min        True      15.85GB      100.9M       20090105     20220323
    stock_30min        True       6.66GB       38.9M       20090105     20220321
    stock_hourly       True       3.41GB       38.3M       20090105     20220318
    stock_daily        True       1.57GB       12.1M     1990-12-19   2022-03-22
    stock_weekly       True      217.9MB        2.4M     1990-12-21   2022-03-18
    stock_monthly      True       87.7MB        638K     1990-12-31   2022-02-28
    index_15min        True       2.07GB       17.6M       20090105     20220323
    index_30min        True       1.12GB        7.6M       20090105     20220318
    index_hourly       True      602.0MB        7.1M       20090105     20220113
    index_daily        True      357.0MB        2.2M     1990-12-19   2022-03-23
    index_weekly       True       56.6MB        611K     1991-07-05   2022-03-18
    index_monthly      True       22.5MB        139K     1991-07-31   2022-02-28
    fund_hourly        True         16KB           0           None         None
    fund_daily         True      165.3MB        1.6M     1998-04-07   2022-03-22
    fund_nav           True      973.0MB       15.0M     2000-01-07   2022-03-22
    fund_share         True       69.7MB        1.1M     1998-03-27   2022-03-18
    fund_manager       True       84.7MB         40K     2000-02-22   2022-03-18
    future_daily       True      384.0MB        2.0M     1995-04-17   2022-03-23
    options_daily      True      753.0MB        5.3M     2015-02-09   2022-03-23
    stock_adj_factor   True      688.0MB       11.0M     1990-12-19   2022-03-23
    fund_adj_factor    True      112.7MB        1.9M     1998-04-07   2022-03-23
    stock_indicator    True       2.31GB       11.6M     1999-01-01   2022-03-23
    stock_indicator2   True      988.0MB        4.8M     2017-06-14   2022-03-23
    index_indicator    True        5.5MB         45K     2004-01-02   2022-03-23
    index_weight       True      841.9MB       10.5M     2005-04-08   2022-03-17
    income             True       94.8MB        189K     1990-12-31   2021-12-31
    balance            True      130.0MB        172K     1989-12-31   2021-12-31
    cashflow           True      111.9MB        186K     1998-12-31   2021-12-31
    financial          True      373.0MB        152K     1989-12-31   2021-12-31
    forecast           True       50.6MB         86K     1998-12-31   2022-12-31
    express            True        4.5MB         23K     2004-12-31   2021-12-31





<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>has_data</th>
      <th>size</th>
      <th>records</th>
      <th>pk1</th>
      <th>records1</th>
      <th>min1</th>
      <th>max1</th>
      <th>pk2</th>
      <th>records2</th>
      <th>min2</th>
      <th>max2</th>
    </tr>
    <tr>
      <th>table</th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>trade_calendar</td>
      <td>True</td>
      <td>2.5MB</td>
      <td>76K</td>
      <td>exchange</td>
      <td>unknown</td>
      <td>CFFEX</td>
      <td>XHKG</td>
      <td>cal_date</td>
      <td>unknown</td>
      <td>1990-10-12</td>
      <td>2022-12-31</td>
    </tr>
    <tr>
      <td>stock_basic</td>
      <td>True</td>
      <td>1.5MB</td>
      <td>5K</td>
      <td>ts_code</td>
      <td>unknown</td>
      <td>000001.SZ</td>
      <td>872925.BJ</td>
      <td>None</td>
      <td>None</td>
      <td>None</td>
      <td>None</td>
    </tr>
    <tr>
      <td>stock_names</td>
      <td>True</td>
      <td>2.4MB</td>
      <td>13K</td>
      <td>ts_code</td>
      <td>unknown</td>
      <td>000001.SZ</td>
      <td>T00018.SH</td>
      <td>start_date</td>
      <td>unknown</td>
      <td>1990-12-10</td>
      <td>2022-03-21</td>
    </tr>
    <tr>
      <td>stock_company</td>
      <td>False</td>
      <td>0</td>
      <td>0</td>
      <td>ts_code</td>
      <td>unknown</td>
      <td>N/A</td>
      <td>N/A</td>
      <td>None</td>
      <td>None</td>
      <td>None</td>
      <td>None</td>
    </tr>
    <tr>
      <td>stk_managers</td>
      <td>False</td>
      <td>0</td>
      <td>0</td>
      <td>ts_code</td>
      <td>unknown</td>
      <td>N/A</td>
      <td>N/A</td>
      <td>ann_date</td>
      <td>unknown</td>
      <td>N/A</td>
      <td>N/A</td>
    </tr>
    <tr>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
    </tr>
    <tr>
      <td>forecast</td>
      <td>True</td>
      <td>50.6MB</td>
      <td>86K</td>
      <td>ts_code</td>
      <td>unknown</td>
      <td>000001.SZ</td>
      <td>871981.BJ</td>
      <td>end_date</td>
      <td>unknown</td>
      <td>1998-12-31</td>
      <td>2022-12-31</td>
    </tr>
    <tr>
      <td>express</td>
      <td>True</td>
      <td>4.5MB</td>
      <td>23K</td>
      <td>ts_code</td>
      <td>unknown</td>
      <td>000001.SZ</td>
      <td>872925.BJ</td>
      <td>end_date</td>
      <td>unknown</td>
      <td>2004-12-31</td>
      <td>2021-12-31</td>
    </tr>
    <tr>
      <td>shibor</td>
      <td>False</td>
      <td>0</td>
      <td>0</td>
      <td>date</td>
      <td>unknown</td>
      <td>N/A</td>
      <td>N/A</td>
      <td>None</td>
      <td>None</td>
      <td>None</td>
      <td>None</td>
    </tr>
    <tr>
      <td>libor</td>
      <td>False</td>
      <td>0</td>
      <td>0</td>
      <td>date</td>
      <td>unknown</td>
      <td>N/A</td>
      <td>N/A</td>
      <td>curr_type</td>
      <td>unknown</td>
      <td>N/A</td>
      <td>N/A</td>
    </tr>
    <tr>
      <td>hibor</td>
      <td>False</td>
      <td>0</td>
      <td>0</td>
      <td>date</td>
      <td>unknown</td>
      <td>N/A</td>
      <td>N/A</td>
      <td>None</td>
      <td>None</td>
      <td>None</td>
      <td>None</td>
    </tr>
  </tbody>
</table>
<p>62 rows × 11 columns</p>





```python
qt.get_table_info('stock_15min', verbose=True)
```

    <stock_15min>, 15.85GB/100.9M records on disc
    primary keys: 
    -----------------------------------
    1:  ts_code:       *<CRITICAL>*
        <unknown> entries
        starts: 000001.SZ, end: 689009.SH
    2:  trade_time:
        <unknown> entries
        starts: 20090105, end: 20220323
    
    columns of table:
    ------------------------------------
          columns       dtypes remarks
    0     ts_code  varchar(20)    证券代码
    1  trade_time     datetime  交易日期时间
    2        open        float     开盘价
    3        high        float     最高价
    4         low        float     最低价
    5       close        float     收盘价
    6         vol       double  成交量(股)
    7      amount       double  成交额(元)





## 连接tushare下载数据并保存到本地数据源

qteasy提供了tushare数据接口，在获取相应tushare权限后，可以直接从tushare批量下载金融数据，并将数据更新到本地数据源中
例如，下面的命令将2022年3月起到9月之间的所有股票日K线数据下载到本地：
在下载数据前检察stock_daily表的信息：

### `qt.refill_data_source(data_source, *args, **kwargs)`

连接到tushare下载所需的数据并保存到相应的数据表，给出需要下载的数据表名称，通过start_date和end_date限定数据的范围，同时可以通过freq、asset_type等指定不同的数据类型，即可下载表格数据并保存到合适的位置。
重复的数据会被忽略或覆盖已有的数据


```python
qt.get_table_info('stock_daily', verbose=False)
```

    <stock_daily>, 1.57GB/12.8M records on disc
    primary keys: 
    -----------------------------------
    1:  ts_code:
        <unknown> entries
        starts: 000001.SZ, end: 873527.BJ
    2:  trade_date:       *<CRITICAL>*
        <unknown> entries
        starts: 1990-12-19, end: 2022-10-31




```python
qt.refill_data_source(tables='stock_daily', 
                      start_date='20220301',
                      end_date='20221031')
```

    [########################################]8/8-100.0%  <trade_calendar:SSE-INE>65417wrtn in 2'24"448
    [########################################]163/163-100.0%  <stock_daily:20220301-20221031>786300wrtn in 2'42"199

```python
qt.get_table_info('stock_daily', verbose=False)
```

    <stock_daily>, 1.57GB/12.8M records on disc
    primary keys: 
    -----------------------------------
    1:  ts_code:
        <unknown> entries
        starts: 000001.SZ, end: 873527.BJ
    2:  trade_date:       *<CRITICAL>*
        <unknown> entries
        starts: 1990-12-19, end: 2022-10-31



## 本地数据的获取和可视化

只要本地数据源中有了数据，就可以非常容易地获取这些数据，如果是量价数据，还可以非常容易地可视化（打印为K线图或价格曲线图）

### 股票或资产的基本信息数据

### `qt.get_basic_info(code_or_name: str, asset_types=None, match_full_name=False, printout=True, verbose=False)`

获取一个股票或证券的基本信息，code_or_name可以是股票的代码，或者股票名称，默认情况下系统会进行全剧匹配查找匹配的证券，如‘000001’会匹配到多种不同的证券，所有匹配的证券都会被列出，除非在asset_type中指定一种或几种证券类型。
如果设置match_full_name=True，则会通过股票或基金的全名来模糊匹配证券


### `qt.get_stock_info(code_or_name: str, asset_types=None, match_full_name=False, printout=True, verbose=False)`

get_basic_info()的别称

### 筛选股票代码

### `qt.filter_stocks(date: str = 'today', **kwargs)`

根据发行日期、地区、行业、规模、指数成份等多种可用的信息筛选出一部分股票，打印出股票的信息

### `qt.filter_stock_codes(date: str = 'today', **kwargs)`

根据发行日期、地区、行业、规模、指数成份等多种可用的信息筛选出一部分股票，返回股票的完整代码

### `qt.get_history_data(htypes, shares=None, start=None, end=None, freq=None, asset_type=None, adj=None, as_data_frame=True, group_by=None, **kwargs)`

这个函数从默认QT_DATA_SOURCE中提取数据，根据输入的数据类型、股票代码、日期范围以及频率等参数，输出多个DataFrame或HistoryPanel对象
这些DataFrame保存在一个dict中，这个dict的键为股票代码或数据类型，值为按股票代码或数据类型分组的数据框

### `qt.candle(stock=None, start=None, end=None, stock_data=None, asset_type=None, freq=None, plot_type='candle', interactive=True, data_source=None, **kwargs）`

这个函数从本地数据源中提取股票的价格数据，并生成一张完整的动态高级K线图


```python
print('information of multiple types of assets with code 000001')
qt.get_stock_info('000300')

print(f'information of "贵州茅台"')
qt.get_basic_info('贵州茅台')
```

    information of multiple types of assets with code 000001
    found 2 matches, matched codes are {'IDX': {'000300.SH': '沪深300'}, 'FD': {'000300.OF': '德邦德利货币A'}, 'count': 2}
    More information for asset type IDX:
    ------------------------------------------
    ts_code     000300.SH
    name            沪深300
    fullname      沪深300指数
    publisher        中证公司
    category         规模指数
    list_date  2005-04-08
    -------------------------------------------
    More information for asset type FD:
    ------------------------------------------
    ts_code        000300.OF
    name             德邦德利货币A
    management          德邦基金
    custodian         中国民生银行
    fund_type          货币市场型
    issue_date    2013-09-02
    issue_amount     14.2247
    invest_type          货币型
    type              契约型开放式
    -------------------------------------------
    information of "贵州茅台"
    found 1 matches, matched codes are {'E': {'600519.SH': '贵州茅台'}, 'count': 1}
    More information for asset type E:
    ------------------------------------------
    ts_code        600519.SH
    name                贵州茅台
    area                  贵州
    industry              白酒
    fullname     贵州茅台酒股份有限公司
    list_status            L
    list_date     2001-08-27
    -------------------------------------------



```python
# 筛选2000年以后发行的HS300指数成份股
qt.filter_stocks(date = '20000101', index='000300.SH')

```



<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>symbol</th>
      <th>name</th>
      <th>area</th>
      <th>industry</th>
      <th>market</th>
      <th>list_date</th>
      <th>exchange</th>
    </tr>
    <tr>
      <th>ts_code</th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>000001.SZ</td>
      <td>000001</td>
      <td>平安银行</td>
      <td>深圳</td>
      <td>银行</td>
      <td>主板</td>
      <td>1991-04-03</td>
      <td>SZSE</td>
    </tr>
    <tr>
      <td>000002.SZ</td>
      <td>000002</td>
      <td>万科A</td>
      <td>深圳</td>
      <td>全国地产</td>
      <td>主板</td>
      <td>1991-01-29</td>
      <td>SZSE</td>
    </tr>
    <tr>
      <td>000063.SZ</td>
      <td>000063</td>
      <td>中兴通讯</td>
      <td>深圳</td>
      <td>通信设备</td>
      <td>主板</td>
      <td>1997-11-18</td>
      <td>SZSE</td>
    </tr>
    <tr>
      <td>000069.SZ</td>
      <td>000069</td>
      <td>华侨城A</td>
      <td>深圳</td>
      <td>旅游景点</td>
      <td>主板</td>
      <td>1997-09-10</td>
      <td>SZSE</td>
    </tr>
    <tr>
      <td>000100.SZ</td>
      <td>000100</td>
      <td>TCL科技</td>
      <td>广东</td>
      <td>元器件</td>
      <td>主板</td>
      <td>2004-01-30</td>
      <td>SZSE</td>
    </tr>
    <tr>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
    </tr>
    <tr>
      <td>603486.SH</td>
      <td>603486</td>
      <td>科沃斯</td>
      <td>江苏</td>
      <td>家用电器</td>
      <td>主板</td>
      <td>2018-05-28</td>
      <td>SSE</td>
    </tr>
    <tr>
      <td>605499.SH</td>
      <td>605499</td>
      <td>东鹏饮料</td>
      <td>深圳</td>
      <td>软饮料</td>
      <td>主板</td>
      <td>2021-05-27</td>
      <td>SSE</td>
    </tr>
    <tr>
      <td>688561.SH</td>
      <td>688561</td>
      <td>奇安信-U</td>
      <td>北京</td>
      <td>软件服务</td>
      <td>科创板</td>
      <td>2020-07-22</td>
      <td>SSE</td>
    </tr>
    <tr>
      <td>688599.SH</td>
      <td>688599</td>
      <td>天合光能</td>
      <td>江苏</td>
      <td>电气设备</td>
      <td>科创板</td>
      <td>2020-06-10</td>
      <td>SSE</td>
    </tr>
    <tr>
      <td>688981.SH</td>
      <td>688981</td>
      <td>中芯国际</td>
      <td>上海</td>
      <td>半导体</td>
      <td>科创板</td>
      <td>2020-07-16</td>
      <td>SSE</td>
    </tr>
  </tbody>
</table>
<p>397 rows × 7 columns</p>
</div>




```python
# 筛选行业为“航空或全国地产,且区域为‘上海、北京及山东“的股票
qt.filter_stocks(industry='航空, 全国地产', area='上海,北京,山东')
```



<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>name</th>
      <th>area</th>
      <th>industry</th>
      <th>market</th>
      <th>list_date</th>
      <th>exchange</th>
    </tr>
    <tr>
      <th>ts_code</th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>000402.SZ</td>
      <td>金融街</td>
      <td>北京</td>
      <td>全国地产</td>
      <td>主板</td>
      <td>1996-06-26</td>
      <td>SZSE</td>
    </tr>
    <tr>
      <td>000620.SZ</td>
      <td>新华联</td>
      <td>北京</td>
      <td>全国地产</td>
      <td>主板</td>
      <td>1996-10-29</td>
      <td>SZSE</td>
    </tr>
    <tr>
      <td>002111.SZ</td>
      <td>威海广泰</td>
      <td>山东</td>
      <td>航空</td>
      <td>中小板</td>
      <td>2007-01-26</td>
      <td>SZSE</td>
    </tr>
    <tr>
      <td>002829.SZ</td>
      <td>星网宇达</td>
      <td>北京</td>
      <td>航空</td>
      <td>中小板</td>
      <td>2016-12-13</td>
      <td>SZSE</td>
    </tr>
    <tr>
      <td>002933.SZ</td>
      <td>新兴装备</td>
      <td>北京</td>
      <td>航空</td>
      <td>中小板</td>
      <td>2018-08-28</td>
      <td>SZSE</td>
    </tr>
    <tr>
      <td>002985.SZ</td>
      <td>北摩高科</td>
      <td>北京</td>
      <td>航空</td>
      <td>中小板</td>
      <td>2020-04-29</td>
      <td>SZSE</td>
    </tr>
    <tr>
      <td>300034.SZ</td>
      <td>钢研高纳</td>
      <td>北京</td>
      <td>航空</td>
      <td>创业板</td>
      <td>2009-12-25</td>
      <td>SZSE</td>
    </tr>
    <tr>
      <td>300719.SZ</td>
      <td>安达维尔</td>
      <td>北京</td>
      <td>航空</td>
      <td>创业板</td>
      <td>2017-11-09</td>
      <td>SZSE</td>
    </tr>
    <tr>
      <td>300965.SZ</td>
      <td>恒宇信通</td>
      <td>北京</td>
      <td>航空</td>
      <td>创业板</td>
      <td>2021-04-02</td>
      <td>SZSE</td>
    </tr>
    <tr>
      <td>600118.SH</td>
      <td>中国卫星</td>
      <td>北京</td>
      <td>航空</td>
      <td>主板</td>
      <td>1997-09-08</td>
      <td>SSE</td>
    </tr>
    <tr>
      <td>600372.SH</td>
      <td>中航电子</td>
      <td>北京</td>
      <td>航空</td>
      <td>主板</td>
      <td>2001-07-06</td>
      <td>SSE</td>
    </tr>
    <tr>
      <td>600657.SH</td>
      <td>信达地产</td>
      <td>北京</td>
      <td>全国地产</td>
      <td>主板</td>
      <td>1993-05-24</td>
      <td>SSE</td>
    </tr>
    <tr>
      <td>600708.SH</td>
      <td>光明地产</td>
      <td>上海</td>
      <td>全国地产</td>
      <td>主板</td>
      <td>1996-06-06</td>
      <td>SSE</td>
    </tr>
    <tr>
      <td>600748.SH</td>
      <td>上实发展</td>
      <td>上海</td>
      <td>全国地产</td>
      <td>主板</td>
      <td>1996-09-25</td>
      <td>SSE</td>
    </tr>
    <tr>
      <td>600760.SH</td>
      <td>中航沈飞</td>
      <td>山东</td>
      <td>航空</td>
      <td>主板</td>
      <td>1996-10-11</td>
      <td>SSE</td>
    </tr>
    <tr>
      <td>600791.SH</td>
      <td>京能置业</td>
      <td>北京</td>
      <td>全国地产</td>
      <td>主板</td>
      <td>1997-01-30</td>
      <td>SSE</td>
    </tr>
    <tr>
      <td>600823.SH</td>
      <td>世茂股份</td>
      <td>上海</td>
      <td>全国地产</td>
      <td>主板</td>
      <td>1994-02-04</td>
      <td>SSE</td>
    </tr>
  </tbody>
</table>
</div>




```python
# 获取历史数据：股票00001.SH的日K线数据
qt.get_history_data(shares='000001.SH', htypes='open,high,low,close,vol', freq='d', start='20200101', end='20201231')
```




    {'000001.SH':                open     high      low    close          vol
     2020-01-02  3066.34  3098.10  3066.34  3085.20  292470208.0
     2020-01-03  3089.02  3093.82  3074.52  3083.79  261496667.0
     2020-01-06  3070.91  3107.20  3065.31  3083.41  312575842.0
     2020-01-07  3085.49  3105.45  3084.33  3104.80  276583111.0
     2020-01-08  3094.24  3094.24  3059.13  3066.89  297872553.0
     ...             ...      ...      ...      ...          ...
     2020-12-25  3351.79  3397.01  3348.35  3396.56  294546895.0
     2020-12-28  3396.36  3412.52  3383.65  3397.29  316181542.0
     2020-12-29  3399.29  3407.09  3376.09  3379.04  311769185.0
     2020-12-30  3375.01  3414.45  3374.42  3414.45  291023543.0
     2020-12-31  3419.73  3474.92  3419.73  3473.07  335673926.0
     
     [261 rows x 5 columns]}




```python
# 获取历史数据：股票00001.SH, 000002.SH的多种价格和财务指标数据，且将数据整理为‘周'频率
qt.get_history_data(shares='000001.SH, 000002.SH, 000003.SH',
                    htypes='pe, ebitda, pb, eps, total_income',
                    freq='w',
                    start='20200101',
                    end='20201231')
```




    {'000001.SH':                pe  ebitda    pb  eps  total_income
     2020-01-03  14.22     NaN  1.42  NaN           NaN
     2020-01-10  14.23     NaN  1.42  NaN           NaN
     2020-01-17  14.14     NaN  1.41  NaN           NaN
     2020-01-24  13.70     NaN  1.36  NaN           NaN
     2020-01-31  13.70     NaN  1.36  NaN           NaN
     2020-02-07  13.29     NaN  1.32  NaN           NaN
     2020-02-14  13.48     NaN  1.34  NaN           NaN
     2020-02-21  13.85     NaN  1.39  NaN           NaN
     2020-02-28  13.14     NaN  1.32  NaN           NaN
     2020-03-06  13.82     NaN  1.39  NaN           NaN
     2020-03-13  13.16     NaN  1.32  NaN           NaN
     2020-03-20  12.51     NaN  1.26  NaN           NaN
     2020-03-27  12.23     NaN  1.27  NaN           NaN
     2020-04-03  11.83     NaN  1.25  NaN           NaN
     2020-04-10  11.96     NaN  1.27  NaN           NaN
     2020-04-17  12.08     NaN  1.29  NaN           NaN
     2020-04-24  11.92     NaN  1.27  NaN           NaN
     2020-05-01  12.16     NaN  1.27  NaN           NaN
     2020-05-08  12.28     NaN  1.28  NaN           NaN
     2020-05-15  12.10     NaN  1.27  NaN           NaN
     2020-05-22  11.89     NaN  1.25  NaN           NaN
     2020-05-29  12.02     NaN  1.26  NaN           NaN
     2020-06-05  12.35     NaN  1.30  NaN           NaN
     2020-06-12  12.30     NaN  1.30  NaN           NaN
     2020-06-19  12.51     NaN  1.31  NaN           NaN
     2020-06-26  12.58     NaN  1.32  NaN           NaN
     2020-07-03  13.34     NaN  1.41  NaN           NaN
     2020-07-10  14.24     NaN  1.51  NaN           NaN
     2020-07-17  13.55     NaN  1.45  NaN           NaN
     2020-07-24  13.34     NaN  1.45  NaN           NaN
     2020-07-31  13.76     NaN  1.50  NaN           NaN
     2020-08-07  13.96     NaN  1.52  NaN           NaN
     2020-08-14  14.03     NaN  1.53  NaN           NaN
     2020-08-21  14.11     NaN  1.54  NaN           NaN
     2020-08-28  14.20     NaN  1.54  NaN           NaN
     2020-09-04  13.98     NaN  1.52  NaN           NaN
     2020-09-11  13.64     NaN  1.48  NaN           NaN
     2020-09-18  13.96     NaN  1.52  NaN           NaN
     2020-09-25  13.48     NaN  1.46  NaN           NaN
     2020-10-02  13.50     NaN  1.46  NaN           NaN
     2020-10-09  13.71     NaN  1.48  NaN           NaN
     2020-10-16  14.00     NaN  1.51  NaN           NaN
     2020-10-23  13.80     NaN  1.49  NaN           NaN
     2020-10-30  13.56     NaN  1.44  NaN           NaN
     2020-11-06  13.94     NaN  1.46  NaN           NaN
     2020-11-13  13.96     NaN  1.46  NaN           NaN
     2020-11-20  14.31     NaN  1.50  NaN           NaN
     2020-11-27  14.51     NaN  1.52  NaN           NaN
     2020-12-04  14.66     NaN  1.54  NaN           NaN
     2020-12-11  14.20     NaN  1.49  NaN           NaN
     2020-12-18  14.39     NaN  1.51  NaN           NaN
     2020-12-25  14.40     NaN  1.51  NaN           NaN,
     '000002.SH':             pe  ebitda  pb  eps  total_income
     2020-01-03 NaN     NaN NaN  NaN           NaN
     2020-01-10 NaN     NaN NaN  NaN           NaN
     2020-01-17 NaN     NaN NaN  NaN           NaN
     2020-01-24 NaN     NaN NaN  NaN           NaN
     2020-01-31 NaN     NaN NaN  NaN           NaN
     2020-02-07 NaN     NaN NaN  NaN           NaN
     2020-02-14 NaN     NaN NaN  NaN           NaN
     2020-02-21 NaN     NaN NaN  NaN           NaN
     2020-02-28 NaN     NaN NaN  NaN           NaN
     2020-03-06 NaN     NaN NaN  NaN           NaN
     2020-03-13 NaN     NaN NaN  NaN           NaN
     2020-03-20 NaN     NaN NaN  NaN           NaN
     2020-03-27 NaN     NaN NaN  NaN           NaN
     2020-04-03 NaN     NaN NaN  NaN           NaN
     2020-04-10 NaN     NaN NaN  NaN           NaN
     2020-04-17 NaN     NaN NaN  NaN           NaN
     2020-04-24 NaN     NaN NaN  NaN           NaN
     2020-05-01 NaN     NaN NaN  NaN           NaN
     2020-05-08 NaN     NaN NaN  NaN           NaN
     2020-05-15 NaN     NaN NaN  NaN           NaN
     2020-05-22 NaN     NaN NaN  NaN           NaN
     2020-05-29 NaN     NaN NaN  NaN           NaN
     2020-06-05 NaN     NaN NaN  NaN           NaN
     2020-06-12 NaN     NaN NaN  NaN           NaN
     2020-06-19 NaN     NaN NaN  NaN           NaN
     2020-06-26 NaN     NaN NaN  NaN           NaN
     2020-07-03 NaN     NaN NaN  NaN           NaN
     2020-07-10 NaN     NaN NaN  NaN           NaN
     2020-07-17 NaN     NaN NaN  NaN           NaN
     2020-07-24 NaN     NaN NaN  NaN           NaN
     2020-07-31 NaN     NaN NaN  NaN           NaN
     2020-08-07 NaN     NaN NaN  NaN           NaN
     2020-08-14 NaN     NaN NaN  NaN           NaN
     2020-08-21 NaN     NaN NaN  NaN           NaN
     2020-08-28 NaN     NaN NaN  NaN           NaN
     2020-09-04 NaN     NaN NaN  NaN           NaN
     2020-09-11 NaN     NaN NaN  NaN           NaN
     2020-09-18 NaN     NaN NaN  NaN           NaN
     2020-09-25 NaN     NaN NaN  NaN           NaN
     2020-10-02 NaN     NaN NaN  NaN           NaN
     2020-10-09 NaN     NaN NaN  NaN           NaN
     2020-10-16 NaN     NaN NaN  NaN           NaN
     2020-10-23 NaN     NaN NaN  NaN           NaN
     2020-10-30 NaN     NaN NaN  NaN           NaN
     2020-11-06 NaN     NaN NaN  NaN           NaN
     2020-11-13 NaN     NaN NaN  NaN           NaN
     2020-11-20 NaN     NaN NaN  NaN           NaN
     2020-11-27 NaN     NaN NaN  NaN           NaN
     2020-12-04 NaN     NaN NaN  NaN           NaN
     2020-12-11 NaN     NaN NaN  NaN           NaN
     2020-12-18 NaN     NaN NaN  NaN           NaN
     2020-12-25 NaN     NaN NaN  NaN           NaN,
     '000003.SH':             pe  ebitda  pb  eps  total_income
     2020-01-03 NaN     NaN NaN  NaN           NaN
     2020-01-10 NaN     NaN NaN  NaN           NaN
     2020-01-17 NaN     NaN NaN  NaN           NaN
     2020-01-24 NaN     NaN NaN  NaN           NaN
     2020-01-31 NaN     NaN NaN  NaN           NaN
     2020-02-07 NaN     NaN NaN  NaN           NaN
     2020-02-14 NaN     NaN NaN  NaN           NaN
     2020-02-21 NaN     NaN NaN  NaN           NaN
     2020-02-28 NaN     NaN NaN  NaN           NaN
     2020-03-06 NaN     NaN NaN  NaN           NaN
     2020-03-13 NaN     NaN NaN  NaN           NaN
     2020-03-20 NaN     NaN NaN  NaN           NaN
     2020-03-27 NaN     NaN NaN  NaN           NaN
     2020-04-03 NaN     NaN NaN  NaN           NaN
     2020-04-10 NaN     NaN NaN  NaN           NaN
     2020-04-17 NaN     NaN NaN  NaN           NaN
     2020-04-24 NaN     NaN NaN  NaN           NaN
     2020-05-01 NaN     NaN NaN  NaN           NaN
     2020-05-08 NaN     NaN NaN  NaN           NaN
     2020-05-15 NaN     NaN NaN  NaN           NaN
     2020-05-22 NaN     NaN NaN  NaN           NaN
     2020-05-29 NaN     NaN NaN  NaN           NaN
     2020-06-05 NaN     NaN NaN  NaN           NaN
     2020-06-12 NaN     NaN NaN  NaN           NaN
     2020-06-19 NaN     NaN NaN  NaN           NaN
     2020-06-26 NaN     NaN NaN  NaN           NaN
     2020-07-03 NaN     NaN NaN  NaN           NaN
     2020-07-10 NaN     NaN NaN  NaN           NaN
     2020-07-17 NaN     NaN NaN  NaN           NaN
     2020-07-24 NaN     NaN NaN  NaN           NaN
     2020-07-31 NaN     NaN NaN  NaN           NaN
     2020-08-07 NaN     NaN NaN  NaN           NaN
     2020-08-14 NaN     NaN NaN  NaN           NaN
     2020-08-21 NaN     NaN NaN  NaN           NaN
     2020-08-28 NaN     NaN NaN  NaN           NaN
     2020-09-04 NaN     NaN NaN  NaN           NaN
     2020-09-11 NaN     NaN NaN  NaN           NaN
     2020-09-18 NaN     NaN NaN  NaN           NaN
     2020-09-25 NaN     NaN NaN  NaN           NaN
     2020-10-02 NaN     NaN NaN  NaN           NaN
     2020-10-09 NaN     NaN NaN  NaN           NaN
     2020-10-16 NaN     NaN NaN  NaN           NaN
     2020-10-23 NaN     NaN NaN  NaN           NaN
     2020-10-30 NaN     NaN NaN  NaN           NaN
     2020-11-06 NaN     NaN NaN  NaN           NaN
     2020-11-13 NaN     NaN NaN  NaN           NaN
     2020-11-20 NaN     NaN NaN  NaN           NaN
     2020-11-27 NaN     NaN NaN  NaN           NaN
     2020-12-04 NaN     NaN NaN  NaN           NaN
     2020-12-11 NaN     NaN NaN  NaN           NaN
     2020-12-18 NaN     NaN NaN  NaN           NaN
     2020-12-25 NaN     NaN NaN  NaN           NaN}




```python
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




![png](02_Financial_Data_Operations/output_18_1.png)
    




![png](02_Financial_Data_Operations/output_18_2.png)
    




![png](02_Financial_Data_Operations/output_18_3.png)
    




![png](02_Financial_Data_Operations/output_18_4.png)
    




![png](02_Financial_Data_Operations/output_18_5.png)
    




![png](02_Financial_Data_Operations/output_18_6.png)
    




![png](02_Financial_Data_Operations/output_18_7.png)
    




![png](02_Financial_Data_Operations/output_18_8.png)
    




![png](02_Financial_Data_Operations/output_18_9.png)
    




![png](02_Financial_Data_Operations/output_18_10.png)
    




![png](02_Financial_Data_Operations/output_18_11.png)
    
