# coding=utf-8
# ======================================
# File:     eastmoney.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2023-11-01
# Desc:
#   Interfaces to eastmoney data
# functions and api, as the default
# api in qteasy, emfuncs provides basic
# functions to acquire price k-lines.
# ======================================

from urllib.parse import urlencode
import pandas as pd
import requests


# eastmoney interface function, call this function to extract data
def acquire_data(api_name, **kwargs):
    """ eastmoney接口函数，根据根据table的内容调用相应的eastmoney API下载数据，并以DataFrame的形式返回数据"""
    func = globals()[api_name]
    res = func(**kwargs)
    return res


def gen_eastmoney_code(rawcode: str) -> str:
    """
    生成东方财富专用的secid

    Parameters
    ----------
    rawcode：str
    6 位股票代码按东方财富格式生成的字符串
    """
    if rawcode[0] != '6':
        return f'0.{rawcode}'
    return f'1.{rawcode}'


def get_k_history(code: str, beg: str = '16000101', end: str = '20500101', klt: int = 1, fqt: int = 1) -> pd.DataFrame:
    """
    功能获取k线数据
    Parameters
    ----------
    code : 6 位股票代码
    beg: 开始日期 例如 20200101
    end: 结束日期 例如 20200201
    klt: k线间距 默认为 101 即日k
        klt:1 1 分钟
        klt:5 5 分钟
        klt:101 日
        klt:102 周
    fqt: 复权方式
        不复权 : 0
        前复权 : 1
            后复权 : 2
    Return
    ------
    DateFrame : 包含股票k线数据
    """
    EastmoneyKlines = {
        'f51': 'datetime',
        'f52': 'open',
        'f53': 'close',
        'f54': 'high',
        'f55': 'low',
        'f56': 'vol',
        'f57': 'amount',
        # 'f58': '振幅',
        # 'f59': '涨跌幅',
        # 'f60': '涨跌额',
        # 'f61': '换手率',
    }
    EastmoneyHeaders = {

        'User-Agent':      'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; Touch; rv:11.0) like Gecko',
        'Accept':          '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Referer':         'http://quote.eastmoney.com/center/gridlist.html',
    }
    fields = list(EastmoneyKlines.keys())
    columns = list(EastmoneyKlines.values())
    fields2 = ",".join(fields)
    secid = gen_eastmoney_code(code)
    params = (
        ('fields1', 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13'),
        ('fields2', fields2),
        ('beg', beg),
        ('end', end),
        ('rtntype', '6'),
        ('secid', secid),
        ('klt', f'{klt}'),
        ('fqt', f'{fqt}'),
    )
    base_url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get'
    # base_url = 'https://push2his.eastmoney.com/api/qt/clist/get'
    url = base_url + '?' + urlencode(params)
    json_response = requests.get(
            url, headers=EastmoneyHeaders).json()
    data = json_response['data']
    import pdb; pdb.set_trace()
    klines = data['klines']
    rows = []
    for _kline in klines:
        kline = _kline.split(',')
        rows.append(kline)
    df = pd.DataFrame(rows, columns=columns)
    return df