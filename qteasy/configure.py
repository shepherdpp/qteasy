# coding=utf-8
# ======================================
# File:     configure.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2024-08-31
# Desc:
#   Functions related to qteasy
# configurations and settings originally
# in core.py.
# ======================================

import os
import warnings

from qteasy._arg_validators import (
    QT_CONFIG,
    ConfigDict,
    _update_config_kwargs,
    _vkwargs_to_text,
)

from qteasy.utilfuncs import (
    str_to_list,
    is_float_like,
    is_integer_like,
)

# 启动配置文件的默认内容
QT_START_UP_FILE_INTRO = '# **********************************\n' \
                         '# qteasy start up configuration file\n' \
                         '# **********************************\n\n' \
                         '# following configurations will be loaded when initialize qteasy\n\n' \
                         '# example:\n' \
                         '# local_data_source = database\n\n'


def configure(config=None, reset=False, only_built_in_keys=True, **kwargs) -> None:
    """ 配置qteasy的运行参数QT_CONFIG

    Parameters
    ----------
    config: ConfigDict 对象
        需要设置或调整参数的config对象，默认为None，此时直接对QT_CONFIG对象设置参数
    reset: bool
        默认值为False，为True时忽略传入的kwargs，将所有的参数设置为默认值
    only_built_in_keys: bool
        默认值False，如果为True，仅允许传入内部参数，False时允许传入任意参数
    **kwargs:
        需要设置的所有参数

    Returns
    -------
    None

    Notes
    -----
    使用get_config()或configuration()查看当前的QT_CONFIG参数

    Examples
    --------
    >>> configure(reset=True)  # 将QT_CONFIG参数设置为默认值
    >>> configure(invest_cash_amounts=[10000, 20000, 30000], invest_cash_dates=['2018-01-01', '2018-02-01', '2018-03-01'])
    >>> get_config('invest_cash_amounts, invest_cash_dates')
    No. Config-Key            Cur Val                       Default val
    -------------------------------------------------------------------
    1   invest_cash_amounts   [10000, 20000, 30000]         <[100000.0]>
    2   invest_cash_dates     ['2018-01-01', '2018-02-01'...<None>

    """
    if config is None:
        set_cfg = QT_CONFIG
    else:
        assert isinstance(config, ConfigDict), TypeError(f'config should be a ConfigDict, got {type(config)}')
        set_cfg = config
    if not reset:
        _update_config_kwargs(set_cfg, kwargs, raise_if_key_not_existed=only_built_in_keys)
    else:
        from qteasy._arg_validators import _valid_qt_kwargs
        default_kwargs = {k: v['Default'] for k, v in zip(_valid_qt_kwargs().keys(),
                                                          _valid_qt_kwargs().values())}
        _update_config_kwargs(set_cfg, default_kwargs, raise_if_key_not_existed=True)


def set_config(config=None, reset=False, only_built_in_keys=True, **kwargs) -> None:
    """ 配置qteasy的运行参数QT_CONFIG，等同于configure()

    Parameters
    ----------
    config: ConfigDict 对象
        需要设置或调整参数的config对象，默认为None，此时直接对QT_CONFIG对象设置参数
    reset: bool
        默认值为False，为True时忽略传入的kwargs，将所有的参数设置为默认值
    only_built_in_keys: bool
        默认值False，如果为True，仅允许传入内部参数，False时允许传入任意参数
    **kwargs:
        需要设置的所有参数

    Returns
    -------
    None

    Examples
    --------
    参见 configure()
    """

    return configure(config=config, reset=reset, only_built_in_keys=only_built_in_keys, **kwargs)


