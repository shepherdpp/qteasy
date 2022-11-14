# QTEASY使用教程01——基础配置及初始化

qteasy是一个完全本地化部署和运行的量化交易分析工具包，具备以下功能：

- 金融数据的获取、清洗、存储以及处理、可视化、使用
- 量化交易策略的创建，并提供大量内置基本交易策略
- 向量化的高速交易策略回测及交易结果评价
- 交易策略参数的优化以及评价
- 交易策略的部署

qteasy使用python创建，使用向量化回测及交易模拟引擎实现了策略的高速回测，同时又兼顾策略框架的灵活性，使得用户可以根据需要灵活定制各种高级策。qteasy提供了多种策略参数优化算法，帮助优化及评价交易策略，同时提供了实时运行模式，使交易策略可以直接部署使用。

本系列教程使用一系列示例介绍qteasy的主要功能以及使用方法。

## 安装环境及依赖包

### 1，依赖包

`qteasy`依赖以下`python`包，推荐使用`Anaconda`搭建一个运行环境：

- *`pandas` version 0.25*
- *`numpy` version 0.19*
- *`TA-lib` version 0.4*
- *`tushare pro` version 1.24.1*
- *`matplotlib.mplfinance` version 0.12*

上面的包中，`TA-lib`需要用户自行安装，大部份的`qteasy`内置交易策略都是基于`TA-lib`提供的金融数据函数创建的，如果`TA-lib`没有正确安装，将会导致大部份内置交易策略无法使用。

### 2，数据管理环境（本地数据源）

`qteasy`可以管理大量的金融数据。`qteasy`的工作方式是将所有的金融数据下载到本地，清洗后存储到事先定义好的数据表中，在需要时（生成K线图、交易信号生成、模拟交易回测、交易结果评价等所有环节都需要用到金融数据）从本地数据源直接读取所需的数据。因此，必须在本地设置一个数据管理环境。

`qteasy`同时支持数据库及文件系统作为数据管理环境，考虑到金融数据量，强烈推荐使用数据库作为本地数据源。`qteasy`支持的本地数据源包括：

- **`mysql` 数据库**（或兼容的Maria DB数据库），强烈推荐使用mysql数据库并确保磁盘有至少1TB的存储空间，速度快
- **`csv` 文件** 占用空间大，但是可以使用Excel读取本地数据，数据量大时速度慢
- **`hdf5` 文件** 占用空间大，数据量大时速度慢
- **`feather` 文件** 占用空间较小，数据量大时速度慢

### 3，tushare依赖

`qteasy`目前完全依赖`tushare`来获取金融数据，系统内建了比较完整的API与`tushare`接口。鉴于`tushare`的接口均有权限或积分要求，建议用户提前准备好相应的`tushare`积分，并开通相应权限。

未来计划增加其他金融数据提供商的API，以扩大数据来源。

## 配置环境变量

qteasy的运行依赖于一系列的环境配置变量，通过环境配置变量，用户可以控制qteasy运行的方方面面。qteasy在运行时允许存在多组不同的环境配置变量对象Config，每一组Config对应一组环境配置变量。在默认情况下，qteasy初始化会创建一个默认环境变量QT_CONFIG并始终使用这个配置变量。

推荐使用以下方式倒入qteasy：

```python
import qteasy as qt
```

所有的环境参数变量值都可以通过`qt.Configuration()`查看，并通过`qt.Configure()`来设置。

### 初始环境变量的配置

在`qteasy`第一次初始化以后，在`qteasy/`文件夹里会创建一个`qteasy.cnf`的文件，这个文件里的内容会在每次`qteasy`被`import`并初始化的时候读取，并作为默认环境参数被读入内存。第一次初始化后创建的qteasy.cnf文件中不会有任何自定义配置，用户可以用文本处理程序打开这个文件，修改其中的内容。

第一次创建的`qteasy.cnf`文件内容如下：

