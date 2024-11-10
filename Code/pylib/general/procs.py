#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
procs - A Python module for managing and logging processes.

This module provides the `ProcInfo` class, which is designed to handle process
management, logging, configuration, and command-line argument parsing in a consistent
and reproducible way. `ProcInfo` is especially useful in long-running scripts or
applications that require detailed logging and process control.

Main Features
-------------
- **Process Logging**: Provides a detailed logging system with configurable log levels.
- **File and Directory Handling**: Includes utilities for creating unique file names,
  managing directories, and backing up existing files.
- **Command Execution**: Offers methods for running shell commands, capturing output,
  and handling errors.
- **Command-line Argument Management**: Simplifies setting up and managing CLI arguments,
  with features like toggling options and setting default values.
- **Reproducibility**: Logs key runtime information (like timestamps and CLI arguments)
  to facilitate process reproducibility.

Classes
-------
- `ProcInfo`: A class designed for managing processes, logging information, and handling configurations.

Usage Examples
--------------
Initialize a process with logging and run a command:
    >>> import argparse
    >>> parser = argparse.ArgumentParser()
    >>> args = parser.parse_args()
    >>> proc = ProcInfo(args)
    >>> proc.info("Process started")
    >>> result = proc.run_cmd(["ls", "-l"])

Backup a file and log an informational message:
    >>> proc.backup("path/to/file.txt")
    >>> proc.info("File backup complete")

Dependencies
------------
- `general.exceptions`: For custom exceptions.
- `general.fsutils`: For filesystem utilities.
- `general.constants`: For common constants.
- `general.term`: For terminal formatting.
- `unitable`: For creating tables.

Author
------
Gabriele Fariello

