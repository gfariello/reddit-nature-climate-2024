"""
This module provides a collection of constants and utility classes for time, scale,
and process-related conversions and formatting.

Classes:
    - TimeConversionConstants: Defines constants for time conversions (e.g., seconds in a minute, hour).
    - ScaleConversionConstants: Holds constants for scale prefixes (e.g., kilo, mega) and their values.
    - MainProcessConstants: Contains constants related to the main process, such as start time and file paths.
    - CommonConstants: Combines time, scale, and process constants for shared use across the module.
    - CommonFormattingBase: Offers utility methods for formatting times, scales, and numbers in a human-readable way.

Usage:
    Import specific constants or utilize the `CommonFormattingBase` class for formatted output.
"""

# __all__ defines the public interface of the module. It specifies the classes
# that will be accessible when the module is imported with a wildcard import (e.g., `from module import *`).
# Only the names listed here will be imported in that case.
__all__ = [
    'TimeConversionConstants',
    'ScaleConversionConstants',
    'MainProcessConstants',
    'CommonConstants',
    'CommonFormattingBase'
]

import os
import datetime
import time
import __main__
from typing import Tuple


class TimeConversionConstants:
    """
    Constants for converting time units to seconds.

    This class provides constants for various time intervals (e.g., minute, hour, day),
    allowing for easy conversion to seconds. These constants are primarily useful for
    calculations involving time intervals in applications needing precise time conversion.

    Attributes:
        SECS_PER_MINUTE (int): Number of seconds in one minute (60).
        SECS_PER_HOUR (int): Number of seconds in one hour (3600).
        SECS_PER_DAY (int): Number of seconds in one day (86400).
        SECS_PER_WEEK (int): Number of seconds in one week (604800).
        SECS_PER_YEAR (int): Approximate number of seconds in one year (31557600).
        SECS_PER_MONTH (int): Approximate number of seconds in one month (2629800).

    Example Usage:
        >>> seconds_in_two_days = 2 * TimeConversionConstants.SECS_PER_DAY
        >>> print(seconds_in_two_days)
        172800
    """

    # Define the number of seconds in a minute
    SECS_PER_MINUTE = 60  # 60 seconds in 1 minute

    # Define the number of seconds in an hour
    SECS_PER_HOUR = 3600  # 3600 seconds in 1 hour

    # Define the number of seconds in a day
    SECS_PER_DAY = 86400  # 86400 seconds in 1 day

    # Define the number of seconds in a week
    SECS_PER_WEEK = 604800  # 604800 seconds in 1 week

    # Approximate number of seconds in one year (365.25 days for leap year adjustment)
    SECS_PER_YEAR = 31557600  # 31557600 seconds in 1 year

    # Approximate number of seconds in one month (average 30.44 days)
    SECS_PER_MONTH = 2629800  # 2629800 seconds in 1 month

    pass  # for auto-indentation


