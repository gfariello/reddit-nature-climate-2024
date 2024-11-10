# -*- coding: utf-8 -*-
"""A module for checking and setting filesystem permissions."""

import os
import sys
import stat
import re
import argparse
from collections import OrderedDict

from .constants import CommonConstants


class DuplicatePathError(Exception):
    """A duplicate path error."""

    pass


class SearchPath:
    """
    A SearchPath class.

    A simple class to hold a bunch of directories in which to search for stuff.

    Parameters
    ----------
    dorectories: list
        A list of directories to search.
    required_perms: int
        A bitmask of permissions which are required on the targe file / directory.
    forbidden_perms: int
        A bitmask of permissions which are forbidden on the file / directory.

    """

    USR_READ = stat.S_IRUSR
    USR_WRITE = stat.S_IWUSR
    USR_EXEC = stat.S_IXUSR
    GRP_READ = stat.S_IRGRP
    GRP_WRITE = stat.S_IWGRP
    GRP_EXEC = stat.S_IXGRP
    OTH_READ = stat.S_IROTH
    OTH_WRITE = stat.S_IWOTH
    OTH_EXEC = stat.S_IXOTH

    def __init__(self, directories=None, required_perms=0, forbidden_perms=0):
        """Init function."""
        self._directories = []
        self._errors = []
        self._searched_history = None
        self._check_perms = True
        self._required_perms = required_perms
        self._forbidden_perms = forbidden_perms
        self._auto_append_dirs = []
        if directories is not None:
            for directory in directories:
                self.append(directory)
                pass
            pass
        pass

    def add_required_perms(self, stat_flag_list):
        """
        Add stat permissions to requried permissions.

        This is a convenience method that allows you to add multiple
        permissions without having to "know" how to create the proper
        bitmask.

        Parameters
        ----------
        stat_flag_list : list
            A list of required permissions flags.

        Returns
        -------
        self


        """
        for stat_flag in stat_flag_list:
            self.add_required_perm(stat_flag)
            pass
        return self

    def add_required_perm(self, stat_flag):
        """
        Add stat permission bitmap to requried permissions.

        Parameters
        ----------
        stat_flag : int
            A bitmask containing the flag(s) to add as required.

        Returns
        -------
        self

        """
        self._required_perms |= stat_flag
        self._forbidden_perms &= ~ stat_flag
        return self

    def set_required_perms(self, stat_flag):
        """
        Set the required stat permission bitmap.

        Parameters
        ----------
        stat_flag : int
            A bitmask containing the flag(s) to set as required.

        Returns
        -------
        self

        """
        self._required_perms = stat_flag
        self._forbidden_perms &= ~ stat_flag
        return self

    def get_required_perms(self):
        """Get the required perms bitmask."""
        return self._required_perms

    required_perms = property(get_required_perms, set_required_perms)

    def add_forbidden_perms(self, stat_flag_list):
        """
        Add stat permissions that are forbidden.

        This is a convenience method that allows you to add multiple
        permissions without having to "know" how to create the proper
        bitmask.

        Parameters
        ----------
        stat_flag_list : list
            A list of forbidden permissions flags.

        Returns
        -------
        self

        """
        for stat_flag in stat_flag_list:
            self.add_forbidden_perm(stat_flag)
            pass
        return self

    def add_forbidden_perm(self, stat_flag):
        """
        Add stat permission bitmap to forbidden permissions.

        Parameters
        ----------
        stat_flag : int
            A bitmask containing the flag(s) to add as forbidden.

        Returns
        -------
        self

        """
        self._required_perms &= ~ stat_flag
        self._forbidden_perms |= stat_flag
        return self

    def get_forbidden_perms(self):
        """Get the forbidden perms bitmask."""
        return self._required_perms

    def set_forbidden_perms(self, stat_flag):
        """
        Set the required stat permission bitmap.

        Parameters
        ----------
        stat_flag : int
            A bitmask containing the flag(s) to set as required.

        Returns
        -------
        self

        """
        self._forbidden_perms = stat_flag
        self._required_perms &= ~ stat_flag
        return self

    forbidden_perms = property(get_forbidden_perms, set_forbidden_perms)

    def get_directories(self):
        """
        Get the array of directories in the path(s) to search.

        Returns
        -------
        list

        """
        return self._directories

    def set_directories(self, directories):
        """
        Set the list of directories in the path(s) to search.

        Parameters
        ----------
        directories : list
            A list of directories to add.

        Returns
        -------
        self

        """
        self._directories = directories
        return self

    directories = property(get_directories, set_directories)

    def get_searched_history(self):
        """
        Get where we looked.

        Returns
        -------
        list

        """
        return self._searched_history

    searched_history = property(get_searched_history)

    def get_auto_append_dirs(self):
        """
        Get auto_append_dirs.

        Get the list of directories to append to each directory in the search path.

        Returns
        -------
        list

        """
        return self._auto_append_dirs

    def set_auto_append_dirs(self, dirnames):
        """
        Set auto_append_dirs.

        Set the list of directories to append to each directory in the search path.

        Parameters
        ----------
        dirnames : list
            A list of directories.

        Returns
        -------
        self

        """
        self._auto_append_dirs = dirnames
        return self

    auto_append_dirs = property(get_auto_append_dirs, set_auto_append_dirs)

    def _append(self, directory, missing_error=False, nondir_error=True,
                dupes='ignore'):
        """
        Append a directory.

        Append a directory, if and only if, it exists, is a directory, and
        has not already been added.

        Parameters
        ----------
        directory : str
            The directory to add to the search path.
        missing_error : bool
            If the directory does not exist, is that an error?
        nondir_error : bool
            If the directory is not a directory, is that an error?
        dupes : str
            'ignore' = ignore and don't add, 'keep' = add them,
            'error' = track as error, 'raise' = raise a DuplicatePathError exception.

        Returns
        -------
        self

        """
        if not os.path.exists(directory):
            if missing_error:
                self._errors.append(f"Directory '{directory}' does not exist.")
                pass
            return self
        if not os.path.isdir(directory):
            if nondir_error:
                self._errors.append(f"Directory '{directory}' is not a "
                                    "directory.")
                pass
            return self
        directory = os.path.realpath(directory)
        if directory in self._directories:
            if 'ignore' == dupes:
                pass
            elif 'error' == dupes:
                self._errors.append(f"Directory '{directory}' already added.")
            elif 'raise' == dupes:
                raise DuplicatePathError("Directory '{directory}' already added.")
            elif 'keep' == dupes:
                self._directories.append(directory)
                pass
            else:
                raise ValueError("Unknown value for dupes provided: '{dupes}'.")
        else:
            self._directories.append(directory)
            pass
        return self

    def append(self, directory, missing_error=False, nondir_error=True,
               dupes='ignore'):
        """
        Append a directory.

        Append a directory, if and only if, it exists, is a directory, and has
        not already been added. If there are directories defined in
        `auto_append_dirs`, append those to this directory and add them as well.

        Notes
        -----
        Sudirectories created by appending `auto_append_dirs` will not cause
        errors (e.g., are called with `missing_error=False`,
        `nondir_error=False`, `dupe_error=False`, and `allow_dupes=False`

        Parameters
        ----------
        directory : str or list
            The directory or list of directories to add to the search path.
        missing_error : bool
            If the directory does not exist, is that an error?
        nondir_error : bool
            If the directory is not a directory, is that an error?
        dupes : str
            'ignore' = ignore and don't add, 'keep' = add them,
            'error' = track as error, 'raise' = raise a DuplicatePathError exception.
        allow_dupes : bool
            If the directory is a duplicate, should we add it anyway?

        Returns
        -------
        self

        """
        if isinstance(directory, list):
            for dirname in directory:
                self.append(dirname, missing_error, nondir_error, dupes)
                pass
            return self
        self._append(directory, missing_error, nondir_error, dupes)
        if self.auto_append_dirs:
            for dirname in self.auto_append_dirs:
                self._append(dirname, missing_error, nondir_error,
                             dupes)
                pass
            pass
        return self

    def find_first(self, filenames):
        """
        Find the first filename.

        Find the first file whose basename is in filenames and was found in the
        search path.

        Notes
        -----
        The filenames are searched for by directory in the path(s)
        first, then by filenames. For example, if you run:::


            sp = SearchPath("i","j")
            sp.find_first(["a","b"])

        This will look for "i/a", "i/b", "j/a", "j/b" in that order.

        Parameters
        ----------
        filenames : list
            A list of filenames to search for.

        Returns
        -------
        `str` or `None`
            The full path plus filename if found, otherwise, `None`.

        """
        self._searched_history = []
        if not isinstance(filenames, list):
            raise ValueError("SearchPath.find_one() requires a list of "
                             "filenames, recieved {filenames} which is a "
                             f"{type(filenames).__name__}.")
        for dirname in self._directories:
            for filename in filenames:
                fullpath = os.path.join(dirname, filename)
                self._searched_history.append(fullpath)
                if os.path.exists(fullpath):
                    if not os.path.isfile(fullpath):
                        self._errors.append(f"'{fullpath}' is not a file.")
                    else:
                        if os.path.realpath(fullpath) != CommonConstants.MAIN_REALPATH:
                            return fullpath
                        pass
                    pass
                pass
            pass
        return None
    pass

    def find_all(self, filenames, required=False):
        """
        Find all filenames.

        Find all the files whose basename is in filenames and were
        found in the search path.

        Notes
        -----
        Search order is the same as for `find_first(filenames)`.

        Parameters
        ----------
        filenames : list or string
            A list of filenames to search for.
        required : boolean
            If true, will throw a FileNotFoundErr if none are found.

        Returns
        -------
        `list`
            A (possibly empty) list with the full paths of found items.

        """
        self._searched_history = []
        found = []
        if isinstance(filenames, str):
            filenames = [filenames]
        elif not isinstance(filenames, list):
            raise ValueError("SearchPath.find_one() requires a list of "
                             "filenames, recieved {filenames} which is a "
                             f"{type(filenames).__name__}.")
        for dirname in self._directories:
            for filename in filenames:
                fullpath = os.path.join(dirname, filename)
                self._searched_history.append(fullpath)
                if os.path.exists(fullpath):
                    if not os.path.isfile(fullpath):
                        self._errors.append(f"'{fullpath}' is not a file.")
                    else:
                        if os.path.realpath(fullpath) != CommonConstants.MAIN_REALPATH:
                            found.append(fullpath)
                        pass
                    pass
                pass
            pass
        if required and not found:
            err = ""
            if len(filenames) > 1:
                err += f"Unable to locate any of the {len(filenames)} files in search path. Files:\n"
                for filename in filenames:
                    err += f" - '{filename}'\n"
                    pass
                err += "Search path:\n"
            else:
                err += f"Unable to locate '{filenames[0]}' in searh path:\n"
                pass
            for dirname in self._directories:
                err += f" - '{dirname}'\n"
                pass
            raise FileNotFoundError(err)
        return found
    pass