def configuration(config_key=None, level=0, up_to=0, default=True, verbose=False) -> None:
    """ 显示qt当前的配置变量，

    Parameters
    ----------
    config_key : str or list of str
        需要显示的配置变量名称，如果不给出任何名称，则按level，up_to等方式显示所有的匹配的变量名
        可以以逗号分隔字符串的形式给出一个或多个变量名，也可以list形式给出一个或多个变量名
        以下两种方式等价：
        'local_data_source, local_data_file_type, local_data_file_path'
        ['local_data_source', 'local_data_file_type', 'local_data_file_path']
    level : int, Default: 0
        需要显示的配置变量的级别。
        如果给出了config，则忽略此参数
    up_to : int, Default: 0
        需要显示的配置变量的级别上限，需要配合level设置。
        例如，当level == 0, up_to == 2时
        会显示级别在0～2之间的所有配置变量
        如果给出了config，则忽略此参数
    default: Bool, Default: False
        是否显示配置变量的默认值，如果True，会同时显示配置变量的当前值和默认值
    verbose: Bool, Default: False
        是否显示完整说明信息，如果True，会同时显示配置变量的详细说明

    Returns
    -------
    None

    Notes
    -----
    使用示例参见get_config()
    """
    assert isinstance(level, int) and (0 <= level <= 5), f'InputError, level should be an integer, got {type(level)}'
    assert isinstance(up_to, int) and (0 <= up_to <= 5), f'InputError, up_to level should be an integer, ' \
                                                         f'got {type(up_to)}'
    if up_to <= level:
        up_to = level
    if up_to == level:
        level = level
    else:
        level = list(range(level, up_to + 1))

    if config_key is None:
        kwargs = QT_CONFIG
    else:
        if isinstance(config_key, str):
            config_key = str_to_list(config_key)
        if not isinstance(config_key, list):
            raise TypeError(f'config_key should be a string or list of strings, got {type(config_key)}')
        assert all(isinstance(item, str) for item in config_key)
        kwargs = {key: QT_CONFIG[key] for key in config_key}
        level = [0, 1, 2, 3, 4, 5]

    from shutil import get_terminal_size
    screen_width = get_terminal_size().columns
    from rich import print as rprint
    rprint(_vkwargs_to_text(
            kwargs=kwargs,
            level=level,
            info=default,
            verbose=verbose,
            width=screen_width,
    ))


def get_configurations(config_key=None, level=0, up_to=0, default=True, verbose=False):
    """ 显示qt当前的配置变量，与get_config / configuration 相同

    Parameters
    ----------
    config_key : str or list of str
        需要显示的配置变量名称，如果不给出任何名称，则按level，up_to等方式显示所有的匹配的变量名
        可以以逗号分隔字符串的形式给出一个或多个变量名，也可以list形式给出一个或多个变量名
        以下两种方式等价：
        'local_data_source, local_data_file_type, local_data_file_path'
        ['local_data_source', 'local_data_file_type', 'local_data_file_path']
    level : int, Default: 0
        需要显示的配置变量的级别。
        如果给出了config，则忽略此参数
    up_to : int, Default: 0
        需要显示的配置变量的级别上限，需要配合level设置。
        例如，当level == 0, up_to == 2时
        会显示级别在0～2之间的所有配置变量
        如果给出了config，则忽略此参数
    default: Bool, Default: False
        是否显示配置变量的默认值，如果True，会同时显示配置变量的当前值和默认值
    verbose: Bool, Default: False
        是否显示完整说明信息，如果True，会同时显示配置变量的详细说明

    Returns
    -------
    None

    Examples
    --------
    使用示例参见get_config()
    """

    return configuration(config_key=config_key, level=level, up_to=up_to, default=default, verbose=verbose)


