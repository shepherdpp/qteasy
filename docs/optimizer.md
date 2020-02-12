### Sub Module Optimizer:
given a portfolio and historical data, find out optimal set of strategy parameters in a way that generates best result given by one of the evaluation functions. This module automatically detects all the parameters that need to be optimized for the strategy, or take as input part of the parameters to optimize, adjust the paramters systematically and repetitively feed the paramters into the strategy signal generator and calculates Looping results on given historical data sets. by comparing looping evaluation results from each and every epoch of tests, the Optimizer module finally decides and output the parameters that generates the best looping results.

This module contains multiple sub-modules and components:

* **Space Class**: that defines the parameter vector space in which optimizer searchs for optimal points, the space can be discret or continuous, or even enumerates of objects, Space class defines the space and create list of extracted points for optimization
* **Evaluation module**: it evaluates the results provided by Op and Loop module, by providing result of KPI
* **Optimization module**: depending on which optimizing algorithm is chosen, extracts points from the searching space and calculates their performances by applying Op, Looper and Evaluator, and finds out the global optimal, local optimal or near optimal points.

#### Space Class
Space Class generates and operates on parameter spaces that contain all possible combinations of parameter elements. For example, the typical DMA timing strategy is defined by three different parameters: (sma, lma, m): 
1. **sma**: the short moving average window
1. **lma**: the long moving average window
1. **m**: the difference average window

All of the three parameters are integers that ranging typically from 1 to 300, then complete set of MACD parameter is a tuple of three integers and can be seen as a point in a typical three dimensinal space so called the **Parameter Space**, and the parameter space of MACD strategy is defined, according to the character of MACD strategy, as that formed by all the integer points in 3-D space whose coordinates ranges between 1 to 300, and each dimension of the space, representing one element of parameters, is defined as an **Axis Object**, in which the range of possible values are defined.

In the MACD space, the points in the space are discrete and the space is a so-called **Discrete space**. if any of the parameters is a real number, for example, the strategy "N day percent drop", the percentage of N-day drop can be any real number, the space thus contains a **Continuous Axis**, which means coordination of points in the space can be any number.

Apart from pure number axis, the Space class also supports an enumerate type of axis, that contains a variaty of different type of data, and can be used flexibly. For example, the cross line strategy has a txt type of parameter ('buy' or 'sell'), which can be described as an enumerate axis, representing two possible values of this parameter. 

The dimension of the parameter space depends on strategy. A space object contains multiple Axis objects, representing one dimension or one element in the parameter group, each containing either upper and lower boundary of possible value of the parameter element, or an enumeration of all possible values. 

#### Iteration over space

##### Uniformal Iteration
The major output of a space object is an iterator on all or a sub set of its elements, determined by a key extraction factor that is called step size, meaning the distance between two neibouring extracted parameter data points. For example, a simple 2-dimensional space may contain all possible interger pairs from (0, 0) to (100, 100), and can be written down as a matrix like this: 

\begin{array}{ccc}
(0,0)&(0,1)&(0,2)&\dots&(0,100)\\
(1,0)&(1,1)&(1,2)&\dots&(1,100)\\
(2,0)&(2,1)&(2,2)&\dots&(2,100)\\
\vdots&\vdots&\vdots&\ddots&\vdots\\
(100,0)&(100,1)&(100,2)&\dots&(100,100)\\
\end{array}

Extracting data from above parameter space with a step factor of 5 means to generate a sub set of parameter pairs along every axis by selecting the items with an incremenets of 5, e.g, following points are selected: 

\begin{array}{ccc}
(0,0)&(0,5)&(0,10)&\dots&(0,100)\\
(5,0)&(5,5)&(5,10)&\dots&(5,100)\\
(10,0)&(10,5)&(10,10)&\dots&(10,100)\\
\vdots&\vdots&\vdots&\ddots&\vdots\\
(100,0)&(100,5)&(100,10)&\dots&(100,100)\\
\end{array}

