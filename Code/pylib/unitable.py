#!/usr/bin/env python
# -*- coding: utf-8 -*-
# texttable - module for creating simple ASCII tables
# Copyright (C) 2018-2024 Gabriele Fariello where applicable, 2003-2019 Gerome Fournier <jef(at)foutaise.org> everywhere else.

r"""module for creating simple ASCII tables.

Example:

    table = UniTable()
    table.set_cols_align(["l", "r", "c"])
    table.set_cols_valign(["t", "m", "b"])
    table.add_rows([["Name", "Age", "Nickname"],
                    ["Ms\\nSarah\\nJones", 27, "Sarah"],
                    ["Mr\\nJohn\\nDoe", 45, "Johnny"],
                    ["Dr\\nEmma\\nBrown", 34, "Em"]])
    print(table.draw() + "\\n")

    table = UniTable()
    table.set_decorations(UniTable.HEADER)
    table.set_cols_dtype(['t',  # text
                          'f',  # float (decimal)
                          'e',  # float (exponent)
                          'i',  # integer
                          'a']) # automatic
    table.set_cols_align(["l", "r", "r", "r", "l"])
    table.add_rows([["text",    "float", "exp", "int", "auto"],
                    ["alpha",    "23.45", 543,   100,    45.67],
                    ["beta",     3.1415,  1.23,  78,    56789012345.12],
                    ["gamma",    2.718,   2e-3,  56.8,  .0000000000128],
                    ["delta",    .045,    1e+10, 92,    89000000000000.9]])
    print(table.draw())

Result:

    +--------+-----+---------+
    |  Name  | Age | Nickname|
    +========+=====+=========+
    | Ms     |     |         |
    | Sarah  |  27 |         |
    | Jones  |     |  Sarah  |
    +--------+-----+---------+
    | Mr     |     |         |
    | John   |  45 |         |
    | Doe    |     | Johnny  |
    +--------+-----+---------+
    | Dr     |     |         |
    | Emma   |  34 |         |
    | Brown  |     |    Em   |
    +--------+-----+---------+

    text    float       exp       int         auto
    ==============================================
    alpha   23.450    5.430e+02   100       45.670
    beta    3.142     1.230e+00   78        5.679e+10
    gamma   2.718     2.000e-03   57        1.280e-11
    delta   0.045     1.000e+10   92        8.900e+13
"""

# TODO: Verify which if these are still needed in Python 3
from __future__ import division  # Ensure division works the same in Python 2 and 3
from wcwidth import wcswidth  # For calculating the display width of unicode characters
import re  # Regular expressions for text processing
import sys  # System-specific parameters and functions
from typing import List, Optional, Iterable, Any  # Type hints for better code clarity
from functools import reduce  # Higher-order function for performing cumulative operations

__all__ = ["UniTable", "ArraySizeError", "StringLengthCalculator"]

__author__ = 'Gabriele Fariello <gfariello@fariel.com>'
__license__ = 'MIT'
__version__ = '1.0.0'
__credits__ = """\
Gerome Fournier <jef(at)foutaise.org>
    - Inspiration from his TextTable Python module from which
      this takes a LOT.
Others who contributed to Gerome's work and therefore mine:

Jeff Kowalczyk:
    - textwrap improved import
    - comment concerning header output

Anonymous:
    - add_rows method, for adding rows in one go

Sergey Simonenko:
    - redefined len() function to deal with non-ASCII characters

Roger Lew:
    - columns datatype specifications

Brian Peterson:
    - better handling of unicode errors

Frank Sachsenheim:
    - add Python 2/3-compatibility

Maximilian Hils:
    - fix minor bug for Python 3 compatibility

frinkelpi:
    - preserve empty lines
"""

# Attempt to define a text wrapping function to wrap text to a specific width
# - Use cjkwrap if available (provides better support for CJK characters)
# - Fallback to textwrap if cjkwrap is not available
try:
    import cjkwrap  # Try importing cjkwrap for better CJK character support

    def textwrapper(txt, width):
        """
        Wrap text to a specified width using cjkwrap.

        Args:
        txt (str): The text to wrap.
        width (int): The maximum width of each line.

        Returns:
        List[str]: A list of wrapped lines.
        """
        return cjkwrap.wrap(txt, width)
    pass  # Close block to ensure proper indentation
except ImportError:  # If cjkwrap is not available, fallback to textwrap
    try:
        import textwrap  # Try importing textwrap for text wrapping

        def textwrapper(txt, width):
            """
            Wrap text to a specified width using textwrap.

            Args:
            txt (str): The text to wrap.
            width (int): The maximum width of each line.

            Returns:
            List[str]: A list of wrapped lines.
            """
            return textwrap.wrap(txt, width)
        pass  # Close block to ensure proper indentation
    except ImportError:  # If both cjkwrap and textwrap are unavailable, raise an error
        sys.stderr.write("Can't import textwrap module!\n")
        raise  # Raise an ImportError if textwrap cannot be imported
    pass  # Close block to ensure proper indentation
pass  # Close block to ensure proper indentation


class StringLengthCalculator:
    """
    A class to calculate the visible length of a string, excluding ANSI escape sequences.

    This class is designed to handle strings containing ANSI escape sequences (used for text formatting) and
    accurately calculate their visible length. ANSI escape sequences are ignored in the length calculation,
    ensuring the actual displayed length of the text is returned.

    Attributes:
    -----------
    ansi_escape : re.Pattern
        A compiled regular expression pattern to match ANSI escape sequences.

    Methods:
    --------
    len(string: str) -> int
        Calculates the visible length of a string, excluding ANSI escape sequences.

    Example:
    --------
    ```
    calculator = StringLengthCalculator()
    colored_string = "\033[1;31mRed text\033[0m"
    length = calculator.len(colored_string)
    print(length)  # Outputs: 8
    ```

    The above example demonstrates how to use the `StringLengthCalculator` to get the length of a string
    without counting the ANSI escape sequences.
    """

    def __init__(self):
        # Regular expression to match ANSI escape sequences
        # ANSI escape sequences are used for text formatting (e.g., colors)
        self.ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        pass  # Close block to ensure proper indentation

    def len(self, string: str) -> int:
        """
        Calculate the visible length of a string, excluding ANSI escape sequences.

        Args:
        -----
        string : str
            The string whose visible length should be calculated.

        Returns:
        --------
        int
            The visible length of the string.

        Example:
        --------
        ```
        calculator = StringLengthCalculator()
        colored_string = "\033[1;31mRed text\033[0m"
        length = calculator.len(colored_string)
        print(length)  # Outputs: 8
        ```

        The above example shows how to use the `len` method to calculate the visible length of a string with ANSI escape sequences.
        """
        # Remove ANSI escape sequences from the string
        visible_string = self.ansi_escape.sub('', string)

        # Return the length of the visible string
        # wcswidth returns the number of cells the string occupies when printed
        return wcswidth(visible_string)
        pass  # Close block to ensure proper indentation

    pass  # Close block to ensure proper indentation