def get_config(config_key=None, level=0, up_to=0, default=True, verbose=False):
    """ 显示qt当前的配置变量，与get_config / configuration 相同

    Parameters
    ----------
    config_key : str or list of str
        需要显示的配置变量名称，如果不给出任何名称，则按level，up_to等方式显示所有的匹配的变量名
        可以以逗号分隔字符串的形式给出一个或多个变量名，也可以list形式给出一个或多个变量名
        以下两种方式等价：
        'local_data_source, local_data_file_type, local_data_file_path'
        ['local_data_source', 'local_data_file_type', 'local_data_file_path']
    level : int, Default: 0
        需要显示的配置变量的级别。
        如果给出了config，则忽略此参数
    up_to : int, Default: 0
        需要显示的配置变量的级别上限，需要配合level设置。
        例如，当level == 0, up_to == 2时
        会显示级别在0～2之间的所有配置变量
        如果给出了config，则忽略此参数
    default: Bool, Default: False
        是否显示配置变量的默认值，如果True，会同时显示配置变量的当前值和默认值
    verbose: Bool, Default: False
        是否显示完整说明信息，如果True，会同时显示配置变量的详细说明

    Returns
    -------
    None

    Examples
    --------
    >>> get_config('local_data_source')
    No. Config-Key            Cur Val        Default val
    ----------------------------------------------------
    1   local_data_source     database       <file>

    >>> get_config('local_data_source, local_data_file_type, local_data_file_path')
    No. Config-Key            Cur Val        Default val
    ----------------------------------------------------
    1   local_data_source     database       <file>
    2   local_data_file_type  csv            <csv>
    3   local_data_file_path  data/          <data/>

    >>> get_config(level=0, up_to=2)
    No. Config-Key            Cur Val        Default val
    ----------------------------------------------------
    1   mode                  1              <1>
    2   time_zone             Asia/Shanghai  <Asia/Shanghai>
    3   asset_pool            000300.SH      <000300.SH>
    4   asset_type            IDX            <IDX>
    5   live_trade_account_id None           <None>
    6   live_trade_account    None           <None>
    7   live_trade_debug_mode False          <False>
    8   live_trade_init_cash  1000000.0      <1000000.0>
    ... (more rows)

    >>> get_config(level=0, up_to=1, verbose=True)
    No. Config-Key            Cur Val        Default val
          Description
    ----------------------------------------------------
    1   mode                  1              <1>
          qteasy 的运行模式:
          0: 实盘运行模式
          1: 回测-评价模式
          2: 策略优化模式
          3: 统计预测模式
    2   time_zone             Asia/Shanghai  <Asia/Shanghai>
          回测时的时区，可以是任意时区，例如：
          Asia/Shanghai
          Asia/Hong_Kong
          US/Eastern
          US/Pacific
          Europe/London
          Europe/Paris
          Australia/Sydney
          Australia/Melbourne
          Pacific/Auckland
          Pacific/Chatham
          etc.
    3   asset_pool            000300.SH      <000300.SH>
          可用投资产品池，投资组合基于池中的产品创建
    4   asset_type            IDX            <IDX>
          投资产品的资产类型，包括：
          IDX  : 指数
          E    : 股票
          FT   : 期货
          FD   : 基金
    """

    return configuration(config_key=config_key, level=level, up_to=up_to, default=default, verbose=verbose)


def _check_config_file_name(file_name, allow_default_name=False):
    """ 检查配置文件名是否合法，如果合法或可以转化为合法，返回合法文件名，否则raise

    parameters
    ----------
    file_name: str
        配置文件名，可以是一个文件名，也可以是不带后缀的文件名，不可以是一个路径
    allow_default_name: bool
        是否允许使用默认的配置文件名qteasy.cfg
    """

    if file_name is None:
        file_name = 'saved_config.cfg'
    if not isinstance(file_name, str):
        raise TypeError(f'file_name should be a string, got {type(file_name)} instead.')
    import re
    if re.match(r'[a-zA-Z_]\w+$', file_name):
        file_name = file_name + '.cfg'  # add .cfg suffix if not given
    if not re.match(r'[a-zA-Z_]\w+\.cfg$', file_name):
        raise ValueError(f'invalid file name given: {file_name}')
    if (file_name == 'qteasy.cfg') and (not allow_default_name):
        # TODO: 实现配置变量写入qteasy.cfg初始配置文件的功能
        raise NotImplementedError(f'"qteasy.cfg" is not an allowed file name, functionality not '
                                  f'implemented yet, please use another file name.')
    return file_name


def save_config(*, config=None, file_name=None, overwrite=True, initial_config=False) -> str:
    """ 将config保存为一个文件
    尚未实现的功能：如果initial_config为True，则将配置更新到初始化配置文件qteasy.cfg中()

    Parameters
    ----------
    config: ConfigDict or dict, Default: None
        一个config对象或者包含配配置变量的dict，如果为None，则保存qt.QT_CONFIG
    file_name: str, Default: None
        文件名，如果为None，文件名为"saved_config.cfg"
    overwrite: bool, Default: True
        默认True，覆盖重名文件，如果为False，当保存的文件已存在时，将报错
    initial_config: bool, Default: False ** FUNCTIONALITY NOT IMPLEMENTED **
        保配置变量到初始配置文件 qteasy.cfg 中，如果qteasy.cfg中已经存在部配置变量了，则覆盖相配置变量
        TODO: 实现将配置变量写入qteasy.cfg初始配置文件的功能
         由于目前使用pickle写入对象为二进制文件，而qteasy.cfg是文本文件，所以需要实现一个新的写入方式

    Returns
    -------
    file_name: str
        保存的文件名
    """

    from qteasy import logger_core
    from qteasy import QT_ROOT_PATH
    import os

    if config is None:
        config = QT_CONFIG
    if not isinstance(config, (ConfigDict, dict)):
        raise TypeError(f'config should be a ConfigDict or a dict, got {type(config)} instead.')

    file_name = _check_config_file_name(file_name=file_name, allow_default_name=initial_config)

    config_path = os.path.join(QT_ROOT_PATH, '../config/')

    # write_binary_file
    from .utilfuncs import write_binary_file
    if overwrite:
        open_method = 'wb'  # overwrite the file
    else:
        open_method = 'xb'  # raise if file already existed
    try:
        file_name = write_binary_file(
                file_path=config_path,
                file_name=file_name,
                data=config,
                mode=open_method,
        )
        logger_core.info(f'config file content written to: {file_name}')
        return file_name
    except Exception as e:
        logger_core.warning(f'{e}, error during writing config to local file.')
        return ""


