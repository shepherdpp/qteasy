# 基础配置及初始化

qteasy是一个完全本地化部署和运行的量化交易分析工具包，具备以下功能：

- 金融数据的获取、清洗、存储以及处理、可视化、使用
- 量化交易策略的创建，并提供大量内置基本交易策略
- 向量化的高速交易策略回测及交易结果评价
- 交易策略参数的优化以及评价
- 交易策略的部署、实盘运行

qteasy使用python创建，使用向量化回测及交易模拟引擎实现了策略的高速回测，同时又兼顾策略框架的灵活性，使得用户可以根据需要灵活定制各种高级策。qteasy提供了多种策略参数优化算法，帮助优化及评价交易策略，同时提供了实时运行模式，使交易策略可以直接部署使用。

通过本系列教程，您将会通过一系列的实际示例，充分了解qteasy的主要功能以及使用方法。

## `qteasy`安装前的准备工作

qteasy可以通过pip来安装，由于依赖包较多，为了避免各依赖包与现有环境中的包产生冲突，建议创建一个独立的python环境来安装qteasy。

创建虚拟环境的方法有很多种，这里介绍两种方法，分别是使用`venv`和`conda`：

要使用venv创建虚拟环境，macOS和Linux用户可以打开终端，进入您需要创建环境的路径，输入以下命令，在当前目录下创建一个名为qteasy-env的虚拟环境，并激活环境：

```commandline
python -m venv qteasy-env  
source qteasy-env/bin/activate
```

Windows用户可以打开命令提示符，进入您需要创建环境的文件夹，输入以下命令，创建虚拟环境并激活：

```commandline
py -m venv qteasy-env  
.venv\Scripts\activate
```

要使用conda创建虚拟环境，可以打开终端，输入以下命令，创建一个名为qteasy-env的虚拟环境，并激活环境：

```commandline
conda create -n qteasy-env python=3.8
conda activate qteasy-env
```

在激活的虚拟环境中，使用以下命令安装qteasy：

```commandline
pip install qteasy
```

### 依赖包

`qteasy`依赖以下`python`包，有些安装包可能不能在安装`qteasy`的时候自动安装，此时可以手动安装依赖包：
:
- *`pandas` version >= 0.25.1, <1.5.3*    `pip install pandas==1.1.0` / `conda install pandas`
- *`numpy` version >= 1.18.1, <=1.21.5*    `pip install numpy==1.21.5` / `conda install numpy`
- *`numba` version >= 0.47*    `pip install numba==0.47.0` / `conda install numba`
- *`tushare` version >= 1.2.89*    `pip install tushare`
- *`mplfinance` version >= 0.11*    `pip install mplfinance` / `conda install -c conda-forge mplfinance`
- *`ta-lib` version >= 0.4.18*  `TA-lib`需要用户自行安装，大部份的`qteasy`内置交易策略都是基于`TA-lib`提供的金融数据函数创建的，如果`TA-lib`没有正确安装，将会导致大部份内置交易策略无法使用。

### 安装可选依赖包
使用`qteasy`需要设置本地数据源，默认使用csv文件作为本地数据源，如果选用其他数据源，需要安装以下可选依赖包，或者在安装`qteasy`时使用可选参数安装这些依赖包：

#### 使用mysql数据库作为本地数据源（**推荐**）

可以使用下面命令安装qteasy时安装mysql数据库的依赖包：
```commandline
pip install qteasy[mysql]
```
或者手动安装pymysql
- *`pymysql` version >= 1.0.0*    `pip install pymysql` / `conda install -c anaconda pymysql`

#### 使用其他文件作为本地数据源 
qteasy还支持使用`hdf5`文件和`feather`文件作为本地数据源，如果使用这两种文件作为本地数据源，可以使用以下命令安装qteasy时安装这些依赖包：
```commandline
pip install qteasy[hdf5]
pip install qteasy[feather]
```
或者手动安装以下依赖包：
- *`pytables` version >= 3.6.1*   `conda install -c conda-forge pytables`
- *`pyarrow` version >= 3*   `pip install pyarrow` / `conda install -c conda-forge pyarrow`

#### 使用完整的内置交易策略
`qteasy`提供了大量内置交易策略，用户可以直接使用这些交易策略通过"混合"的方式组合成自己的交易策略，但是大部份内置交易策略需要借助`TA-Lib`发挥作用
`TA-Lib`是供C语言的一个的一个金融交易技术分析函数包，里面包含大量的技术指标、K线形态识别、基础统计分析等函数，`python`提供了这个包的`wrapper`，要
在`python`中使用`ta-lib`，需要先安装C语言的`TA-Lib`后，再安装`python`的`ta-lib`包：