class ColorAwareWrapper:
    """
    Class to wrap text to a specified width, excluding ANSI escape sequences.

    This class ensures that text containing ANSI escape sequences (used for text formatting) is wrapped correctly
    without disrupting the formatting. It calculates the visible length of text by excluding these sequences
    and wraps the text to the specified width.

    Attributes:
    -----------
    calculator : StringLengthCalculator
        An instance of StringLengthCalculator to handle the calculation of string lengths excluding ANSI escape sequences.

    Methods:
    --------
    wrap(text: str, width: int) -> str
        Wraps text to the specified width, ignoring ANSI escape sequences.

    Example:
    --------
    ```
    wrapper = ColorAwareWrapper()
    colored_text = "This is \033[1;31mred\033[0m and this is \033[1;32mgreen\033[0m."
    wrapped_text = wrapper.wrap(colored_text, 20)
    print(wrapped_text)
    ```

    The above example would produce:
    ```
    This is \033[1;31mred\033[0m
    and this is
    \033[1;32mgreen\033[0m.
    ```
    """
    def __init__(self):
        # Initialize an instance of StringLengthCalculator to handle ANSI escape sequences
        self.calculator = StringLengthCalculator()
        pass  # Close block to ensure proper indentation

    def wrap(self, text: str, width: int) -> str:
        """
        Wraps text to the specified width, ignoring ANSI escape sequences.

        Args:
        -----
        text : str
            The text to wrap.
        width : int
            The maximum width of each line.

        Returns:
        --------
        str
            The wrapped text with lines not exceeding the specified width.

        Example:
        --------
        ```
        wrapper = ColorAwareWrapper()
        sample_text = "This is a sample text to demonstrate wrapping functionality."
        wrapped_text = wrapper.wrap(sample_text, 15)
        print(wrapped_text)
        ```

        The above example would produce:
        ```
        This is a sample
        text to
        demonstrate
        wrapping
        functionality.
        ```
        """
        # Split the text into individual words
        words = text.split()

        # Initialize an empty line to build up words and an empty list to hold the result
        line, result = [], []

        # Iterate over the words in the text
        for word in words:
            # Calculate the length of the current line and the length of the next word
            line_length = self.calculator.len(' '.join(line))
            word_length = self.calculator.len(word)

            # If adding the next word to the current line would exceed the specified width...
            if line_length + word_length + len(line) > width:  # +len(line) accounts for spaces between words
                # ...then add the current line to the result and start a new line
                result.append(' '.join(line))
                line = []  # Reset the line

            # Add the word to the current line
            line.append(word)

        # If there are any remaining words in the line, add the line to the result
        if line:
            result.append(' '.join(line))

        # Join the lines in the result with line breaks and return the wrapped text
        return '\n'.join(result)
        pass  # Close block to ensure proper indentation

    pass  # Close block to ensure proper indentation


def obj2unicode(obj: Any) -> str:
    """
    Return a unicode representation of a Python object.

    This function converts a given Python object to its unicode string representation.
    It handles strings, bytes, and other types by converting them appropriately.

    Args:
    -----
    obj : Any
        The Python object to convert to a unicode string.

    Returns:
    --------
    str
        The unicode string representation of the input object.

    Example:
    --------
    ```
    print(obj2unicode("test"))  # Outputs: 'test'
    print(obj2unicode(b'test'))  # Outputs: 'test'
    print(obj2unicode(123))  # Outputs: '123'
    ```
    """
    if isinstance(obj, str):
        return obj  # Return the string as it is
    elif isinstance(obj, bytes):
        return obj.decode()  # Decode bytes to string
    return str(obj)  # Convert other types to string


class ArraySizeError(Exception):
    """
    Exception raised when specified rows don't fit the required size.

    This custom exception is used to indicate that an operation involving rows in
    a table or array has failed because the specified rows do not match the expected size.

    Attributes:
    -----------
    msg : str
        The error message describing the reason for the exception.

    Methods:
    --------
    __str__() -> str
        Returns the error message as a string.
    """

    def __init__(self, msg: str):
        """
        Initialize the ArraySizeError with an error message.

        Args:
        -----
        msg : str
            The error message describing the reason for the exception.

        Example:
        --------
        ```
        raise ArraySizeError("Row size mismatch")
        ```
        """
        self.msg = msg  # Store the error message
        Exception.__init__(self, msg, '')  # Initialize the base Exception class
        pass  # Close block to ensure proper indentation

    def __str__(self) -> str:
        """
        Return the error message as a string.

        Returns:
        --------
        str
            The error message describing the reason for the exception.

        Example:
        --------
        ```
        error = ArraySizeError("Row size mismatch")
        print(str(error))  # Outputs: 'Row size mismatch'
        ```
        """
        return self.msg  # Return the stored error message
        pass  # Close block to ensure proper indentation

    pass  # Close block to ensure proper indentation


class FallbackToText(Exception):
    """
    Exception used for failed conversion to float.

    This custom exception indicates that a conversion to a float has failed and
    the operation should fallback to handling the value as text.

    Example:
    --------
    ```
    try:
        value = float(some_value)
    except ValueError:
        raise FallbackToText()
    ```
    """
    pass  # Close block to ensure proper indentation


