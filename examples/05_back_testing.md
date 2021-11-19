## Back Testing

## qteasy策略历史回测

本示例演示qteasy中的策略历史回测功能，覆盖以下内容：
* 回测交易区间的设置
* 交易费用的设置
* 选股策略的回测
* 择时策略的回测
* 回测结果的评价和分析

```python
import sys
sys.path.append('../')
import qteasy as qt
%matplotlib inline
```
```python
op = qt.Operator(timing_types=['dma'])
op.set_parameter('t-0', pars=(23, 166, 196))
op.set_parameter('s-0', (0.5,))
op.set_parameter('r-0', ())
op.info()
qt.configure(mode=1)
```
```
OPERATION MODULE INFO:
=========================
Information of the Module
=========================
Total count of SimpleSelecting strategies: 1
the blend type of selecting strategies is 0
Parameters of SimpleSelecting Strategies:
<class 'qteasy.built_in.SelectingAll'> at 0x7ff7230f9b38
Strategy type: SIMPLE SELECTING
Optimization Tag and opti ranges: 0 [(0, 1)]
Parameter Loaded: <class 'tuple'> (0.5,)
=========================
Total count of timing strategies: 1
The blend type of timing strategies is pos-1
Parameters of timing Strategies:
<class 'qteasy.built_in.TimingDMA'> at 0x7ff7230f9cc0
Strategy type: QUICK DMA STRATEGY
Optimization Tag and opti ranges: 0 [(10, 250), (10, 250), (10, 250)]
Parameter Loaded: <class 'tuple'> (23, 166, 196)
=========================
Total count of Risk Control strategies: 1
The blend type of Risk Control strategies is add
<class 'qteasy.built_in.RiconNone'> at 0x7ff7230f9da0
Strategy type: NONE
Optimization Tag and opti ranges: 0 []
Parameter Loaded: <class 'tuple'> ()
=========================
```
```python
res = qt.run(op, visual=True)
```
![backtest result](https://user-images.githubusercontent.com/34448648/123519279-be5f5500-d6dc-11eb-99c9-519785e3b8d1.png)

```python
qt.configure(asset_pool='000300.SH', 
             asset_type='I',
             invest_start = '20080101',
             invest_cash_dates = None)
res=qt.run(op)
```

![backtest result](https://user-images.githubusercontent.com/34448648/123519314-f9618880-d6dc-11eb-9025-7dab3dcfcdeb.png)

```python
qt.configure(asset_pool='000300.SH', 
             asset_type='I',
             invest_start = '20190312',
             invest_cash_dates = None)
res=qt.run(op)
```

![backtest result](https://user-images.githubusercontent.com/34448648/123519319-02525a00-d6dd-11eb-81fe-ba5cfcf8acb8.png)


```python
res=qt.run(op, 
           mode=1,
           asset_pool='000004.SH',
          invest_start='20190505',
          invest_end='20191231',
          invest_cash_dates=None)
```

![backtest result](https://user-images.githubusercontent.com/34448648/123519347-3cbbf700-d6dd-11eb-9ae8-087a8181aec4.png)

```python
qt.configure(asset_pool=['000004.SH', '000300.SH'], asset_type='I')
res=qt.run(op,
          invest_start='20190101',
          invest_end='20201221')
```
![backtest result](https://user-images.githubusercontent.com/34448648/123519395-9de3ca80-d6dd-11eb-9b15-8002e96dd0e2.png)

```python
qt.configure(asset_pool=['000001.SZ', '000002.SZ', '000005.SZ', '000006.SZ', '000007.SZ'], 
             asset_type='E',
             visual=True,
             print_backtest_log=False)
res=qt.run(op)
```
![backtest result](https://user-images.githubusercontent.com/34448648/123519400-ab00b980-d6dd-11eb-9acf-db1afa830640.png)
### 测试选股策略

使用内置选股策略进行测试

```python
op = qt.Operator(timing_types='long', selecting_types='finance', ricon_types='ricon_none')
all_shares = qt.stock_basic()
shares_banking = list((all_shares.loc[all_shares.industry == '银行']['ts_code']).values)
shares_estate = list((all_shares.loc[all_shares.industry == "全国地产"]['ts_code']).values)
print(f'选出全国地产股票的前十位为：\n{shares_estate[0:20]}')
print(f'这些股票的信息为：\n{all_shares[all_shares.ts_code.isin(shares_estate[0:20])]}')
```

```OUTPUT
选出全国地产股票的前十位为：
['000002.SZ', '000014.SZ', '000031.SZ', '000036.SZ', '000042.SZ', '000402.SZ', '000616.SZ', '000620.SZ', '000667.SZ', '000736.SZ', '000797.SZ', '000918.SZ', '001979.SZ', '002133.SZ', '002146.SZ', '600048.SH', '600067.SH', '600077.SH', '600162.SH', '600173.SH']
这些股票的信息为：
        ts_code  symbol  name area industry list_date
1     000002.SZ  000002   万科A   深圳     全国地产  19910129
11    000014.SZ  000014  沙河股份   深圳     全国地产  19920602
24    000031.SZ  000031   大悦城   深圳     全国地产  19931008
28    000036.SZ  000036  华联控股   深圳     全国地产  19940617
33    000042.SZ  000042  中洲控股   深圳     全国地产  19940921
73    000402.SZ  000402   金融街   北京     全国地产  19960626
188   000616.SZ  000616  海航投资   辽宁     全国地产  19961108
191   000620.SZ  000620   新华联   北京     全国地产  19961029
219   000667.SZ  000667  美好置业   云南     全国地产  19961205
273   000736.SZ  000736  中交地产   重庆     全国地产  19970425
307   000797.SZ  000797  中国武夷   福建     全国地产  19970715
388   000918.SZ  000918   嘉凯城   浙江     全国地产  19990720
454   001979.SZ  001979  招商蛇口   深圳     全国地产  20151230
585   002133.SZ  002133  广宇集团   浙江     全国地产  20070427
597   002146.SZ  002146  荣盛发展   河北     全国地产  20070808
2420  600048.SH  600048  保利地产   广东     全国地产  20060731
2437  600067.SH  600067  冠城大通   福建     全国地产  19970508
2445  600077.SH  600077  宋都股份   浙江     全国地产  19970520
2519  600162.SH  600162  香江控股   深圳     全国地产  19980609
2529  600173.SH  600173  卧龙地产   浙江     全国地产  19990415
```

```python
qt.configure(asset_pool=shares_banking[0:20],
             asset_type='E',
             reference_asset='000300.SH',
             ref_asset_type='I',
             opti_output_count=50,
             invest_start='20070101',
             invest_end='20181130',
             invest_cash_dates=None,
             trade_batch_size=1.,
             mode=1,
             log=False)
op.set_parameter('t-0', pars=(0, 0))
op.set_parameter('s-0', pars=(True, 'linear', 'greater', 0, 0, 0.4),
                 sample_freq='Q',
                 data_types='basic_eps',
                 sort_ascending=True,
                 weighting='proportion',
                 condition='greater',
                 ubound=0,
                 lbound=0,
                 _poq=0.4)
op.set_parameter('r-0', pars=(0, 0))
op.set_blender('ls', 'avg')
op.info()
print(f'test portfolio selecting from shares_estate: \n{shares_estate}')
qt.configuration()
qt.run(op, visual=True, trade_batch_size=100)
```

![backtest result](https://user-images.githubusercontent.com/34448648/123519435-e56a5680-d6dd-11eb-8f1d-debee0ddab88.png)