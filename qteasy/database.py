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

from .history import stack_dataframes, get_price_type_raw_data, get_financial_report_type_raw_data
from .utilfuncs import regulate_date_format, str_to_list, progress_bar, is_market_trade_day

from ._arg_validators import PRICE_TYPE_DATA, INCOME_TYPE_DATA
from ._arg_validators import BALANCE_TYPE_DATA, CASHFLOW_TYPE_DATA
from ._arg_validators import INDICATOR_TYPE_DATA
from ._arg_validators import COMPOSIT_TYPE_DATA

LOCAL_DATA_FOLDER = 'qteasy/data/'
LOCAL_DATA_FILE_EXT = '.csv'


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
        return path.exists(LOCAL_DATA_FOLDER + file_name + LOCAL_DATA_FILE_EXT)

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
        dataframe.to_csv(LOCAL_DATA_FOLDER + file_name + LOCAL_DATA_FILE_EXT)
        # debug
        # print(f'\nIn func: new_file()\n'
        #       f'new file will be created, following data will be writen to disc as file name {file_name}:\n'
        #       f'{dataframe}')
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
            raise FileNotFoundError(f'File {LOCAL_DATA_FOLDER + file_name + LOCAL_DATA_FILE_EXT} not found!')

        df = pd.read_csv(LOCAL_DATA_FOLDER + file_name + LOCAL_DATA_FILE_EXT, index_col=0)
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

        df.to_csv(LOCAL_DATA_FOLDER + file_name + LOCAL_DATA_FILE_EXT)
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
        # print(f'merging file, expanding index: {index_expansion}, expanding columns: {column_expansion}')
        if index_expansion:
            additional_index = [index for index in new_index if index not in original_df.index]
            combined_index = list(set(original_df.index) | set(additional_index))
            # print(f'adding new index {additional_index}')
            original_df = original_df.reindex(combined_index)
            original_df.loc[additional_index] = np.inf
            original_df.sort_index(inplace=True)

        if column_expansion:
            additional_column = [c for c in new_columns if c not in original_df.columns]
            # print(f'adding new columns {additional_column}')
            for col in additional_column:
                original_df[col] = np.inf

        for col in new_columns:
            original_df[col].loc[new_index] = df[col].values
        # debug
        # print(f'values assigned! following DataFrame will be saved on disc as file name {file_name}:\n{original_df}')

        self.overwrite_file(file_name, original_df)

    def extract_data(self, file_name, shares, start, end, freq: str = 'd'):
        expected_index = pd.date_range(start=start, end=end, freq=freq)
        expected_columns = shares

        df = self.open_file(file_name)
        # debug
        # print(f'\nin extract_data() function from local file, df is read from file, before processing:'
        #       f'\ntype of df index is {type(df.index[0])}\n'
        #       f'the index of extracted data is\n'
        #       f'{df.index[:10]}\n'
        #       f'are they all trading date? \n'
        #       f'{all([is_market_trade_day(date) for date in df.index])}\n'
        #       f'first 30 indices are:\n'
        #       f'{df.index[:30]}')
        # df.info()

        index_missing = any(index not in df.index for index in expected_index)
        column_missing = any(column not in df.columns for column in expected_columns)

        if index_missing:
            additional_index = [index for index in expected_index if index not in df.index]
            # debug
            # print(f'\nIn extract_date from local file'
            #       f'\nexpected index is:\n{expected_index}\n'
            #       f'original index is:\n{df.index}\n'
            #       f'adding new index \n{additional_index}')
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

    def get_and_update_data(self, start, end, freq, shares, htypes, asset_type: str = 'E'):
        """ the major work interface of DataSource object, extracts data directly from local
        files when all requested records exists locally. extract data online if they don't
        and merges online data back to local files.

        :param start:
        :param end:
        :param freq:
        :param shares:
        :param htypes:
        :param asset_type:
        :return:
        """
        #TODO: No file saving is needed if no new data is downloaded online
        all_dfs = []
        if isinstance(htypes, str):
            htypes = str_to_list(input_string=htypes, sep_char=',')
        if isinstance(shares, str):
            shares = str_to_list(input_string=shares, sep_char=',')
        share_count = len(shares)
        i = 0
        progress_count = len(htypes) * len(shares) + len(htypes)
        progress_bar(i, progress_count, f'total progress count: {progress_count}')
        data_downloaded = False
        for htype in htypes:
            file_name = htype
            if freq.upper() != 'D':
                file_name = file_name + '-' + freq.upper()
            if asset_type.upper() != 'E':
                file_name = file_name + '-' + asset_type.upper()

            i += 1
            progress_bar(i, progress_count, 'extracting local file')
            if self.file_exists(file_name):
                df = self.extract_data(file_name, shares=shares, start=start, end=end)
                # debug
                # if htype == 'close':
                #     print(f'\nIn func get_and_update_data() while htype == {htype}:\n'
                #           f'historical data is extracted from local file: {file_name}.csv\n:{df.head()}\n'
                #           f'are all the index of the df trading days? \n'
                #           f'{all([is_market_trade_day(date) for date in df.index])}\n'
                #           f'first 30 trading day assessment results:\n'
                #           f'{[is_market_trade_day(date) for date in df.index[:30]]}\n'
                #           f'is 688680.SH in share? {"688680.SH" in df.columns}')
            else:
                df = pd.DataFrame(np.inf, index=pd.date_range(start=start, end=end, freq=freq), columns=shares)
                for share in [share for share in shares if share not in df.columns]:
                    df[share] = np.inf
                # debug
                # print(f'\nIn func get_and_update_data():\n'
                #       f'historical data can not be found locally with the name {file_name}.csv\n'
                #       f'empty dataframe is created:\n{df}')
            data_index = df.index
            index_count = len(df.index)
            for share, share_data in df.iteritems():
                progress_bar(i, progress_count, 'searching for missing data')
                missing_data = share_data.iloc[np.isinf(share_data).values]
                i += 1
                progress_bar(i, progress_count, 'downloading missing data')
                if missing_data.count() > 0:
                    data_downloaded = True
                    missing_data_start = regulate_date_format(missing_data.index[0])
                    missing_data_end = regulate_date_format(missing_data.index[-1])
                    start = missing_data.index[0]
                    end = missing_data.index[-1]
                    # print(f'\nIn func get_and_update_data():\n'
                    #       f'missing data for share {share} is not empty, they are:\n'
                    #       f'{missing_data}')
                    if htype in PRICE_TYPE_DATA:
                        online_data = get_price_type_raw_data(start=missing_data_start,
                                                              end=missing_data_end,
                                                              freq=freq,
                                                              shares=share,
                                                              htypes=htype,
                                                              asset_type=asset_type,
                                                              parallel=4,
                                                              progress=False)[0]

                    elif htype in CASHFLOW_TYPE_DATA + BALANCE_TYPE_DATA + INCOME_TYPE_DATA + INDICATOR_TYPE_DATA:
                        inc, ind, blc, csh = get_financial_report_type_raw_data(start=missing_data_start,
                                                                                end=missing_data_end,
                                                                                shares=share,
                                                                                htypes=htype,
                                                                                progress=False)
                        online_data = (inc + ind + blc + csh)[0]

                    # 按照原来的思路，下面的代码是将下载的数据（可能是稀疏数据）一个个写入到目标区域中，再将目标区域中的
                    # np.inf逐个改写为np.nan。但是其实粗暴一点的做法是直接把下载的数据reindex，然后整体覆盖目标区域
                    # 就可以了。
                    # 这里是整体覆盖的代码：
                    share_data[start:end] = online_data.reindex(share_data[start:end].index)[htype]

                        # 这里是单独分别写入的代码：
                    # if online_data.empty:
                    #     # 当下载的数据为空时，就不要改写任何数据
                    #     # (这点不一定，如果下载的是稀疏数据，可能这段时间本来就没有数据，这时应该写入空数据到数据库中
                    #     # ，避免下次再重新从网上下载数据)
                    #     # 例如，对于某些新上市的股票，如688680.SH，于2021年1月23日上市，在2021年以前没有财务数据
                    #     # 这样就会取到空数据，这时候应该写入空数据而不是np.inf到数据库中，除了避免重新下载数据以外，
                    #     # 还可以避免生成的loop数据中含有np.inf，从而导致loop失败
                    #     # print(f'EMPTY data loaded, will skip')
                    #     try:
                    #         # debug
                    #         print(f'i-locations of data to be set are:\n'
                    #               f'{np.searchsorted(data_index, online_data.index).clip(0, index_count-1)}\n'
                    #               f'data that are to be set are:\n'
                    #               f'{online_data[htype].values}\n'
                    #               f'data to be replaced are \n'
                    #               f'{share_data.iloc[np.searchsorted(data_index, online_data.index).clip(0, index_count-1)]}\n'
                    #               f'DOING THE WORK...')
                    #
                    #         share_data.iloc[np.searchsorted(data_index,
                    #                                         online_data.index).clip(0,
                    #                                                                 index_count-1)] = \
                    #             online_data[htype]
                    #         # online_data.values will cause potential problem
                    #         # using 'iloc' is 3~5 times faster than 'loc'
                    #         share_data.iloc[np.isinf(share_data).values] = np.nan
                    #     except Exception as e:
                    #     # debug
                    #         print(f'\nERROR OCCURED! {e}\n=====  <get_and_updated_data()>: \n'
                    #               f'share_data len: {index_count}, online_data len: {len(online_data)}, by '
                    #               f'searching for {htype} in:\n'
                    #               f'range: between {missing_data_start} and {missing_data_end}\n'
                    #               f'searched index locations are: '
                    #               f'{np.searchsorted(data_index, online_data.index).clip(0, index_count-1)}\n')
                    #         print(f'share data:\n{share_data}\nonline_data: \n{online_data}')
                    # else:
                    #     try:
                    #         # debug
                    #         print(f'i-locations of data to be set are:\n'
                    #               f'{np.searchsorted(data_index, online_data.index).clip(0, index_count-1)}\n'
                    #               f'data that are to be set are:\n'
                    #               f'{online_data[htype].values}\n'
                    #               f'data to be replaced are \n'
                    #               f'{share_data.iloc[np.searchsorted(data_index, online_data.index).clip(0, index_count-1)]}\n'
                    #               f'DOING THE WORK...')
                    #
                    #         share_data.iloc[np.searchsorted(data_index,
                    #                                         online_data.index).clip(0,
                    #                                                                 index_count-1)] = \
                    #             online_data[htype]
                    #         # online_data.values will cause potential problem
                    #         # using 'iloc' is 3~5 times faster than 'loc'
                    #         share_data.iloc[np.isinf(share_data).values] = np.nan
                    #     except Exception as e:
                    #     # debug
                    #         print(f'\nERROR OCCURED! {e}\n=====  <get_and_updated_data()>: \n'
                    #               f'share_data len: {index_count}, online_data len: {len(online_data)}, by '
                    #               f'searching for {htype} in:\n'
                    #               f'range: between {missing_data_start} and {missing_data_end}\n'
                    #               f'searched index locations are: '
                    #               f'{np.searchsorted(data_index, online_data.index).clip(0, index_count-1)}\n')
                    #         print(f'share data:\n{share_data}\nonline_data: \n{online_data}')

            progress_bar(i, progress_count, 'Writing data to local files')
            if data_downloaded:
                if self.file_exists(file_name):
                    self.merge_file(file_name, df)
                else:
                    self.new_file(file_name, df)
            progress_bar(i, progress_count, 'Extracting data')
            df = self.extract_data(file_name, shares=shares, start=start, end=end)
            # debug
            # print(f'\nIn func get_and_update_data():\n'
            #       f'historical data is extracted from local file: {file_name}.csv\n:{df.head()}\n'
            #       f'are all the index of the df trading days? \n'
            #       f'{all([is_market_trade_day(date) for date in df.index])}\n'
            #       f'first 30 trading day assessment results:\n'
            #       f'{[is_market_trade_day(date) for date in df.index[:30]]}')
            all_dfs.append(df)

        hp = stack_dataframes(dfs=all_dfs, stack_along='htypes', htypes=htypes)
        return hp