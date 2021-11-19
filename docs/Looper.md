### sub module Looper: 
Looper Module simulates trading transactions and provide historical trading simulation results with taking into consideration of trading rules, trading costs and time effects

The whole work is done in iterations. in order to speed up the iteration the dataframe is converted to an ndarray with using nditer as a fast iteration tool, further, the storage structure of the ndarray is properly set so that external loop can be used to loop over every row of the data frame instead of looping over each item in the matrix, thus the efficiency is high
##### step1: the operation list
the operation table listed all operations (buy-in or sell-out) in a time history list, the data is created in the Op module, as proposed operation signals. mind that the operation dates are sparse, that means we don't need to iterate over each open date during the whole history period

date | 000001 | 600848 | 600519 | 002442 
:-- | :--: | --:|:--: |:-- 
2019-01-01 | 0.2 | 0 | 0|0
2019-01-02 | 0 | 0.3 | 0 |0
2019-02-12 | 0 | -1 |0 |0
2019-02-13 | 0 |  0| 1 |0

##### Step2: the price matrix
the price history table contains historical price data of related investment products or shares:

we will have to extract partial of the data in a way that the dates of extracted records fit that of the operation list, in this way two lists are aligned and there is a row-to-row match of dates between two lists. therefore, when we iterate over two tables there's no need to worry about dates, and thus make it possible to use pure ndarrays with nditer

here's the original historical price list:

date | 000001 | 600848 | 600519 | 002442 
--| -- |--|--|--
2019-01-01 |1| 33.5 | 715.2 | 3.45
2019-01-02 |1| 34.5 | 720.3 | 3.57
2019-01-03 |1| 35.2 | 730.2 | 3.77
2019-01-04 |1| 35.7 | 720.3 | 3.79
... | ... | ... | ... | ...
2019-02-12 |1| 39.45 | 812.5 | 5.99
2019-02-13 |1| 40.15 | 828.1 | 6.24
2019-02-14 |1| 41.52 | 855.3 | 6.45

the extracted historical price data will have exactly the same set of date labels as the operation list: 

date | 000001 | 600848 | 600519 | 002442 
--| -- |--|--|--
2019-01-01 |1| 33.5 | 715.2 | 3.45
2019-01-02 |1| 34.5 | 720.3 | 3.57
2019-02-12 |1| 39.45 | 812.5 | 5.99
2019-02-13 |1| 40.15 | 828.1 | 6.24

##### Step3: iteration
before iteration above two tables are converted to ndarrays, and then use nditer plus external loop to enables us realize fast row-by-row iteration. in order to realize row-by-row or column-by-column iteration the ndarray should be stored in the memory differently as how external loop is set to carry out, meaning, if the ndarray is stored in memory in C-order then external loop should be carried out in Fortran-order and vise versa. therefore, we can not just conver the dataframe into ndarray by df.value, instead, we have to explicitly convert the DF into an array with np.array() with order = 'F' and loop with order = 'C', this will give us the desired result. if we would like to loop column-by-column then the array should be stored in C order and loop with 'F' order

with above setting, we will be able to carryout fast iteration with each row of the two dataframes being extracted at a time:

the share prices are extracted row by row, with prices of each share in the same day, forming a vector of float numbers, the price vector $ V_p$:

iteration steps | 000001 | 600848 | 600519 | 002442 
--| -- |--|--|--
step 1 -> |1| 33.5 | 715.2 | 3.45
step 2 -> |1| 34.5 | 720.3 | 3.57
step 3 -> |1| 39.45 | 812.5 | 5.99
step 4 -> |1| 40.15 | 828.1 | 6.24

thus in step 1: $$ V_p = [1, 33.5, 715.2, 3.45] $$

a second vector, the operations vector $V_o$, can also be extracted with the same manner from the operations matrix with all the operation signs of the same group of shares as in the price matrix:

iteration steps | 000001 | 600848 | 600519 | 002442 
:-- | :--: | --:|:--: |:--
step 1 -> | 0.2 | 0 | 0|0
step 2 -> | 0 | 0.3 | 0 |0
step 3 -> | 0 | -1 |0 |0
step 4 -> | 0 |  0| 1 |0

thus in step 1: $$V_o = [0.2, 0, 0, 0]$$

within each step of the iteration, above two vectors are extracted from each matrix to calculate all results.

##### Step 3.1 Iteration step:

In each iteration step, remaining cash, stock holdings and trading fee or trading costs are calculated according to previous step results. In order to initialize the calculation, an initial cash amount and stock holdings, a vector in the same dimension as the operation vector and price vector, are to be set. Then the results are calculated in following steps:

