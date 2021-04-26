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
        extracted.dropna(how='all', inplace=True)

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

    def get_and_update_data(self,
                            start,
                            end,
                            freq,
                            shares,
                            htypes,
                            asset_type: str = None,
                            parallel=None,
                            delay=None,
                            delay_every=None,
                            progress=None,
                            refresh=False):
        """ the major work interface of DataSource object, extracts data directly from local
        files when all requested records exists locally. extract data online if they don't
        and merges online data back to local files.

        :param start:
        :param end:
        :param freq:
        :param shares:
        :param htypes:
        :param asset_type:
        :param parallel:
        :param delay:
        :param delay_every:
        :param progress:

        :param refresh:
            bool, 是否忽略已有的数据，重新下载最新数据，并覆盖已有的数据
        :return:
        """
        # TODO: No file saving is needed if no new data is downloaded online
        all_dfs = []
        if isinstance(htypes, str):
            htypes = str_to_list(input_string=htypes, sep_char=',')
        if isinstance(shares, str):
            shares = str_to_list(input_string=shares, sep_char=',')
        share_count = len(shares)
        if asset_type is None:
            asset_type = 'E'

        i = 0
        progress_count = len(htypes) * len(shares) + len(htypes)
        progress_bar(i, progress_count, f'total progress count: {progress_count}')
        data_downloaded = False
        # import pdb; pdb.set_trace()
        for htype in htypes:
            file_name = htype
            if freq.upper() != 'D':
                file_name = file_name + '-' + freq.upper()
            if asset_type.upper() != 'E':
                file_name = file_name + '-' + asset_type.upper()

            i += 1
            progress_bar(i, progress_count, 'extracting local file')
            if self.file_exists(file_name) and (not refresh):
                df = self.extract_data(file_name, shares=shares, start=start, end=end)
            else:
                df = pd.DataFrame(np.inf, index=pd.date_range(start=start, end=end, freq=freq), columns=shares)
                for share in [share for share in shares if share not in df.columns]:
                    df[share] = np.inf
            data_index = df.index
            index_count = len(df.index)
            for share, share_data in df.iteritems():
                progress_bar(i, progress_count, 'searching for missing data')
                missing_data = share_data.iloc[np.isinf(share_data.fillna(np.nan)).values]
                i += 1
                progress_bar(i, progress_count, 'downloading missing data')
                if missing_data.count() > 0:
                    data_downloaded = True
                    missing_data_start = regulate_date_format(missing_data.index[0])
                    missing_data_end = regulate_date_format(missing_data.index[-1])
                    start = missing_data.index[0]
                    end = missing_data.index[-1]
                    if htype in PRICE_TYPE_DATA:
                        online_data = get_price_type_raw_data(start=missing_data_start,
                                                              end=missing_data_end,
                                                              freq=freq,
                                                              shares=share,
                                                              htypes=htype,
                                                              asset_type=asset_type,
                                                              parallel=parallel,
                                                              delay=delay,
                                                              delay_every=delay_every,
                                                              progress=False)

                    elif htype in CASHFLOW_TYPE_DATA + BALANCE_TYPE_DATA + INCOME_TYPE_DATA + INDICATOR_TYPE_DATA:
                        inc, ind, blc, csh = get_financial_report_type_raw_data(start=missing_data_start,
                                                                                end=missing_data_end,
                                                                                shares=share,
                                                                                htypes=htype,
                                                                                parallel=parallel,
                                                                                delay=delay,
                                                                                delay_every=delay_every,
                                                                                progress=False)
                        online_data = (inc + ind + blc + csh)

                    # 按照原来的思路，下面的代码是将下载的数据（可能是稀疏数据）一个个写入到目标区域中，再将目标区域中的
                    # np.inf逐个改写为np.nan。但是其实粗暴一点的做法是直接把下载的数据reindex，然后整体覆盖目标区域
                    # 就可以了。
                    # 这里是整体覆盖的代码：
                    if len(online_data) != 0:
                        if online_data[0] is not None:
                            # 注意，必须确保输出数据中所有的np.inf都被覆盖掉，因为如果输出数据中含有np.inf，将会影响到
                            # 非交易日的判断（目前非交易日是通过所有股价全部是np.nan来判断的），导致非交易日数据被输入到
                            # op.generate中，导致产生大量异常交易信号和异常数据
                            share_data[start:end] = online_data[0].reindex(share_data[start:end].index)[htype]
                        else:
                            print(f'Oops! online data for {share} is empty!')

            progress_bar(i, progress_count, 'Writing data to local files')
            if data_downloaded:
                if self.file_exists(file_name):
                    self.merge_file(file_name, df)
                else:
                    self.new_file(file_name, df)
            progress_bar(i, progress_count, 'Extracting data')
            df = self.extract_data(file_name, shares=shares, start=start, end=end)
            all_dfs.append(df)

        hp = stack_dataframes(dfs=all_dfs, stack_along='htypes', htypes=htypes)
        return hp
    