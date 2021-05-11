# coding=utf-8
# database.py

# ======================================
# This file contains DataSource class, that
# maintains and manages local historical
# data in a specific folder, and provide
# seamless historical data operation for
# qteasy.
# ======================================

import numpy as np
import pandas as pd
from os import path
from qteasy import QT_ROOT_PATH

from .history import stack_dataframes, get_price_type_raw_data, get_financial_report_type_raw_data
from .utilfuncs import regulate_date_format, str_to_list, progress_bar, is_market_trade_day

from ._arg_validators import PRICE_TYPE_DATA, INCOME_TYPE_DATA
from ._arg_validators import BALANCE_TYPE_DATA, CASHFLOW_TYPE_DATA
from ._arg_validators import INDICATOR_TYPE_DATA
from ._arg_validators import COMPOSIT_TYPE_DATA

LOCAL_DATA_FOLDER = 'qteasy/data/'
LOCAL_DATA_FILE_EXT = '.dat'

# TODO: IMPROVE - 研究是否应该使用parquet文件格式取代feather：
# TODO:           feather的读取和存储速度均比parquet更快：读取耗时少75%，写入耗时少50%
# TODO:           但是parquet更适合于长期存储数据，feather适合于短期数据交换
class DataSource():
    """ The DataSource object manages data sources in a specific location that
    contains historical data.

    the data in local source is managed in a way that Historical Panels can be
    easily extracted in order to satisfy needs for qteasy operators specified
    by History objects, data can be firstly downloaded from online, and then
    all downloaded data, if they are downloaded by DataSource objects, are
    automatically saved and merged with local data source, and starting from the
    next time these data can be extracted directly from local files. unless
    the data does not exist locally or they are manually updated.

    local data files are stored in .csv or .hdf files, in the future SQL or Mongo
    DB can be used for large data management.

    """

    def __init__(self, **kwargs):
        """

        :param kwargs: the args can be improved in the future
        """
        pass

    def __str__(self):
        raise NotImplementedError

    def __repr__(self):
        raise NotImplementedError

    def __contains__(self, item):
        """ checks if elements are contained in datasource

        :return:
        """
        return None

    def __getitem__(self, item):
        """ get a data type from local data source

        :param item:
        :return:
        """
        return None

    @property
    def location(self):
        """ return the folder location

        :return:
        """
        return None

    @property
    def data_types(self):
        """ return all available data types of current data

        """
        return None

    @property
    def shares(self):
        """ return names of shares

        :return:
        """
        return None

    @property
    def date_range(self):
        """ return the date range of existing data

        :return:
        """
        return None

    @property
    def highest_freq(self):
        """ return the highest frequency of data

        :return:
        """
        return None

    @property
    def lowest_freq(self):
        """ return the lowest frequency of data

        :return:
        """
        return None

    def info(self):
        """ print out information of current object

        :return:
        """
        raise NotImplementedError

    def regenerate(self):
        """ refresh some data or all data in local files, meaning re-download
        all data online to keep local data up-to-date

        :return:
        """
        raise NotImplementedError

    def file_exists(self, file_name):
        """ returns whether a file exists or not

        :param file_name:
        :return:
        """
        if not isinstance(file_name, str):
            raise TypeError(f'file_name name must be a string, {file_name} is not a valid input!')
        return path.exists(QT_ROOT_PATH + LOCAL_DATA_FOLDER + file_name + LOCAL_DATA_FILE_EXT)

    def new_file(self, file_name, dataframe):
        """ create given dataframe into a new file with file_name

        :param dataframe:
        :param file_name:
        :return:
        """
        if not isinstance(file_name, str):
            raise TypeError(f'file_name name must be a string, {file_name} is not a valid input!')
        df = self.validated_dataframe(dataframe)

        if self.file_exists(file_name):
            raise FileExistsError(f'the file with name {file_name} already exists!')
        # dataframe.to_csv(QT_ROOT_PATH + LOCAL_DATA_FOLDER + file_name + LOCAL_DATA_FILE_EXT)
        dataframe.reset_index().to_feather(QT_ROOT_PATH + LOCAL_DATA_FOLDER + file_name + LOCAL_DATA_FILE_EXT)
        return file_name

    def del_file(self, file_name):
        """ delete file

        :param file_name:
        :return:
        """
        raise NotImplementedError

    def open_file(self, file_name):
        """ open the file with name file_name and return the df

        :param file_name:
        :return:
        """
        if not isinstance(file_name, str):
            raise TypeError(f'file_name name must be a string, {file_name} is not a valid input!')
        if not self.file_exists(file_name):
            raise FileNotFoundError(f'File {QT_ROOT_PATH + LOCAL_DATA_FOLDER + file_name + LOCAL_DATA_FILE_EXT} '
                                    f'not found!')

        # df = pd.read_csv(QT_ROOT_PATH + LOCAL_DATA_FOLDER + file_name + LOCAL_DATA_FILE_EXT, index_col=0)
        df = pd.read_feather(QT_ROOT_PATH + LOCAL_DATA_FOLDER + file_name + LOCAL_DATA_FILE_EXT)
        df.index = df['date']
        df.drop(columns=['date'], inplace=True)
        df = self.validated_dataframe(df)
        return df

    def overwrite_file(self, file_name, df):
        """ save df as file name or overwrite file name if file_name already exists

        :param file_name:
        :param df:
        :return:
        """
        if not isinstance(file_name, str):
            raise TypeError(f'file_name name must be a string, {file_name} is not a valid input!')
        df = self.validated_dataframe(df)
        # df.to_csv(QT_ROOT_PATH + LOCAL_DATA_FOLDER + file_name + LOCAL_DATA_FILE_EXT)
        df.reset_index().to_feather(QT_ROOT_PATH + LOCAL_DATA_FOLDER + file_name + LOCAL_DATA_FILE_EXT)
        return file_name

    # TODO: this function is way too slow, should investigate how to improve
    def merge_file(self, file_name, df):
        """ merge some data stored in df into file_name,

        the downloaded data are stored in df, a pandas DataFrame, that might
        contain more rows and/or columns than the original file.

        if downloaded data contains more rows than original file, the original
        file will be extended to contain more rows of data, those columns that
        are not covered in downloaded data, np.inf will be used to pad missing
        data to identify missing data.

        if more columns are downloaded, the same thing will happen as more rows
        are downloaded.

        :param file_name:
        :param df:
        :return:
        """
        original_df = self.open_file(file_name)
        new_index = df.index
        new_columns = df.columns
        index_expansion = any(index not in original_df.index for index in new_index)
        column_expansion = any(column not in original_df.columns for column in new_columns)
        if index_expansion:
            additional_index = [index for index in new_index if index not in original_df.index]
            combined_index = list(set(original_df.index) | set(additional_index))
            original_df = original_df.reindex(combined_index)
            original_df.loc[additional_index] = np.inf
            original_df.sort_index(inplace=True)

        if column_expansion:
            additional_column = [c for c in new_columns if c not in original_df.columns]
            for col in additional_column:
                original_df[col] = np.inf

        for col in new_columns:
            original_df[col].loc[new_index] = df[col].values
        self.overwrite_file(file_name, original_df)

    def extract_data(self, file_name, shares, start, end, freq: str = 'd'):
        """ 从文件中读取数据片段，指定股票代码、开始日期、结束日期和数据频率（数据频率必须低于文件所含数据的频率，否则会缺失数据

            数据中若存在NaN值，会原样返回

        :param file_name:   文件名
        :param shares:     需要读取的数据片段包含的股票代码
        :param start:      读取数据的开始日期时间
        :param end:        读取数据的结束日期时间
        :param freq:       读取数据的时间频率，该频率应该低于文件中所存储的数据的时间频率，例如
                                可以从频率为'd'的文件中读取'w'或者'q'的数据，反之则会出现缺失数据
        :return:
            DataFrame:     包含所需数据片段的DataFrame，行标签为日期时间，列标签为股票代码
        """
        expected_index = pd.date_range(start=start, end=end, freq=freq)
        expected_columns = shares

        df = self.open_file(file_name)

        index_missing = any(index not in df.index for index in expected_index)
        column_missing = any(column not in df.columns for column in expected_columns)

        if index_missing:
            additional_index = [index for index in expected_index if index not in df.index]
            df = df.reindex(expected_index)
            df.loc[additional_index] = np.inf

        if column_missing:
            additional_column = [c for c in expected_columns if c not in df.columns]
            # print(f'adding new columns {additional_column}')
            for col in additional_column:
                df[col] = np.inf

        extracted = df[expected_columns].loc[expected_index]

        return extracted

    def validated_dataframe(self, df):
        """ checks the df input, and validate its index and prepare sorting

        :param df:
        :return:
        """
        if not isinstance(df, pd.DataFrame):
            raise TypeError(f'data should be a pandas df, the input is not in valid format!')
        try:
            df.rename(index=pd.to_datetime, inplace=True)
            df.sort_index()
            df.index.name='date'
        except:
            raise RuntimeError(f'Can not convert index of input data to datetime format!')
        return df

    def update(self):
        """ download the latest data in order to make local data set up-to-date.

        :return:
        """
        raise NotImplementedError

    def file_datetime_range(self, file_name):
        """ get the datetime range start and end of the file

        :param file_name:
        :return:
        """
        df = self.open_file(file_name)
        return df.index[0], df.index[-1]

    def file_columns(self, file_name):
        """ get the list of shares in the file

        :param file_name:
        :return:
        """
        df = self.open_file(file_name)
        return df.columns

    # following methods are secondary tier

    def share_datetime_range(self, dtype, share):
        """

        :param dtype:
        :param share:
        :return:
        """
        raise NotImplementedError

    def get_and_update_data(self,
                            start,
                            end,
                            freq,
                            shares,
                            htypes,
                            asset_type: str = None,
                            adj=None,
                            parallel=None,
                            delay=None,
                            delay_every=None,
                            progress=None,
                            refresh=False):
        """ 临时函数，根据需要从本地文件中读取股票的历史数据，并检查数据是否存在，如果数据在指定的区间不存在，则
        从网上下载数据并合并到本地文件中。

            目前临时使用，效率极低，且不符合单一功能原则，将过多功能揉杂在此，本函数需要重构

        :param start:   需要获取的历史数据时间起点
        :param end:     需要获取的历史数据时间终点
        :param freq:    需要获取的历史数据的时间频率，'d', 'q' 等
        :param shares:  需要获取的历史数据的股票代码或资产代码
        :param htypes:  需要获取的历史数据类型
        :param asset_type:
                        需要获取历史数据的股票或投资产品类型
                            'E'
                            'I'
                            'FD'
                            'F'
        :param adj:     价格数据复权方式，'none'
        :param parallel:在线获取数据时的工作线程数量
        :param delay:   在线获取数据的工作延迟时间
        :param delay_every:
                        在线获取数据时的工作延迟间隔
        :param progress:是否显示工作进度条

        :param refresh: bool, 是否强制在线获取数据，为True时重新下载最新数据，并覆盖已有的数据

        :return:
            HistoryPanel
        """
        all_dfs = []
        if isinstance(htypes, str):
            htypes = str_to_list(input_string=htypes, sep_char=',')
        if isinstance(shares, str):
            shares = str_to_list(input_string=shares, sep_char=',')
        if asset_type is None:
            asset_type = 'E'
        if adj is None:
            adj = 'none'
        if delay is None:
            delay = 0
        if progress is None:
            progress = True

        i = 0
        progress_bar(i, len(htypes), f'total progress count: {progress_count}')
        data_downloaded = False
        for htype in htypes:
            file_name = htype
            if freq.upper() != 'D':
                file_name = file_name + '-' + freq.upper()
            if asset_type.upper() != 'E':
                file_name = file_name + '-' + asset_type.upper()
            if asset_type.upper() == 'E' and adj != 'none':
                file_name = file_name + '-FQ'

            i += 1
            progress_bar(i, len(htypes), 'extracting local file')
            if self.file_exists(file_name) and (not refresh):
                df = self.extract_data(file_name, shares=shares, start=start, end=end)
                df.dropna(how='all', inplace=True)
            else:
                df = pd.DataFrame(np.inf, index=pd.date_range(start=start, end=end, freq=freq), columns=shares)
                for share in [share for share in shares if share not in df.columns]:
                    df[share] = np.inf
            # 一次性下载所有缺数据的股票的历史数据
            # 找到所有存在inf值的shares
            shares_with_inf = list(df.columns[np.where(np.isinf(df).any())])
            if len(shares_with_inf) > 0:
                online_data = {}
                data_downloaded = True
                if htype in PRICE_TYPE_DATA:
                    # get price type data online
                    online_data = get_price_type_raw_data(start=start,
                                                          end=end,
                                                          freq=freq,
                                                          shares=shares_with_inf,
                                                          htypes=htype,
                                                          asset_type=asset_type,
                                                          adj=adj,
                                                          parallel=parallel,
                                                          delay=delay,
                                                          delay_every=delay_every,
                                                          progress=progress,
                                                          prgrs_txt=f'Downloading data: "{htype}"')
                if htype in CASHFLOW_TYPE_DATA + INDICATOR_TYPE_DATA + BALANCE_TYPE_DATA + CASHFLOW_TYPE_DATA:
                    # download financial report type data
                    inc, ind, blc, csh = get_financial_report_type_raw_data(start=start,
                                                                            end=end,
                                                                            shares=shares_with_inf,
                                                                            htypes=htype,
                                                                            parallel=parallel,
                                                                            delay=delay,
                                                                            delay_every=delay_every,
                                                                            progress=progress,
                                                                            prgrs_txt=f'Downloading data: "{htype}"')
                    online_data = [d for d in [inc, ind, blc, csh] if len(d) > 0][0]
                # 现在所有所需的数据都已经下载下来了。且存储在一个dict中，且keys为股票代码
                # 下面循环把所有下载下来的online_data 覆盖到下载下来的df中
                j = 0
                for share_code in online_data:
                    progress_bar(j, len(online_data), f'Writing online data: {share_code}')
                    if not online_data[share_code].empty:
                        df[share_code] = online_data[share_code]

            progress_bar(i, len(htypes), 'Writing data to local files')
            if data_downloaded:
                if self.file_exists(file_name):
                    self.merge_file(file_name, df)
                else:
                    self.new_file(file_name, df)
            progress_bar(i, len(htypes), 'Extracting data')
            df = self.extract_data(file_name, shares=shares, start=start, end=end)
            with pd.option_context('mode.use_inf_as_na', True):
                df.dropna(how='all', inplace=True)
            all_dfs.append(df)

        hp = stack_dataframes(dfs=all_dfs, stack_along='htypes', htypes=htypes)
        return hp
    