which resulting in a much smaller set of data that are uniformly distributed over the whole parameter space. of cause, the step factor can be set to 1 to create a sub-set of parameters which are exactly the same as the whole space. in case of continuous parameter space, such as the space containing all real number pairs between (0, 100), there are indefinete number of points in the space, and the step factor can be set to between 0 and 1 to provide a fairly large subset of space, for example, extracted subset from above mensioned space with step factor of 0.2 will end up with a sub set of parameters as following:

\begin{array}{ccc}
(0.0,0.2)&(0.0,0.4)&(0.0,0.6)&\dots&(0.0,100.0)\\
(0.2,0.2)&(0.2,0.4)&(0.2,0.6)&\dots&(0.2,100.0)\\
(0.4,0.2)&(0.4,0.4)&(0.4,0.6)&\dots&(0.4,100.0)\\
\vdots&\vdots&\vdots&\ddots&\vdots\\
(100.0,0.2)&(100.0,0.4)&(100.0,0.6)&\dots&(100.0,100.0)\\
\end{array}

In case of an enumeration type of Axis, the step factor works as well (the second parameter is an enumerate Axis containing letters 'A', 'B', 'C', ... 'Z'):

\begin{array}{ccc}
(0,A)&(0,F)&(0,K)&\dots&(0,U)\\
(5,A)&(5,F)&(5,K)&\dots&(5,U)\\
(10,A)&(10,F)&(10,K)&\dots&(10,U)\\
\vdots&\vdots&\vdots&\ddots&\vdots\\
(100,A)&(100,F)&(100,K)&\dots&(100,U)\\
\end{array}

##### Random Iteraiton (Montecarlo)

For any type of space, random extraction or iteration over its elements is available as well. Instead of step size in the uniform iteration, the total number of points to be extracted is provided as key parameter of extraction. For example, one can extract 16 points randomly from a 2D space [(0, 1), (0, 1)]:

\begin{array}{ccc}
(0.05 , 0.955)&(0.726, 0.381)&(0.069, 0.89 )&(0.848, 0.782)\\
(0.122, 0.233)&(0.255, 0.371)&(0.26 , 0.496)&(0.033, 0.576)\\
(0.764, 0.068)&(0.728, 0.236)&(0.221, 0.949)&(0.063, 0.641)\\
(0.635, 0.706)&(0.499, 0.236)&(0.984, 0.336)&(0.171, 0.896)\\
\end{array}

Random or Montecarlo extraction works as well for Spaces containing descrete and enumerate types of Axis

##### Conversion to Iterators

The points extracted from Spaces are packed into an iterator object, so that all of the points in the itertor will be sent to Operation and Looper module for investment operation creation and result simulations. the module itertools is imported to do so. 

#### Evaluation Module

To find out the optimal strategy parameters, the output of investment simulation should be evaluated in a certain way. There are multiple different types of evaluation methods can be adopted, each with its own advantages and disacvantages. choose carefully between those evaluation methhods might help identify the best strategy. 

All the evaluation methods are defined in the evaluation module as functions that take as input the complete historical investment operation record, and output a float number, the so called performance indicator, that represents the performance of the parameters.

##### Final Value (FV)

Final value is the most natural and strait forward indicator of the performance of strategy. just by simply taking the total value of all investment products and cash as the value of evaluation function output, we can conclude that the strategy is performing better if the FV is higher, of cause the investment period and initial investment should be exactly the same to make sure and apple-to-apple comparison.

#### Optimization Module

Optimization is the process of searching for the best performing parameter of a given strategy in the parameter space, normally, consisting millions or billions of legal combimations of parameters. The target, defined as the one or more set of parameters that generates the best performance on a given investment period with given investment initial plan over the whole space, is called the **Global Optimal** parameter, and is the ultimate goal of the process; however, due to the enormity of space and the size of parameter combinations to be checked and tested, normally we are also satisfied with a "good enough" set of parameters that performes better than enough number of its nabours, which is refered to as the **Local Optimal** parameter.

