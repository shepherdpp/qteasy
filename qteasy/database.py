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
import os
from os import path

LOCAL_DATA_FOLDER = 'qteasy/data/'

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
    def __init__(self, kwargs):
        """

        :param kwargs: the args can be improved in the future
        """
        raise NotImplementedError

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
        all data online to keep local data

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
        return path.exists(file_name)

    def new_file(self, file_name, dataframe):
        """ create given dataframe into a new file with file_name

        :param dataframe:
        :param file_name:
        :return:
        """
        if not isinstance(file_name, str):
            raise TypeError(f'file_name name must be a string, {file_name} is not a valid input!')
        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError(f'data should be a pandas dataframe, the input is not in valid format!')
        if not isinstance(dataframe.index[0], pd.Timestamp):
            raise TypeError(f'input data should be indexed by timestamp!')

        if self.file_exists(file_name):
            raise FileExistsError(f'the file with name {file_name} already exists!')
        dataframe.to_csv(file_name)
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
        if self.file_exists(file_name):
            df = pd.read_csv(file_name)
            return df
        else:
            raise FileNotFoundError(f'File {file_name} not found!')

    def append_file(self, file_name, df):
        """ append the contents to the existing file with the name file_name

        :param file_name:
        :param df:
        :return:
        """
        if not isinstance(file_name, str):
            raise TypeError(f'file_name name must be a string, {file_name} is not a valid input!')
        if not isinstance(df, pd.DataFrame):
            raise TypeError(f'data should be a pandas df, the input is not in valid format!')
        if not isinstance(df.index[0], pd.Timestamp):
            raise TypeError(f'input data should be indexed by timestamp!')

        if not self.file_exists(file_name):
            self.new_file(file_name, df)
            return df
        else:
            original_df = self.open_file(file_name)
            
            return df


    def update(self):
        """ download the latest data in order to make local data set up-to-date.

        :return:
        """
        raise NotImplementedError

    def get_data(self, kwargs):
        """ the major work method of DataSource object, extracts data directly from local
        files when all requested records exists locally. extract data online if they don't.

        merge data downloaded from online.

        :param kwargs:
        :return:
        """
        raise NotImplementedError

    def merge_data(self, data):
        """ merge given data with existing data

        :param data:
        :return:
        """