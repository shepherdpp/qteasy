# coding=utf-8
# ======================================
# File:     frequency.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2024-05-04
# Desc:
#   Definition of frequency class that
# contains functions to facilitate
# frequency operations for history data.
# ======================================

import re


class DataFreq():
    """ DataFreq class for frequency operations for history data.

    """

    # validator of frequency string: zero or more digits followed by letters or digits separated by '-', ignore case

    freq_string_validator = re.compile(r'^\d*(T|H|d|W|M|MIN)?-*\w*', re.IGNORECASE)

    # a re pattern that checks if zero or more digits followed with any of ['a', 'b', 'abv']
    re_pattern = re.compile(r'^\d*[a-z]+$', re.IGNORECASE)

    available_major_freq = ['T', 'MIN', 'H', 'D', 'W', 'M']
    # possible days in a week
    available_minor_freq_for_week = [
        'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN',
        '1', '2', '3', '4', '5', '6', '7',
        'M', 'T', 'W', 'TH', 'F', 'S', 'SU',
    ]
    # possible days in a month
    available_minor_freq_for_month = [
        '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12',
        '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24',
        '25', '26', '27', '28', '29', '30', '31',
        '1ST', '2ND', '3RD', '4TH', '5TH', '6TH', '7TH', '8TH', '9TH', '10TH',
        '11TH', '12TH', '13TH', '14TH', '15TH', '16TH', '17TH', '18TH', '19TH', '20TH',
        '21ST', '22ND', '23RD', '24TH', '25TH', '26TH', '27TH', '28TH', '29TH', '30TH', '31ST',
    ]

    def __init__(self, freq_str=None, *, multiple=1, major=None, minor=None):
        """

        Parameters:
        -----------
        freq_str: str
            一个字符串，表示数据的频率，包括主频率和次频率以及频率乘数等信息。如果给出了freq_str，
            则不需要给出multiple, major, minor，这些参数如果给出了，将会被忽略。
        multiple: int, optional, default:  1
            主频率和次频率之间的倍数关系，默认为None。
        major: int, optional
            主频率，默认为None。
        minor: int, optional
            次频率，默认为None。
        """

        if freq_str is not None:
            if not isinstance(freq_str, str):
                raise TypeError('freq_str should be a string.')
            self._freq_str = freq_str
            self._multiple, self._major, self._minor = self.parse_freq_str(freq_str)
        else:
            if major is None:
                raise ValueError('Both major and minor should be given.')
            self._multiple = int(multiple)
            self._major = major
            self._minor = minor
            self._freq_str = self.generate_freq_str(multiple, major, minor)

    @property
    def freq_str(self):
        return self._freq_str

    @property
    def multiple(self):
        return self._multiple

    @property
    def major(self):
        return self._major

    @property
    def freq(self):
        # alias of major
        return self._major

    @property
    def minor(self):
        return self._minor

    def parse_freq_str(self, freq_str):
        """解析频率字符串。

        Parameters:
        -----------
        freq_str: str
            一个字符串，表示数据的频率，包括主频率和次频率以及频率乘数等信息。

        Returns:
        --------
        multiple: int
            主频率和次频率之间的倍数关系。
        major: int
            主频率。
        minor: int
            次频率。
        """
        # check if the freq_str is valid
        if not self.freq_string_validator.match(freq_str):
            raise ValueError(f'Invalid frequency string: {freq_str}.')

        freq_str = freq_str.upper()

        # re pattern to extract integer part at the beginning of string as multiple
        multiple_pattern = re.compile(r'^\d*')
        # extract multiple
        multiple_str = multiple_pattern.match(freq_str)
        multiple_str = multiple_str.group()
        multiple = int(multiple_str) if multiple_str != '' else 1

        freq_str_without_multiple = freq_str[len(multiple_str):] if multiple_str is not None else freq_str

        # major and minor parts are separated by '-'
        major_minor = freq_str_without_multiple.split('-')
        major_str = major_minor[0]

        if major_str == 'T':
            major_str = 'MIN'

        if major_str.upper() not in self.available_major_freq:
            raise ValueError(f'Invalid major frequency: {major_str}.')

        if major_str.upper() in ['W']:
            if len(major_minor) < 2:
                minor_str = 'Fri'  # default day of week is Friday
                return multiple, major_str, minor_str
            minor_str = major_minor[1]
            if minor_str not in self.available_minor_freq_for_week:
                raise ValueError(f'Invalid minor frequency for week: {minor_str}.')
            return multiple, major_str, minor_str
        elif major_str.upper() in ['M']:
            if len(major_minor) < 2:
                minor_str = '1'
                return multiple, major_str, minor_str
            minor_str = major_minor[1]
            if minor_str not in self.available_minor_freq_for_month:
                raise ValueError(f'Invalid minor frequency for month: {minor_str}.')
            return multiple, major_str, minor_str
        else:
            return multiple, major_str, None

    def generate_freq_str(self, multiple, major, minor):
        """生成频率字符串。

        Parameters:
        -----------
        multiple: int
            主频率的倍数，如3D表示3天。
        major: int
            主频率。
        minor: int
            次频率，如3W-Fri表示3周的周五。

        Returns:
        --------
        freq_str: str
            一个字符串，表示数据的频率，包括主频率和次频率以及频率乘数等信息。
        """
        if not isinstance(multiple, int):
            raise TypeError('multiple should be an integer.')
        if not isinstance(major, str):
            raise TypeError('major should be a string.')
        if not isinstance(minor, str) and minor is not None:
            raise TypeError('minor should be a string.')

        major = major.upper()
        if major == 'T':
            major = 'MIN'

        if major not in self.available_major_freq:
            raise ValueError(f'Invalid major frequency: {major}.')

        if minor:
            minor = minor.upper()
            if major == 'W':
                if minor not in self.available_minor_freq_for_week:
                    raise ValueError(f'Invalid minor frequency for week: {minor}.')
            elif major == 'M':
                if minor not in self.available_minor_freq_for_month:
                    raise ValueError(f'Invalid minor frequency for month: {minor}.')
            else:
                raise ValueError(f'Invalid minor frequency for major frequency: {major}.')

            if multiple == 1:
                return f'{major}-{minor}'

            return f'{multiple}{major}-{minor}'

        if multiple == 1:
            return major

        return f'{multiple}{major}'
