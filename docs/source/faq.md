# FAQ

## 问题目录

- [如何搭建不同python版本的安装环境](如何搭建不同python版本的安装环境)
- [使用国内的pip镜像源](使用国内的pip镜像源)
- [如何安装TA-Lib](如何安装TA-Lib)
- [python3.11环境下安装qteasy失败](在较高版本python环境中安装qteasy)
- [连接数据库失败](在qteasy.cfg中添加配置信息后，为何仍然提示数据库连接失败)
- [系统提示建议安装sqlalchemy](从数据库中读取数据时，为什么会出现提示建议安装\`sqlalchemy\`\？)
- [从tushare下载数据受频率限制失败](从tushare下载数据时提示下载频率过高而失败)

---

## 如何搭建不同python版本的安装环境

在`qteasy` Tutorial中，我们介绍了使用`venv`创建虚拟环境安装`qteasy`的方法。但是，有时候用户可能需要在不同的`python`版本下安装`qteasy`，例如在`python`3.9、`python`3.10、`python`3.11、`python`3.12等等版本下安装`qteasy`。这里我们介绍一种方法，可以在不同的`python`版本下安装`qteasy`。

使用Anaconda创建不同python版本的环境：

Anaconda是一个科学计算的Python发行版，它包含了conda、Python等180多个科学包及其依赖项。因此，我们可以使用Anaconda创建不同python版本的环境，然后在不同的环境下安装qteasy。

Anaconda可以在其官网下载，下载地址为：[Anaconda](https://www.anaconda.com/products/distribution)。针对不同操作系统，下载对应的版本，然后安装。

安装Anaconda后，我们可以使用conda命令创建不同的python版本的环境，并在其中安装python包。例如：

```bash
$ conda create -n py39 python=3.9  # 创建python3.9环境
$ conda activate py39  # 激活python3.9环境
$ pip install qteasy  # 在python3.9环境下安装qteasy
```
在conda环境中，使用pip安装的软件包也能被正确地识别和管理。

下面有一些常用的conda命令：

```bash
$ conda env list  # 查看所有的环境
$ conda activate py39  # 激活python3.9环境
$ conda deactivate  # 退出当前环境
$ conda remove -n py39 --all  # 删除python3.9环境
$ conda list  # 查看当前环境下安装的包
$ conda list -n py39  # 查看python3.9环境下安装的包
```
---

## 使用国内的pip镜像源

在国内，由于网络环境的原因，有时候使用pip安装python包会很慢，甚至失败。这时候，我们可以使用国内的pip镜像源，例如清华大学的pip镜像源。

在使用pip安装python包时，可以使用`-i`参数指定pip镜像源，例如：

```bash
$ pip install -i https://pypi.tuna.tsinghua.edu.cn/simple qteasy
```
---

## 如何升级qteasy到最新版本

在使用qteasy时，我们可能需要升级到最新版本。升级qteasy到最新版本的方法如下：

```bash
$ pip install qteasy --upgrade
```
或者使用下面的命令：

```bash
$ pip isntall qteasy -U
```
如果要使用国内的清华镜像源，可以使用下面的命令：

```bash
$ pip install -i https://pypi.tuna.tsinghua.edu.cn/simple qteasy --upgrade
```

---

## 如何安装TA-Lib

完整的TA-Lib包无法通过pip安装，因为通过`pip install ta-lib`安装的只是TA-Lib包的一个`python wrapper`, 用户必须首先安装C语言的TA-Lib才能在python中使用它。

> 有些用户可以用下面的方法安装C语言的TA-Lib包：
> `conda install -c conda-forge libta-lib`

在不同的系统下安装C语言的TA-Lib包的方法：

### Windows

* 下载 [ta-lib-0.4.0-msvc.zip](http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-msvc.zip) 并解压至 `C:\ta-lib`.
* 下载并安装 `Visual Studio Community` (2015 或更新版本)， 选择 `[Visual C++]` 功能
* Windows 开始菜单, 启动 `[VS2015 x64 Native Tools Command Prompt]`
* 移动至 `C:\ta-lib\c\make\cdr\win32\msvc`
* `nmake`

### Mac OS

首先安装homebrew，然后通过homebrew安装C语言TA-LIB包：

```bash
$ /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
$ brew install ta-lib
```

如果使用Apple Silicon芯片，可以使用：

```bash
$ /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
$ arch -arm64 brew install ta-lib
```

### Linux

下载 [ta-lib-0.4.0-src.tar.gz](http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz) ，然后:

```bash
$ tar -xzf ta-lib-0.4.0-src.tar.gz
$ cd ta-lib/
$ ./configure --prefix=/usr
$ make
$ sudo make install
```
C语言TA-LIB包安装完成后，即可以通过pip安装python的TA-Lib包：

```bash
$ pip install ta-lib
```
如果需要在arm64架构的Mac上安装TA-Lib，可以使用下面的命令：

```bash
$ arch -arm64 python -m pip install --no-cache-dir ta-lib
```

如果您使用Arm64架构的电脑，但是安装ta-lib后出现导入错误`ImportError:`，可能是因为环境的问题，请参考[这篇文章](https://blog.csdn.net/Shepherdppz/article/details/138253619)解决您的问题。

---

## 在较高版本python环境中安装qteasy

解决方案是升级到最新的`qteasy`版本。较新版本的`qteasy`已经在`python`3.7 ~ 3.12环境中进行了测试，可以在这些环境中正常运行。

```bash
$ pip install qteasy --upgrade
```

较早版本的`qteasy`没有在高版本的`python`环境中进行充分测试，因此存在一些兼容性问题。这样的问题主要存在于v1.1.4及以前的`qteasy`分发版中。

同时，较早版本的`qteasy`在也使用了一些在高版本的`pandas`、`numpy`中即将被弃用的API，这也可能导致对高版本`pandas`、`numpy`的兼容性问题，在v1.1.7及以后版本的`qteasy`中，已经对这些问题进行了修复。

---

## 在qteasy.cfg中添加配置信息后，提示数据库连接失败

有用户反馈，在`qteasy.cfg`文件中配置好数据库连接信息后，仍然提示数据库连接失败。并得到下面类似的错误信息：

```text
C:\Users\yuewe\Documents\GitHub\qteasy-1.0.26\qteasy\database.py:2504: RuntimeWarning: (1045, "Access denied for user 'yuewe'@'localhost' (using password: NO)"), Can not set data source type to "db", will fall back to default type
warnings.warn(f'{str(e)}, Can not set data source type to "db",'
```

如果您第一次遇到这样的问题，可能应该首先检查您的`qteasy.cfg`文件。主要检查下面两方面：

- 配置的key是否错误，`qteasy`稳定版本使用的数据库连接信息配置key是`local_db_host` / `local_db_port` ... 等等，而不是`database_host`，以前在官方文档中曾经存在一些错误，这些错误已经在最新的文档中修正了。
- 在文件中给出配置信息的时候，请不要加其他字符，如`"`, `<`和`>`等等，否则，这些字符也会被认为是`token`或者数据库名的一部份。从而导致连接数据库失败。

`qteasy`在解析配置文件的时候，会根据配置的类型，自动转换为正确的格式，例如，数据库端口`3306`应该是`int`变量，直接使用：

```
local_db_port = 3306
```

即可。`qteasy`会将字符串`3306`转换为`int`型`3306`。·

下面这个配置文件的例子是正确的：

```
tushare_token = 2dff3f034aa966479c81e4b4b0736fb081b740abb2xxxxxxxxxxxxxxxxxxxxx

local_data_source = database

local_db_host = localhost
local_db_port = 3306
local_db_user = user_name
local_db_password = pass_word
local_db_name = ts_db
```
---

## 从数据库中读取数据时，提示建议安装`sqlalchemy`

有时候，在使用数据库作为数据源，并从数据库中读取数据时，您可能会看到以下提示信息：

```text
UserWarning: pandas only supports SQLAlchemy connectable (engine/connection) or database string URI or sqlite3 DBAPI2 connection. Other DBAPI2 objects are not tested. Please consider using SQLAlchemy.
```
以上提示信息建议用户使用`sqlalchemy`.

总的来说，这是一条`UserWarning`。其实并没有错误发生，数据读取是成功的。出现这条警告信息的原因跟您安装的`pandas`的版本有关。您不需要安装`sqlalchemy`，`qteasy`已经移除了对`sqlalchemy`的依赖.
为了确认为何会出现这条警告，请检查一下您的`pandas`版本.

```python
import pandas as pd
pd.__version__
```

如果您使用的`pandas`版本为1.1以上，有可能会出现这条`UserWarning`，但一般来说应该不会影响使用：
这是因为`qteasy`使用`pymysql`作为数据库连接API，但`pandas`从1.1版本以后，逐步开始将`pymysql`的支持去掉了，尽管经过测试，在`pandas`的1.5版本下`qteasy`仍然能够正确读取数据，但是会收到警告信息。

以上问题已经进入了我的修改清单，在接下来的小升级中，会去掉对`pandas`的sql API依赖，直接使用`pymysql`读取数据库，这样就不会出现这条警告信息了。如果您不希望看到这条警告信息，也可以降级`pandas`的版本到`1.1.0`。`qteasy`在开发初期一致固定使用较低版本的`pandas`，绝大部分的稳定性测试基于`pandas`的1.1版本，如果使用1.1版本的`pandas`就不会出现这个提示信息，其他所有功能也都正常。

---

## 从tushare下载数据时提示下载频率过高而失败

某些tushare数据存在每分钟读取频率限制，如果积分不够，下载频率是会被限制的，从而导致某些数据下载不完整，例如下面的情况：

运行脚本： 

```python
>>> qt.refill_data_source(tables='events', start_date='20230101', end_date='20240403',reversed_par_seq=True)
```

出现下列报错：
    
```text
[##############--------------------------]6000/16923-35.5% <fund_share:016407.OF>37107wrtn/about 19 minleftC:\ProgramData\anaconda3\envs\qteasy-env-p311\Lib\site-packages\qteasy*database.py:5134*: UserWarning:
抱歉，您每分钟最多访问该接口600次，权限的具体详情访问：https://tushare.pro/document/1?doc_id=108。:
download process interrupted at [fund_share]:<F180003.OF>-<016408.OF>
37107 rows downloaded, will proceed with next table!
warnings.warn(msg)
[#######################-----------------]10000/16923-59.1% <fund_manager:012277.OF>1264483wrtn/about 15 minleftC:\ProgramData\anaconda3\envs\qteasy-env-p311\Lib\site-packages\qteasy\database.py:5134: UserWarning:
抱歉，您每分钟最多访问该接口500次，权限的具体详情访问：https://tushare.pro/document/1?doc_id=108。:
download process interrupted at [fund_manager]:<F180003.OF>-<012278.OF>
1264483 rows downloaded, will proceed with next table!
warnings.warn(msg)
```

为此，qteasy设计了专门的重试机制来规避或缓解这个问题。

您可以尝试修改qteasy的下面几个配置，调整下载数据时的重试次数和延时设置，这几个配置参数是专门为了应对tushare的读取频率限制设置的：

QT_CONFIG.hist_dnld_retry_cnt - 下载数据时失败重试的次数，默认为7次
QT_CONFIG.hist_dnld_retry_wait - 第一次下载失败时的等待时长，单位为秒，默认为1秒
QT_CONFIG.hist_dnld_backoff - 等待后仍然失败时等待时间的倍增乘数，默认为2倍

qteasy在调用所有的tushare函数时，会自动retry，每两次retry之间会逐渐延长间隔。比如，第一次下载不成功时，会暂停一秒重试，如果重试仍然有问题，会等待2秒重试，下一次等待4秒、再等待8秒。。。依此类推，一直到重试次数用光，这时才会raise。

正常来讲，重试7次后的延时会倍增到32秒，加上前面延时的长度，已经超过1分钟了，正常是不会触发频率错误的，但如果网速过快，或者同时启用的线程太多，可能会有上面的问题。

这时可以尝试将重试次数改成10次或更多（这样会显著延长下载时间），或者增加等待初始时长：

```python
>>> qt.configure(hist_dnld_retry_cnt=10, hist_dnld_retry_wait=2.)
>>> qt.refill_data_source(tables='events', start_date='20230101', end_date='20240403',reversed_par_seq=True)
```

---

## 从`tushare`分批下载数据

某些时候我们需要分批下载数据，在每批次之间暂停一定时间，例如tushare的某些数据表设置了频率限制，限定每分钟最多下载的次数，如果超过这个次数，会导致下载失败。
这时，我们可以通过下面两个配置参数来实现这样的分批下载和停顿：

- **`QT_CONFIG.hist_dnld_delay`**: 默认值为0，如果设置为一个大于0的整数，表示分批下载时每批的下载数量
- **`QT_CONFIG.hist_dnld_delay_evy`**': 默认值为0，如果设置为一个大于0的整数，表示两个下载批次之间等待的秒数
以下配置可以使得每下载600组数据就等待一分钟：

```python
>>> qt.configure(hist_dnld_delay=60, hist_dnld_delay_evy=600)
>>> qt.configure(hist_dnld_retry_cnt=3)  # 同时减少重试的次数以缩短报错前等待的时间，这个配置并不是必要的
```
按照上述方法设置后，每次下载数据时，即使使用并行下载的方式，`qteasy`也不会将所有任务同时提交给进程池，而是分批提交，等待一段时间后，再次提交下一批。

上述功能是在`qteasy`的`v1.1.11`版本中新增的，如果您的`qteasy`版本较低，请升级至最新版本。