depending on the size, type and character of parameter spaces, there are multiple ways of searching for global or local optimal parameters. The Optimization Module consists of multiple optimization algorithms which, although varies a lot in many ways, employes the Space object to extract multiple parameters from the parameter space, sends parameters to evaluation module for performance evaluation by creating simulated investment result on pre-given historical period and investment plan, and somehow "washes away" sub-optimal parameters or climbs to the optimal results.

##### Exauhstive Searching

The Exauhstive searching algorithm is the simplest algorithm of all, that one just checks every and all possible parameter combinations in the parameter space, and compare their performances with each other one at a time. a performance pool, containing pre-given numbers of parameter sets, is created at the begining of the algorithm. Each and every parameter in the space is extracted and compared with all the parameters in the pool and put into the pool to replace the least performing parameter in the pool only if it out-performs it. After iteratively checking all the parameters in the space, the **GLABAL OPTIMAL** parameters are then found and stored in the pool.

The nature of exauhstive searching is global and slow, thus it makes this algorithm not suitable for very large parameter spaces, which may contain billions of parameters. if it takes 1 millisecond to check one set of parameter, checking all 1 billion sets of parameters will cost one million seconds, which is 11.6 days. In such sircumstances, a sub-exauhstive searching algorithm should be employed to achieve balancing between performance and time. But in this case, Glocal optimal solution may not be garanteed, what we achieve finally will probably be only a local optimal.

There is a parameter of *step size* for the algorithm, which is 1 for default, controls the step size by which the algorithm extracts the neibouring points. setting this parameter to be more than 1, for instance, 2, will reduce the total number of parameters to be checked to $2^n$ -th of how much it would have been if the step size were 1, but of cause that means the Global optimal parameter may simply be omitted during iteration. Nevertheless, even in the worst case the global optimal parameter will only be 1 step away from one of the checked value, which will very likely to be one of the local optimal unless the function of the performance on the parameter space is purely random and are irelevant to each other.

Another drawback of the exaustive searching algorithm is that it does not work for continuous Axis, simply because it is impossible to exauhst all the real numbers on the number axis. no matter how small or how short the distance between lower and upper boundary is. Applying exaustive searching algorithm on a space containing continuous axis  means taking numbers along the continuous axis at a step of 1, such as: 

$$1.5, 2.5, 3.5, 4.5, 5.5, \dots, 100.5$$

The parameter of *stepsize* can be either a number, in such case the algorith automatically applys the same step size along all the axis of the space, or a list containing multiple numbers, in which case different step sizes are applied on the axes. The length of the list of numbers does not have to be the same as the dimension of the space, the module pads missing numbers with 1 or omitts the eccessive numbers given in the list. For example, if a *stepsize = [2, 2]* is given for a 4-dimensional space, the step sizes are automatically padded to [2, 2, 1, 1] and then applied to four dimensions of the space respectively

##### MonteCarlo Searching

MonteCarlo Searching algorithm is one that searches only part of the parameter space, by uniformally or randomly picking up points from the parameter spaces, a fairly good coverage of points in the space is guarenteed and thus allow us a very good chance of achieving a value very close to the global optimal or next to the global optimal value while in the same time drastically reducing the number of parameter sets need to be checked. 

Two major forms of MonteCarlo searching can be performed according to how the parameter points are taken out from the space, a uniform one and random one. In former form a step size is given as the key parameter of the algorithm and point count for the latter. Now the uniformal way of extraction is integrated with the exauhstive searching, and the MonteCarlo searching here provides only random selection of points out of the space.

This Algorithm does not work directly by letting you to specify the total number of points to take from the space, instead, it requires the user to specify a list of numbers , each representing the number of coordinates to be taken randomly from each of the axis of the space, and combine all these coordinates into parameter sets. However, the algorithm automatically pads single number into complete list of numbers by duplicate the same number on each dimension. For example, `point_count = 100` for a 3-D space equals to `point_count = [100, 100, 100]`, and 100 number of random points will be taken out on each axis.

