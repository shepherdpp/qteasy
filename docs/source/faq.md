# FAQ

## TABLE OF CONTENTS 问题目录

- [如何安装TA-Lib](如何安装TA-Lib)
- [python3.11环境下安装qteasy失败]()
- [连接数据库失败](在qteasy.cfg中添加配置信息后，为何仍然提示数据库连接失败)
- [系统提示建议安装sqlalchemy](从数据库中读取数据时，为什么会出现提示建议安装\`sqlalchemy\`\？)

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

```bash
$ brew install ta-lib
```

如果使用Apple Silicon芯片，可以使用：

```bash
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

更完整的TA-Lib的安装方法请参考[这里](https://pypi.org/prject/TA-Lib/)

---

## 在较高版本python环境中安装qteasy

解决方案是升级到最新的`qteasy`版本。较新版本的`qteasy`已经在`python`3.7 ~ 3.12环境中进行了测试，可以在这些环境中正常运行。

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
