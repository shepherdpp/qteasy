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

from .tsfuncs import get_bar
from .history import stack_dataframes, get_price_type_raw_data
from .utilfuncs import regulate_date_format

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
        print()
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

    def expand_file(self, file_name, df):
        """ expand the file by adding more columns to the file with the name file_name

        in this case the datetime range of the file does not change, data that are out of
        original datetime range will be discarded.

        :param file_name:
        :param df:
        :return:
        """
        if not isinstance(file_name, str):
            raise TypeError(f'file_name name must be a string, {file_name} is not a valid input!')
        df = self.validated_dataframe(df)

        if not self.file_exists(file_name):
            self.new_file(file_name, df)
            return df
        else:
            original_df = self.open_file(file_name)
            if any(column in original_df.columns for column in df.columns):
                raise KeyError(f'one or more column in df already exists in file, use self.append instead!')
            new_df = original_df.join(df, how='outer')
            self.overwrite_file(file_name, new_df)
            return new_df

    def append_file(self, file_name, df):
        """ append more rows to the data thus datetime range is expended,
        in this case the datetime range of df should not overlap with that
        of the file

        :param file_name:
        :param df:
        :return:
        """
        original_df = self.open_file(file_name)
        return df

    def merge_file(self, file_name, df):
        """ merge some data stored in df into file_name,

        the idea is that this method deals with the data frame whose index
        is covered in file name, but data are not downloaded

        :param file_name:
        :param df:
        :return:
        """
        raise NotImplementedError

    def extract_data(self, file_name, shares, start, end):
        df = self.open_file(file_name)
        df = self.validated_dataframe(df)
        return df


    def validated_dataframe(self, df):
        """ checks the df input, and validate its index and prepare sorting

        :param df:
        :return:
        """
        if not isinstance(df, pd.DataFrame):
            raise TypeError(f'data should be a pandas df, the input is not in valid format!')
        try:
            df.rename(index=pd.to_datetime, inplace=True)
            df.drop_duplicates(inplace=True)
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
        all_dfs = []
        for htype in htypes:
            file_name = htype
            if self.file_exists(file_name):
                df = self.extract_data(file_name, shares=shares, start=start, end=end)
            else:
                df = pd.DataFrame(np.inf, index=pd.date_range(start=start, end=end, freq=freq), columns=shares)

            for share in [share for share in shares if share not in df.columns]:
                df[share] = np.inf

            print(df)

            for share, share_data in df.iteritems():
                missing_data = share_data.loc[share_data == np.inf]
                if missing_data.count() > 0:
                    missing_data_start = regulate_date_format(missing_data.index[0])
                    missing_data_end = regulate_date_format(missing_data.index[-1])
                    print(f'will get price type raw data for:\n'
                          f'share:    {share}\n'
                          f'htype:    {htype}\n'
                          f'start:    {missing_data_start}\n'
                          f'end:      {missing_data_end}')
                    online_data = get_price_type_raw_data(start=missing_data_start,
                                                          end=missing_data_end,
                                                          freq=freq,
                                                          shares=share,
                                                          htypes=htype)[0]

                    print(f'\ngot missing data (index type: {type(missing_data.index[0])}):\n'
                          f'{missing_data}\n'
                          f'and online data (index type: {type(online_data.index[0])}):\n{online_data}')
                    share_data.loc[share_data == np.inf] = np.nan
                    share_data.loc[online_data.index] = online_data.values.squeeze()
                    print(f'historical data merged with online data, and got result:\n{share_data}')

            if self.file_exists(file_name):
                self.overwrite_file(file_name, df)
            else:
                self.new_file(file_name, df)
            all_dfs.append(df)

        hp = stack_dataframes(dfs=all_dfs, stack_along='htypes', htypes=htypes)
        return hp