class ScaleConversionConstants:
    """
    Constants and methods for scale conversions.

    This class provides constants for converting various scale prefixes and symbols (e.g., kilo, mega)
    to their corresponding numeric values, aiding in handling large or small numerical values
    through unit prefixes.

    Attributes:
        SCALE_PREFIXES (list[str]): List of common scale prefixes (e.g., "kilo", "mega").
        SCALE_SYMBOLS (list[str]): List of symbols corresponding to each prefix (e.g., "k" for "kilo").
        SCALE_PREFIX_MAPPER (dict): Maps scale names to their numeric values (initialized in `init`).
        SCALE_SYMBOL_MAPPER (dict): Maps scale symbols to their numeric values (initialized in `init`).
        SCALE_MIN (float): Minimum scale value, representing "pico" (1e-12).
        PICO, NANO, MICRO, MILI, KILO, MEGA, GIGA, TERA, PETA, EXA, ZETTA, YOTTA:
            Named constants for various scale values (1e-12 to 1e24).

    Methods:
        get_scale(cls, name): Returns the scale factor for a given name or symbol.
        init(cls): Initializes scale mappings (must be called once to populate mappings).

    Example Usage:
        >>> ScaleConversionConstants.get_scale("kilo")
        1000.0
        >>> ScaleConversionConstants.get_scale("M")
        1000000.0
    """

    # List of scale names from smallest to largest
    SCALE_PREFIXES = ["pico", "nano", "micro", "milli", "", "kilo", "mega", "giga", "tera", "peta", "exa", "zetta", "yotta"]

    # Corresponding symbols for each scale name
    SCALE_SYMBOLS = ["p", "n", "μ", "m", "", "k", "M", "G", "T", "P", "E", "Z", "Y"]

    # Dictionary to map scale names to values (populated in `init`)
    SCALE_PREFIX_MAPPER = {}

    # Dictionary to map symbols to values (populated in `init`)
    SCALE_SYMBOL_MAPPER = {}

    # Minimum scale value, starting with "pico" at 1e-12
    SCALE_MIN = 1e-12

    # Scale values as constants for common usage
    PICO = 1e-12
    NANO = 1e-9
    MICRO = 1e-6
    MILI = 1e-3
    KILO = 1e3
    MEGA = 1e6
    GIGA = 1e9
    TERA = 1e12
    PETA = 1e15
    EXA = 1e18
    ZETTA = 1e21
    YOTTA = 1e24

    @classmethod
    def get_scale(cls, name):
        """
        Get the scale factor based on the name or symbol provided.

        Args:
            name (str): The name or symbol of the scale (e.g., "kilo", "M").

        Returns:
            float: The corresponding scale factor.

        Raises:
            ValueError: If the name or symbol is not found in the scale mappings.

        Example:
            >>> ScaleConversionConstants.get_scale("kilo")
            1000.0
            >>> ScaleConversionConstants.get_scale("M")
            1000000.0
        """
        # Check for uppercase name in the prefix mapper
        if name.upper() in ScaleConversionConstants.SCALE_PREFIX_MAPPER:
            return ScaleConversionConstants.SCALE_PREFIX_MAPPER[name.upper()]

        # Check for the name in the symbol mapper
        if name in ScaleConversionConstants.SCALE_SYMBOL_MAPPER:
            return ScaleConversionConstants.SCALE_SYMBOL_MAPPER[name]

        # Raise error if the name or symbol is invalid
        raise ValueError(f"No such scale prefix or symbol: '{name}'")

    @classmethod
    def init(cls):
        """
        Initialize scale mappings by populating `SCALE_PREFIX_MAPPER` and `SCALE_SYMBOL_MAPPER`.

        This method assigns numeric values to each scale prefix and symbol, starting from `SCALE_MIN`
        (1e-12) and increasing by powers of 1000 for each subsequent scale.

        Example:
            >>> ScaleConversionConstants.init()
            >>> ScaleConversionConstants.SCALE_PREFIX_MAPPER["KILO"]
            1000.0
        """
        # Start with the minimum scale value
        value = ScaleConversionConstants.SCALE_MIN

        # Populate mappings for each prefix and symbol
        for idx, name in enumerate(ScaleConversionConstants.SCALE_PREFIXES):
            setattr(cls, name.upper(), value)  # Set class attribute for prefix
            ScaleConversionConstants.SCALE_PREFIX_MAPPER[name.upper()] = value  # Map prefix to value
            symbol = ScaleConversionConstants.SCALE_SYMBOLS[idx]
            setattr(cls, symbol, value)  # Set class attribute for symbol
            ScaleConversionConstants.SCALE_SYMBOL_MAPPER[symbol] = value  # Map symbol to value
            value *= 1000  # Increase value by 1000 for the next scale

            pass  # for auto-indentation

        # Set the maximum scale value for reference
        setattr(cls, 'SCALE_MAX', value)

        pass  # for auto-indentation

    pass  # for auto-indentation


# Initialize mappings for scale constants
ScaleConversionConstants.init()