######  1, Calculate cash gained by selling out shares:

One gains cash by selling out shares in each step, and shares to be sold in the step are defined by the negtive values in the $V_o$, that represents the percentage of stock holdings to be turned into cash, thus the cash-gained $C_g$ and stock amount sold $AS$ can be calculated like this. in the fomular $AP_i$ is i-th element in previous stock holding amount Vector, $AS_i$ is the i-th element of Amount sold vector, $O_i$ is the i-th element in $V_o$, $P_i$ is the i-th element in $V_P$, and R_s is the trade cost rate of selling: 
$$AS_i = AP_i * O_i, where: O_i < 0 $$
$$C_g = \sum_{i=o}^{n}AS_i * P_i * (1 - R_s), where: O_i < 0 $$ 

###### 2, Calculate the cash spent and stock amount aqcuired:

After aqcuiring cash from stock amount sold, stock amount purchasing or aqcuiring and cash spent $C_s$ can be calculated as following: in the fomular V is the vector of Value of stock to be purchased, $PV$ is previous total value of investment, $O$ is the operation vector, $AG$ is amount purchased, $R_p$ is the purchase cost rate
$$V_i = PV * O_i, where: O_i > 0$$
$$AG_i = \frac{V_i}{P_i * (1 + R_p)}, where: O_i > 0$$
$$C_s = \sum_{i=0}^{n}AG_i * P_i * (1 + R_p), where: O_i > 0$$

In above fomulars, $ \sum V_i$ might not be the same as $ C_s $ because the actual purchased amount of stock might not be the same as that intended, due to the reason of purchasing quantity limitations, for example, given stock price 15 and intended purchasing value 10000, Amount gained $AG$ would be 10000 / 15 = 666.67 shares which, however, is not valid in current stock market, which allows the shares to be purchased in the multiple of 100, thus actually only 600 shares are purchased, thus $C_s = 600 * 15 = 9000$
###### 3, Calculate period end Stock amounts, cash, and trade cost

After calculationg of cash change and amounts change in above steps, period-end cash $C$ and amounts $A$ can be calculated:
$$C = C_p - C_s + C_g$$
$$A = AP + AG - AS$$
the trade cost is calculated by cumulating all the cost in each transaction of the same period:
$$fee = \sum_{i=0}^{n}Cs_i * R_p + \sum_{i=0}^{n}Cg_i * R_s$$

with above said, the looper takes total cash value, and stock holding amount from previous period as input, together with the operation codes and stock prices of current period, calculates what's after transactions: the cash and new amounts of stock holdings, which, in turn, will be used for next round of calculation. Thus a looper step function is compiled to complete all the work in one step, and numpy iterator np.nditer() is employeed to extract every row of data from the price and operation matrix, calculating transaction results. 

###### 4, Cash investment plan (FUNCTION TO BE COMPLETED!!)

In the simplest case, cash investment can be viewed as one time investment at the beginning of whole investment period. In this looping model, a simple initial cash value is asigned to the looper iteration. however, a more sufisticated solution of simulating cash investment is a cash plan table, that contains the amount of cash investment or extraction on different dates. 

date | cash 
:-- | :--: 
2019-01-01 | 20000
2019-02-12 | 10000 

before looping iteration the cash investment table is also converted into numpy ndarray that has the same number of rows of data as the operation / price matrix, further, the dates of each row are also aligned with that of the other two matrices, so that the correct value of cash can be extracted while date comparison is not needed:

date | cash 
:-- | :--: 
2019-01-01 | 20000
2019-01-02 |0
2019-02-12 | 10000 
2019-02-13 |0

date | cash 
:-- | :--: 
Step 1 -> | 20000
Step 2 -> |0
Step 3 -> | 10000 
Step 4 -> |0

then during the iteration, the value of cash extracted from the ndarray can be simply added to the total cash in each period $C_{Inv}$ is the value of invested cash in the period:
$$C = C_p =C_s + C_g + C_{Inv}$$

##### Step 4, output of results
with iterations of looping over historical/operational data the result matrix can be created also as an ndarray of stock holding amounts and list of cash, total investment values in each period. these matrices contains adequate infomration for most types of performance analysis and assessments, however, sometimes it is required fo display or visualize the complete historical list or convert current data in a different historical frequency.

Thus a special function is created to complete all the data that has been removed because their operation codes are empty. This task is fairly easy because since there are no operation codes during these days the stock holding amount and cash will remail the same, thus value can be easily calculated.