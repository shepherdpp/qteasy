��          �               ,     -     J     Z     j     �     �     �     �  '   �  &        (     5  $  N  F   s     �     �  }  �     m     �     �     �  !   �     �            '   4  '   \     �     �  �  �  c   \  2   �     �   ![png](img/output_4_1_3.png) 1. 策略代码 2. 策略回测 买入批量：100股 创建自定义交易策略： 初始资金：100万 卖出批量：1股 回测参数： 回测时间为:2021-01-01到2022-12-31 回测时间：2021-01-01到2022-12-31 回测结果 指数增强选股策略 本策略以0.8为初始权重跟踪指数标的沪深300中权重大于0.35%的成份股. 个股所占的百分比为(0.8*成份股权重)*100%.然后根据个股是否: 1.连续上涨5天 2.连续下跌5天 来判定个股是否为强势股/弱势股,并对其把权重由0.8调至1.0或0.6 策略运行频率：每日运行 策略运行时间：每日收盘前 资产池：沪深300成份股 资产类型：股票 Project-Id-Version: qteasy 1.4
Report-Msgid-Bugs-To: 
POT-Creation-Date: 2025-03-03 20:50+0800
PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE
Last-Translator: FULL NAME <EMAIL@ADDRESS>
Language: en
Language-Team: en <LL@li.org>
Plural-Forms: nplurals=2; plural=(n != 1);
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8
Content-Transfer-Encoding: 8bit
Generated-By: Babel 2.15.0
 ![png](img/output_4_1_3.png) 1. Strategy code 2. Strategy backtest Purchase batch: 100 shares Create a custom trading strategy: Initial investment: 1 million Sell batch: 1 share Backtest parameters: Backtest time: 2021-01-01 to 2022-12-31 Backtest time: 2021-01-01 to 2022-12-31 Backtest results Enhanced Index Stock Selection This strategy tracks the index constituents of the Shanghai and Shenzhen 300 with an initial weight of 0.8. The percentage of individual stocks is (0.8 * constituent stock weight) * 100%. Then, according to whether the individual stocks: 1. rose for 5 consecutive days 2. fell for 5 consecutive days, to determine whether the individual stocks are strong stocks/weak stocks, and adjust their weights from 0.8 to 1.0 or 0.6. Frequency of strategy run: daily operation Time of strategy operation: before the close of each day Asset pool: Shanghai and Shenzhen 300 constituents Asset type: stocks 