class MainProcessConstants:
    """
    Constants related to the `__main__` process execution.

    This class captures various process-related constants at the start of the main script, such as
    timestamps, process IDs, and paths. These constants provide information about the execution
    environment and can be useful for logging or tracking process metadata.

    Attributes:
        START_DATETIME (datetime): The timestamp when the script started.
        START_SECS (float): The monotonic start time in seconds.
        START_WORKING_DIRECTORY (str): The directory where the script was launched.
        MAIN_REALPATH (str): The real path to the main script file.
        MAIN_ABSPATH (str): The absolute path to the main script file.
        MAIN_BASENAME (str): The basename of the main script file.
        MAIN_BASENAME_NO_EXT (str): The basename of the main script without the file extension.
        MAIN_PID (int): The process ID of the main script.
        MAIN_DIRNAME (str): The directory of the main script file.
        START_SHORT_TIMESTAMP_STR (str): Short timestamp format (YYYYMMDD-HHMMSS).
        START_TIMESTAMP_STR (str): Full timestamp format (YYYY-MM-DD-HH:MM:SS).
        TIMESTAMP_BASENAME (str): Combined basename and timestamp.
        UNIQUE_BASENAME (str): Unique identifier combining basename, timestamp, and process ID.

    Example Usage:
        >>> print(MainProcessConstants.START_DATETIME)
        2024-11-09 12:34:56
        >>> print(MainProcessConstants.MAIN_BASENAME)
        "script_name"
    """

    START_DATETIME = datetime.datetime.now()  # Capture the start date and time of the script execution
    START_SECS = time.monotonic()  # Monotonic start time in seconds since an unspecified starting point
    START_WORKING_DIRECTORY = os.getcwd()  # Directory where the script was launched

    # Paths and file information
    MAIN_REALPATH = os.path.realpath(__main__.__file__)  # Real path to the main script file
    MAIN_ABSPATH = os.path.abspath(__main__.__file__)  # Absolute path to the main script file
    MAIN_BASENAME = os.path.basename(__main__.__file__)  # Basename (filename) of the main script file
    MAIN_BASENAME_NO_EXT = os.path.splitext(MAIN_BASENAME)[0]  # Basename without file extension

    # Process information
    MAIN_PID = os.getpid()  # Process ID of the main script
    MAIN_DIRNAME = os.path.dirname(os.path.abspath(__main__.__file__))  # Directory containing the main script

    # Timestamps for logging or file naming
    START_SHORT_TIMESTAMP_STR = START_DATETIME.strftime("%Y%m%d-%H%M%S")  # Short timestamp format (YYYYMMDD-HHMMSS)
    START_TIMESTAMP_STR = START_DATETIME.strftime("%Y-%m-%d-%H:%M:%S")  # Full timestamp format (YYYY-MM-DD-HH:MM:SS)

    # File naming conventions using timestamps and process ID
    TIMESTAMP_BASENAME = f"{MAIN_BASENAME_NO_EXT}-{START_SHORT_TIMESTAMP_STR}"  # Basename combined with timestamp
    UNIQUE_BASENAME = f"{MAIN_BASENAME_NO_EXT}-{START_SHORT_TIMESTAMP_STR}-{MAIN_PID}"  # Unique name with PID and timestamp

    pass  # for auto-indentation


class CommonConstants(TimeConversionConstants, ScaleConversionConstants, MainProcessConstants):
    """Common constants combining time, scale, and process-related constants."""

    pass  # for auto-indentation