- *`TA-lib` version >= 0.4.18*    `pip install ta-lib` 更多的安装信息，请参见[FAQ-TA-lib安装方法](https://qteasy.readthedocs.io/zh/latest/faq.html)

### 2，数据管理环境（本地数据源）

`qteasy`可以管理大量的金融数据。`qteasy`的工作方式是将所有的金融数据下载到本地，清洗后存储到事先定义好的数据表中，在需要时（生成K线图、交易信号生成、模拟交易回测、交易结果评价等所有环节都需要用到金融数据）从本地数据源直接读取所需的数据。因此，必须在本地设置一个数据管理环境。

`qteasy`同时支持数据库及文件系统作为数据管理环境，考虑到金融数据量，强烈推荐使用数据库作为本地数据源。`qteasy`支持的本地数据源包括：

- **`csv` 文件** 默认数据源。占用空间大，但是可以使用Excel读取本地数据，数据量大时速度慢
- **`mysql` 数据库**，强烈推荐使用mysql数据库并确保磁盘有至少1TB的存储空间，速度快
- **`hdf5` 文件** 占用空间大，数据量大时速度慢
- **`feather` 文件** 占用空间较小，数据量大时速度慢

为了实现最佳的数据存储效率，建议使用`mysql`数据库作为本地数据源。如果使用`mysql`数据库作为本地数据源。

如果需要使用数据库作为本地数据源，参照以下方法安装`MySQL`数据库，如果使用文件作为本地数据源，可以跳过这一步。

在`MySQL`的[官网](https://dev.mysql.com/downloads/mysql/)可以直接找到社区开源版本下载:
网站提供了dmg和tar等多种不同的安装方式，而且还有针对M1芯片的版本可选：

![png](https://user-images.githubusercontent.com/34448648/128119283-5c9c3aba-6564-4463-83b6-a2e7216ae3cd.png)

安装完成后，创建用户，设置访问方式并设置密码：

``` mysql
# 创建新的用户，并允许客户通过localhost连接
mysql> CREATE USER '用户名'@'localhost' IDENTIFIED BY '初始密码';
Query OK, 0 rows affected (0.46 sec)

# 设置用户的权限
mysql> GRANT ALL ON *.* TO '用户名'@'localhost';
Query OK, 0 rows affected (0.06 sec)

# 创建新的用户，并允许客户通过远程连接
mysql> CREATE USER '用户名'@'%' IDENTIFIED BY '初始密码';
Query OK, 0 rows affected (0.46 sec)

# 设置用户的权限
mysql> GRANT ALL ON *.* TO '用户名'@'%';
Query OK, 0 rows affected (0.06 sec)
```
数据库设置好之后，`qteasy`会自动创建数据库表，将金融数据存储到数据库中。


### 3，创建tushare账号并获取token

`qteasy`目前主要依赖`tushare`来获取金融数据，系统内建了比较完整的API与`tushare`接口。鉴于`tushare`的接口均有权限或积分要求，建议用户提前准备好相应的`tushare`积分，并开通相应权限。

申请tushare积分和权限的方法请参见[tushare pro主页](https://tushare.pro):
![tushare主页](https://img-blog.csdnimg.cn/direct/34816903637b43e09c01b160b38b8dd9.png#pic_center)

如果不创建tushare账号，`qteasy`仍然可以获得一些数据，但是数据的种类非常有限，访问频率和次数也受到限制，很多`qteasy`功能的使用将会受到限制。
未来计划增加其他金融数据提供商的API，以扩大数据来源。


## 使用`QTEASY`

当qteasy的所有依赖包正确安装后，即可使用以下方式导入`qteasy`：

```python
import qteasy as qt
print(qt.__version__)
```
第一次安装的qteasy会自动初始化，初始化过程会创建一个`qteasy.cnf`文件，这个文件用于存储qteasy的环境配置变量，用户可以通过修改这个文件来修改qteasy的环境配置变量。

默认情况下，qteasy使用csv文件保存本地数据，速度较慢而且占用空间较大。为了更好地使用qteasy，用户还应该完成本地数据源的基本配置。


## 配置环境变量和数据源

qteasy的运行依赖于一系列的环境配置变量，通过环境配置变量，用户可以控制qteasy运行的方方面面。qteasy在运行时允许存在多组不同的环境配置变量对象Config，每一组Config对应一组环境配置变量。在默认情况下，qteasy初始化会创建一个默认环境变量QT_CONFIG并始终使用这个配置变量。

> - 使用`qt.QT_ROOT_PATH`可以查看qteasy的根目录
> - 使用`qt.QT_CONFIG`可以查看当前使用的环境配置变量

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
```
完成上述配置后，`qteasy`会将上述配置读取后写入`qt.QT_CONFIG`环境变量，这样在运行中就会使用这一组配置变量。


### 配置qteasy环境变量

例如：

下面的示例显示`qteasy`的环境配置变量：


```python
qt.configuration(level=0, up_to=1, default=True)
```

输出如下


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

输出如下：

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


### API 参考

关于qteasy环境变量的AP，以及所有的环境变量，请参考 [Configuration APIs](../api_reference.rst)