Therefore, if `point_count = [100, 100, 100]` is given for a 3-D space then one million ($100*100*100=1,000,000$) total points will be extracted from the space. By allowing and requesting users to specify for each axis the number of coordinates to be extracted provides more manipulation and flexibility to the users.

It can be assumed that, due to its randomality nature, the number of points taken out from each axis is not limited to the total count of points in the axis. That means if one of the axis has only 100 points, one can still specify 200 as the point count of this parameter, it means that a number will be randomly picked out of the 100 numbers for 200 times, and then coordicate with other numbers or points picked from other axis, forming sets of parameters.

Apart from how the parameters are taken and generated from the space, the following steps of optimization are exactly the same as those of exauhstive searching: A pool object is designated to store all the result generated, compared and out-performed existing parameters, and finally, by washing our all sub-performing parameters, identify all the best parameters extracted from the space.

Further, since the points are taken randomly from the space, the MonteCarlo searching is suitable for all types of axes.

##### Incremental Steped Searching (ISS)

The ISS algorithm is designed to seek a better balance between closeness to the **Global Optimal** and total number of parameters to be checked, which is, to some extent, already attended to in the step-sized exauhstive searching and MonteCarlo searching. The ISS algorithm takes one big step forward if the space meets a certain criteria and achieves much faster execution speed and a very good chance to achieve the **GLOBAL OPTIMAL**

The assumption for the algorithm works is that the extent of continuity of performances of parameters in the space. Here continuity is defined as one of the key features of the performances of the points taken from the space: if the performance value of a point from the space is relatively close to those of its neibours, and the distance between them tends to increase as compare to further neibours, then we can say that the performance of parameters are largely continuous. In other words, the continuity reveals the fact that high performers are somewhat close to each other, and low-performers likewise.

Imagine a map with altitude of terrain marked on it, the altitude of any point on the coordination of the map represents the performance of the parameter consisted with the two numbers longtitude and latitude. In most of the maps the terrains are continuous in a way that very sharp cliffs are very rare, thus the altitude of any two points very closed to each other are also close to each other. And in a large birds view we can see mountains and valleys over the terrain, the work of looking for the global optimal point is equal to finding the ultimate point of mountain in the area.

Looking for the ultimate point in the area using exauhstive searching algorithm means check the altitude of all points on the intersections of a mesh of 1 meter grid over the area, which obviously, is a tiresome job, because there might be billions of points to check. 

However, the facts that the terrains are continuous allows us to adopt a much faster way of pin pointing the exact location of the ultimate peak. intuitively, we can start with a very rough searching over the area by searching the intersections of a mesh of grids with much larger distance, for example, of 1000 meters. It will be very unlikely that one of the points is the exact ultimate, but because of the continuity character of the terrain, the higher points that we found might well be more likely to be closer to the ultimate peak, and the beauty of searching at such large step size is that the number of searching points are very little, and we can very quickly find multiple points that are higher than other points.

Next, we will re-start the searching at a smaller step size, let's say, of 200 meters, but only "around" those points whose altitudes are higher than the others. The reason why we don't search only the perenfersis of **the current highest point** is that the current highest may only close to a local peak instead of a global peak. thus we will search all the neibouring area of multiple high points. Because we have already start from a few higher points, we may say we start from either half way up the mountains or already on the mountains. we may safely conclude that if we search only around those points it is more likely for us to be closer to the ultimate points, which we will because in the second round of searching we simply remove those points that are lower, in which case means we are farther away from the peak, and keep those points that are higher, probably higher than current ones.

The searching like this will go in rounds, with each round reduced size of searching step, and only on the higher points found in previous round. In such iterations we finally converge to the single point or multiple points of highest peak when the searching step reduces to 1 meter and searching area to 1.