class UniTable:
    """
    A class that provides functionality for creating and manipulating ASCII tables.

    This class allows users to create, style, and manipulate text-based tables in ASCII format.
    It supports various styles, borders, headers, and decorations to enhance the table presentation.

    Attributes:
    -----------
    BORDER : int
        A constant for enabling border decoration.
    HEADER : int
        A constant for enabling header decoration.
    HLINES : int
        A constant for enabling horizontal lines between rows.
    VLINES : int
        A constant for enabling vertical lines between columns.
    TOP : int
        A constant representing the top border position.
    MIDDLE : int
        A constant representing the middle position for lines.
    BOTTOM : int
        A constant representing the bottom border position.
    STYLES : dict
        A dictionary mapping style names to their corresponding border characters.
    STYLE_MAPPER : dict
        A dictionary mapping complex style patterns to their corresponding characters.

    Example usage:
    --------------
    ```
    table = UniTable()
    table.set_cols_align(["l", "r", "c"])
    table.add_rows([["Name", "Age"], ["Alice", 25], ["Bob", 30]])
    print(table.draw())
    ```
    """

    # Constants for table decorations
    BORDER = 1  # Border around the table
    HEADER = 1 << 1  # Header line below the header
    HLINES = 1 << 2  # Horizontal lines between rows
    VLINES = 1 << 3  # Vertical lines between columns

    # Constants for line positions
    TOP = 0  # Top border position
    MIDDLE = 1  # Middle position for lines
    BOTTOM = 2  # Bottom border position

    # Dictionary defining various table styles and their corresponding border characters
    STYLES = {
        "ascii": "-|+-",  # Basic ASCII style
        "ascii2": "-|+=",  # ASCII style with different corner characters
        "bold": "━┃┏┓┗┛┣┫┳┻╋━┣┫╋",  # Bold style with thicker lines
        "double": "═║╔╗╚╝╠╣╦╩╬═╠╣╬",  # Double line style
        "light2": "─│┌┐└┘├┤┬┴┼═╞╡╪",  # Light line style with different corners
        "round": "─│╭╮╰╯├┤┬┴┼─├┤┼",  # Round corners style
        "round2": "─│╭╮╰╯├┤┬┴┼═╞╡╪",  # Another round corners style
        "light": "─│┌┐└┘├┤┬┴┼─├┤┼",  # Light line style
        "none": ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ],  # No lines style
        "none2": ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ],  # Another no lines style
    }

    # Dictionary mapping complex style patterns to specific characters
    STYLE_MAPPER = {
        "heavy": {
            "---w": " ", "--e-": " ", "--ew": "━", "-s--": " ", "-s-w": "┓", "-se-": "┏", "-sew": "┳",
            "n---": " ", "n--w": "┛", "n-e-": "┗", "n-ew": "┻", "ns--": "┃", "ns-w": "┫", "nse-": "┣", "nsew": "╋",
        },
        "light2": {
            "---w": " ", "--e-": " ", "--ew": "-", "-s--": " ", "-s-w": "┐", "-se-": "┌", "-sew": "┬",
            "n---": " ", "n--w": "┘", "n-e-": "└", "n-ew": "┴", "ns--": "│", "ns-w": "┤", "nse-": "├", "nsew": "┼",
        },
        "round": {
            "---w": " ", "--e-": " ", "--ew": "-", "-s--": " ", "-s-w": "╮", "-se-": "╭", "-sew": "┬",
            "n---": " ", "n--w": "╯", "n-e-": "╰", "n-ew": "┴", "ns--": "│", "ns-w": "┤", "nse-": "├", "nsew": "┼",
        },
        "double": {
            "---w": " ", "--e-": " ", "--ew": "═", "-s--": " ", "-s-w": "╗", "-se-": "╔", "-sew": "╦",
            "n---": " ", "n--w": "╝", "n-e-": "╚", "n-ew": "╩", "ns--": "║", "ns-w": "╣", "nse-": "╠", "nsew": "╬",
        },
        "heavy:light": {
            "---w:--e-": "╾", "---w:-s--": "┑", "---w:-se-": "┲", "---w:n---": "┙", "---w:n-e-": "┺", "---w:ns--": "┥", "---w:nse-": "┽",
            "--e-:---w": "╼", "--e-:-s--": "┍", "--e-:-s-w": "┮", "--e-:n---": "┙", "--e-:n--w": "┶", "--e-:ns--": "┝", "--e-:ns-w": "┾",
            "--ew:-s--": "┰", "--ew:n---": "┸", "--ew:ns--": "┿", "-s--:---w": "┒", "-s--:--e-": "┎", "-s--:--ew": "┰", "-s--:n---": "╽",
            "-s--:n--w": "┧", "-s--:n-e-": "┟", "-s--:n-ew": "╁", "-s-w:--e-": "┱", "-s-w:n---": "┧", "-s-w:n-e-": "╅", "-se-:---w": "┲",
            "-se-:n---": "┢", "-se-:n--w": "╆", "-sew:n---": "╈", "n---:---w": "┖", "n---:--e-": "┚", "n---:--ew": "┸", "n---:-s--": "╿",
            "n---:-s-w": "┦", "n---:-se-": "┞", "n---:-sew": "╀", "n--w:--e-": "┹", "n--w:-s--": "┩", "n--w:-se-": "╃", "n-e-:---w": "┺",
            "n-e-:-s--": "┡", "n-e-:-s-w": "╄", "n-ew:-s--": "╇", "ns--:---w": "┨", "ns--:--e-": "┠", "ns--:--ew": "╂", "ns-w:--e-": "╉",
            "nse-:---w": "╊",
        }
    }

    def __init__(self, rows: Optional[Iterable[Iterable]] = None, max_width: int = 80,
                 style: str = 'light', padding: int = 1, alignment: Optional[str] = None):
        """
        Initializes a new instance of the UniTable class.

        This constructor sets up the initial state of the table, allowing for optional
        initial rows, maximum width, style, padding, and column alignment.

        Args:
        -----
        rows : Optional[Iterable[Iterable]]
            An iterable containing rows to be added to the table. Each row should be an iterable of cell values. Default is None.
        max_width : int, optional
            The maximum width of the table. Default is 80. If this is set to 0, no wrapping will occur.
        style : str, optional
            The style of the table. Default is 'light'. See set_style().
        padding : int, optional
            The amount of padding (left and right) for the cells. Default is 1. See set_padding().
        alignment : Optional[str], optional
            The alignment of columns. See set_cols_align().

        Example:
        --------
        ```
        # Creates a new UniTable instance with initial rows and a maximum width of 100
        table = UniTable(rows=[["Name", "Age"], ["Alice", 25], ["Bob", 30]], max_width=100)
        print(table.draw())
        ```

        If no rows are provided during initialization, they can be added later using the `add_row` or `add_rows` methods.
        """
        # Initialize table properties with default values
        self._has_border = True  # Whether the table has a border
        self._has_header = True  # Whether the table has a header
        self._has_hline_between_headers = True  # Whether there is a horizontal line between headers
        self._has_hline_header_2_cell = True  # Whether there is a horizontal line between header and cells
        self._has_hline_between_cells = True  # Whether there are horizontal lines between cells
        self._has_vline_between_headers = True  # Whether there are vertical lines between headers
        self._has_vline_header_2_cell = True  # Whether there are vertical lines between header and cells
        self._has_vline_between_cells = True  # Whether there are vertical lines between cells

        # Initialize helper classes for string length calculation and color-aware wrapping
        self._vislen = StringLengthCalculator()  # For calculating visible string length excluding ANSI sequences
        self._cwrap = ColorAwareWrapper()  # For wrapping text with ANSI sequences

        # Reset table properties
        self.reset()

        self._precision = 3  # Default precision for numeric values

        # Added to support rows arg (i.e., adding entire table definition in initialization).
        if rows is not None:
            self.add_rows(rows)  # Add initial rows to the table if provided
            pass  # Close block to ensure proper indentation

        self.set_max_width(max_width)  # Set the maximum width of the table

        # Regular expressions for handling ANSI escape sequences in table content
        self.no_end_reset = re.compile(r'\033\[0m(?!.*\033\[((?!0m)[0-?]*[ -/]*[@-~]))')
        self.non_reset_sequence = re.compile(r'\033\[((?!0m)[0-?]*[ -/]*[@-~])')
        self.non_reset_not_followed_by_reset = re.compile(r'(\033\[(?:(?!0m)[0-?]*[ -/]*[@-~]))(?!.*\033\[0m)')
        self.ansi_norm = "\033[0m"  # ANSI reset sequence

        # Set default table decorations (border, header, horizontal and vertical lines)
        self._deco = UniTable.VLINES | UniTable.HLINES | UniTable.BORDER | UniTable.HEADER

        self.set_style(style)  # Set the table style
        self.set_padding(padding)  # Set the cell padding

        if alignment is not None:
            self.set_cols_align(alignment)  # Set the column alignment if provided
            pass  # Close block to ensure proper indentation

        pass  # Close block to ensure proper indentation

    def vislen(self, iterable: Iterable) -> int:
        """Calculate the visible legnth of strings or the length for anythine else."""
        if isinstance(iterable, bytes) or isinstance(iterable, str):
            return self._vislen.len(iterable)
        return iterable.__len__()

    @property
    def has_border(self) -> bool:
        """Get is this has a border."""
        return self._has_border

    @has_border.setter
    def has_border(self, value):
        self._has_border = value
        return value

    @property
    def has_header(self):
        """Get if this has a header."""
        return self._has_header

    @has_header.setter
    def has_header(self, value):
        self._has_header = value
        return value

    def reset(self):
        """Reset the instance.

        - reset rows and header
        """
        self._hline_string = None
        self._row_size = None
        self._header = []
        self._rows = []
        self._style = "light"
        return self

    @property
    def max_width(self):
        """Get the maximum width of the table. If 0, no max."""
        return self._max_width

    @max_width.setter
    def max_width(self, val):
        self.set_max_width(val)

    def set_max_width(self, max_width: int) -> 'UniTable':
        """Set the maximum width of the table.

        - max_width is an integer, specifying the maximum width of the table
        - if set to 0, size is unlimited, therefore cells won't be wrapped
        """
        self._max_width = max_width if max_width > 0 else False
        return self

    def set_style(self, style: str = "light") -> 'UniTable':
        """Set the characters used to draw lines between rows and columns to one of defined types.

        Examples:
            "light": Use unicode light box borders (─│┌┐└┘├┤┬┴┼)
            "bold":  Use unicode bold box borders (━┃┏┓┗┛┣┫┳┻╋)
            "double": Use unicode double box borders (═║╔╗╚╝╠╣╦╩╬)

        Default if none provided is "light"

        """
        self._style = style
        if style in UniTable.STYLES:
            self.set_table_lines(UniTable.STYLES[style])
            return self
        raise ValueError("style must be one of '%s' not '%s'" % ("', '".join(sorted(UniTable.STYLES.keys())), style))

    def _set_table_lines(self, table_lines: str) -> 'UniTable':
        """Set the characters used to draw lines between rows and columns.

        The table_lines is in the following format:
        [
          ew,    # The character connecting east and west to use for a horizantal line (e.g. "-" or "─" )
          ns,    # The character connecting north and south to use for a vertical line (e.g. "|" or "|" )
          se,    # The character connecting south and east to use for the top- and left-most corner (e.g. "+", or "┌")
          sw,    # The character connecting south and west to use for the top- and right-most corner (e.g. "+" or "┐")
          ne,    # The character connecting north and east to use for the bottom- and left-most corner (e.g. "+" or "└")
          nw,    # The character connecting north and west to use for the bottom- and right-most corner (e.g. "+" or "┘")
          nse,   # The character connecting north, south, and east (e.g., "+" or "┤")
          nsw,   # The character connecting north, south, and west (e.g., "+" or "├")
          sew,   # The character connecting south, east, and west (e.g., "+" or "┬")
          new,   # The character connecting north, east, and west (e.g., "+" or "┴")
          nsew,  # The character connecting north, south, east, and west (e.g., "+" or "┴")
          hew,   # The character connecting east and west to use for a line separating headers (e.g. "=" or "═" )
          hnse,  # The character connecting north, south and east to use for a line separating headers (e.g. "+" or "╞" )
          hnsw,  # The character connecting north, south, and west to use for a line separating headers (e.g. "+" or "╡" )
          hnsew, # The character connecting north, south, east and west to use for a line separating headers (e.g. "+" or "╪" )
        ]
        For legacy default it would be "-|+++++++++=+++"
        """
        if len(table_lines) != 15:
            raise ArraySizeError("string/array should contain 15 characters not %d as in '%s'" % (len(table_lines), table_lines))
        (
            self._char_ew,
            self._char_ns,
            self._char_se,
            self._char_sw,
            self._char_ne,
            self._char_nw,
            self._char_nse,
            self._char_nsw,
            self._char_sew,
            self._char_new,
            self._char_nsew,
            self._char_hew,
            self._char_hnse,
            self._char_hnsw,
            self._char_hnsew,
        ) = table_lines
        return self

    def set_table_lines(self, table_lines: str) -> 'UniTable':
        """Set the characters used to draw lines between rows and columns.

        - the table_lines should contain either 4 fields or 15. For 4:

            [horizontal, vertical, corner, header]

        - default is set to (both are the same):

            "-|+="
            "-|+++++++++=+++"
        """
        if len(table_lines) == 15:
            return self._set_table_lines(table_lines)
        if len(table_lines) != 4:
            raise ArraySizeError("string/array should contain either 4 or 15 characters not %d as in '%s'" % (len(table_lines), table_lines))
        (hor, ver, cor, hea) = table_lines
        self._set_table_lines([hor, ver, cor, cor, cor, cor, cor, cor, cor, cor, cor, hea, cor, cor, cor])
        return self

    def set_decorations(self, decorations: int) -> 'UniTable':
        """Set the table decoration.

        - 'decorations' can be a combinasion of:

            UniTable.BORDER: Border around the table
            UniTable.HEADER: Horizontal line below the header
            UniTable.HLINES: Horizontal lines between rows
            UniTable.VLINES: Vertical lines between columns

           All of them are enabled by default

        - example:

            UniTable.BORDER | UniTable.HEADER
        """
        self._deco = decorations
        return self

    def set_header_align(self, array: str) -> 'UniTable':
        """Set the desired header alignment.

        - the elements of the array should be either "l", "c" or "r":

            * "l": column flushed left
            * "c": column centered
            * "r": column flushed right
        """
        if isinstance(array, str):
            array = [c for c in array]
            pass
        self._check_row_size(array)
        self._header_align = array
        return self

    def set_cols_align(self, array: str) -> 'UniTable':
        """Set the desired columns alignment.

        - the elements of the array should be either "l", "c" or "r":

            * "l": column flushed left
            * "c": column centered
            * "r": column flushed right
        """
        if isinstance(array, str):
            array = [c for c in array]
            pass
        self._check_row_size(array)
        self._align = array
        return self

    def set_cols_valign(self, array: str) -> 'UniTable':
        """Set the desired columns vertical alignment.

        - the elements of the array should be either "t", "m" or "b":

            * "t": column aligned on the top of the cell
            * "m": column aligned on the middle of the cell
            * "b": column aligned on the bottom of the cell
        """
        if isinstance(array, str):
            array = [c for c in array]
            pass
        self._check_row_size(array)
        self._valign = array
        return self

    def set_cols_dtype(self, array: str) -> 'UniTable':
        """
        Sets the data types for the columns in the table.

        Args:
        array (List[str]): A list of strings representing the data types for the columns.
                           Acceptable values are: 't' (text), 'f' (float, decimal),
                           'e' (float, exponent), 'i' (integer), and 'a' (automatic).

        Example usage:
        ```
        table = UniTable()
        table.set_cols_dtype("ti")  # one text column, one integer column
        table.set_cols_dtype(['t', 'i'])
        ```

        - the elements of the array should be either a callable or any of
          "a", "t", "f", "e" or "i":

            * "a": automatic (try to use the most appropriate datatype)
            * "t": treat as text
            * "f": treat as float in decimal format
            * "e": treat as float in exponential format
            * "i": treat as int
            * "I": treat as int, but print with commas separating thousands
            * a callable: should return formatted string for any value given

        - by default, automatic datatyping is used for each column
        """
        if isinstance(array, str):
            array = [c for c in array]
            pass
        self._check_row_size(array)
        self._dtype = array
        return self

    def set_cols_width(self, array: str) -> 'UniTable':
        """Set the desired columns width.

        - the elements of the array should be integers, specifying the
          width of each column. For example:
                [10, 20, 5]
        """
        self._check_row_size(array)
        try:
            array = list(map(int, array))
        except ValueError:
            sys.stderr.write("Wrong argument in column width specification\n")
            raise
        if reduce(min, array) <= 0:
            raise ValueError("Values less than or equal to zero not allowed. Input: %s" % array)
        self._width = array
        return self

    def set_precision(self, width: int) -> 'UniTable':
        """Set the desired precision for float/exponential formats.

        - width must be an integer >= 0
        - default value is set to 3
        """
        if not type(width) is int or width < 0:
            raise ValueError('width must be an integer greater then 0')
        self._precision = width
        return self

    @property
    def padding(self) -> int:
        """Get the amount of padding."""
        return self._pad

    @padding.setter
    def padding(self, val: int) -> 'UniTable':
        """Set the amount of padding."""
        self.set_padding(val)
        return self

    def set_padding(self, amount: int) -> 'UniTable':
        """Set the amount of spaces to pad cells (right and left, we don't do top bottom padding).

        - width must be an integer >= 0
        - default value is set to 1
        """
        if not type(amount) is int or amount < 0:
            raise ValueError('padding must be an integer greater then 0')
        self._pad = amount
        return self

    def header(self, array: List[Any]) -> 'UniTable':
        """Specify the header of the table."""
        self._check_row_size(array)
        self._header = list(map(obj2unicode, array))
        return self

    def add_row(self, array: List[str]) -> 'UniTable':
        """Add a row in the rows stack.

        - cells can contain newlines and tabs
        """
        self._check_row_size(array)
        if not hasattr(self, "_dtype"):
            self._dtype = ["a"] * self._row_size
        cells = []
        for i, x in enumerate(array):
            cells.append(self._str(i, x))
        self._rows.append(cells)
        return self

    def add_rows(self, rows, header=True) -> 'UniTable':
        """Add several rows in the rows stack.

        - The 'rows' argument can be either an iterator returning arrays,
          or a by-dimensional array
        - 'header' specifies if the first row should be used as the header
          of the table
        """
        # nb: don't use 'iter' on by-dimensional arrays, to get a
        #     usable code for python 2.1
        if header:
            if hasattr(rows, '__iter__') and hasattr(rows, 'next'):
                self.header(rows.next())
            else:
                self.header(rows[0])
                rows = rows[1:]
        for row in rows:
            self.add_row(row)
        return self

    def set_rows(self, rows, header=True) -> 'UniTable':
        """Replace all rows in the table with the provided rows."""
        self._rows = []
        return self.add_rows(rows, header)

    def draw(self):
        """Draw the table and return as string."""
        if not self._header and not self._rows:
            return
        self._compute_cols_width()
        self._check_align()
        out = ""
        if self.has_border:
            out += self._hline(location=UniTable.TOP)
        if self._header:
            out += self._draw_line(self._header, isheader=True)
            if self.has_header:
                out += self._hline_header(location=UniTable.MIDDLE)
                pass
            pass
        num = 0
        length = len(self._rows)
        for row in self._rows:
            num += 1
            out += self._draw_line(row)
            if self.has_hlines() and num < length:
                out += self._hline(location=UniTable.MIDDLE)
        if self._has_border:
            out += self._hline(location=UniTable.BOTTOM)
        return out[:-1]

    @classmethod
    def _to_float(cls, x):
        if x is None:
            raise FallbackToText()
        try:
            return float(x)
        except (TypeError, ValueError):
            raise FallbackToText()

    @classmethod
    def _fmt_int(cls, x, **kw):
        """Integer formatting class-method.

        - x will be float-converted and then used.
        """
        return str(int(round(cls._to_float(x))))

    @classmethod
    def _fmt_comma_int(cls, x, **kw):
        """Integer formatting class-method.

        - x will be float-converted and then used.
        """
        return f"{int(round(cls._to_float(x))):,d}"

    @classmethod
    def _fmt_float(cls, x, **kw):
        """Float formatting class-method.

        - x parameter is ignored. Instead kw-argument f being x float-converted
          will be used.

        - precision will be taken from `n` kw-argument.
        """
        n = kw.get('n')
        return '%.*f' % (n, cls._to_float(x))

    @classmethod
    def _fmt_exp(cls, x, **kw):
        """Format exponent.

        Args:
            x(any): parameter is ignored. Instead kw-argument f being x
            float-converted will be used.

        Note:
            precision will be taken from `n` kwarg.
        """
        n = kw.get('n')
        return '%.*e' % (n, cls._to_float(x))

    @classmethod
    def _fmt_text(cls, x, **kw):
        """Format string / text."""
        return obj2unicode(x)

    @classmethod
    def _fmt_auto(cls, x, **kw):
        """Auto formatting class-method."""
        f = cls._to_float(x)
        if abs(f) > 1e8:
            fn = cls._fmt_exp
        elif f != f:  # NaN
            fn = cls._fmt_text
        elif f - round(f) == 0:
            fn = cls._fmt_int
        else:
            fn = cls._fmt_float
        return fn(x, **kw)

    def _str(self, i, x):
        """Handle string formatting of cell data.

        Args:
            i(int): index of the cell datatype in self._dtype
            x(any): cell data to format
        """
        format_map = {
            'a': self._fmt_auto,
            'i': self._fmt_int,
            'I': self._fmt_comma_int,
            'f': self._fmt_float,
            'e': self._fmt_exp,
            't': self._fmt_text,
        }

        n = self._precision
        dtype = self._dtype[i]
        try:
            if callable(dtype):
                return dtype(x)
            else:
                return format_map[dtype](x, n=n)
        except FallbackToText:
            return self._fmt_text(x)

    def _check_row_size(self, array):
        """Check that the specified array fits the previous rows size."""
        if not self._row_size:
            self._row_size = len(array)
        elif self._row_size != len(array):
            raise ArraySizeError("array should contain %d elements not %s (array=%s)"
                                 % (self._row_size, len(array), array))

    def has_vlines(self):
        """Return a boolean, if vlines are required or not."""
        return self._deco & UniTable.VLINES > 0

    def has_hlines(self):
        """Return a boolean, if hlines are required or not."""
        return self._deco & UniTable.HLINES > 0

    def _hline_header(self, location=MIDDLE):
        """Print header's horizontal line."""
        return self._build_hline(is_header=True, location=location)

    def _hline(self, location):
        """Print an horizontal line."""
        # if not self._hline_string:
        #   self._hline_string = self._build_hline(location)
        # return self._hline_string
        return self._build_hline(is_header=False, location=location)

    def _build_hline(self, is_header=False, location=MIDDLE):
        """Return a string used to separated rows or separate header from rows."""
        if self._style == "none":
            return ""
        horiz_char = self._char_hew if is_header else self._char_ew
        if UniTable.TOP == location:
            left, mid, right = self._char_se, self._char_sew, self._char_sw
        elif UniTable.MIDDLE == location:
            if is_header:
                left, mid, right = self._char_hnse, self._char_hnsew, self._char_hnsw
            else:
                left, mid, right = self._char_nse, self._char_nsew, self._char_nsw
                pass
        elif UniTable.BOTTOM == location:
            # NOTE: This will not work as expected if the table is only headers.
            left, mid, right = self._char_ne, self._char_new, self._char_nw
        else:
            raise ValueError("Unknown location '%s'. Should be one of UniTable.TOP, UniTable.MIDDLE, or UniTable.BOTTOM." % (location))
        # compute cell separator
        cell_sep = "%s%s%s" % (horiz_char * self._pad, [horiz_char, mid][self.has_vlines()], horiz_char * self._pad)
        # build the line
        hline = cell_sep.join([horiz_char * n for n in self._width])
        # add border if needed
        if self.has_border:
            hline = "%s%s%s%s%s\n" % (left, horiz_char * self._pad, hline, horiz_char * self._pad, right)
        else:
            hline += "\n"
        return hline

    def _len_cell(self, cell):
        """Return the width of the cell.

        Special characters are taken into account to return the width of the
        cell, such like newlines and tabs.
        """
        cell_lines = cell.split('\n')
        maxi = 0
        for line in cell_lines:
            length = 0
            parts = line.split('\t')
            for part, i in zip(parts, list(range(1, len(parts) + 1))):
                length = length + self.vislen(part)
                if i < len(parts):
                    length = (length // 8 + 1) * 8
            maxi = max(maxi, length)
        return maxi

    def _compute_cols_width(self) -> None:
        """
        Compute and set the width of each column in the table.

        This method calculates the width of each column based on the content and
        adjusts the widths to fit within the maximum table width if specified.
        If a specific column width is already set, the method exits early.
        If the total width exceeds the desired table width, the column widths
        are recomputed to fit, and cell content is wrapped as necessary.

        Raises:
        -------
        ValueError
            If the maximum width is too low to render the data properly.

        Example:
        --------
        ```
        table = UniTable()
        table.add_rows([["Name", "Age"], ["Alice", 25], ["Bob", 30]])
        table._compute_cols_width()
        ```
        """
        # Check if column widths have already been computed. If so, exit early.
        if hasattr(self, "_width"):
            return

        # Initialize a list to store the maximum width of each column.
        maxi = []

        # If there is a header, calculate the maximum width for each column in the header.
        if self._header:
            maxi = [self._len_cell(x) for x in self._header]

        # Calculate the maximum width for each column based on the content of each row.
        for row in self._rows:
            for cell, i in zip(row, range(len(row))):
                try:
                    # Update the maximum width for the current column.
                    maxi[i] = max(maxi[i], self._len_cell(cell))
                except (TypeError, IndexError):
                    # If the column index doesn't exist in maxi, append the new width.
                    maxi.append(self._len_cell(cell))

        # Calculate the number of columns in the table.
        ncols = len(maxi)
        # Calculate the total content width by summing the maximum widths of all columns.
        content_width = sum(maxi)
        # Calculate the width required for decorations (borders and spaces).
        deco_width = 3 * (ncols - 1) + [0, 4][self.has_border]

        # Check if the total width (content + decorations) exceeds the maximum allowed width.
        if self._max_width and (content_width + deco_width) > self._max_width:
            # If the maximum width is too low to render the table, raise an error.
            if self._max_width < (ncols + deco_width):
                raise ValueError(f"max_width ({self._max_width}) too low to render data. The minimum for this table would be {ncols + deco_width}.")

            # Calculate the available width for content after accounting for decorations.
            available_width = self._max_width - deco_width
            # Initialize a new list to store the adjusted maximum widths.
            newmaxi = [0] * ncols
            i = 0

            # Distribute the available width among the columns.
            while available_width > 0:
                if newmaxi[i] < maxi[i]:
                    newmaxi[i] += 1
                    available_width -= 1
                # Cycle through columns to distribute width evenly.
                i = (i + 1) % ncols

            # Update the column widths with the adjusted values.
            maxi = newmaxi

        # Set the computed column widths as the table's column widths.
        self._width = maxi

    def _check_align(self) -> None:
        """
        Ensure that column alignment settings are specified, set default values if not.

        This method checks if the alignment, header alignment, and vertical alignment
        settings for the columns are specified. If not, it sets default alignment values.

        Example:
        --------
        ```
        table = UniTable()
        table._check_align()
        ```
        """
        # Check if header alignment is set; if not, set default alignment to center.
        if not hasattr(self, "_header_align"):
            self._header_align = ["c"] * self._row_size
        # Check if column alignment is set; if not, set default alignment to left.
        if not hasattr(self, "_align"):
            self._align = ["l"] * self._row_size
        # Check if vertical alignment is set; if not, set default alignment to top.
        if not hasattr(self, "_valign"):
            self._valign = ["t"] * self._row_size

    def _draw_line(self, line: List[str], isheader: bool = False) -> str:
        """
        Draw a line of the table.

        This method splits the given line into individual cells and arranges them
        according to the specified alignments and widths. It handles the drawing
        of borders and spaces between cells as well.

        Args:
        -----
        line : List[str]
            The line (list of cell content) to be drawn.
        isheader : bool, optional
            Indicates if the line to be drawn is a header line. Default is False.

        Returns:
        --------
        str
            The formatted line as a string.

        Example:
        --------
        ```
        table = UniTable()
        line = ["Name", "Age"]
        print(table._draw_line(line, isheader=True))
        ```
        """
        # Split the line into individual cells, handling headers if necessary.
        line = self._splitit(line, isheader)
        space = " "
        out = ""

        # Iterate over each row of the split line.
        for i in range(self.vislen(line[0])):
            # Add the left border if the table has borders.
            if self.has_border:
                out += f"{self._char_ns}{' ' * self._pad}"
                pass

            length = 0

            # Iterate over each cell in the line.
            for cell, width, align in zip(line, self._width, self._align):
                length += 1
                cell_line = cell[i]
                fill = width - self.vislen(cell_line)

                # Use header alignment if the line is a header.
                if isheader:
                    align = self._header_align[length - 1]
                    pass

                # Align cell content based on the specified alignment.
                if align == "r":
                    out += fill * space + cell_line
                elif align == "c":
                    out += (int(fill / 2) * space + cell_line + int(fill / 2 + fill % 2) * space)
                else:
                    out += cell_line + fill * space
                    pass

                # Add spaces and vertical lines between cells.
                if length < self.vislen(line):
                    out += "%s%s%s" % (" " * self._pad, [space, self._char_ns][self.has_vlines()], " " * self._pad)
                    pass

                pass

            # Add the right border if the table has borders.
            out += "%s\n" % ['', " " * self._pad + self._char_ns][self.has_border]

        return out

    def _splitit(self, line: List[str], isheader: bool) -> List[List[str]]:
        """
        Split each element of the line to fit the column width.

        Each element is turned into a list, resulting from wrapping the string
        to the desired width. This method ensures that each cell content fits
        within the specified column width and handles vertical alignment.

        Args:
        -----
        line : List[str]
            The line (list of cell content) to be split and wrapped.
        isheader : bool
            Indicates if the line to be split is a header line.

        Returns:
        --------
        List[List[str]]
            The processed and wrapped lines.

        Example:
        --------
        ```
        table = UniTable()
        line = ["Name", "Age"]
        wrapped_line = table._splitit(line, isheader=True)
        print(wrapped_line)
        ```
        """
        line_wrapped = []

        # Iterate over each cell and its corresponding column width
        for cell, width in zip(line, self._width):
            array = []
            # Split cell content by new lines and wrap each part to fit the column width
            for c in cell.split('\n'):
                if c.strip() == "":
                    array.append("")  # Preserve empty lines
                else:
                    array.extend(textwrapper(c, width))  # Wrap text to fit the column width
            line_wrapped.append(array)

        # Find the maximum number of lines in any cell
        max_cell_lines = reduce(max, list(map(len, line_wrapped)))

        # Adjust each cell's vertical alignment
        for cell, valign in zip(line_wrapped, self._valign):
            if isheader:
                valign = "t"  # Header cells are always top-aligned
            if valign == "m":
                # Middle alignment: add missing lines evenly to the top and bottom
                missing = max_cell_lines - self._vislen.len(cell)
                cell[:0] = [""] * (missing // 2)
                cell.extend([""] * (missing // 2 + missing % 2))
            elif valign == "b":
                # Bottom alignment: add missing lines to the top
                cell[:0] = [""] * (max_cell_lines - self.vislen(cell))
            else:
                # Top alignment (default): add missing lines to the bottom
                cell.extend([""] * (max_cell_lines - self.vislen(cell)))
                pass
            pass

        return self._process_lines(line_wrapped)

    def _process_lines(self, lines_2d: List[List[str]]) -> List[List[str]]:
        """
        Process a list of lines to ensure all ANSI escape sequences are
        properly terminated and continued onto the next line if necessary.

        This method handles ANSI escape sequences in table content, ensuring
        that they do not disrupt the visual layout when lines are wrapped.

        Args:
        -----
        lines_2d : List[List[str]]
            The lines to process, where each line is a list of cell content.

        Returns:
        --------
        List[List[str]]
            The processed lines with proper ANSI sequence handling.

        Example:
        --------
        ```
        table = UniTable()
        lines_2d = [["\033[1mBold\033[0m", "Text"], ["Normal", "Text"]]
        processed_lines = table._process_lines(lines_2d)
        print(processed_lines)
        ```
        """
        # Initialize a variable to hold any unterminated ANSI escape sequences
        unterminated_sequences = ""

        # Iterate over each line in the 2D list
        for lines in lines_2d:
            for i in range(len(lines)):
                # If there was a non-reset sequence in the last line, prepend it to this line
                if unterminated_sequences:
                    lines[i] = unterminated_sequences + lines[i]
                    unterminated_sequences = ""

                # Save any ANSI escape sequences that are not terminated by a reset sequence
                unterminated_sequences = "".join(self.non_reset_not_followed_by_reset.findall(lines[i]))
                if unterminated_sequences:
                    # Add a reset sequence to the end of the line
                    lines[i] += "\033[0m"
                    pass
                pass
            pass

        return lines_2d

    pass


def split_list(input_list: List[Any], split_length: int, fill_value: Optional[Any] = None) -> List[List[Any]]:
    """
    Split a list into sub-lists of a specified length.

    If the last sub-list is shorter than the specified length, it will be filled
    with the specified fill value.

    Args:
    -----
    input_list : List[Any]
        The list to split.
    split_length : int
        The length of the sub-lists.
    fill_value : Optional[Any], optional
        The value to fill the last sub-list with. Default is None.

    Returns:
    --------
    List[List[Any]]
        A list of sub-lists.

    Example:
    --------
    ```
    original_list = [1, 2, 3, 4, 5, 6, 7, 8]
    result = split_list(original_list, 3, fill_value=0)
    print(result)  # Outputs: [[1, 2, 3], [4, 5, 6], [7, 8, 0]]
    ```
    """
    # Calculate the number of chunks needed
    num_chunks = (len(input_list) + split_length - 1) // split_length

    # Create the chunks by slicing the input list
    chunks = [input_list[i * split_length:(i + 1) * split_length] for i in range(num_chunks)]

    # If the last chunk is shorter than split_length, fill it with the fill_value
    if len(chunks[-1]) < split_length:
        chunks[-1] += [fill_value] * (split_length - len(chunks[-1]))

    return chunks


def example_table(style: str, padding: int = 1) -> str:
    """
    Create an example table with specified style and padding.

    This function generates a simple table with a specified style and padding
    and returns its string representation.

    Args:
    -----
    style : str
        The style of the table.
    padding : int, optional
        The padding for the cells. Default is 1.

    Returns:
    --------
    str
        The string representation of the example table.

    Example:
    --------
    ```
    print(example_table("bold"))
    ```
    """
    return UniTable([["Hd1", "Hd2"], ["Ce1", "Ce2"], ["Ce3", "Ce4"]], style=style, padding=padding).draw()


if __name__ == '__main__':
    # Print a heading for the demo
    print("\033[1m\033[1;31mANSI\033[0m\033[1m Color / Escape Sequence Aware Text-Based Tables\033[0m:")

    # Create a UniTable instance with initial rows
    t1 = UniTable([
        ["Test 1", "Test 2", "Test 3", "Test 4"],
        [
            "This is some \033[1;31mRed text\033[0m to show the ability to wrap \033[38;5;226mcolored text\033[0m correctly.",
            "\033[4mThis text is underlined, \033[1mbold, and \033[34mblue.\033[0m This is not.",
            "This is some normal text in the middle to ensure that it is working properly.",
            "Some \033[1;31mRed mandarin: 这是一个 美好的世界！\033[0m for testing.",
        ]
    ])
    t1.set_max_width(80)  # Set the maximum width of the table
    print(t1.draw())  # Draw and print the table

    import textwrap3  # Import the textwrap3 module for wrapping text
    width = 18  # Set the width for wrapping text

    # Print a separator line
    print("-" * width)

    # Wrap and print plain text
    for line in textwrap3.wrap("This is some Red text to show the ability to wrap colored text correctly.", width):
        print(line)

    # Print another separator line
    print("-" * width)

    # Wrap and print colored text
    for line in textwrap3.wrap("This is some \033[1;31mRed text\033[0m to show the ability to wrap \033[38;5;226mcolored text\033[0m correctly.", width):
        print(line)

    print()

    # Print a heading for the available styles
    print("\033[1mAvailable Styles\033[0m (Note: the default is \"light\"):")
    style_list = sorted(UniTable.STYLES.keys())  # Get the list of available styles
    data = []

    # Split the list of styles into rows of 4 styles each
    for row in split_list(style_list, 4):
        style_row = []
        tables_row = []

        # Generate example tables for each style in the row
        for style in row:
            if style is None:
                style_row.append("")
                tables_row.append("")
            else:
                style_row.append(style)
                tables_row.append(example_table(style))

        data.append(style_row)
        data.append(tables_row)
        data.append(["", "", "", ""])  # Add an empty row for spacing

    # Create a UniTable with the data and draw it
    t1 = UniTable(data, max_width=120, style="none", alignment="cccc")
    print(t1.draw())
    exit()