def load_config(*, config=None, file_name=None) -> ConfigDict:
    """ 从文件file_name中读取相应的config参数，写入到config中，如果config为
        None，则保存参数到QT_CONFIG中

    Parameters
    ----------
    config: ConfigDict 对象
        一个config对象，默认None，如果不为None且为一个ConfigDict对象，则将读取的配置参数写入到config中
    file_name: str
        文件名，默认None，如果为None，文件名为saved_config.cfg

    Returns
    -------
    config: ConfigDict
        读取的配置参数

    Raises
    ------
    FileNotFoundError
        如果给定文件不存在，则报错。如果没有给定文件名，则当config/saved_config.cfg不存在时，报错

    Examples:
    --------
    >>> load_config()
    """
    from qteasy import logger_core
    from qteasy import QT_ROOT_PATH

    file_name = _check_config_file_name(file_name=file_name, allow_default_name=False)

    config_path = os.path.join(QT_ROOT_PATH, '../config/')

    # read_binary_file
    from .utilfuncs import read_binary_file
    try:
        saved_config = read_binary_file(
            file_path=config_path,
            file_name=file_name,
            mode='rb',
        )
        logger_core.info(f'read configuration file: {file_name}')
    except FileNotFoundError as e:
        msg = f'{e}\nConfiguration file {file_name} not found! nothing will be read.'
        logger_core.warning(msg)
        saved_config = {}

    if config is not None:
        if not isinstance(config, ConfigDict):
            msg = f'config should be a ConfigDict, got {type(config)} instead.'
            raise TypeError(msg)
        configure(config=config,
                  only_built_in_keys=False,
                  **saved_config)

    return ConfigDict(saved_config)


def view_config_files(details=False) -> None:
    """ 查看已经保存的配置文件，并显示其主要内容

    Parameters
    ----------
    details: bool, Default: False
        是否显示配置文件的详细内容

    Returns
    -------
    None

    Notes
    -----
    该函数只显示config文件夹下的配置文件，不显示qteasy.cfg中的配置
    """

    # TODO: add unittests
    # 1. list all files in config folder
    # 2. read each file and display its content if details is True
    # 3. display only file names if details is False

    from qteasy import QT_ROOT_PATH
    import pickle

    config_path = os.path.join(QT_ROOT_PATH, '../config/')

    files = os.listdir(config_path)
    files = [f for f in files if f.endswith('.cfg')]

    if len(files) == 0:
        print('No config files found in config folder.')

    if details:
        for file in files:
            with open(os.path.join(config_path, file), 'rb') as f:
                config = pickle.load(f)
            print(f'File: {file}')
            print(config)

    else:
        print('Config files found in config folder:')
        for file in files:
            print(file)


def start_up_settings() -> None:
    """ 打印qteasy启动配置文件中存储的启动设置内容

    Returns
    -------
    None

    Examples
    --------
    >>> import qteasy as qt
    >>> qt.start_up_settings()
    Start up settings:
    --------------------
    local_data_source = file
    local_data_file_type = csv
    local_data_file_path = data/
    """
    from qteasy import QT_ROOT_PATH
    start_up_config_lines = _read_start_up_file(os.path.join(QT_ROOT_PATH, 'qteasy.cfg'))

    config_lines = []

    if len(start_up_config_lines) == 0:
        print('Start up setting file is empty')
        return None

    print(f'Start up settings:\n{"-" * 20}')
    for line in start_up_config_lines:
        # 忽略注释行
        if line[0] == '#':
            continue
        # 忽略空行
        if len(line.strip()) == 0:
            continue
        # 删除行尾的换行符
        print(line.strip())
        config_lines.append(line.strip())

    return None