Version
-------
1.0.0
"""

import stat
import os
import sys
import logging
import time
import tqdm
import datetime
import subprocess
import shlex
import argparse
import _io
import unitable
from typing import TypeVar, Any, Callable

from general.exceptions import NoUniquePathException
from general.fsutils import SearchPath
from general.constants import CommonConstants, CommonFormattingBase
from general.term import Term

ProcInfoT = TypeVar('T', bound='ProcInfo')


class ProcInfo(CommonFormattingBase):
    """
    A class for managing processes and logging information.

    This class can be used directly or subclassed by a process or used within a script
    to manage logging, configuration, and process execution.

    Attributes
    ----------
    max_warning_count : int
        The maximum number of warnings allowed before taking action.
    warning_count : int
        The current count of warnings.
    max_error_count : int
        The maximum number of errors allowed before taking action.
    error_count : int
        The current count of errors.
    critical_count : int
        The current count of critical errors.
    main_t_0 : datetime.datetime
        The start time of the script.
    initial_wd : str
        The initial working directory of the script.
    main_proc_realpath : str
        The 'realpath' of the 'main' script.
    main_abspath : str
        The 'abspath' of the 'main' script.
    main_basename : str
        The basename (resolved from symlinks) of the 'main' script.
    basename_no_ext : str
        The basename (resolved from symlinks) of the 'main' script without the last extension.
    pid : int
        The process ID of the 'main' script.
    main_dirname : str
        The 'dirname' of the 'main' script.
    short_start_timestamp : str
        A short string representation of the start-time of 'main'.
    start_timestamp : str
        A string representation of the start-time of 'main'.
    unique_basename : str
        A unique basename (for creating new files) based on the 'main' script name.
    rerun_command_str : str
        The string needed to re-run this command.
    log_dir : str
        The directory to which logs are written.
    args : argparse.Namespace
        The command-line arguments.

    Methods
    -------
    __init__(args: argparse.Namespace, log: bool = True, prefix_console: bool = True, stderr: bool = False) -> None
        Initializes the ProcInfo instance with the given arguments.
    set_log_to_file(val: bool) -> ProcInfoT
        Sets the flag to log to file.
    set_args(args: argparse.Namespace) -> ProcInfoT
        Sets the command-line arguments.
    save_settings_log() -> 'ProcInfo'
        Saves a file containing information about the settings used to run this process.
    get_arg(name, default=None, set_it=False) -> Any
        Gets an argument value if available, or returns the default.
    run_cmd(cmd, fatal_on_fail=True) -> subprocess.CompletedProcess
        Runs a command and logs the execution.
    run_proc(cmd_args, log_stdout=False, log_stderr=None, fail_fatal=True, **kwargs)
        Runs a command with optional logging.
    set_argparse_parser(cls, parser) -> None
        Sets the argument parser for the class.
    toggler(cls, args, desc, default, dest) -> None
        Creates a toggle-able option in the argument parser.
    """

    _logger = None
    _to_stdout = True
    _console_fh = sys.stdout
    _verbosity = 1
    _term_colors = True
    _args = None
    _debug = False
    _parser = None  # The argparse parser for ALL ProcInfos
    _toggle_args = {}  # To track toggler() args for display / checking

    def __init__(self, args: argparse.Namespace, log: bool = True, prefix_console: bool = True, stderr: bool = False) -> None:
        """
        Initialize the ProcInfo instance with the given arguments.

        Parameters
        ----------
        args : argparse.Namespace
            The command-line arguments.
        log : bool, optional
            Flag to log to file (default is True).
        prefix_console : bool, optional
            Flag to prefix console messages (default is True).
        stderr : bool, optional
            Flag to direct console output to stderr (default is False).
        """
        self.set_args(args)
        self._log_to_file = log or self.get_arg('no_log', False)
        self._prefix_console = prefix_console
        self._config_file = None
        self._critical_count = 0
        self._error_count = 0
        self._max_error_count = 0
        self._exception_count = 0
        self._to_stdout = True
        self._warning_count = 0
        self._max_warning_count = 0
        self._t_0 = self.START_SECS
        self._verbosity = getattr(args, 'verbosity', 1)
        self._rerun_cmd_str = None
        self._log_dir = None
        self._console_fh = sys.stderr if stderr else sys.stdout
        ProcInfo._init_term()

        # Set log directory from args if provided
        if hasattr(args, 'log_dir'):
            self.log_dir = args.log_dir  # Use the property setter
        pass  # for auto-indentation

    def set_log_to_file(self, val: bool) -> ProcInfoT:
        """
        Set whether or not to log to a file.

        This method sets the flag that determines whether logging information
        should be written to a file. By default, logging to a file is enabled,
        but this can be controlled using this method.

        Parameters
        ----------
        val : bool
            Flag indicating whether to log to a file (True) or not (False).

        Returns
        -------
        ProcInfoT
            Returns the instance of ProcInfo to allow for method chaining.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> proc.set_log_to_file(True)  # Enable logging to a file
        >>> proc.set_log_to_file(False)  # Disable logging to a file
        """
        self._log_to_file = bool(val)
        return self

    def set_args(self, args: argparse.Namespace) -> ProcInfoT:
        """
        Set the command-line arguments for the process.

        This method initializes the command-line arguments provided to the process.
        It also sets various flags based on the arguments, such as debugging and verbosity levels.

        Parameters
        ----------
        args : argparse.Namespace
            The namespace object containing the command-line arguments.

        Returns
        -------
        ProcInfoT
            Returns the instance of ProcInfo to allow for method chaining.

        Example
        -------
        >>> import argparse
        >>> parser = argparse.ArgumentParser()
        >>> parser.add_argument('--debug', action='store_true')
        >>> parser.add_argument('--verbosity', type=int, default=1)
        >>> args = parser.parse_args(['--debug', '--verbosity', '2'])
        >>> proc = ProcInfo(args)
        >>> proc.set_args(args)

        Notes
        -----
        - The method checks for the presence of debugging-related arguments and sets the internal `_debug` flag accordingly.
        - It also determines whether output should be directed to stdout or not based on the provided arguments.
        - The verbosity level is adjusted based on the `verbosity` or `verbose` arguments.
        """
        self._args = args
        self._debug = False
        for attr in ["debug", "debug_on", "debugging", "debugging_on"]:
            if self.get_arg(attr):
                self._debug = True
        if not self.get_arg('no_stdout', False) or self.get_arg('to_stdout', True):
            self._to_stdout = True
        elif self.get_arg('no_stdout', False) or not self.get_arg('to_stdout', True):
            self._to_stdout = False
        if self.get_arg('verbosity', False) is not False:
            self._verbosity = self.get_arg('verbosity', False)
        elif self.get_arg('verbose', False) is not False:
            self._verbosity = self.get_arg('verbose', False)
        else:
            self._verbosity = 1
        return self

    @property
    def max_warning_count(self) -> int:
        """
        Get the maximum number of warnings allowed before taking action.

        This property returns the maximum number of warnings that can occur
        before a specific action is taken (e.g., stopping the process). A value
        of 0 means there is no maximum limit.

        Returns
        -------
        int
            The maximum number of warnings allowed (0 = no max).

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> max_warnings = proc.max_warning_count
        """
        return self._max_warning_count

    @max_warning_count.setter
    def max_warning_count(self, val: int):
        """
        Set the maximum number of warnings allowed before taking action.

        This property sets the maximum number of warnings that can occur
        before a specific action is taken (e.g., stopping the process). A value
        of 0 means there is no maximum limit.

        Parameters
        ----------
        val : int
            The maximum number of warnings allowed (0 = no max).

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> proc.max_warning_count = 10  # Set maximum warnings to 10
        """
        self._max_warning_count = val

    @property
    def warning_count(self) -> int:
        """
        Get the current count of warnings.

        This property returns the number of warnings that have occurred so far
        in the process.

        Returns
        -------
        int
            The current count of warnings.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> warnings = proc.warning_count
        """
        return self._warning_count

    @property
    def max_error_count(self) -> int:
        """
        Get the maximum number of errors allowed before taking action.

        This property returns the maximum number of errors that can occur
        before a specific action is taken (e.g., stopping the process). A value
        of 0 means there is no maximum limit.

        Returns
        -------
        int
            The maximum number of errors allowed (0 = no max).

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> max_errors = proc.max_error_count
        """
        return self._max_error_count

    @max_error_count.setter
    def max_error_count(self, val: int):
        """
        Set the maximum number of errors allowed before taking action.

        This property sets the maximum number of errors that can occur
        before a specific action is taken (e.g., stopping the process). A value
        of 0 means there is no maximum limit.

        Parameters
        ----------
        val : int
            The maximum number of errors allowed (0 = no max).

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> proc.max_error_count = 5  # Set maximum errors to 5
        """
        self._max_error_count = val

    @property
    def error_count(self) -> int:
        """
        Get the current count of errors.

        This property returns the number of errors that have occurred so far
        in the process.

        Returns
        -------
        int
            The current count of errors.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> errors = proc.error_count
        """
        return self._error_count

    @property
    def critical_count(self) -> int:
        """
        Get the current count of critical errors.

        This property returns the number of critical errors that have occurred so far
        in the process.

        Returns
        -------
        int
            The current count of critical errors.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> critical_errors = proc.critical_count
        """
        return self._critical_count

    @property
    def main_t_0(self) -> datetime.datetime:
        """
        Get the datetime.datetime of the start of the script.

        This property returns the datetime object representing the start time
        of the script.

        Returns
        -------
        datetime.datetime
            The start time of the script.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> start_time = proc.main_t_0
        """
        return self.START_DATETIME

    @property
    def initial_wd(self) -> str:
        """
        Get the initial working directory of this script.

        This property returns the initial working directory from which the
        script was started.

        Returns
        -------
        str
            The initial working directory of the script.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> initial_dir = proc.initial_wd
        """
        return self.START_WORKING_DIRECTORY

    @property
    def main_proc_realpath(self) -> str:
        """
        Get the 'realpath' of the 'main' script.

        This property returns the canonical path of the main script, resolving
        any symbolic links.

        Returns
        -------
        str
            The canonical path of the main script.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> realpath = proc.main_proc_realpath
        """
        return self.MAIN_REALPATH

    @property
    def main_abspath(self) -> str:
        """
        Get the 'abspath' of the 'main' script.

        This property returns the absolute path of the main script.

        Returns
        -------
        str
            The absolute path of the main script.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> abspath = proc.main_abspath
        """
        return self.MAIN_ABSPATH

    @property
    def main_basename(self) -> str:
        """
        Get the basename (resolved from symlinks) of the 'main' script.

        This property returns the base name of the main script, resolving any
        symbolic links.

        Returns
        -------
        str
            The base name of the main script.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> basename = proc.main_basename
        """
        return self.MAIN_BASENAME

    @property
    def basename_no_ext(self) -> str:
        """
        Get the basename (resolved from symlinks) of the 'main' script without the last extension.

        This property returns the base name of the main script, resolving any
        symbolic links and removing the last extension.

        Returns
        -------
        str
            The base name of the main script without the last extension.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> basename_no_ext = proc.basename_no_ext
        """
        return self.MAIN_BASENAME_NO_EXT

    @property
    def pid(self) -> int:
        """
        Get the PID of the 'main' script.

        This property returns the process ID of the main script.

        Returns
        -------
        int
            The process ID of the main script.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> process_id = proc.pid
        """
        return self.MAIN_PID

    @property
    def main_dirname(self) -> str:
        """
        Get the 'dirname' of the 'main' script.

        This property returns the directory name of the main script.

        Returns
        -------
        str
            The directory name of the main script.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> dirname = proc.main_dirname
        """
        return self.MAIN_DIRNAME

    @property
    def short_start_timestamp(self) -> str:
        """
        Get a short string of the timestamp for the start-time of 'main'.

        This property returns a short string representation of the start time
        of the main script.

        Returns
        -------
        str
            A short string representation of the start time of the main script.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> short_timestamp = proc.short_start_timestamp
        """
        return self.START_SHORT_TIMESTAMP_STR

    @property
    def start_timestamp(self) -> str:
        """
        Get a string of the timestamp for the start-time of 'main'.

        This property returns a string representation of the start time
        of the main script.

        Returns
        -------
        str
            A string representation of the start time of the main script.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> timestamp = proc.start_timestamp
        """
        return self.START_TIMESTAMP_STR

    @property
    def unique_basename(self) -> str:
        """
        Get a unique basename (for creating new files) based on the 'main' script name.

        This property returns a unique base name derived from the name of the main script,
        which can be used for creating new files.

        Returns
        -------
        str
            A unique base name based on the main script name.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> unique_name = proc.unique_basename
        """
        return self.UNIQUE_BASENAME

    @property
    def rerun_command_str(self) -> str:
        """
        Get the string needed to re-run this command.

        This property returns the string that can be used to re-run the current
        command exactly as it was originally executed.

        Returns
        -------
        str
            The command string needed to re-run this command.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> rerun_command = proc.rerun_command_str
        """
        return self._rerun_cmd_str

    @property
    def log_dir(self) -> str:
        """
        Get the directory to which logs are written.

        This property returns the directory path where log files are stored.

        Returns
        -------
        str
            The directory path for log files.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> log_directory = proc.log_dir
        """
        if self._log_dir is None:
            # Set a default log directory if none is provided
            self._log_dir = self.get_arg('output_dir', self.START_WORKING_DIRECTORY)
            pass  # for auto-indentation
        return self._log_dir

    @log_dir.setter
    def log_dir(self, path: str) -> None:
        """
        Set the directory path for logging and ensure the directory exists.

        This setter assigns the log directory path for the process. If the specified
        directory does not exist, it will be created automatically, ensuring that
        logging operations can proceed without errors. This setup is useful for
        long-running or complex processes that require detailed logging in a
        specified location.

        Parameters
        ----------
        path : str
            The directory path where log files will be saved.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> proc.log_dir = "/path/to/logs"  # Set log directory and create if missing

        Notes
        -----
        - The directory will be created if it doesn’t already exist.
        - A message is logged to confirm the directory creation.
        """
        # Assign the provided path to the _log_dir attribute
        self._log_dir = path

        # Check if the directory exists; create it if not
        if not os.path.exists(self._log_dir):
            os.makedirs(self._log_dir, exist_ok=True)  # Ensure directory creation
            self.info(f"Created log directory: {self._log_dir}")  # Log directory creation
            pass  # for auto-indentation
        pass  # for auto-indentation

    @property
    def args(self) -> argparse.Namespace:
        """
        Get the command-line arguments namespace.

        This property returns the namespace object that contains the parsed
        command-line arguments.

        Returns
        -------
        argparse.Namespace
            The namespace object with command-line arguments.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> arguments = proc.args
        """
        return self._args

    def _get_argparse_info(self, dest):
        """
        Get the command-line argument string and help text for an args attribute name.

        This method retrieves the command-line argument string and the help text
        for a specified argument attribute name. It also checks if the argument
        was provided in the command line.

        Parameters
        ----------
        dest : str
            The destination name of the argument attribute.

        Returns
        -------
        tuple
            A tuple containing the argument string, help text, and a boolean indicating
            if the argument was provided.

        Raises
        ------
        IndexError
            If there is an issue accessing the argument's option strings or help text.

        Example
        -------
        >>> parser = argparse.ArgumentParser()
        >>> parser.add_argument('--verbosity', type=int, help="Set the verbosity level.")
        >>> args = parser.parse_args()
        >>> proc = ProcInfo(args)
        >>> arg_string, help_text, provided = proc._get_argparse_info('verbosity')
        >>> print(arg_string, help_text, provided)
        --verbosity Set the verbosity level. False
        """
        provided = False
        for action in self._parser._actions:
            if action.dest == dest:
                for arg in action.option_strings:
                    if arg in sys.argv[1:]:
                        provided = True
                        break
                try:
                    if action.option_strings:
                        return action.option_strings[0], action.help, provided
                    else:
                        return '', action.help, provided
                except IndexError as err:
                    self.err("Failed to get argparse info.")
                    self.err(f" - action={action}")
                    self.err(f" - action.option_strings={action.option_strings}")
                    self.err(f" - action.help={action.help}")
                    self.err(f" - provided={provided}")
                    raise err
        return dest, '', provided

    def get_settings_info(self, include_env: bool = True, include_args: bool = True) -> list:
        """
        Retrieve information about the settings used to run the process.

        This method collects information about the environment, command-line arguments,
        and other settings used to run the current process. It returns a list of lists,
        where each sublist contains a description and the corresponding value.

        Parameters
        ----------
        include_env : bool, optional
            Whether to include environment variables in the information (default is True).
        include_args : bool, optional
            Whether to include command-line arguments in the information (default is True).

        Returns
        -------
        list
            A list of lists containing the setting descriptions and their values.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> settings_info = proc.get_settings_info()
        >>> for setting in settings_info:
        >>>     print(f"{setting[0]}: {setting[1]}")

        Notes
        -----
        - The returned list includes:
            - The command to re-run the process.
            - The start datetime and directory.
            - The log directory and log file path.
            - Environment variables (if `include_env` is True).
            - Command-line arguments and their values (if `include_args` is True).
        """
        info = [
            ['Command to re-run', self.rerun_command_str],
            ['Start Datetime', self.START_DATETIME],
            ['Start Directory', self.START_WORKING_DIRECTORY],
            ['Log Directory', self.log_dir],
            ['Log File', self.logfile],
            ['Settings Log', os.path.join(self.log_dir, f"settings-{ProcInfo.START_SHORT_TIMESTAMP_STR}.log")],
        ]
        if include_env:
            info.append(['Environment Info:'])
            for k, v in os.environ.items():
                v = v.replace("'", "\\'")
                info.append([f"${k}", v])
        if include_args:
            for row in self.get_args_info():
                info.append(row)
        return info

    def get_arg(self, name, default=None, set_it=False) -> Any:
        """
        Get the value of a command-line argument if available, or return a default value.

        This method retrieves the value of a specified command-line argument from
        the argument namespace. If the argument is not available, it returns the
        provided default value. Optionally, it can set the default value to the
        argument if it is not present.

        Parameters
        ----------
        name : str
            The name of the argument to retrieve.
        default : Any, optional
            The default value to return if the argument is not available (default is None).
        set_it : bool, optional
            Flag indicating whether to set the default value to the argument if it is not present (default is False).

        Returns
        -------
        Any
            The value of the argument if available, otherwise the default value.

        Example
        -------
        >>> import argparse
        >>> parser = argparse.ArgumentParser()
        >>> parser.add_argument('--verbosity', type=int, default=1)
        >>> args = parser.parse_args()
        >>> proc = ProcInfo(args)
        >>> verbosity = proc.get_arg('verbosity', 0)
        >>> print(verbosity)
        1
        """
        if self._args is None:
            return default
        if hasattr(self._args, name):
            return getattr(self._args, name)
        if set_it:
            setattr(self._args, name, default)
        return default

    @property
    def logger(self) -> logging.Logger:
        """
        Get the logger instance.

        This property returns the logger instance used for logging messages.
        If the logger is not already initialized, it initializes it.

        Returns
        -------
        logging.Logger
            The logger instance.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> logger = proc.logger
        >>> logger.info("This is an info message.")
        """
        if ProcInfo._logger is None:
            self._init_logger()
        return ProcInfo._logger

    @property
    def coarse_elapsed_td(self) -> datetime.timedelta:
        """
        Get a coarse elapsed time as a timedelta without milliseconds.

        This property returns the elapsed time since the start of the script
        as a timedelta object, rounded to the nearest second.

        Returns
        -------
        datetime.timedelta
            The elapsed time since the start of the script, rounded to the nearest second.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> elapsed_time = proc.coarse_elapsed_td
        >>> print(elapsed_time)
        0:01:23
        """
        return datetime.timedelta(seconds=int(time.monotonic() - CommonConstants.START_SECS))

    def now(self) -> float:
        """
        Get the current monotonic time.

        This method returns the current monotonic time, which is useful for measuring
        elapsed time intervals.

        Returns
        -------
        float
            The current monotonic time.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> current_time = proc.now()
        >>> print(current_time)
        123456.789
        """
        return time.monotonic()

    def _get_log_filename(self) -> str:
        """
        Generate a unique filename for the log file.

        This method generates a unique filename for the log file based on the provided
        arguments. It ensures that the log directory exists and creates it if necessary.

        Returns
        -------
        str
            The unique filename for the log file.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> log_filename = proc._get_log_filename()
        >>> print(log_filename)
        /path/to/log/directory/logfile.log
        """
        log_filename = self.get_arg('log_filename')
        if log_filename is not None:
            return log_filename
        self._log_dir = self.get_arg('log_dir', self.get_arg('output_dir'))
        if self._log_dir is None:
            if self.get_arg('output') is not None:
                self._log_dir = self.get_arg('output')
                if not os.path.isdir(self._log_dir):
                    self._log_dir = os.path.dirname(self._log_dir)
                    pass  # for auto-indentation
                pass  # for auto-indentation
            else:
                self._log_dir = self.START_WORKING_DIRECTORY
                pass  # for auto-indentation
        if not os.path.exists(self._log_dir):
            os.makedirs(self._log_dir)
            pass  # for auto-indentation
        return self.get_unique_filename('log', directory=self._log_dir)

    def _init_logger(self) -> None:
        """
        Initialize and configure the logger.

        This method sets up the logger for the process, configuring the log level,
        log format, and log file. It ensures that the logger is initialized only once.
        If logging to a file is enabled, it creates the necessary log directory and file.
        It also constructs the command string needed to re-run the process.

        Raises
        ------
        ValueError
            If the specified log level is not a valid logging level.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> proc._init_logger()
        >>> logger = proc.logger
        >>> logger.info("Logger initialized.")

        Notes
        -----
        - The log format, date format, file mode, and log level are retrieved from the command-line arguments.
        - If logging to a file is enabled, the log file is created in the specified directory.
        - The method constructs a command string that can be used to re-run the process with the same arguments.
        """
        # raise Exception("Doh!")
        # print(f"{Term.BOLD}{Term.RED_BG}{Term.BLACK}INIT LOGGER!!!!{Term.NORMAL}")
        if ProcInfo._logger is not None:
            self.warning("(Re)setting args value for {self.__class__.__name__} "
                         "after logger has been configured. One or more "
                         "Logger(s) may not contain all output.")
            pass  # for auto-indentation
        log_line_format = self.get_arg('log_line_format', '%(asctime)s %(levelname)-8s %(message)s')
        log_date_format = self.get_arg('log_date_format', '%Y-%m-%d %H:%M:%S')
        log_file_mode = self.get_arg('log_file_mode', 'a')
        log_level = self.get_arg('log_level', 'DEBUG')
        if hasattr(logging, log_level):
            log_level = getattr(logging, log_level)
        else:
            raise ValueError("Unable to set file logging level to "
                             f"'{log_level}'."
                             f" There is no logging.{log_level} level.")
        if self._log_to_file:
            self.logfile = self._get_log_filename()
            if not os.path.exists(os.path.dirname(self.logfile)):
                os.makedirs(os.path.dirname(self.logfile), exist_ok=True)
                pass  # for auto-indentation
        else:
            self.logfile = None
            pass  # for auto-indentation
        logging.basicConfig(
            level=log_level,
            format=log_line_format,
            datefmt=log_date_format,
            filename=self.logfile,
            filemode=log_file_mode,
        )
        ProcInfo._logger = logging.getLogger()
        if self._log_to_file:
            self.info(f"Writing to log file '{self.logfile}'")
            self._rerun_cmd_str = []
            for arg in sys.argv:
                if " " in arg:
                    arg = arg.replace("\\", "\\\\")
                    arg = arg.replace("'", "\\'")
                    arg = f"'{arg}'"
                    pass  # for auto-indentation
                self._rerun_cmd_str.append(arg)
            self._rerun_cmd_str = f"cd {self.START_WORKING_DIRECTORY} && " + " ".join(self._rerun_cmd_str)
            self.info(f"To Re-run This Command:\n{self._rerun_cmd_str}")
            self.info(f"DEBUG LEVEL: {logging.DEBUG}")
            self.info(f"Global Log Level: {logging.getLogger().getEffectiveLevel()}")
            self.info(f"This ProcInfo Log Level: {ProcInfo._logger.getEffectiveLevel()}")
            pass  # for auto-indentation
        pass  # for auto-indentation

    def get_unique_filename(self, extension: str = 'txt', basename: str = None, directory: str = None, max_tries: int = 1000) -> str:
        """
        Generate a unique filename with the specified properties.

        This method attempts to generate a unique filename with the given extension,
        basename, and directory. If the filename already exists, it appends a number
        to the basename until a unique filename is found or the maximum number of tries
        is reached.

        Parameters
        ----------
        extension : str, optional
            The file extension to use (default is 'txt').
        basename : str, optional
            The base name to use for the file (default is None).
        directory : str, optional
            The directory in which to create the file (default is the starting working directory).
        max_tries : int, optional
            The maximum number of attempts to find a unique filename (default is 1000).

        Returns
        -------
        str
            A unique filename with the specified properties.

        Raises
        ------
        NoUniquePathException
            If unable to find a unique filename after the specified number of tries.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> unique_filename = proc.get_unique_filename(extension='log', basename='process', directory='/logs')
        >>> print(unique_filename)
        /logs/process.log
        """
        extension = f".{extension}" if extension else ""
        directory = directory if directory is not None else self.START_WORKING_DIRECTORY
        if not basename:
            filename = os.path.join(directory, f"{self.TIMESTAMP_BASENAME}{extension}")
            if not os.path.exists(filename):
                return filename
            basename = self.UNIQUE_BASENAME
            pass  # for auto-indentation
        num = 0
        filename = os.path.join(directory, f"{basename}{extension}")
        while os.path.exists(filename):
            num += 1
            if num > max_tries:
                raise NoUniquePathException(
                    "Unable to find an unused and non-existent "
                    f"filename with base '{basename}' and extension"
                    f" '{extension}' in directory '{directory}' after"
                    f" {num:,} tries.")
            filename = os.path.join(directory, f"{basename}-{num:03d}{extension}")
            pass  # for auto-indentation
        return filename

    def get_unique_path(self, extension: str = None, basename: str = None, directory: str = None, max_tries: int = 1000, create: bool = True) -> str:
        """
        Generate a unique directory path with the specified properties.

        This method attempts to generate a unique directory path with the given extension,
        basename, and directory. If the path already exists, it appends a number to the
        basename until a unique path is found or the maximum number of tries is reached.

        Parameters
        ----------
        extension : str, optional
            The extension to use for the path (default is None).
        basename : str, optional
            The base name to use for the path (default is None).
        directory : str, optional
            The directory in which to create the path (default is the starting working directory).
        max_tries : int, optional
            The maximum number of attempts to find a unique path (default is 1000).
        create : bool, optional
            Flag indicating whether to create the directory if it does not exist (default is True).

        Returns
        -------
        str
            A unique directory path with the specified properties.

        Raises
        ------
        NoUniquePathException
            If unable to find a unique path after the specified number of tries.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> unique_path = proc.get_unique_path(basename='process_data', directory='/data')
        >>> print(unique_path)
        /data/process_data
        """
        extension = f".{extension}" if extension else ""
        directory = directory if directory is not None else self.START_WORKING_DIRECTORY
        if not basename:
            filename = os.path.join(directory, f"{self.TIMESTAMP_BASENAME}{extension}")
            if not os.path.exists(filename):
                return filename
            basename = self.UNIQUE_BASENAME
            pass  # for auto-indentation
        num = 0
        fullpath = os.path.join(directory, f"{basename}")
        while os.path.exists(fullpath):
            num += 1
            if num > max_tries:
                raise NoUniquePathException(
                    "Unable to find an unused and non-existent "
                    f"directory path with base '{basename}' in directory '{directory}' after"
                    f" {num:,} tries.")
            fullpath = os.path.join(directory, f"{basename}-{num:03d}")
            pass  # for auto-indentation
        if create:
            self.mkdir(fullpath)
            pass  # for auto-indentation
        return fullpath

    def mkdir(self, fullpath: str):
        """
        Create a directory if it does not already exist.

        This method creates a directory at the specified path if it does not already exist.
        If the path exists but is not a directory, it raises an OSError.

        Parameters
        ----------
        fullpath : str
            The full path of the directory to create.

        Returns
        -------
        ProcInfo
            Returns the instance of ProcInfo to allow for method chaining.

        Raises
        ------
        OSError
            If the path exists but is not a directory.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> proc.mkdir('/path/to/directory')
        >>> print("Directory created.")
        """
        if os.path.exists(fullpath):
            if os.path.isdir(fullpath):
                self.debug(f"Not re-creating existing directory '{fullpath}'.")
                return self
            else:
                raise OSError(f"Cannot create directory '{fullpath}'. File exists and is not a directory.")
            pass  # for auto-indentation
        self.info(f"Creating directory '{fullpath}'.")
        os.makedirs(fullpath, exist_ok=True)
        return self

    @staticmethod
    def preserve_tell(file_handle: _io._IOBase) -> None:
        """
        Preserve the tell() method on a file handle.

        This static method iterates over the lines of a file handle, ensuring that
        the current file position is preserved after reading each line. This is useful
        when you need to read lines from a file without losing the current file position.

        Parameters
        ----------
        file_handle : _io._IOBase
            The file handle to read from.

        Yields
        ------
        str
            Lines read from the file handle.

        Example
        -------
        >>> with open('example.txt', 'r') as f:
        >>>     for line in ProcInfo.preserve_tell(f):
        >>>         print(line, end='')
        """
        while True:
            line = file_handle.readline()
            if not line:
                break
            yield line
            pass  # for auto-indentation
        pass  # for auto-indentation

    @staticmethod
    def _init_term() -> None:
        """
        Initialize terminal color settings for logging.

        This static method initializes the terminal color settings for logging messages.
        It sets different color codes for various log levels (debug, info, warning, error, etc.)
        based on whether terminal colors are enabled.

        Example
        -------
        >>> ProcInfo._init_term()
        """
        if ProcInfo._term_colors:
            ProcInfo._debu_prefix = f"[{Term.CYAN}DEBU{Term.NORMAL}]"
            ProcInfo._info_prefix = f"[{Term.GREEN}INFO{Term.NORMAL}]"
            ProcInfo._warn_prefix = f"[{Term.YELLOW}WARN{Term.NORMAL}]"
            ProcInfo._erro_prefix = f"[{Term.RED}ERRO{Term.NORMAL}]"
            ProcInfo._crit_prefix = f"[{Term.BOLD}{Term.RED}CRIT{Term.NORMAL}]"
            ProcInfo._fata_prefix = f"[{Term.BOLD}{Term.RED}FATA{Term.NORMAL}]"
            ProcInfo._exep_prefix = f"[{Term.BOLD}{Term.RED}EXCE{Term.NORMAL}]"
        else:
            ProcInfo._debu_prefix = "[DEBU]"
            ProcInfo._info_prefix = "[INFO]"
            ProcInfo._warn_prefix = "[WARN]"
            ProcInfo._erro_prefix = "[ERRO]"
            ProcInfo._crit_prefix = "[CRIT]"
            ProcInfo._fata_prefix = "[FATA]"
            ProcInfo._exep_prefix = "[EXCE]"
            pass  # for auto-indentation
        pass  # for auto-indentation

    def use_term_colors(self, val: bool) -> ProcInfoT:
        """
        Enable or disable terminal colors for logging.

        This method sets the flag to enable or disable terminal colors for logging messages.
        It then re-initializes the terminal settings to apply the changes.

        Parameters
        ----------
        val : bool
            Flag indicating whether to use terminal colors (True) or not (False).

        Returns
        -------
        ProcInfoT
            Returns the instance of ProcInfo to allow for method chaining.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> proc.use_term_colors(True)  # Enable terminal colors
        >>> proc.use_term_colors(False)  # Disable terminal colors
        """
        ProcInfo._term_colors = bool(val)
        self._init_term()
        return self

    @property
    def console_fh(self) -> _io._IOBase:
        """
        Get the console file handle.

        This property returns the file handle used for console output, which can be
        stdout, stderr, or a progress bar handle.

        Returns
        -------
        _io._IOBase
            The file handle used for console output.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> console_handle = proc.console_fh
        >>> print(console_handle)
        <_io.TextIOWrapper name='<stdout>' mode='w' encoding='UTF-8'>
        """
        return self._console_fh

    @property
    def has_bar(self) -> bool:
        """
        Check if the console file handle is attached to a progress bar.

        This property returns True if the console file handle is an instance of a
        progress bar (tqdm.tqdm), and False otherwise.

        Returns
        -------
        bool
            True if the console file handle is a progress bar, False otherwise.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> if proc.has_bar:
        >>>     print("Progress bar is attached to console handle.")
        >>> else:
        >>>     print("No progress bar attached to console handle.")
        """
        return isinstance(self._console_fh, tqdm.tqdm)

    def set_console_fh(self, val: _io._IOBase) -> ProcInfoT:
        """
        Set the console file handle.

        This method sets the file handle used for console output. It can be a regular
        file handle (e.g., stdout or stderr) or a progress bar handle (tqdm.tqdm).
        If the current console handle is not a progress bar, it flushes the output.

        Parameters
        ----------
        val : _io._IOBase
            The file handle to set for console output.

        Returns
        -------
        ProcInfoT
            Returns the instance of ProcInfo to allow for method chaining.

        Example
        -------
        >>> import tqdm
        >>> proc = ProcInfo(args)
        >>> with tqdm.tqdm(total=100) as pbar:
        >>>     proc.set_console_fh(pbar)
        >>>     for i in range(100):
        >>>         pbar.update(1)
        """
        if isinstance(val, tqdm.tqdm):
            self.debug(f"Setting Logger console_fh to a tqdm type='{type(val).__name__}' progress bar '{val}'.")
        else:
            self.debug(f"Setting Logger console_fh to '{val}'.")
            pass  # for auto-indentation
        if not self.has_bar:
            self._console_fh.flush()
        self._console_fh = val
        return self

    def _console(self, prefix: str, msg: str, lvl: int = -999):
        """
        Handle printing to stdout/stderr in a way that works with tqdm.

        This method handles printing messages to stdout or stderr, ensuring compatibility
        with tqdm progress bars. It considers verbosity levels and whether to prefix messages
        with elapsed time.

        Parameters
        ----------
        prefix : str
            The prefix to prepend to the message.
        msg : str
            The message to print.
        lvl : int, optional
            The verbosity level of the message (default is -999).

        Returns
        -------
        ProcInfoT
            Returns the instance of ProcInfo to allow for method chaining.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> proc._console("[INFO]", "This is an info message.", lvl=1)

        Notes
        -----
        - If the message is a list, the method recursively processes each item in the list.
        - Messages are only printed if the verbosity level is sufficient.
        - The method handles whether the console output is directed to a progress bar or a regular console.
        """
        if not ProcInfo._logger:
            self._init_logger()
            pass  # for auto-indentation
        if isinstance(msg, list):
            for m in msg:
                self._console(prefix, m, lvl)
                pass  # for auto-indentation
            return self
        if self._to_stdout and lvl <= self._verbosity:
            if self._prefix_console:
                prefix = f"{prefix} {self.coarse_elapsed_td}: "
            elif prefix:
                prefix = f"{prefix}: "
            else:
                prefix = ""
                pass  # for auto-indentation
            if self.has_bar:
                if msg.endswith("\n"):
                    self._console_fh.write(f"{prefix}{msg}", end="")
                else:
                    self._console_fh.write(f"{prefix}{msg}", end="\n")
                    pass  # for auto-indentation
            else:
                if msg.endswith("\n"):
                    self._console_fh.write(f"{prefix}{msg}")
                else:
                    self._console_fh.write(f"{prefix}{msg}\n")
                    pass  # for auto-indentation
                self._console_fh.flush()
                pass  # for auto-indentation
            pass  # for auto-indentation
        return self

    def info_table(self, table: 'unitable.Unitable', *args, lvl: int = 1, **kwargs) -> ProcInfoT:
        """
        Log a UniTable table.

        This method logs the content of a UniTable table, line by line, using the info log level.
        It ensures that the table content is logged in a readable format.

        Parameters
        ----------
        table : unitable.Unitable
            The UniTable table to log.
        lvl : int, optional
            The verbosity level of the log messages (default is 1).
        *args
            Additional arguments to pass to the info logging method.
        **kwargs
            Additional keyword arguments to pass to the info logging method.

        Returns
        -------
        ProcInfoT
            Returns the instance of ProcInfo to allow for method chaining.

        Example
        -------
        >>> import unitable
        >>> proc = ProcInfo(args)
        >>> table = unitable.Unitable()
        >>> table.add_row(["Header1", "Header2"])
        >>> table.add_row(["Value1", "Value2"])
        >>> proc.info_table(table, lvl=1)

        Notes
        -----
        - The method splits the table content into lines and logs each line separately.
        - The verbosity level controls whether the table content is logged based on the configured verbosity.
        """
        for line in table.draw().splitlines():
            self.info(f"{line}", *args, lvl=lvl, **kwargs)
            pass  # for auto-indentation
        return self

    def _do_output(self, console_prefix: str, to_console: bool, console_level: int, logger_func: Callable, msg: int, *args, **kwargs) -> ProcInfoT:
        """
        Handle output to console and log file.

        This method handles output to the console and the log file. It prints the
        message to the console if `to_console` is True and logs the message using
        the provided logging function if `_log_to_file` is True.

        Parameters
        ----------
        console_prefix : str
            The prefix to prepend to the console message.
        to_console : bool
            Flag indicating whether to print the message to the console.
        console_level : int
            The verbosity level for console output.
        logger_func : Callable
            The logging function to use for logging the message.
        msg : int
            The message to log.
        *args
            Additional arguments to pass to the logging function.
        **kwargs
            Additional keyword arguments to pass to the logging function.

        Returns
        -------
        ProcInfoT
            Returns the instance of ProcInfo to allow for method chaining.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> proc._do_output("[INFO]", True, 1, proc.logger.info, "This is an info message.")
        """
        if to_console:
            self._console(console_prefix, msg, lvl=console_level)
            pass  # for auto-indentation
        if self._log_to_file:
            logger_func(msg, *args, **kwargs)
            pass  # for auto-indentation
        return self

    def debug(self, msg: str, *args, lvl: int = 1, **kwargs) -> ProcInfoT:
        """
        Log a debugging message.

        This method logs a debugging message. It prints the message to the console
        if debugging is enabled and logs the message using the logger's debug method.

        Parameters
        ----------
        msg : str
            The debugging message to log.
        lvl : int, optional
            The verbosity level of the message (default is 1).
        *args
            Additional arguments to pass to the logger's debug method.
        **kwargs
            Additional keyword arguments to pass to the logger's debug method.

        Returns
        -------
        ProcInfoT
            Returns the instance of ProcInfo to allow for method chaining.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> proc.debug("This is a debug message.", lvl=2)
        """
        return self._do_output(self._debu_prefix, self._debug, lvl, self.logger.debug, msg, *args, **kwargs)

    def info(self, msg: str, *args, lvl: int = 1, **kwargs) -> ProcInfoT:
        """
        Log an informational message.

        This method logs an informational message. It prints the message to the console
        and logs the message using the logger's info method.

        Parameters
        ----------
        msg : str
            The informational message to log.
        lvl : int, optional
            The verbosity level of the message (default is 1).
        *args
            Additional arguments to pass to the logger's info method.
        **kwargs
            Additional keyword arguments to pass to the logger's info method.

        Returns
        -------
        ProcInfoT
            Returns the instance of ProcInfo to allow for method chaining.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> proc.info("This is an info message.", lvl=1)
        """
        return self._do_output(self._info_prefix, True, lvl, self.logger.info, msg, *args, **kwargs)

    def print(self, msg: str, *args, lvl: int = 1, **kwargs) -> ProcInfoT:
        """
        Log an informational message.

        This method logs an informational message. It prints the message to the console
        and logs the message using the logger's info method. This method is an alias for `info`.

        Parameters
        ----------
        msg : str
            The informational message to log.
        lvl : int, optional
            The verbosity level of the message (default is 1).
        *args
            Additional arguments to pass to the logger's info method.
        **kwargs
            Additional keyword arguments to pass to the logger's info method.

        Returns
        -------
        ProcInfoT
            Returns the instance of ProcInfo to allow for method chaining.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> proc.print("This is a print message.", lvl=1)
        """
        return self._do_output("", True, lvl, self.logger.info, msg, *args, **kwargs)

    def warning(self, msg: str, *args: argparse.Namespace, lvl: int = -999, **kwargs) -> 'ProcInfo':
        """
        Log a warning message.

        This method logs a warning message. It prints the message to the console
        and logs the message using the logger's warning method. If the maximum number
        of warnings is reached, it logs an error message and exits the process.

        Parameters
        ----------
        msg : str
            The warning message to log.
        lvl : int, optional
            The verbosity level of the message (default is -999).
        *args
            Additional arguments to pass to the logger's warning method.
        **kwargs
            Additional keyword arguments to pass to the logger's warning method.

        Returns
        -------
        ProcInfo
            Returns the instance of ProcInfo to allow for method chaining.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> proc.warning("This is a warning message.", lvl=1)
        """
        self._warning_count += 1
        if self._max_warning_count and self._warning_count >= self._max_warning_count:
            self._do_output(self._warn_prefix, True, lvl, self.logger.warning, msg, *args, **kwargs)
            if self._max_error_count:
                self.err(f"There {'was' if self._error_count == 1 else 'were'} {self._error_count:,d} "
                         f"errors ({self._max_error_count:,d} was the maximum).")
            else:
                self.err(f"There {'was' if self._error_count == 1 else 'were'} {self._error_count:,d} "
                         f"errors (There was no the maximum).")
                pass  # for auto-indentation
            self.fatal(f"There {'was' if self._warning_count == 1 else 'were'} {self._warning_count:,d} "
                       f"warnings which exceeds the maximum number of allowed warnings.")
            return self
        return self._do_output(self._warn_prefix, True, lvl, self.logger.warning, msg, *args, **kwargs)

    warn = warning

    def error(self, msg: str, *args, lvl: int = -999, **kwargs) -> ProcInfoT:
        """
        Log an error message.

        This method logs an error message. It prints the message to the console
        and logs the message using the logger's error method. If the maximum number
        of errors is reached, it logs a critical error message and exits the process.

        Parameters
        ----------
        msg : str
            The error message to log.
        lvl : int, optional
            The verbosity level of the message (default is -999).
        *args
            Additional arguments to pass to the logger's error method.
        **kwargs
            Additional keyword arguments to pass to the logger's error method.

        Returns
        -------
        ProcInfoT
            Returns the instance of ProcInfo to allow for method chaining.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> proc.error("This is an error message.", lvl=1)
        """
        self._error_count += 1
        if self._max_error_count and self._error_count >= self._max_error_count:
            self._do_output(self._erro_prefix, True, lvl, self.logger.error, msg, *args, **kwargs)
            if self._max_warning_count:
                self.err(f"There {'was' if self._warning_count == 1 else 'were'} {self._warning_count:,d} "
                         f"warnings ({self._max_warning_count:,d} was the maximum).")
            else:
                self.err(f"There {'was' if self._warning_count == 1 else 'were'} {self._warning_count:,d} "
                         f"warnings (There was no the maximum).")
                pass  # for auto-indentation
            self.fatal(f"There {'was' if self._error_count == 1 else 'were'} {self._error_count:,d} "
                       f"errors which exceeds the maximum number of allowed errors.")
            return self
        return self._do_output(self._erro_prefix, True, lvl, self.logger.error, msg, *args, **kwargs)

    err = error

    def critical(self, msg: str, *args, lvl: int = -999, **kwargs) -> ProcInfoT:
        """
        Log a critical error message.

        This method logs a critical error message. It prints the message to the console
        and logs the message using the logger's critical method. It also increments the
        critical error count.

        Parameters
        ----------
        msg : str
            The critical error message to log.
        lvl : int, optional
            The verbosity level of the message (default is -999).
        *args
            Additional arguments to pass to the logger's critical method.
        **kwargs
            Additional keyword arguments to pass to the logger's critical method.

        Returns
        -------
        ProcInfoT
            Returns the instance of ProcInfo to allow for method chaining.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> proc.critical("This is a critical error message.", lvl=1)
        """
        self._error_count += 1
        self._critical_count += 1
        return self._do_output(self._crit_prefix, True, lvl, self.logger.critical, msg, *args, **kwargs)

    def fatal(self, msg: str, exception: Exception = None, *args, lvl: int = -999, **kwargs) -> ProcInfoT:
        """
        Log a fatal error message and exit the process.

        This method logs a fatal error message. It prints the message to the console
        and logs the message using the logger's critical method. It also increments the
        error and critical error counts. If an exception is provided, it raises the
        exception; otherwise, it exits the process with a status code of 1.

        Parameters
        ----------
        msg : str
            The fatal error message to log.
        exception : Exception, optional
            The exception to raise after logging the message (default is None).
        lvl : int, optional
            The verbosity level of the message (default is -999).
        *args
            Additional arguments to pass to the logger's critical method.
        **kwargs
            Additional keyword arguments to pass to the logger's critical method.

        Returns
        -------
        ProcInfoT
            Returns the instance of ProcInfo to allow for method chaining.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> proc.fatal("This is a fatal error message.", lvl=1)

        Notes
        -----
        - If an exception is provided, it is raised after logging the message.
        - If no exception is provided, the process exits with a status code of 1.
        """
        self._error_count += 1
        self._critical_count += 1
        self._do_output(self._fata_prefix, True, lvl, self.logger.critical, msg, *args, **kwargs)
        if exception:
            raise exception
        return sys.exit(1)

    def exit_errors(self) -> None:
        """
        Exit the process with a fatal error if there were any errors.

        This method checks if there were any errors during the process execution.
        If there were any errors, it logs a fatal error message and exits the process.

        Returns
        -------
        None

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> proc.exit_errors()

        Notes
        -----
        - If there were errors, the method constructs a message indicating the number
          of errors and warnings, and exits the process with a fatal error.
        - If there were no errors, the method returns None.
        """
        if self._error_count > 0:
            errs = 's' if self._error_count > 1 else ''
            warns = 's' if self._warning_count > 1 else ''
            return self.fatal(f"There were {self._error_count:,d} error{errs} and "
                              f"{self._warning_count:,d} warning{warns}. Exiting.")
        return None

    def exception(self, msg: str, *args, lvl: int = -999, **kwargs) -> ProcInfoT:
        """
        Log an exception message.

        This method logs an exception message. It increments the error and critical
        error counts, prints the message to the console, and logs the message using
        the logger's error method.

        Parameters
        ----------
        msg : str
            The exception message to log.
        lvl : int, optional
            The verbosity level of the message (default is -999).
        *args
            Additional arguments to pass to the logger's error method.
        **kwargs
            Additional keyword arguments to pass to the logger's error method.

        Returns
        -------
        ProcInfoT
            Returns the instance of ProcInfo to allow for method chaining.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> try:
        >>>     raise ValueError("An example exception.")
        >>> except ValueError as e:
        >>>     proc.exception(f"Exception occurred: {e}")
        """
        self._error_count += 1
        self._critical_count += 1
        return self._do_output(self._exep_prefix, True, lvl, self.logger.error, msg, *args, **kwargs)

    def _append_dirs(self, arr, basedir, dirnames):
        """
        Append directories to a list based on a base directory and directory names.

        This method appends directory paths to the given list. The directory paths
        are constructed by joining the base directory with each directory name.

        Parameters
        ----------
        arr : list
            The list to which the directory paths will be appended.
        basedir : str
            The base directory.
        dirnames : list
            The directory names to append to the base directory.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> dirs = []
        >>> proc._append_dirs(dirs, '/base', ['dir1', 'dir2'])
        >>> print(dirs)
        ['/base/dir1', '/base/dir2']
        """
        for dirname in dirnames:
            arr.append(os.path.join(basedir, dirname))
            pass  # for auto-indentation
        pass  # for auto-indentation

    def get_config_file(self, search_path=None, filenames=None):
        """
        Get a configuration file based on specified criteria.

        This method searches for a configuration file in specified directories
        and with specified filenames. If a configuration file is found, it returns
        the full path to the file. Otherwise, it returns None.

        Parameters
        ----------
        search_path : SearchPath, optional
            The search path object to use for finding the configuration file.
            If None, a default search path is used.
        filenames : list, optional
            The filenames of the configuration file to search for. If None, default
            filenames based on the script name are used.

        Returns
        -------
        str or None
            The full path to the configuration file if found, otherwise None.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> config_file = proc.get_config_file()
        >>> if config_file:
        >>>     print(f"Configuration file found: {config_file}")
        >>> else:
        >>>     print("No configuration file found.")

        Notes
        -----
        - The default search path includes the current working directory, the user home directory,
          the ".config" directory in the user home directory, and the current script directory.
        - The default filenames include variations of the script basename with extensions such as
          ".conf", ".cfg", and ".config".
        """
        if self._config_file is not None:
            return self._config_file
        if search_path is None:
            search_path = SearchPath()
            search_path.required_perms = stat.S_IRUSR
            search_path.auto_append_dirs([".config", ".conf", ".cfg",
                                          "config", "conf", "cfg"])
            cwd = os.getcwd()
            search_path.append(cwd)
            if cwd != self.START_WORKING_DIRECTORY:
                search_path.append(self.START_WORKING_DIRECTORY)
                pass  # for auto-indentation
            homedir = os.path.expanduser("~")
            search_path.append(homedir)
            search_path.append(self.MAIN_DIRNAME)
        if filenames is None:
            bname = self.main_basename
            filenames = [
                f"{bname}", f".{bname}",
                f".{bname}.cfg", f"{bname}.cfg",
                f".{bname}.conf", f"{bname}.conf",
                f".{bname}.config", f"{bname}.config",
            ]
            pass  # for auto-indentation
        return search_path.find_first(filenames)

    def backup(self, filename):
        """
        Backup a file.

        This method creates a backup of the specified file by renaming it with a
        unique extension. If the file does not exist, it raises a FileNotFoundError.

        Parameters
        ----------
        filename : str
            The name of the file to backup.

        Returns
        -------
        str
            The new filename after renaming.

        Raises
        ------
        FileNotFoundError
            If the specified file does not exist.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> backup_filename = proc.backup('example.txt')
        >>> print(f"File backed up as: {backup_filename}")

        Notes
        -----
        - The method generates a unique filename with a '.bu' extension and renames
          the original file to the new filename.
        """
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Cannot backup '{filename}' since it does not exist.")
        new_filename = self.get_unique_filename(extension='bu', basename=filename)
        self.info(f"Backing up previous '{filename}' to '{new_filename}'.")
        return os.rename(filename, new_filename)

    def open(self, filename, mode='r', backup_before_overwrite=True, **kwargs):
        """
        Open a file, backing it up if it already exists.

        This method opens a file with the specified mode. If the file already exists and
        is opened in write mode, it backs up the file before overwriting it. It logs
        the action taken for the file.

        Parameters
        ----------
        filename : str
            The name of the file to open.
        mode : str, optional
            The mode in which to open the file (default is 'r').
        backup_before_overwrite : bool, optional
            Flag indicating whether to backup the file before overwriting (default is True).
        **kwargs
            Additional keyword arguments to pass to the open function.

        Returns
        -------
        file object
            The opened file object.

        Raises
        ------
        FileNotFoundError
            If the file does not exist and is opened in read mode.
        ValueError
            If the mode is not understood or the filename is not a regular file.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> with proc.open('example.txt', mode='w') as f:
        >>>     f.write("Hello, world!")

        Notes
        -----
        - The method logs the action taken, such as creating a new file, appending to
          an existing file, or backing up an existing file before overwriting it.
        - If the mode is read-only and the file does not exist, it logs a fatal error
          and exits the process.
        """
        if mode in {"r", "rb", "r+", "rb+", "rt", "rt+"}:
            self.info(f"Opening file '{filename}' with mode '{mode}'.")
            try:
                return open(filename, mode=mode, **kwargs)
            except FileNotFoundError as err:
                self.fatal(f"Unable to open '{filename}' with mode '{mode}': no such file or directory.",
                           exception=err)
                sys.exit(1)
                pass  # for auto-indentation
        if os.path.exists(filename) and not os.path.isfile(filename):
            raise ValueError(f"'{filename}' is not a regular file, so I can't open it with mode '{mode}'.")
        if mode not in {"w", "wb", "w+", "wb+", "wt", "wt+", "a", "ab", "a+", "ab+", "at", "at+"}:
            raise ValueError(f"Do not understand mode '{mode}', so I can't open '{filename}' for you.")
        if not os.path.exists(filename):
            self.info(f"Creating new file '{filename}' using mode '{mode}'.")
            return open(filename, mode=mode, **kwargs)
        elif mode in {"w", "wb", "w+", "wb+", "wt", "wt+"}:
            if backup_before_overwrite:
                self.backup(filename)
                pass  # for auto-indentation
            else:
                self.warn(f"Overwriting file '{filename}' using mode '{mode}'.")
                pass  # for auto-indentation
        elif mode in {"a", "ab", "a+", "ab+", "at", "at+"}:
            self.info(f"Appending to '{filename}' using mode '{mode}'.")
            pass  # for auto-indentation
        return open(filename, mode=mode, **kwargs)

    def Popen(self, cmd_args, **kwargs):
        """
        Run a command using subprocess.Popen() and log before running.

        This method runs a command using subprocess.Popen() after logging the command.
        It splits the command string into arguments if necessary and logs the command
        before execution.

        Parameters
        ----------
        cmd_args : str or list
            The command to run. If a string, it is split into arguments.
        **kwargs
            Additional keyword arguments to pass to subprocess.Popen().

        Returns
        -------
        subprocess.Popen
            The Popen object for the running command.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> proc.Popen("ls -l")

        Notes
        -----
        - The method logs the command string before running it.
        - If cmd_args is a string, it is split into arguments using shlex.split().
        """
        if isinstance(cmd_args, str):
            cmd_args = shlex.split(cmd_args)
            pass  # for auto-indentation
        cmd_str = "'" + "' '".join(cmd_args) + "'"
        self.info(f"Running: {cmd_str}")
        self._last_subprocess = subprocess.Popen(cmd_args, **kwargs)
        return self._last_subprocess

    run = Popen

    def run_cmd(self, cmd, fatal_on_fail=True):
        """
        Run a command and log the execution.

        This method runs a command using subprocess.run() and logs the command execution.
        If the command exits with a non-zero status, it logs an error or fatal message
        based on the fatal_on_fail flag.

        Parameters
        ----------
        cmd : list
            The command to run as a list of arguments.
        fatal_on_fail : bool, optional
            Flag indicating whether to log a fatal error and exit on failure (default is True).

        Returns
        -------
        subprocess.CompletedProcess
            The CompletedProcess object for the executed command.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> proc.run_cmd(["ls", "-l"])

        Notes
        -----
        - The method logs the command being run and its output.
        - If the command exits with a non-zero status, it logs an error or fatal message
          based on the fatal_on_fail flag.
        """
        self.info("Running:")
        self.info(f"{' '.join(cmd)}")
        proc = subprocess.run(cmd)
        if proc.returncode != 0:
            if fatal_on_fail:
                self.fatal(f"The {cmd[0]} command exited abnormally with exit code {proc.returncode}. Cannot continue.")
            else:
                self.warn(f"The {cmd[0]} command exited abnormally with exit code {proc.returncode}.")
            pass  # for auto-indentation
        return proc

    def run_proc(self, cmd_args, log_stdout=False, log_stderr=None, fail_fatal=True,
                 bufsize=-1, executable=None, stdin=None, stdout=None, stderr=None,
                 preexec_fn=None, close_fds=True, shell=False, cwd=None, env=None,
                 universal_newlines=None, startupinfo=None, creationflags=0,
                 restore_signals=True, start_new_session=False, pass_fds=(), *,
                 encoding=None, errors=None, text=None):
        """
        Run a command with optional logging.

        This method runs a command and minimally logs that the command was run
        (capturing the entire command-line). If log_stdout or log_stderr are True,
        it waits for the process to finish before returning.

        Parameters
        ----------
        cmd_args : str or list
            A string (e.g., "ps -auxw") which will be split into arguments or
            a list of strings which represent the arguments. The first argument
            should be the command to be run.
        log_stdout : bool, optional
            If True, captures the STDOUT from the command into the log (default is False).
        log_stderr : bool, optional
            If True, captures the STDERR from the command into the log (default is None,
            which means it will be set to the same value as log_stdout).
        fail_fatal : bool, optional
            If True, logs a critical error and exits non-zero if the command returns
            non-zero (default is True).
        bufsize : int, optional
            See subprocess.Popen() documentation (default is -1).
        executable : optional
            See subprocess.Popen() documentation.
        stdin : optional
            See subprocess.Popen() documentation.
        stdout : optional
            See subprocess.Popen() documentation.
        stderr : optional
            See subprocess.Popen() documentation.
        preexec_fn : optional
            See subprocess.Popen() documentation.
        close_fds : bool, optional
            See subprocess.Popen() documentation (default is True).
        shell : bool, optional
            See subprocess.Popen() documentation (default is False).
        cwd : str, optional
            See subprocess.Popen() documentation (default is None).
        env : dict, optional
            See subprocess.Popen() documentation (default is None).
        universal_newlines : bool, optional
            See subprocess.Popen() documentation (default is None).
        startupinfo : optional
            See subprocess.Popen() documentation.
        creationflags : int, optional
            See subprocess.Popen() documentation (default is 0).
        restore_signals : bool, optional
            See subprocess.Popen() documentation (default is True).
        start_new_session : bool, optional
            See subprocess.Popen() documentation (default is False).
        pass_fds : tuple, optional
            See subprocess.Popen() documentation (default is ()).
        encoding : str, optional
            See subprocess.Popen() documentation.
        errors : str, optional
            See subprocess.Popen() documentation.
        text : bool, optional
            See subprocess.Popen() documentation.

        Returns
        -------
        subprocess.CompletedProcess
            The CompletedProcess instance.

        Example
        -------
        >>> proc = ProcInfo(args)
        >>> result = proc.run_proc(["ls", "-l"], log_stdout=True)
        >>> print(result.stdout)

        Notes
        -----
        - If log_stdout or log_stderr are True, the method waits for the process to finish
          and captures the output.
        - If the command exits with a non-zero status and fail_fatal is True, the method
          logs a critical error and exits the process.
        """
        if isinstance(cmd_args, str):
            cmd_args = shlex.split(cmd_args)

        self.info(f"Running command: {' '.join(cmd_args)}")

        if log_stderr is None:
            log_stderr = log_stdout

        if log_stdout or log_stderr:
            stdout = subprocess.PIPE if log_stdout else stdout
            stderr = subprocess.PIPE if log_stderr else stderr

        proc = subprocess.Popen(
            cmd_args,
            bufsize=bufsize,
            executable=executable,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            preexec_fn=preexec_fn,
            close_fds=close_fds,
            shell=shell,
            cwd=cwd,
            env=env,
            universal_newlines=universal_newlines,
            startupinfo=startupinfo,
            creationflags=creationflags,
            restore_signals=restore_signals,
            start_new_session=start_new_session,
            pass_fds=pass_fds,
            encoding=encoding,
            errors=errors,
            text=text,
        )

        if log_stdout or log_stderr:
            out, err = proc.communicate()
            if log_stdout and out:
                self.info(f"STDOUT:\n{out}")
            if log_stderr and err:
                self.error(f"STDERR:\n{err}")
        else:
            proc.wait()

        if proc.returncode != 0:
            if fail_fatal:
                self.fatal(f"Command '{' '.join(cmd_args)}' failed with return code {proc.returncode}")
            else:
                self.warn(f"Command '{' '.join(cmd_args)}' failed with return code {proc.returncode}")

        return proc

    @classmethod
    def set_argparse_parser(cls, parser):
        """
        Set the argparse parser for the class.

        This method sets the argparse parser for the class, allowing other class methods
        such as `toggler` to utilize the parser for adding arguments.

        Parameters
        ----------
        parser : argparse.ArgumentParser
            The argparse parser to set for the class.

        Returns
        -------
        cls
            The class itself to allow for method chaining.

        Example
        -------
        >>> parser = argparse.ArgumentParser()
        >>> ProcInfo.set_argparse_parser(parser)
        """
        cls._parser = parser
        return cls

    @classmethod
    def toggler(cls, args, desc, default, dest):
        """
        Create a toggle-able option for the argparse parser.

        This method creates a toggle-able option for the argparse parser. It adds both
        "yes" and "no" versions of the option to the parser, allowing users to explicitly
        enable or disable the option.

        Parameters
        ----------
        args : list
            A list of arguments (e.g., ["-f", "--force"]).
        desc : str
            The description of the option.
        default : bool
            The default value of the option (True or False).
        dest : str
            The destination variable name for the option.

        Raises
        ------
        ValueError
            If the argparse parser is not set before calling this method, or if a duplicate
            argument name is encountered.

        Example
        -------
        >>> parser = argparse.ArgumentParser()
        >>> ProcInfo.set_argparse_parser(parser)
        >>> ProcInfo.toggler(["-v", "--verbose"], "Enable verbose output", default=False, dest="verbose")
        """
        if not hasattr(cls, '_parser') or not cls._parser:
            raise ValueError(f"Must set argparse parser using {cls.__name__}.set_argparse_parser() before calling this method.")
            pass  # for auto-indentation

        yes_args, no_args, first_arg_name = [], [], None
        for arg in args:
            if first_arg_name is None:
                first_arg_name = arg
                pass  # for auto-indentation
            if arg.startswith("-"):
                # -foo becomes --foo and --no-foo
                yes, no = "-" + arg, "--no" + arg
            else:
                # foo becomes -foo and -nofoo
                yes, no = "-" + arg, "-no" + arg
                pass  # for auto-indentation
            yes_args.append(yes)
            no_args.append(no)

        parser = cls._parser
        desc_yes = desc.split(" ", 1)
        desc_yes = desc_yes[0].capitalize() + ' ' + desc_yes[1] if len(desc_yes) > 1 else desc.capitalize()
        desc_no = "Don't " + desc

        parser.add_argument(
            *yes_args,
            default=default,
            action='store_true',
            dest=dest,
            help=f"{'✔ ' if default else '. '} {desc_yes}"
        )
        parser.add_argument(
            *no_args,
            default=default,
            action='store_false',
            dest=dest,
            help=f"{'✔ ' if not default else '. '}{desc_no}"
        )

        first_arg_name = first_arg_name[1:] if first_arg_name.startswith("-") else first_arg_name
        if first_arg_name in cls._toggle_args:
            raise ValueError(f"Duplicate arg '{first_arg_name}' encountered.")
            pass  # for auto-indentation

        cls._toggle_args[first_arg_name] = {'desc': desc_yes, 'dest': dest}
        pass  # for auto-indentation

    pass  # for auto-indentation for class definition


def _main():
    """
    Main function for testing this module.

    This function serves as the entry point for testing the functionality of this module.
    It sets up the argparse parser, parses command-line arguments, and runs tests based
    on the provided arguments.

    Example
    -------
    To run the module with debugging on and increased verbosity:
    $ python module_name.py --debug --verbose

    To test the logger functionality:
    $ python module_name.py --logger

    To test the file progress bar functionality:
    $ python module_name.py --fbar
    """
    print("Testing this module...")
    import argparse
    parser = argparse.ArgumentParser(
        prog=CommonConstants.MAIN_BASENAME,
        description='A module for running and logging processes that need reproducibility.')

    parser.add_argument('--debug', '-d', default=False, action='store_true', dest='debug', help="Turn debugging on.")
    parser.add_argument('--verbose', '-v', default=0, dest='verbosity', action='count', help="Increase verbosity. Can have multiple.")
    parser.add_argument('--fbar', default=False, dest='test_fbar', action='store_true', help="Test out the file progress bar.")
    parser.add_argument('--logger', default=False, dest='test_logger', action='store_true', help="Test out the logger.")
    parser.add_argument('--quiet', '-q', default=0, dest='quiet', action='count', help="Decrease verbosity. Can have multiple.")

    args = parser.parse_args()
    args.verbosity = 1 + args.verbosity - args.quiet

    if args.test_logger:
        proc = ProcInfo(args)
        proc.info("This is some info.")
        proc.warn("This is a warning.")
        proc.err("This is an error.")
        proc.debug("This is a debug message.")
        pass  # for auto-indentation

    if args.test_fbar:
        pass  # for auto-indentation

    return 0


if __name__ == "__main__":
    sys.exit(_main())
    pass  # for auto-indentation

# End
