# FAQ

## 如何安装TA-Lib？

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
