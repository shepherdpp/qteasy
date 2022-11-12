## Basic Usage of qteasy

本示例演示了一个最常见的基金择时策略的优化过程，本示例演示了以下内容：
- 创建一个包含均线择时策略的`oeprator`对象，该对象包含的策略采用内置的'DMA‘择时策略
- 通过`qt.configure()`设置相关的环境变量
- 通过对过去10年左右的沪深300指数历史数据，对策略进行参数寻优，最终演示寻优后的结果

## Example Start 示例开始
首先我们导入qteasy模块

同时，为了在线打印图表，使用`matplotlib inline`设置图表打印模式为在线打印

```python
import qteasy as qt
```
### 配置qteasy的基本运行参数
qteasy的所有基本运行参数都可以在qt.configure()函数中设置：
- 投资回报率的对比数据采用沪深300指数
- 同时设置对比数据的数据类型为“I”

```python
qt.configure(benchmark_asset = '000300.SH', 
             benchmark_asset_type = 'IDX')
```

- 设置参与投资组合创建的股票池，因为是纯择时策略，因此设置股票池中只有一个沪深300指数，同样设置资产类型为“I” 指数。

```python
qt.configure(asset_pool = '000300.SH',
             asset_type = 'IDX')
```

### 获取金融数据


### 设置投资相关参数：
- moq为0，意味着不存在着必须买卖整数股的条件
- 默认的投资金额为10000元，投入日期为2006年4月6日
- 投资费率是一个Cost对象，以下设置意味着买入费率为千分之一点五，卖出费率为0，没有最低费用的限制，滑点为0

```python
qt.configure(trade_batch_size = 0)
qt.configure(invest_start = '20100105')
qt.configure(invest_end = '20201231')
qt.configure(invest_cash_dates = '20101231')
```