def get_start_up_settings() -> dict:
    """ 返回qteasy启动配置文件中存储的启动设置内容

    Returns
    -------
    start_up_settings: dict
        当前qteasy.cfg中存储的启动设置内容，以dict形式返回

    Examples
    --------
    >>> import qteasy as qt
    >>> settings = qt.get_start_up_settings()
    >>> print(settings)
    {
        'local_data_source': 'file'
        'local_data_file_type': 'csv'
        'local_data_file_path': 'data/'
    }
    """

    from qteasy import QT_ROOT_PATH
    start_up_config_lines = _read_start_up_file(os.path.join(QT_ROOT_PATH, 'qteasy.cfg'))

    return _parse_start_up_config_lines(config_lines=start_up_config_lines)


def update_start_up_setting(**kwargs) -> None:
    """ 更新qteasy启动配置文件中存储的启动设置

    启动设置中可以包括系统定义配置参数以及用户自定义配置参数

    Parameters
    ----------
    **kwargs:
        需要更新的配置参数

    Returns
    -------
    None

    Examples
    --------
    >>> import qteasy as qt

    >>> qt.start_up_settings()
    Start up settings:
    --------------------
    local_data_source = file
    local_data_file_type = csv
    local_data_file_path = data/

    >>> qt.update_start_up_setting(local_data_source='database', local_data_file_type='feather')
    Start up settings updated successfully!

    >>> qt.start_up_settings()
    Start up settings:
    --------------------
    local_data_source = file
    local_data_file_type = feather
    local_data_file_path = data/
    """

    from qteasy import QT_ROOT_PATH
    from qteasy.utilfuncs import is_integer_like, is_float_like
    from qteasy._arg_validators import _valid_qt_kwargs, _validate_key_and_value
    start_up_config_lines = _read_start_up_file(os.path.join(QT_ROOT_PATH, 'qteasy.cfg'))
    start_up_config = _parse_start_up_config_lines(start_up_config_lines)

    for k, v in kwargs.items():
        if isinstance(v, str):
            # 字符串类型的参数值，如果是数字、浮点数、布尔值或None，需要加上引号
            if is_integer_like(v) or is_float_like(v):
                v = f'"{v}"'
            elif v.lower() in ['true', 'false', 'none']:
                v = f'"{v}"'  # True, False, None
            else:
                v = v

        # validate the value if key is in valid_qt_kwargs
        validated = True
        if k in _valid_qt_kwargs():
            validated = _validate_key_and_value(k, v)

        if validated:
            start_up_config[k] = v

    config_lines = [f'{k} = {v}\n' for k, v in start_up_config.items()]
    _write_start_up_file(os.path.join(QT_ROOT_PATH, 'qteasy.cfg'), config_lines)

    print('Start up settings updated successfully! The settings will be effective next time you start qteasy.')


def remove_start_up_setting(*args) -> None:
    """ 删除qteasy启动配置文件中存储的一项或者多项启动设置

    必须给出需要删除的配置参数名称，可以同时删除多个配置参数

    Parameters
    ----------
    *args: str
        需要的配置参数名称清单

    Returns
    -------
    None

    Examples
    --------
    >>> import qteasy as qt
    >>> qt.start_up_settings()
    Start up settings:
    --------------------
    local_data_source = file
    local_data_file_type = csv
    local_data_file_path = data/

    >>> qt.remove_start_up_setting('local_data_source')
    Start up settings removed:  ('local_data_source',)

    >>> qt.start_up_settings()
    Start up settings:
    --------------------
    local_data_file_type = csv
    local_data_file_path = data/
    """

    from qteasy import QT_ROOT_PATH
    start_up_config_lines = _read_start_up_file(os.path.join(QT_ROOT_PATH, 'qteasy.cfg'))
    start_up_config = _parse_start_up_config_lines(start_up_config_lines)

    for arg in args:
        if arg in start_up_config:
            start_up_config.pop(arg)
        else:
            print(f'Parameter {arg} not found in start up settings, nothing to remove.')

    config_lines = [f'{k} = {v}\n' for k, v in start_up_config.items()]
    _write_start_up_file(os.path.join(QT_ROOT_PATH, 'qteasy.cfg'), config_lines)

    print(f'Start up settings removed: {args}\nThe settings will be effective next time you start qteasy.')