```
# qteasy configs
# following configurations will be activated during initialization
```
建议用户在使用qteasy前使用qteasy.cnf文件配置tushare 的token，以及本地数据源的配置，例如：

```
# qteasy configs
# following configurations will be activated during initialization

# 设置tushare的token
tushare_token = <your tushare token>

# 设置本地数据源，如果使用database作为本地数据源
local_data_source = database
# 需要设置数据库服务器信息
local_db_host = localhost
local_db_user = <user name>
local_db_password = <your password>
local_db_name = <your db name>

# 或者如果使用csv文件作为本地数据源：
local_data_source = file
# 需要设置数据库服务器信息
local_data_file_type = csv  # 或者hdf/fth分别代表hdf5文件或feather文件
local_data_file_path = qteasy/data  # 或者其他指定的文件存储目录
```
完成上述配置后，`qteasy`会将上述配置读取后写入**`QT_CONFIG`**，这样在运行中就会使用这一组配置变量。

### 运行时修改环境变量

`qteasy`运行时可以使用以下几个函数查看或修改系统环境变量

### `qt.configuration(config_key=None, level=0, up_to=0, default=True, verbose=False)`
查看`qteasy`运行环境变量,如果传入参数config_key，则只显示输入的key的值，否则显示所有相应level的`config_key`
设置`default=True`以及`verbose=True`可以看到更详细的信息以及`config_key`的默认值

### `qt.configure(config=None, reset=False, only_built_in_keys=True, **kwargs)`
设置`qteasy`运行环境变量

### `qt.save_config()`
保存`qteasy`运行环境变量

### `qt.load_connfig()`
读取`qteasy`运行环境变量

例如：

下面的示例显示`qteasy`的环境配置变量：


```python
qt.configuration(level=0, up_to=1, default=True)
```


    No. Config-Key            Cur Val        Default val
    ----------------------------------------------------
    1   mode                  1              <1>
    2   asset_pool            000300.SH      <000300.SH>
    3   asset_type            IDX            <IDX>
    4   trade_batch_size      0.0            <0.0>
    5   sell_batch_size       0.0            <0.0>
    6   parallel              True           <True>
    7   trade_log             True           <True>
    8   benchmark_asset       000300.SH      <000300.SH>
    9   benchmark_asset_type  IDX            <IDX>
    10  benchmark_dtype       close          <close>
    11  report                True           <True>
    12  visual                True           <True>
    13  cost_rate_buy         0.0003         <0.0003>
    14  cost_rate_sell        0.0001         <0.0001>
    15  invest_start          20160405       <20160405>
    16  invest_end            20210201       <20210201>
    17  invest_cash_amounts   [100000.0]     <[100000.0]>
    18  opti_start            20160405       <20160405>
    19  opti_end              20191231       <20191231>
    20  opti_cash_amounts     [100000.0]     <[100000.0]>
    21  test_start            20200106       <20200106>
    22  test_end              20210201       <20210201>
    23  test_cash_amounts     [100000.0]     <[100000.0]>
    24  optimize_target       final_value    <final_value>
    25  maximize_target       True           <True>
    26  opti_method           1              <1>
    


如果设置`verbose=True`，并传入`config_key`参数，可以显示特定`config_key`的详细描述


```python
qt.configuration(config_key='mode, asset_pool, report, visual', default=True, verbose=True)
```

    No. Config-Key            Cur Val        Default val
          Description
    ----------------------------------------------------
    1   mode                  1              <1>
          qteasy 的运行模式: 
          0: 实时信号生成模式
          1: 回测-评价模式
          2: 策略优化模式
          3: 统计预测模式
          
    
    2   asset_pool            000300.SH      <000300.SH>
          可用投资产品池，投资组合基于池中的产品创建                         
    
    3   report                True           <True>
          为True时打印运行结果报告
          实时模式显示策略运行报告，回测模式显示回测结果报告，优化模式显示优化结果报告
    
    4   visual                True           <True>
          为True时使用图表显示可视化运行结果
          （回测模式显示回测报告，优化模式显示优化结果报告）
    
    