class CommonFormattingBase(CommonConstants):
    """
    Base class providing common formatting and utility methods.

    This class combines various formatting utilities for use with time, byte size,
    and argument handling. It is intended to support other classes in formatting
    and processing data in a human-readable format.

    Attributes:
        _args (any): Stores the arguments passed to the instance, if set.

    Methods:
        args: Property that retrieves the current arguments.
        set_args(args): Sets and stores arguments for later use.
        class_attr_type_check(attr_val, attr_name, attr_type): Validates the type of an attribute.
        elapsed(t_0, t_n): Calculates the elapsed time between two moments.
        pbytes(num): Formats a byte value into a human-readable string.

    Example Usage:
        >>> formatter = CommonFormattingBase()
        >>> formatter.set_args(['arg1', 'arg2'])
        >>> print(formatter.args)
        ['arg1', 'arg2']
        >>> print(CommonFormattingBase.pbytes(1048576))
        "1.0MB"
    """

    @property
    def args(self) -> any:
        """
        Retrieve stored arguments.

        Returns:
            any: The stored arguments if set.
        """
        return self._args  # Return the stored arguments

    def set_args(self, args: any) -> "CommonFormattingBase":
        """
        Set and store arguments for the instance.

        Args:
            args (any): The arguments to be stored.

        Returns:
            CommonFormattingBase: The instance itself for chaining.
        """
        self._args = args  # Store the provided arguments
        return self  # Enable method chaining

    def class_attr_type_check(self, attr_val: any, attr_name: str, attr_type: type) -> "CommonFormattingBase":
        """
        Check the type of an attribute and raise an error if it is incorrect.

        Args:
            attr_val (any): The attribute value to check.
            attr_name (str): The name of the attribute.
            attr_type (type): The expected type of the attribute.

        Raises:
            ValueError: If `attr_val` is not of the expected `attr_type`.

        Example:
            >>> formatter.class_attr_type_check("text", "attr_name", str)  # Passes
            >>> formatter.class_attr_type_check(100, "attr_name", str)  # Raises ValueError
        """
        # Check if the attribute value is of the expected type
        if not isinstance(attr_val, attr_type):
            raise ValueError(
                f"The '{attr_name}' for a {type(self).__name__} must be of type {type(attr_type).__name__}. "
                f"Received a '{attr_val}' of type '{type(attr_val).__name__}' instead."
            )
        return self  # Enable method chaining

    @staticmethod
    def elapsed(t_0: float = None, t_n: float = None) -> float:
        """
        Calculate elapsed time between two time points.

        Args:
            t_0 (float, optional): The start time. Defaults to the process start time.
            t_n (float, optional): The end time. Defaults to the current monotonic time.

        Returns:
            float: The time elapsed between `t_0` and `t_n`.

        Example:
            >>> CommonFormattingBase.elapsed()  # Elapsed time from process start
            1.23
        """
        # Set `t_n` to the current monotonic time if not provided
        if t_n is None:
            t_n = time.monotonic()
            pass  # for auto-indentation

        # Set `t_0` to the start time if not provided
        if t_0 is None:
            t_0 = CommonConstants.START_SECS
            pass  # for auto-indentation

        return (t_n - t_0)  # Calculate and return the elapsed time

    @staticmethod
    def pbytes(num: float) -> str:
        """
        Format a byte value into a human-readable string.

        Args:
            num (float): The byte value to format.

        Returns:
            str: A formatted string representing the byte value with appropriate units.

        Example:
            >>> CommonFormattingBase.pbytes(1048576)
            "1.0MB"
        """
        val = None  # Initialize the formatted value

        # Determine the appropriate unit and format the value
        if num >= CommonConstants.PETA:
            val = "%0.1fPB" % (num / CommonConstants.PETA)  # Format in petabytes
        elif num >= CommonConstants.TERA:
            val = "%0.1fTB" % (num / CommonConstants.TERA)  # Format in terabytes
        elif num >= CommonConstants.GIGA:
            val = "%0.1fGB" % (num / CommonConstants.GIGA)  # Format in gigabytes
        elif num >= CommonConstants.MEGA:
            val = "%0.1fMB" % (num / CommonConstants.MEGA)  # Format in megabytes
        elif num >= CommonConstants.KILO:
            val = "%0.1fKB" % (num / CommonConstants.KILO)  # Format in kilobytes
        else:
            val = "%3s b" % (num)  # Format in bytes
            pass  # for auto-indentation

        return val  # Return the formatted byte value

    @staticmethod
    def prate(rate: float, unit: str = "") -> str:
        """
        Format a rate as a human-readable string with appropriate time intervals.

        Converts a rate into a string with units per second, minute, hour, or day,
        depending on the rate size. It also adapts to large unit prefixes
        (e.g., kilo, mega) if the rate is sufficiently high.

        Args:
            rate (float): The rate to format.
            unit (str, optional): The unit of measure for the rate (e.g., "B" for bytes).

        Returns:
            str: A formatted string representing the rate with appropriate units.

        Example:
            >>> CommonFormattingBase.prate(1000, "B")
            "1.0KB/s"
            >>> CommonFormattingBase.prate(0.1, "B")
            "8.6B/hr"
        """
        # Return "0{unit}/s" if rate is zero
        if not rate:
            return f"0{unit}/s"

        inv_rate = 1.0 / rate  # Calculate the inverse rate for time conversion
        rate_str: str  # Declare the formatted rate string

        # Determine the appropriate unit based on rate size and interval
        if inv_rate >= CommonConstants.SECS_PER_DAY:
            rate_str = f"{rate * CommonConstants.SECS_PER_DAY:0.1f}{unit}/day"  # Format in units per day
        elif inv_rate >= CommonConstants.SECS_PER_HOUR:
            rate_str = f"{rate * CommonConstants.SECS_PER_HOUR:0.1f}{unit}/hr"  # Format in units per hour
        elif inv_rate >= CommonConstants.SECS_PER_MINUTE:
            rate_str = f"{rate * CommonConstants.SECS_PER_MINUTE:0.1f}{unit}/min"  # Format in units per minute
        elif rate >= CommonConstants.PETA:
            rate_str = f"{rate / CommonConstants.PETA:0.1f}P{unit}/s"  # Format in petas per second
        elif rate >= CommonConstants.TERA:
            rate_str = f"{rate / CommonConstants.TERA:0.1f}T{unit}/s"  # Format in teras per second
        elif rate >= CommonConstants.GIGA:
            rate_str = f"{rate / CommonConstants.GIGA:0.1f}G{unit}/s"  # Format in gigas per second
        elif rate >= CommonConstants.MEGA:
            rate_str = f"{rate / CommonConstants.MEGA:0.1f}M{unit}/s"  # Format in megas per second
        elif rate >= CommonConstants.KILO:
            rate_str = f"{rate / CommonConstants.KILO:0.1f}K{unit}/s"  # Format in kilos per second
        else:
            rate_str = f"{rate:0.1f}{unit}/s"  # Default to units per second
            pass  # for auto-indentation

        return rate_str  # Return the formatted rate string

    @staticmethod
    def pbyterate(rate: float) -> str:
        """
        Format a byte rate as a human-readable string with per-second intervals.

        Args:
            rate (float): The rate in bytes per second.

        Returns:
            str: A formatted string representing the rate in bytes per second with units.

        Example:
            >>> CommonFormattingBase.pbyterate(1048576)
            "1.0MB/s"
        """
        return CommonFormattingBase.prate(rate, "B")  # Use `prate` with "B" as the unit

    @staticmethod
    def pnum(num: float) -> str:
        """
        Format a large number with appropriate unit prefixes.

        Converts a large number into a human-readable string with a suitable
        scale prefix (e.g., kilo, mega, giga). This is useful for representing
        large numbers in a compact and readable form.

        Args:
            num (float): The number to format.

        Returns:
            str: A formatted string with the number and an appropriate scale prefix.

        Example:
            >>> CommonFormattingBase.pnum(1000000)
            " 1.00M"
        """
        # Determine the appropriate unit prefix based on the number size
        if num >= CommonConstants.PETA:
            num = "%0.2fP" % (num / CommonConstants.PETA)  # Format in petas
        elif num >= CommonConstants.TERA:
            num = "%0.2fT" % (num / CommonConstants.TERA)  # Format in teras
        elif num >= CommonConstants.GIGA:
            num = "%0.2fG" % (num / CommonConstants.GIGA)  # Format in gigas
        elif num >= CommonConstants.MEGA:
            num = "%0.2fM" % (num / CommonConstants.MEGA)  # Format in megas
        elif num >= CommonConstants.KILO:
            num = "%0.2fK" % (num / CommonConstants.KILO)  # Format in kilos
        else:
            num = "%0.2f " % (num)  # No prefix needed
        return "%7s" % (num)  # Return the formatted number with right alignment

    @staticmethod
    def splitsecs(secs):
        """Split seconds into some value and unit.

        This will take some seconds and return a number and
        unit in a unit that is more representative of the
        time.

        Args:
            secs(int|foat): The number of seconds
        Returns:
            int|foat: The new value for the unit time
            str: The units (all lowercase)

        """
        val, units = "", ""
        if secs >= CommonConstants.SECS_PER_YEAR:
            val, units = secs / CommonConstants.SECS_PER_YEAR, "years"
        elif secs >= CommonConstants.SECS_PER_MONTH:
            val, units = secs / CommonConstants.SECS_PER_MONTH, "months"
        elif secs >= CommonConstants.SECS_PER_WEEK:
            val, units = secs / CommonConstants.SECS_PER_WEEK, "weeks"
        elif secs >= CommonConstants.SECS_PER_DAY:
            val, units = secs / CommonConstants.SECS_PER_DAY, "days"
        elif secs >= CommonConstants.SECS_PER_HOUR:
            val, units = secs / CommonConstants.SECS_PER_HOUR, "hours"
        elif secs >= CommonConstants.SECS_PER_MINUTE:
            val, units = secs / CommonConstants.SECS_PER_MINUTE, "mins"
        else:
            val, units = secs, "secs"
            pass
        return val, units

    @staticmethod
    def _secs_to_str(secs: float, divisor: float) -> Tuple[int, float]:
        """
        Convert seconds into a value and remainder using a given divisor.

        Args:
            secs (float): The number of seconds.
            divisor (float): The divisor to break down the seconds.

        Returns:
            tuple[int, float]: A tuple containing the divided value and the remaining seconds.

        Example:
            >>> CommonFormattingBase._secs_to_str(3661, 3600)
            (1, 61)
        """
        val = int(secs / divisor)  # Divide and convert to integer for whole units
        return val, secs - (val * divisor)  # Return quotient and remainder

    @staticmethod
    def secs2str(secs: float) -> str:
        """
        Get a string representation of a number of seconds.

        This function takes a number of seconds and converts it into a string in
        "DDd HH:MM:SS" format if days are present, or "HH:MM:SS" format otherwise.

        Args:
            secs (float): The number of seconds to format.

        Returns:
            str: A string representation of the seconds in "DDd HH:MM:SS" or "HH:MM:SS" format.

        Example:
            >>> CommonFormattingBase.secs2str(90061)
            "1d 01:01:01"
            >>> CommonFormattingBase.secs2str(3661)
            "01:01:01"
        """
        # Convert days, hours, minutes, and remaining seconds
        days, secs = CommonFormattingBase._secs_to_str(secs, CommonConstants.SECS_PER_DAY)
        hrs, secs = CommonFormattingBase._secs_to_str(secs, CommonConstants.SECS_PER_HOUR)
        mins, secs = CommonFormattingBase._secs_to_str(secs, CommonConstants.SECS_PER_MINUTE)

        # Format the result based on the presence of days
        if days:
            return f"{days}d {hrs:02d}:{mins:02d}:{int(secs):02d}"
        return f"{hrs:02d}:{mins:02d}:{int(secs):02d}"

    def psecs(self, secs: float = None) -> str:
        """
        Convert seconds into a human-readable format with larger time units if applicable.

        This function provides a readable format of time in seconds by converting
        large values into weeks, months, or years.

        Args:
            secs (float, optional): The number of seconds. If None, uses elapsed time.

        Returns:
            str: A formatted string representing the time in the most appropriate unit.

        Example:
            >>> formatter = CommonFormattingBase()
            >>> formatter.psecs(31557600)
            "1.00 Years"
        """
        # Use elapsed time if secs is not provided
        if secs is None:
            secs = CommonFormattingBase.elapsed()
            pass  # for auto-indentation

        # Determine the appropriate time unit based on the value of secs
        if secs >= CommonConstants.SECS_PER_YEAR:
            secs = f"{secs / CommonConstants.SECS_PER_YEAR:0.2f}"
            return f"{secs:4s} Years"
        if secs >= CommonConstants.SECS_PER_MONTH:
            secs = f"{secs / CommonConstants.SECS_PER_MONTH:0.2f}"
            return f"{secs:4s} Months"
        if secs >= CommonConstants.SECS_PER_WEEK:
            secs = f"{secs / CommonConstants.SECS_PER_WEEK:0.2f}"
            return f"{secs:4s} Weeks"
        if secs >= CommonConstants.SECS_PER_DAY:
            secs = f"{secs / CommonConstants.SECS_PER_DAY:0.2f}"
            return f"{secs:4s} Days"
        if secs >= CommonConstants.SECS_PER_HOUR:
            secs = f"{secs / CommonConstants.SECS_PER_HOUR:0.1f}"
            return f"{secs:4s} Hours"
        if secs >= CommonConstants.SECS_PER_MINUTE:
            secs = f"{secs / CommonConstants.SECS_PER_MINUTE:0.1f}"
            return f"{secs:4s} Mins"

        # Default to seconds if less than a minute
        secs = f"{secs:0.1f}"
        return f"{secs:4s} Secs"

    def _get_part(self, secs: float, part_size: float, label: str = None) -> Tuple[float, str | int]:
        """
        Divide seconds by a part size and return the quotient and remaining seconds.

        This helper method divides the `secs` by `part_size`, returning both the
        remainder and a formatted label or integer count based on the `label` parameter.

        Args:
            secs (float): The number of seconds.
            part_size (float): The size of the part to divide by (e.g., seconds in a day).
            label (str, optional): A label to append if returning a formatted string.

        Returns:
            tuple[float, str | int]: Remaining seconds and either a formatted string with
                                      label or an integer count if no label is given.

        Example:
            >>> formatter = CommonFormattingBase()
            >>> formatter._get_part(90061, CommonConstants.SECS_PER_DAY, "days")
            (61.0, "1 days ")
        """
        # Return secs unchanged and empty string or zero if secs is less than part_size
        if secs < part_size:
            if label:
                return secs, ""  # Return remainder and empty string if label is provided
            else:
                return secs, 0  # Return remainder and zero if no label is provided
            pass  # for auto-indentation

        parts = int(secs / part_size)  # Calculate integer quotient
        # Return formatted string with label if provided, else return integer part count
        if label:
            return secs - (parts * part_size), f"{parts:,d} {label} "
        else:
            return secs - (parts * part_size), parts
        pass  # for auto-indentation

    def ptime(self, secs: float = None) -> str:
        """
        Format seconds into a human-readable time string with years, days, hours, minutes, and seconds.

        This method provides a human-readable format for seconds by calculating
        years, days, hours, minutes, and seconds from the total time in seconds.

        Args:
            secs (float, optional): The number of seconds to format. Defaults to elapsed time if None.

        Returns:
            str: A string representing the formatted time with each unit if applicable.

        Example:
            >>> formatter = CommonFormattingBase()
            >>> formatter.ptime(90061)
            "1 days 01:01:01"
        """
        # Use elapsed time if secs is not provided
        if secs is None:
            secs = CommonFormattingBase.elapsed()
            pass  # for auto-indentation

        # Convert secs into years, days, hours, minutes, and remaining seconds
        secs, years = self._get_part(secs, CommonConstants.SECS_PER_YEAR, "years")
        secs, days = self._get_part(secs, CommonConstants.SECS_PER_DAY, "days")
        secs, hours = self._get_part(secs, CommonConstants.SECS_PER_HOUR)
        secs, minutes = self._get_part(secs, CommonConstants.SECS_PER_MINUTE)

        # Format the time string based on calculated components
        return f"{years}{days}{hours:02d}:{minutes:02d}:{int(secs):02d}"

    pass  # for auto-indentation


# End