def _read_start_up_file(file_path_name) -> list:
    """ 读取qteasy.cfg文件中存储的内容到一个列表中

    如果启动配置文件不存在，则创建一个新的启动配置文件，并返回一个空列表

    Parameters
    ----------
    file_path_name: str
        启动配置文件的路径

    """
    try:
        with open(file_path_name) as f:
            config_lines = f.readlines()

    except FileNotFoundError:
        _new_start_up_file(file_path_name)

        config_lines = []  # 本地配置文件行
        msg = f'qteasy.cfg not found, a new start up configuration file is created, \nview file at: ' \
              f'{file_path_name}'
        warnings.warn(msg)
    except Exception as e:
        msg = f'Error reading start up configuration file, all configurations will fall back to default! \n{e}'
        warnings.warn(msg)
        config_lines = []

    return config_lines


def _new_start_up_file(file_path_name) -> str:
    """ 创建一个新的启动配置文件qteasy.cfg

    如果文件已经存在，则覆盖原有文件

    Parameters
    ----------
    file_path_name: str
        启动配置文件的路径
    """

    try:
        with open(file_path_name, mode='w', encoding='utf-8') as f:
            intro = QT_START_UP_FILE_INTRO
            f.write(intro)
    except Exception as e:
        err = FileNotFoundError(f'Error creating start up configuration file: {e}')
        raise err

    return file_path_name


def _write_start_up_file(file_path_name, config_lines) -> str:
    """ 将配置文件中的配置参数写入到文件中

    如果文件不存在，创建一个新的文件，并写入内容；如果文件存在，则覆盖原有文件

    Parameters
    ----------
    file_path_name: str
        启动配置文件的路径
    config_lines: list
        配置文件中的所有行

    Returns
    -------
    file_path_name: str
        写入的文件名
    """

    file_path_name = _new_start_up_file(file_path_name)

    try:
        with open(file_path_name, mode='w', encoding='utf-8') as f:
            intro = QT_START_UP_FILE_INTRO
            f.write(intro)

            f.writelines(config_lines)
    except Exception as e:
        err = FileNotFoundError(f'Error writing start up configuration file: {e}')
        raise err

    return file_path_name


def _parse_start_up_config_lines(config_lines) -> dict:
    """ 解析配置文件中的配置参数

    Parameters
    ----------
    config_lines: list
        配置文件中的所有行

    Returns
    -------
    configs: dict
        解析后的配置参数
    """
    # 解析config_lines列表，依次读取所有存储的属性
    start_up_config = {}

    for line in config_lines:
        if line[0] in '#;':  # 忽略注释行(# 与 ;)
            continue
        line = line.split('=')
        if len(line) == 2:
            arg_name = line[0].strip()
            read_value = line[1].strip()
            if (read_value[0] in ['\'', '"']) and (read_value[-1] in ['\'', '"']):
                read_value = str(read_value[1:-1])
            elif read_value == 'True':
                read_value = True
            elif read_value == 'False':
                read_value = False
            elif read_value == 'None':
                read_value = None
            elif is_integer_like(read_value):
                read_value = int(read_value)
            elif is_float_like(read_value):
                read_value = float(read_value)
            else:
                pass

            arg_value = read_value
            try:
                start_up_config[arg_name] = arg_value
            except Exception as e:
                msg = f'{e}, invalid parameter: {arg_name}'
                warnings.warn(msg)

    return start_up_config


def reset_config(config=None):
    """ 重设config对象，将所有的参数都设置为默认值
        如果config为None，则重设qt.QT_CONFIG

    Parameters
    ----------
    config: ConfigDict
        需要重设的config对象

    Returns
    -------
    None

    Notes
    -----
    等同于调用configure(config, reset=True)
    """
    from qteasy import logger_core
    if config is None:
        config = QT_CONFIG
    if not isinstance(config, ConfigDict):
        raise TypeError(f'config should be a ConfigDict, got {type(config)} instead.')
    logger_core.info(f'{config} is now reset to default values.')
    configure(config, reset=True)