class FSPermsRegExp:
    """
    A classs to specify setting permissions based on regular expressions, etc.

    A FSPermsRegExp object used to check if a given path matches
    criteria set by the ftype and regular expression. Used to
    determine if permissions are set correctly

    Parameters
    ----------
    re_str : str
        A regular expression (either as string or re) which the full path
        filename must match in order for this rule to apply to a file or
        directory.
    permissions_str : str
        A string defining the permissions to set. '*' means don't change.
    ftype : char
        A character defining the type of thing to work on. 'f' is for 'file',
        '*' is for anything, 'd' is for 'directory', and 'l' is for symlink
        (which is unpredictable, so don't use it.).

    Attributes
    ----------
    permissions_str : str
         Same as above.

    """

    _type_check = {
        '*': os.path.exists,
        'f': os.path.isfile,
        'd': os.path.isdir,
        'l': os.path.islink,
    }

    def __init__(self, re_str, permissions_str, ftype):
        """Init this object."""
        self._re_str = re_str
        self._compiled_re = re.compile(self._re_str)
        self._permissions_str = permissions_str
        self._ftype = self._ftype_is_valid(ftype)
        self._ftype_check = FSPermsRegExp._type_check[self._ftype]
        pass

    @property
    def permissions_str(self):
        """Get the string representation of the permissions."""
        return self._permissions_str

    @staticmethod
    def _ftype_is_valid(ftype):
        if ftype not in FSPermsRegExp._type_check:
            raise ValueError(f"fype must be one of f, d, l, or *. Got '{ftype}'.")
        return ftype

    def type_match(self, fullpath):
        """Check if the types match this object."""
        return self._ftype_check(fullpath)

    def re_match(self, fullpath):
        """Check if the this object's regular expression matches this fullpath."""
        return self._compiled_re.match(fullpath)

    def match(self, fullpath):
        """Check if the this object permissions should be applied to this fullpath."""
        return self._ftype_check(fullpath) and self._compiled_re.match(fullpath)

    pass