In order to ensure a proper coverage of searching area a practical strategy is to start searching with step size of $2^n$, and keep 50 highest points, and in next rounds of searching reduce the step size by half and search the area around each highest points from previous round across the distance of $2^n$ over every axis, until step size is 1. In this way we can guarrantee complete coverage of searching area.

The practical algorithm has following four parameters:

- **output_count** the number of points around which the neibours are searched in the next round
- **init_step** the searching step size in the first round of searching
- **inc_step** incremental step, the multiply factor with which step size divides after each round
- **min_step** minimum step size, stop the cycle while current step size is smaller than minimum size

Once initial step size is decided, the algorithm performes the first round of searching just like exauhstive searching with step size equal to initial step size, and store the same number of results in the pool as output_count. For each of the results in pool, a sub space is created that covers just its neibouring area. After one round of searching, all of the sub spaces are searched with smaller step size, and the best results of all sub spaces are stored in the pool, again. Above process is repeated until the step size is too small.

The performance of ISS can be very high -- if parameters properly chosen, ISS can be thousands of times faster than exauhstive searching, while still keep reasonably good hit rate on global optimal. The largest concern of using ISS is that the performance function being not continuous. Further, the selection of initial step size is also critical, the more continuous the performance function is, the larger the initial step size may be. While larger initial step size helps a lot in reducing total calculating time, it increases the chance for missing the global optimal point. However, increasing output_count might mitigate that effect.

Finally, although the ISS algorithm does imporve a lot the performance of exauhstive searching algorithms, it does not change foundamentally its exauhstive searching nature, and does not exceed its limitation: that these algorithms are not suitable for ultra-dimensional parameter spaces. For normal and traditional investment strategies the parameter dimensions are normally small, traditionally people can not process parameter which is more than 10-dimensional. 

However, new methods and algorithms related to machine learning and big data started to utilize ultra-large parameter spaces. Imagine that we would like to find out the optimal operation in past 2000 trade days directly from all possible legal operations. Consider the simplest situation in which we can choose to buy, sell, or hold the investment product in each trade day, thus the parameter space is a 2000-D space with each dimension have 3 possible values: buy, sell, hold. Such ultra-huge space has $3^{2000}$ possible combinations and NONE of above algorithms is capable of solving the problem in a reasonable period of time. For such problems, new concepts has to be adopted, there are multiple machine learning algorithms are potentially possible 

##### Genetic Algorithm Searching (GA)

Genetic Algorithm is one of the algorithms that are capable of searching for global / local optimal in ultra-large spaces.

Genetic algorithm simulates the process of biological genetic hybriding and mutation that improves adaptivity of biological populations during the evolvement in given environment. The algorith takes place in multiple, in most cases thousands or even millions of, iterations, in which a "population" of parameters live or die, and reproduce at a certain percentage that is related to the adaptivity of each individule in the population, the higher one parameter performs, the higher the chance for it to give off sprint and survive, or vise versa. In other words, in each iteration, the high-performers are more likely to survive, and repreduce -- passing its own gene to the next generation -- and then given enough time of regeneration, the good genes -- the part of the parameter that tends to generate higher result -- will cumulate to an extent that formulate the global optimal solution in the space.

The algorithm starts with a fixed population randomly selected from the space, for example 1000 individule parameters. Each individule is evalated and its adaptivity is calculated according to its performance, based on which its surviving rate and repreducing rate being calculated. Then, following actions take place on each individule: 

- **SURVIVE**: that the individule will survive to the next generation
- **DIE**: that the individule will NOT survive to the next generation
- **REPREDUCE** that the individule will repreduce an offsprint, there are basically two different ways of reproducing:
   - **SWAPPING**: that the offspring is generated by combining part from individule A and the other part from individule B
   - **REPLACING**: that the offspring is generated by replacing a small part of the parent individule with a new random section
- **MUTATION**: that a small change is applied randomly on a single gene of the individule

##### Artificial Neural Networks (ANN)