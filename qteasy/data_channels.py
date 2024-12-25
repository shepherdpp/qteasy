# coding=utf-8
# ======================================
# File:     data_channels.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2024-10-09
# Desc:
#   Definition of interface to
# acquire or download historical data
# that can be stored in the datasource
# from different channels such as
# tushare, yahoo finance, akshare, etc.
# ======================================

# functions to acquire data from different channels, such as tushare, akshare, etc.
# and convert them into pandas DataFrame that can be easily accepted and processed
# by and stored in the DataSource class.


TUSHARE_API_PARAM_COLUMNS = {
    'api',  # 1, 从tushare获取数据时使用的api名
    'fill_arg_name',  # 2, 从tushare获取数据时使用的api参数名
    'fill_arg_type',  # 3, 从tushare获取数据时使用的api参数类型
    'arg_rng',  # 4, 从tushare获取数据时使用的api参数取值范围
    'arg_allowed_code_suffix',  # 5, 从tushare获取数据时使用的api参数允许的股票代码后缀
    'arg_allow_start_end',  # 6, 从tushare获取数据时使用的api参数是否允许start_date和end_date
    'start_end_chunk_size',  # 7, 从tushare获取数据时使用的api参数start_date和end_date时的分段大小
}

TUSHARE_API_PARAMS = {
    'trade_calender': ['trade_cal', 'exchange', 'list', 'SSE,SZSE,BSE,CFFEX,SHFE,CZCE,DCE,INE,XHKG', '', '', '',],
    'stock_basic': ['stock_basic', 'exchange', 'list', 'SSE,SZSE,BSE', '', '', '',]
}

AKSHARE_API_PARAM_COLUMNS = {
    'akshare',  # 13, 从akshare获取数据时使用的api名
    'ak_fill_arg_name',  # 14, 从akshare获取数据时使用的api参数名
    'ak_fill_arg_type',  # 15, 从akshare获取数据时使用的api参数类型
    'ak_arg_rng',  # 16, 从akshare获取数据时使用的api参数取值范围
}

AKSHARE_API_PARAMS = {

}