class FSPerms:
    """A Fyle System Permissions Handler Object.

    To help manage filesystem permissions.
    """

    def __init__(self, args):
        """Init this object."""
        self._args = args
        self._perms_dict = OrderedDict()
        self._verbosity = 0
        self._file_default_mask = "r..r--r--"
        self._dir_default_mask = "r.x--x--x"
        self._logger = None
        if not hasattr(args, 'fake'):
            self._args.fake = False
            pass
        if not hasattr(args, 'debug'):
            self._args.debug = False
            pass
        pass

    def _add_fspermsre(self, re_str, permissions_str, ftype):
        if re_str not in self._perms_dict:
            fspermsre = FSPermsRegExp(re_str, permissions_str, ftype)
            self._perms_dict[re_str] = fspermsre
            pass
        pass

    def set_for_web(self):
        """Set permissions for "web" directories."""
        # directories that start with '.'
        self._add_fspermsre(r"^\.|.*/\..+$", "r.x------", 'd')
        # directories inside directories that start with '.'
        self._add_fspermsre(r".*/\..+", "r.x------", 'd')
        # Defualt for directories
        self._add_fspermsre(r".*", "r.x--x--x", 'd')
        # files inside directories that start with '.'
        self._add_fspermsre(r".*\/\..+\/.*", "r..------", 'f')
        # files that start with '.' or end with '~' or '#'
        self._add_fspermsre(r"^\.|.*\/\.(?!ht).*$|.*[~#]$", "r..------", 'f')
        # "normal" files that need to be served
        self._add_fspermsre(r".*\.(s?html?|png|jpe?g|svg|pdf|gif|js|json|css)$", "r.-r--r--", 'f')
        # "normal" files that need to execute
        self._add_fspermsre(r".*\.(sh|cgi|py|pl)$", "r.xr-xr-x", 'f')
        # Default for files
        self._add_fspermsre(r".*", "r..r--r--", 'f')
        pass

    @staticmethod
    def booltext(val, txt_true, txt_false='-'):
        """Return a string based on boolean input."""
        if val:
            return txt_true
        return txt_false

    @staticmethod
    def chkmodetext(txt, pos, char, val):
        """Check perms text string."""
        if txt[pos] == char:
            return val
        if txt[pos] == '-':
            return 0
        raise ValueError(
            f"Found char '{txt[pos]}' at pos={pos}. Was expecting either '-' "
            "or '{char}'.\n The text representation of a mode must be in "
            "\"-rwxrwxrwx\" format with the first character ignored or in "
            "\"rwxrwxrwx\" format, not \"{txt}\".")

    def mode2text(self, mode):
        """Convert a mode int to a perms string."""
        txt = ''
        if stat.S_ISDIR(mode):
            txt += 'd'
        elif stat.S_ISLNK(mode):
            txt += 'l'
        else:
            txt += '-'
            pass
        txt += self.booltext(mode & stat.S_IRUSR, 'r', '-')
        txt += self.booltext(mode & stat.S_IWUSR, 'w', '-')
        txt += self.booltext(mode & stat.S_IXUSR, 'x', '-')
        txt += self.booltext(mode & stat.S_IRGRP, 'r', '-')
        txt += self.booltext(mode & stat.S_IWGRP, 'w', '-')
        txt += self.booltext(mode & stat.S_IXGRP, 'x', '-')
        txt += self.booltext(mode & stat.S_IROTH, 'r', '-')
        txt += self.booltext(mode & stat.S_IWOTH, 'w', '-')
        txt += self.booltext(mode & stat.S_IXOTH, 'x', '-')
        return txt

    def text2mode(self, txt):
        """Convert a text perms string to an int mode."""
        tlen = len(txt)
        if tlen > 10 or tlen < 9:
            raise ValueError(
                "The text representation of a mode must be in \"-rwxrwxrwx\" "
                "format with the first character ignored or in \"rwxrwxrwx\" "
                f"format, not \"{txt}\".")
        if tlen > 9:
            txt = txt[1:]
            pass
        return (
            0 |
            self.chkmodetext(txt, 0, 'r', stat.S_IRUSR) |
            self.chkmodetext(txt, 1, 'w', stat.S_IWUSR) |
            self.chkmodetext(txt, 2, 'x', stat.S_IXUSR) |
            self.chkmodetext(txt, 3, 'r', stat.S_IRGRP) |
            self.chkmodetext(txt, 4, 'w', stat.S_IWGRP) |
            self.chkmodetext(txt, 5, 'x', stat.S_IXGRP) |
            self.chkmodetext(txt, 6, 'r', stat.S_IROTH) |
            self.chkmodetext(txt, 7, 'w', stat.S_IWOTH) |
            self.chkmodetext(txt, 8, 'x', stat.S_IXOTH))

    def mask2mode(self, mask, mode):
        """Convert a mask to an int mode."""
        tlen = len(mask)
        if tlen > 10 or tlen < 9:
            raise ValueError(
                "The text representation of a mode must be in \"-rwxrwxrwx\" "
                "format with the first character ignored or in \"rwxrwxrwx\" "
                f"format, not \"{mask}\".")
        if tlen > 9:
            mask = mask[1:]
            pass
        mode = self._maskprivchar(mode, mask, 0, 'r', stat.S_IRUSR)
        mode = self._maskprivchar(mode, mask, 1, 'w', stat.S_IWUSR)
        mode = self._maskprivchar(mode, mask, 2, 'x', stat.S_IXUSR)
        mode = self._maskprivchar(mode, mask, 3, 'r', stat.S_IRGRP)
        mode = self._maskprivchar(mode, mask, 4, 'w', stat.S_IWGRP)
        mode = self._maskprivchar(mode, mask, 5, 'x', stat.S_IXGRP)
        mode = self._maskprivchar(mode, mask, 6, 'r', stat.S_IROTH)
        mode = self._maskprivchar(mode, mask, 7, 'w', stat.S_IWOTH)
        mode = self._maskprivchar(mode, mask, 8, 'x', stat.S_IXOTH)
        return mode

    @staticmethod
    def _maskprivchar(mode, mask, pos, char, val):
        # Don't change
        mchar = mask[pos]
        if mchar == '*' or mchar == '.':
            return mode
        # Remove
        if mchar == '-':
            # Already no priv
            if not mode & val:
                return mode
            # Remove priv
            return mode ^ val
        # Add
        if mchar == char:
            # Already has priv
            if mode & val:
                return mode
            return mode | val
        raise ValueError(
            "The mask must be in \"-rw-r*xr-x\" format with the first "
            f"caracter ignored or in \"r-*r--r**\" format, not \"{mask}\".")

    @staticmethod
    def mode_to_text(mode):
        """Take a mode as returned by os.stat() and render it in 'drwxrwxrwx' fromat."""
        if stat.S_ISDIR(mode):
            first = 'd'
        elif stat.S_ISLNK(mode):
            first = 'l'
        else:
            first = "-"
            pass
        text = ""
        letters = "xwrxwrxwr"
        for char in letters:
            if 0b000000001 & mode:
                text += char
            else:
                text += "-"
                pass
            mode = mode >> 1
            pass
        return first + text[::-1]

    def get_long_stat(self, fname):
        """Return the octal mode and text representation of the mode for a given filename."""
        mode = os.lstat(fname).st_mode
        return mode, self.mode_to_text(mode)

    @staticmethod
    def chars_to_bits(chars):
        """Convert three chars (e.g., "-wx") into the octal equivalent."""
        if not isinstance(chars, str):
            raise ValueError(
                "chars_to_bits() requires a string with three characters in "
                f"\"rwx\" format not '{chars}' which is of type "
                f"{type(chars).__name__}.")
        if 3 != len(chars):
            raise ValueError(
                "chars_to_bits() requires a string with three characters in "
                f"\"rwx\" format. It got '{chars}' which is {len(chars)} "
                "characters long.")
        errors = []
        val = 0
        for idx, valid_char in "rwx":
            if '-' == chars[idx] and valid_char != chars[idx]:
                val = val << 1
            elif valid_char == chars[idx]:
                val = val << 1 | 1
            else:
                errors.append([idx, chars[idx], valid_char])
                pass
            pass
        if errors:
            error_str = ""
            for error in errors:
                error_str += f" Character '{error[1]}' at index {error[0]} "\
                             "may only be either '-' or '{error[2]}'."
                pass
            raise ValueError(
                "chars_to_bits() requires a string with three characters in "
                f"\"rwx\" format. It got '{chars}'. Details:{error_str}")
        return val

    def text_to_mode(self, text_mode):
        """Translate a text-representation of a file mode to a numeric value."""
        if (len(text_mode) != 9 or not re.match(r'^[rwx-]+$', text_mode)):
            raise ValueError(f"Mode  needs to be in \"rwx--x--x\" format. Received \"{text_mode}\"")
        try:
            numeric_mode = 0
            numeric_mode |= self.chars_to_bits(text_mode[0:3]) << 6
            numeric_mode |= self.chars_to_bits(text_mode[3:6]) << 3
            numeric_mode |= self.chars_to_bits(text_mode[6:9])
            # self.debug("Converted '%s' to '%o'" %(text_mode, numeric_mode))
        except ValueError:
            raise ValueError(
                "Unable to process text mode permissions 'text_mode' "
                f"(u={text_mode[0:3]},g={text_mode[3:6]},o={text_mode[6:9]}). "
                "Should be in 'rwxrwxrwx' format with each subgroup "
                "(u='rwx',g='rwx',o='rwx') in that order, replacing "
                "r,w,x with '-' where no permissions are grandted.")
        return numeric_mode

    def _update_mode(self, fs_perms_re, fullpath):
        if not fs_perms_re.match(fullpath):
            return False
        old = os.stat(fullpath).st_mode
        # print([fs_perms_re.permissions_str])
        new = self.mask2mode(fs_perms_re.permissions_str, old)
        if old != new:
            if self._args.fake:
                print(
                    f"CHMOD {self.mode2text(old)} => {self.mode2text(new)} "
                    f"for '{fullpath}' [FAKED]"
                )
            else:
                print(
                    f"CHMOD {self.mode2text(old)} => {self.mode2text(new)} "
                    f"for '{fullpath}'"
                )
                os.chmod(fullpath, new)
                pass
            pass
        else:
            if self._args.debug:
                print(f"KEEP                {self.mode2text(new)} for '{fullpath}'")
                pass
            pass
        return True

    def _check_perms_dict(self, fullpath):
        for fs_perms_re in self._perms_dict.values():
            if self._update_mode(fs_perms_re, fullpath):
                return True
            pass
        return False

    def walk(self, path):
        """Walk a path and "fix" permissions."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"File or directory '{path}' not found.")
        if not os.path.isdir(path):
            raise NotADirectoryError(f"File '{path}' is not a directory.")
        if not self._perms_dict:
            raise ValueError("Cannot call walk() if there are no permissions set.")
        for (base, directories, files) in os.walk(path):
            for directory in directories:
                self._check_perms_dict(os.path.join(base, directory))
                pass
            for filename in files:
                self._check_perms_dict(os.path.join(base, filename))
                pass
            pass
        pass
    pass


def test_mode2text(fsp, mode, text):
    """Run a test."""
    new_text = fsp.mode2text(mode)
    result = " :OK" if new_text == text else f" ≠ \"{text}\": ERROR"
    print(f" - TEST: fsp.mode2text(0o{mode:04o})       = \"{new_text}\" {result}")
    new_mode = fsp.text2mode(text)
    result = " :OK" if new_text == text else f" ≠ 0o{mode:04o}: ERROR"
    print(f" - TEST: fsp.text2mode(\"{text}\") = 0o{new_mode:04o} {result}")
    pass


def test_mask2mode(fsp, mask, mode, expected_mode_str):
    """Run a test."""
    expected_mode = fsp.text2mode(expected_mode_str)
    new_mode = fsp.mask2mode(mask, mode)
    new_mode_str = fsp.mode2text(new_mode)
    result = "                        :OK" if new_mode == expected_mode else f" ≠ 0o{expected_mode:04o} \"{expected_mode_str}\"  :ERROR"
    print(f" - TEST: fsp.mask2mode(\"{mask}\",0o{mode:04o}) = 0o{new_mode:04o} \"{new_mode_str}\" {result}")
    pass


def run_tests_1(fsp):
    """Run some tests."""
    mode = "rwxrwxrwx"
    for mode, text in [
            (0o777, "-rwxrwxrwx"),
            (0o700, "-rwx------"),
            (0o644, "-rw-r--r--"),
            (0o751, "-rwxr-x--x"),
            (0o222, "--w--w--w-"),
            (0o000, "----------"), ]:
        test_mode2text(fsp, mode, text)
        pass
    for mask, mode, expected_mode in [
            ("*********", 0o777, "-rwxrwxrwx"),
            ("rw*-***-*", 0o777, "-rwx-wxr-x"),
            ("rw*-***-*", 0o000, "-rw-------"),
            ("rw*rwxrwx", 0o000, "-rw-rwxrwx"),
            ("rwx...r-x", 0o644, "-rwxr--r-x"), ]:
        test_mask2mode(fsp, mask, mode, expected_mode)
        pass
    pass


def set_web_perms(fsp, path):
    """Set default permissions for "web" directories."""
    fsp.set_for_web()
    fsp.walk(path)
    pass


def run_tests_2(fsp):
    """Run some tests."""
    set_web_perms(fsp, "..//ansurv/")
    pass


def _main():
    """Run as if a program."""
    parser = argparse.ArgumentParser(description='Manage, check, change file and directory permissions.')
    parser.add_argument('--debug', '-d', default=False, action='store_true', dest='debug', help="Turn debugging on.")
    parser.add_argument('--quiet', '-q', default=0, dest='quiet', action='count', help="Decrease verbosity. Can have multiple.")
    parser.add_argument('--fake', default=0, dest='fake', action='store_true', help="Pretend, don't do.")
    parser.add_argument('--run-tests-1', default=False, action='store_true', dest='run_tests_1', help="Run some tests.")
    parser.add_argument('--run-tests-2', default=False, action='store_true', dest='run_tests_2', help="Run some tests.")
    parser.add_argument('--web-perms', default=None, type=str, dest='web_perms_dir', help="Set permissions for 'Web' on given directory.")
    parser.add_argument('--verbose', '-v', default=0, dest='verbosity', action='count', help="Increase verbosity. Can have multiple.")

    args = parser.parse_args()
    args.verbosity = 1 + args.verbosity - args.quiet

    fsp = FSPerms(args=args)
    did_something = False
    if args.run_tests_1:
        did_something = True
        run_tests_1(fsp)
        pass
    if args.run_tests_2:
        did_something = True
        run_tests_2(fsp)
        pass
    if args.web_perms_dir:
        did_something = True
        set_web_perms(fsp, args.web_perms_dir)
        pass
    if not did_something:
        print("This is just a module that should be used from somewhere else, "
              "however, you can try --help for more info.")
        pass
    return 0


if __name__ == "__main__":
    sys.exit(_main())
    pass
