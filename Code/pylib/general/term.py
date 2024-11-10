"""A module with stoff for terminals."""

# import tty
import sys
import re


class Term:
    """Constants for TERM colors."""

    NORMAL = "\033[0m"
    # Standard colors
    BLACK = "\033[30m"
    BLACK_BG = "\033[40m"
    BLACK_BRIGHT = "\033[30;1m"
    BLACK_BRIGHT_BG = "\033[40;1m"
    BLUE = "\033[34m"
    BLUE_BG = "\033[44m"
    BLUE_BRIGHT = "\033[34;1m"
    BLUE_BRIGHT_BG = "\033[44;1m"
    CYAN = "\033[36m"
    CYAN_BG = "\033[46m"
    CYAN_BRIGHT = "\033[36;1m"
    CYAN_BRIGHT_BG = "\033[46;1m"
    GREEN = "\033[32m"
    GREEN_BG = "\033[42m"
    GREEN_BRIGHT = "\033[32;1m"
    GREEN_BRIGHT_BG = "\033[42;1m"
    MAGENTA = "\033[35m"
    MAGENTA_BG = "\033[45m"
    MAGENTA_BRIGHT = "\033[35;1m"
    MAGENTA_BRIGHT_BG = "\033[45;1m"
    RED = "\033[31m"
    RED_BG = "\033[41m"
    RED_BRIGHT = "\033[31;1m"
    RED_BRIGHT_BG = "\033[41;1m"
    WHITE = "\033[37m"
    WHITE_BG = "\033[47m"
    WHITE_BRIGHT = "\033[37;1m"
    WHITE_BRIGHT_BG = "\033[47;1m"
    YELLOW = "\033[33m"
    YELLOW_BG = "\033[43m"
    YELLOW_BRIGHT = "\033[33;1m"
    YELLOW_BRIGHT_BG = "\033[43;1m"
    # Decorators
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    REVERSED = "\033[7m"
    # Movement & Line Clearing
    UP = "\033[A"
    DOWN = "\033[B"
    RIGHT = "\033[C"
    LEFT = "\033[D"
    # Visibility
    HIDE_CURSOR = "\033[?25l"
    SHOW_CURSOR = "\033[?25h"
    # Clears
    CS_EOF = "\033[K"
    CS_BOF = "\033[1J"
    CS = "\033[2J"
    CL_EOL = "\033[K"
    CL_BOL = "\033[1K"
    CL = "\033[2K"

    def __init__(self, args=None, output_fh=sys.stdout):
        self.args = args
        self.output_fh = output_fh
        pass

    def write(self, what, flush=True):
        self.output_fh.write(what)
        if flush:
            self.output_fh.flush()
            pass
        return self

    def up(self, num=1): return self.write(f"\033[{num}A")
    def down(self, num=1): return self.write(f"\033[{num}B")
    def left(self, num=1): return self.write(f"\033[{num}C")
    def right(self, num=1): return self.write(f"\033[{num}D")
    def prev_line(self, num=1): return self.write(f"\033[{num}E")
    def next_line(self, num=1): return self.write(f"\033[{num}F")
    def col(self, num=1): return self.write(f"\033[{num}G")
    def abs_pos(self, line=1, col=1): return self.write(f"\033[{line};{col}H")
    def cs_eof(self): return self.write("\033[J")
    def cs_bof(self): return self.write("\033[1J")
    def cs(self): return self.write("\033[2J")
    def cl_eol(self): return self.write("\033[K")
    def cl_bol(self): return self.write("\033[1K")
    def cl(self): return self.write("\033[2K")
    def page_up(self, num=1): return self.write(f"\033[{num}S")
    def page_down(self, num=1): return self.write(f"\033[{num}T")
    def goto(self, line=1, col=1): return self.write(f"\033[{line};{col}f")
    def red(self): return self.write("\033[30m")
    def normal(self): return self.write("\033[0m")
    def black(self): return self.write("\033[30m")
    def black_bg(self): return self.write("\033[40m")
    def black_bright(self): return self.write("\033[30;1m")
    def black_bright_bg(self): return self.write("\033[40;1m")
    def blue(self): return self.write("\033[34m")
    def blue_bg(self): return self.write("\033[44m")
    def blue_bright(self): return self.write("\033[34;1m")
    def blue_bright_bg(self): return self.write("\033[44;1m")
    def cyan(self): return self.write("\033[36m")
    def cyan_bg(self): return self.write("\033[46m")
    def cyan_bright(self): return self.write("\033[36;1m")
    def cyan_bright_bg(self): return self.write("\033[46;1m")
    def green(self): return self.write("\033[32m")
    def green_bg(self): return self.write("\033[42m")
    def green_bright(self): return self.write("\033[32;1m")
    def green_bright_bg(self): return self.write("\033[42;1m")
    def magenta(self): return self.write("\033[35m")
    def magenta_bg(self): return self.write("\033[45m")
    def magenta_bright(self): return self.write("\033[35;1m")
    def magenta_bright_bg(self): return self.write("\033[45;1m")
    def red(self): return self.write("\033[31m")
    def red_bg(self): return self.write("\033[41m")
    def red_bright(self): return self.write("\033[31;1m")
    def red_bright_bg(self): return self.write("\033[41;1m")
    def white(self): return self.write("\033[37m")
    def white_bg(self): return self.write("\033[47m")
    def white_bright(self): return self.write("\033[37;1m")
    def white_bright_bg(self): return self.write("\033[47;1m")
    def yellow(self): return self.write("\033[33m")
    def yellow_bg(self): return self.write("\033[43m")
    def yellow_bright(self): return self.write("\033[33;1m")
    def yellow_bright_bg(self): return self.write("\033[43;1m")
    def hide_cursor(self): return self.write("\033[?25l")
    def show_cursor(self): return self.write("\033[?25h")

    @staticmethod
    def get_cursor_up(num=1):
        """Get string to move the cursor up num or 1 lines."""
        return f"\033[{num}A"

    @staticmethod
    def get_cursor_down(num=1):
        """Get string to move the cursor down num or 1 lines."""
        return f"\033[{num}B"

    @staticmethod
    def get_cursor_right(num=1):
        """Get string to move the cursor right num or 1 cols."""
        return f"\033[{num}C"

    @staticmethod
    def get_cursor_left(num=1):
        """Get string to move the cursor left num or 1 cols."""
        return f"\033[{num}D"

    @staticmethod
    def get_previous_line(number=1):
        """Get string to go to the start of the previous (up) number line(s)."""
        return f"\033[{number}E"

    @staticmethod
    def get_next_line(number=1):
        """Get string to go to the start of the next (down) number line(s)."""
        return f"\033[{number}F"

    @staticmethod
    def get_set_cursor_col(num=1):
        """Get string to set the cursor to the absolute column num or 1."""
        return f"\033[{num}G"

    @staticmethod
    def get_set_cursor_pos(line=1, col=1):
        """Get string to set the cursor to the absolute position or 1,1."""
        return f"\033[{line};{col}H"

    @staticmethod
    def get_clear_screen_end():
        """Get string to clear screen from cursor to end."""
        return "\033[0J"

    @staticmethod
    def get_clear_screen_start():
        """Get string to clear screen from cursor to start."""
        return "\033[1J"

    @staticmethod
    def get_clear_screen():
        """Get string to clear the entire screen."""
        return "\033[2J"

    @staticmethod
    def get_clear_screen_and_scrollback():
        """Get string to clear the entire screen and scrollback buffer."""
        return "\033[3J"

    @staticmethod
    def get_clear_line_end():
        """Get string to clear line from cursor to end. Cursor pos stays the same."""
        return "\033[0K"

    @staticmethod
    def get_clear_line_start():
        """Get string to clear line from cursor to start. Cursor pos stays the same."""
        return "\033[1K"

    @staticmethod
    def get_clear_line():
        """Get string to clear the entire line. Cursor pos stays the same."""
        return "\033[2K"

    @staticmethod
    def get_page_up(num=1):
        """Get string to page up num or 1 number of pages."""
        return f"\033[{num}S"

    @staticmethod
    def get_page_down(num=1):
        """Get string to page down num or 1 number of pages."""
        return f"\033[{num}T"

    @staticmethod
    def get_get_cursor_pos():
        """
        Get the cursor position.

        Get where the terminal thinks the current cursor position is as reported by the terminal.


        Notes
        -----
        Unlike other methods, this prints to STDOUT and reads from STDIN. Use with caution as this is not 100% reliable or thread-safe.

        Returns:
        -------
        col, line

        """
        # From https://stackoverflow.com/questions/38465171/python-3-capture-return-of-x1b6n-0336n-e6n-ansi-sequence
        import tty, termios
        buf = ""
        stdin = sys.stdin.fileno()
        tattr = termios.tcgetattr(stdin)
        try:
            tty.setcbreak(stdin, termios.TCSANOW)
            sys.stdout.write("\x1b[6n")
            sys.stdout.flush()

            while True:
                buf += sys.stdin.read(1)
                if buf[-1] == "R":
                    break
        finally:
            termios.tcsetattr(stdin, termios.TCSANOW, tattr)
        # reading the actual values, but what if a keystroke appears while reading
        # from stdin? As dirty work around, getpos() returns if this fails: None
        try:
            matches = re.match(r"^\x1b\[(\d*);(\d*)R", buf)
            groups = matches.groups()
        except AttributeError:
            return None

        return (int(groups[0]), int(groups[1]))

    @staticmethod
    def get_save_cursor():
        """Get string to save the current cursor position."""
        return f"\033[s"

    @staticmethod
    def get_restore_cursor():
        """Get string to save the current cursor position."""
        return f"\033[u"

    @staticmethod
    def get_one_color(color, string):
        """Get a string in a color, but reset to normal at the end."""
        return f"{color}{string}{Term.NORMAL}"

    @staticmethod
    def get_black(string):
        """Return a black string."""
        return Term.one_color(Term.BLACK, string)

    @staticmethod
    def get_blue(string):
        """Return a blue string."""
        return Term.one_color(Term.BLUE, string)

    @staticmethod
    def get_cyan(string):
        """Return a cyan string."""
        return Term.one_color(Term.CYAN, string)

    @staticmethod
    def get_green(string):
        """Return a green string."""
        return Term.one_color(Term.GREEN, string)

    @staticmethod
    def get_magenta(string):
        """Return a magenta string."""
        return Term.one_color(Term.MAGENTA, string)

    @staticmethod
    def get_red(string):
        """Return a red string."""
        return Term.one_color(Term.RED, string)

    @staticmethod
    def get_white(string):
        """Return a white string."""
        return Term.one_color(Term.WHITE, string)

    @staticmethod
    def get_yellow(string):
        """Return a yellow string."""
        return Term.one_color(Term.YELLOW, string)

    ok = green
    warn = yellow
    warning = yellow
    err = red
    error = red
    no_ok = red

    pass
