### QTeasy Module component: History Class

History is a module that manages historical data warehouse and creates historical data sets for specific shares and portfolios

this module uses a DataFrame that is called the "warehouse" to store and manage all historical data. a warehouse is a complete list of historical prices of one specific price type under one specific time interval. currently possible price types are [close. open, high, low, volume], and intervals are [daily, weekly, 30min, 15min]. thus there are 20 different warehouses stored on the disc that containing share historical prices of one of any possible combanation of price type and interval. for example, daily close price or weekly low prices

any segment of historical data can be extracted from warehouse but you have to open the warehouse first with warehouse_open() function, and then you can expend the warehouse or append new record to the warehouse by get_new_price() with tushare. one thing to keep in mind is that the prices downloaded with tushare are prices exclude rights, but rehabilitated prices are needed in the warehouse to run meaningful looping, thus get_new_price() finds out the last valid price of one specific share from the warehouse and then calculates rehabilitated price there on up to today

the class History has following public properties:

* History.

the class History has following public methods:

* History.info()
* History.warehouse_new()
* History.warehouse_open()
* History.warehouse_save()
* History.warehouse_close()
* History.warehouse_extract()
* History.warehouse_update()