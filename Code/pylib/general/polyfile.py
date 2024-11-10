#!/usr/bin/env python3
"""
polyfile - A Python module for versatile file handling.

This module provides utility classes and functions for reading and writing files of various formats
(plain text, gzip, bz2, zst) and from various sources (local files, HTTP/HTTPS URLs, FTP, SSH, and SFTP servers).

Classes
-------
- `FTPSessionWrapper`: A wrapper around `ftplib.FTP` for more flexible FTP session handling.
- `PolyReader`: A class designed for reading files line-by-line with support for various
   compression formats and remote sources.
- `PolyWriter`: A class designed for writing files line-by-line with support for various
   compression formats and remote destinations.

Usage
-----
To read from a local gzipped file:
    >>> with PolyReader("path/to/localfile.gz") as reader:
    >>>     for line in reader:
    >>>         process(line)

To read from a remote HTTP source:
    >>> with PolyReader("http://example.com/data.txt") as reader:
    >>>     for line in reader:
    >>>         process(line)

To read from a remote SSH server with zstd compression:
    >>> with PolyReader("ssh://username:password@hostname/path/to/remote.zst") as reader:
    >>>     for line in reader:
    >>>         process(line)

To write to a local bz2 compressed file:
    >>> with PolyWriter("path/to/outputfile.bz2") as writer:
    >>>     writer.write("Some data to write")

To write to a remote SFTP server:
    >>> with PolyWriter("sftp://username:password@hostname/path/to/outputfile.txt") as writer:
    >>>     writer.write("Some data to write")

To write to a local file with zstd compression:
    >>> with PolyWriter("path/to/outputfile.zst") as writer:
    >>>     writer.write("Some data to write")

Dependencies
------------
- `paramiko`: For SSH/SFTP support.
- `zstandard`: For zst file support.
- `requests`: For HTTP/HTTPS support.
- `ftputil`: For enhanced FTP utilities.
- `tqdm`: For progress bars.

Author
------
Gabriele Fariello

Version
-------
1.0.0
"""
import argparse
import io
import bz2
import gzip
import paramiko
import zstandard as zstd
import requests
from urllib.parse import urlparse, ParseResult
from tqdm import tqdm
import ftplib
import ftputil
import os


class FTPSessionWrapper(ftplib.FTP):
    """
    A wrapper around ftplib.FTP for handling FTP connections with a specified port.

    This class extends ftplib.FTP to allow connections to FTP servers on non-standard ports.
    It is primarily intended for internal use within the PolyReader and PolyWriter classes
    and not for direct use by end users.

    Attributes
    ----------
    host : str
        The hostname of the FTP server.
    userid : str
        The username for FTP login.
    password : str
        The password for FTP login.
    port : int
        The port to connect to on the FTP server.

    Methods
    -------
    __init__(host, userid, password, port):
        Initializes the FTP connection and logs in with the provided credentials.
    """

    def __init__(self, host: str, userid: str, password: str, port: int):
        """
        Initialize the FTPSessionWrapper with the given host, userid, password, and port.

        This method connects to the specified FTP server on the given port and logs in
        using the provided credentials.

        Parameters
        ----------
        host : str
            The hostname of the FTP server.
        userid : str
            The username for FTP login.
        password : str
            The password for FTP login.
        port : int
            The port to connect to on the FTP server.
        """
        # Initialize the parent ftplib.FTP class
        ftplib.FTP.__init__(self)
        # Connect to the specified FTP server on the given port
        self.connect(host, port)
        # Log in to the FTP server with the provided username and password
        self.login(userid, password)
        pass  # for auto-indentation

    pass  # for auto-indentation


class PolyReader:
    """
    A class used to read files line by line, with support for gzip, bz2, and zst compression formats,
    as well as remote files over HTTP, HTTPS, FTP, SSH, and SFTP.

    Attributes
    ----------
    filename : str
        The name of the file to read.
    show_progress : bool
        Whether to show a progress bar.

    Methods
    -------
    open() -> 'PolyReader':
        Opens the file for reading, decompressing it on the fly if necessary.
    close():
        Closes the file.
    """

    def __init__(self, filename: str, show_progress: bool = False):
        """
        Initialize PolyReader with a filename.

        Parameters
        ----------
        filename : str
            The name of the file to read.
        show_progress : bool
            Whether to show a progress bar.
        """
        self.filename = filename
        self.show_progress = show_progress
        self._fh = None
        self._sftp = None
        self._ftp = None
        self._progress = None
        self._request_iterator = False
        self._http_file_size = None

    def __enter__(self) -> 'PolyReader':
        """
        Open the file when entering the context.

        This method is called when the context is entered using the `with` statement.

        Returns
        -------
        PolyReader
            The PolyReader instance with the file opened for reading.
        """
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Close the file when exiting the context.

        This method is called when the context is exited using the `with` statement.

        Parameters
        ----------
        exc_type : type
            The exception type.
        exc_value : Exception
            The exception instance.
        traceback : traceback
            The traceback object.

        Returns
        -------
        None
        """
        self.close()
        pass  # for auto-indentation

    def __iter__(self) -> 'PolyReader':
        """
        Make the PolyReader object iterable.

        This method allows the PolyReader to be used as an iterator.

        Returns
        -------
        PolyReader
            The PolyReader instance itself.
        """
        return self

    def __next__(self):
        """
        Provide the next line in the file.

        This method is used to retrieve the next line when iterating over the file.

        Returns
        -------
        str
            The next line in the file.

        Raises
        ------
        StopIteration
            When the end of the file is reached.
        """
        if self._request_iterator:
            line = next(self._fh)
        else:
            line = self._fh.readline()
            pass  # for auto-indentation

        if self.show_progress and self._progress is not None:
            self._progress.update(len(line))

        if not line:
            # End of file
            raise StopIteration
        if isinstance(line, bytes):
            return line.decode()
        return line

    def _wrap_ssh(self, parsed: ParseResult):
        """
        Wrap self._fh to handle SSH/SFTP connections and file operations.

        This method establishes an SSH connection using paramiko, opens the specified file via SFTP,
        and wraps it with appropriate decompression handlers based on the file extension.

        Parameters
        ----------
        parsed : ParseResult
            The parsed URL containing the SSH/SFTP connection details and file path.

        Returns
        -------
        None
        """
        # Initialize an SSH client
        client = paramiko.SSHClient()
        # Load system host keys for the SSH client
        client.load_system_host_keys()
        # Connect to the SSH server using the parsed hostname, username, and password
        client.connect(parsed.hostname, username=parsed.username, password=parsed.password)
        # Open an SFTP session over the SSH connection
        self._sftp = client.open_sftp()

        try:
            # Attempt to open the specified file on the remote server in binary read mode
            self._sftp = self._sftp.file(parsed.path, 'rb')
        except FileNotFoundError as err:
            # If the file is not found, print an error message and exit
            print(f"ERROR: No such file found: {self.filename}")
            return exit(1), err

        # Set the file handle to the SFTP file object
        self._fh = self._sftp

        # Check the file extension to determine the appropriate decompression method
        if self.filename.endswith('.zst'):
            # Initialize a Zstandard decompressor with a maximum window size
            dctx = zstd.ZstdDecompressor(max_window_size=2**31)
            # Wrap the file handle with a text IO wrapper for decompressed stream reading
            self._fh = io.TextIOWrapper(dctx.stream_reader(self._fh), encoding='utf-8')
        elif self.filename.endswith('.bz2'):
            # Wrap the file handle with a BZ2 file object for decompression
            self._fh = bz2.BZ2File(self._fh)
        elif self.filename.endswith('.gz'):
            # Wrap the file handle with a Gzip file object for decompression
            self._fh = gzip.GzipFile(fileobj=self._fh)
            pass  # for auto-indentation
        pass  # for auto-indentation

    def _wrap_http(self):
        """
        Wrap self._fh to handle HTTP/HTTPS connections and file operations.

        This method fetches the specified file via HTTP/HTTPS, wraps the response content
        with appropriate decompression handlers based on the file extension, and sets the file
        handle to the decompressed content. It also stores the file size in self._http_file_size.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        # Make a GET request to the specified URL with streaming enabled
        response = requests.get(self.filename, stream=True)

        # Store the file size from the Content-Length header
        self._http_file_size = int(response.headers.get('Content-Length', 0))

        # Check the file extension to determine the appropriate decompression method
        if self.filename.endswith(".zst"):
            # Initialize a Zstandard decompressor with a maximum window size
            dctx = zstd.ZstdDecompressor(max_window_size=2**31)
            # Wrap the response content with a text IO wrapper for decompressed stream reading
            self._fh = io.TextIOWrapper(dctx.stream_reader(response.raw, read_across_frames=True), encoding='utf-8')
        elif self.filename.endswith(".bz2"):
            # Wrap the response raw content with a BZ2 file object for decompression
            self._fh = bz2.open(response.raw, 'rt')
        elif self.filename.endswith(".gz"):
            # Wrap the response raw content with a Gzip file object for decompression
            self._fh = gzip.open(response.raw, 'rt')
        else:
            # For non-compressed files, set the file handle to iterate over response lines
            self._fh = response.iter_lines()
            # Indicate that the request iterator will yield bytes that need decoding
            self._request_iterator = True
            pass  # for auto-indentation
        pass  # for auto-indentation

    def _wrap_local(self):
        """
        Wrap self._fh to handle local file operations with optional decompression.

        This method opens the specified local file and wraps it with appropriate decompression
        handlers based on the file extension, setting the file handle to the decompressed content.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        # Check the file extension to determine the appropriate decompression method
        if self.filename.endswith('.zst'):
            # Initialize a Zstandard decompressor with a maximum window size
            dctx = zstd.ZstdDecompressor(max_window_size=2**31)
            # Open the file in binary read mode and wrap it with a text IO wrapper for decompressed stream reading
            self._fh = io.TextIOWrapper(dctx.stream_reader(open(self.filename, 'rb')), encoding='utf-8')
        elif self.filename.endswith('.bz2'):
            # Open the BZ2 file in text read mode for decompression
            self._fh = bz2.open(self.filename, 'rt')
        elif self.filename.endswith('.gz'):
            # Open the Gzip file in text read mode for decompression
            self._fh = gzip.open(self.filename, 'rt')
        else:
            # Open the file in text read mode if no decompression is needed
            self._fh = open(self.filename, 'r')
            pass  # for auto-indentation
        pass  # for auto-indentation

    def open(self) -> 'PolyReader':
        """
        Open the file for reading, decompressing it on the fly if necessary.

        This method determines the file type and source, and opens the file
        with the appropriate handler and decompression method.

        Returns
        -------
        PolyReader
            The PolyReader instance with the file opened for reading.
        """
        # Parse the URL to determine the file scheme (e.g., sftp, http, file)
        parsed = urlparse(self.filename)

        # Handle SFTP and SSH URLs
        if parsed.scheme in ('sftp', 'ssh'):
            self._wrap_ssh(parsed)
        # Handle HTTP and HTTPS URLs
        elif parsed.scheme in ('http', 'https'):
            self._wrap_http()
        # Handle local files
        else:
            self._wrap_local()
            pass  # for auto-indentation

        # If show_progress is enabled, initialize the progress bar
        if self.show_progress:
            file_size = self._get_file_size()
            if file_size is not None:
                self._progress = tqdm(total=file_size, unit='B', unit_scale=True)
                pass  # for auto-indentation
            pass  # for auto-indentation
        return self

    def _get_file_size(self) -> int:
        """
        Get the size of the file in bytes.

        This method determines the size of the file, whether it is local, on an SFTP server,
        or accessible via HTTP/HTTPS.

        Returns
        -------
        int
            The size of the file in bytes.
        """
        # Check if the file is on an SFTP server
        if self._sftp is not None:
            return self._sftp.stat(self.filename).st_size
        # Check if the HTTP/HTTPS file size is already stored
        if self._http_file_size is not None:
            return self._http_file_size
        # Get the size of a local file
        return os.path.getsize(self.filename)

    def close(self):
        """
        Close the file.

        This method closes the file handle and any associated resources.

        Returns
        -------
        None
        """
        if self._fh is not None:
            self._fh.close()
        if self._sftp is not None:
            self._sftp.close()
        if self._progress is not None:
            self._progress.close()
            pass  # for auto-indentation
        pass  # for auto-indentation

    pass  # for auto-indentation


class PolyWriter:
    """
    A class used to write files line by line, with support for gzip, bz2, and zst compression formats,
    as well as remote files over FTP, SSH, and SFTP.

    Attributes
    ----------
    filename : str
        The name of the file to write to.

    Methods
    -------
    open(append: bool = False, backup: bool = True) -> 'PolyWriter':
        Opens the file for writing, compressing it on the fly if necessary.
    write(data):
        Writes data to the file.
    close():
        Closes the file.
    """

    def __init__(self, filename: str):
        """
        Initialize PolyWriter with a filename.

        Parameters
        ----------
        filename : str
            The name of the file to write to.
        """
        self.filename = filename
        self._fh = None
        self._ftp = None
        self._sftp = None
        pass  # for auto-indentation

    def __enter__(self) -> 'PolyWriter':
        """
        Open the file for writing when entering the context.

        This method is called when the context is entered using the `with` statement.

        Returns
        -------
        PolyWriter
            The PolyWriter instance with the file opened for writing.
        """
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Close the file when exiting the context.

        This method is called when the context is exited using the `with` statement.

        Parameters
        ----------
        exc_type : type
            The exception type.
        exc_value : Exception
            The exception instance.
        traceback : traceback
            The traceback object.

        Returns
        -------
        None
        """
        self.close()
        pass  # for auto-indentation

    def _wrap_ftp(self, parsed: ParseResult, append: bool, backup: bool):
        """
        Wrap self._fh to handle FTP connections and file operations.

        This method establishes an FTP connection using ftputil, opens the specified file for writing,
        and wraps it with appropriate compression handlers based on the file extension.

        Parameters
        ----------
        parsed : ParseResult
            The parsed URL containing the FTP connection details and file path.
        append : bool
            Whether to open the file in append mode.
        backup : bool
            Whether to create a backup of the file if it exists.

        Returns
        -------
        None
        """
        self._ftp = ftputil.FTPHost(parsed.hostname, parsed.username, parsed.password, port=parsed.port,
                                    session_factory=FTPSessionWrapper)
        self.remote_filename = parsed.path

        if backup and self._ftp.path.exists(parsed.path):
            num = 1
            backup_filename = f"{parsed.path}.{num:03d}.bu"
            while self._ftp.path.exists(backup_filename):
                num += 1
                backup_filename = f"{parsed.path}.{num:03d}.bu"
            self._ftp.rename(parsed.path, backup_filename)

        mode = 'ab' if append else 'wb'
        self._fh = self._ftp.open(parsed.path, mode)
        if parsed.path.endswith('.zst'):
            dctx = zstd.ZstdCompressor(level=22)
            self._fh = io.TextIOWrapper(dctx.stream_writer(self._fh), encoding='utf-8')
        elif self.filename.endswith('.bz2'):
            self._fh = bz2.open(self._fh, compresslevel=9, mode='at' if append else 'wt')
        elif self.filename.endswith('.gz'):
            self._fh = gzip.open(self._fh, compresslevel=9, mode='at' if append else 'wt')
        pass  # for auto-indentation

    def _ssh_backup_if(self, sftp, path):
        """
        Backup the specified file on the SSH/SFTP server if it exists.

        This method creates a backup of the file if it exists by renaming it
        with a .bu extension and an incrementing number.

        Parameters
        ----------
        sftp : paramiko.SFTPClient
            The SFTP client instance.
        path : str
            The path of the file to be backed up.

        Returns
        -------
        None
        """
        try:
            sftp.stat(path)
            num = 1
            backup_filename = f"{path}.{num:03d}.bu"
            while True:
                try:
                    sftp.stat(backup_filename)
                    num += 1
                    backup_filename = f"{path}.{num:03d}.bu"
                except FileNotFoundError:
                    break
            sftp.rename(path, backup_filename)
        except FileNotFoundError:
            pass
        pass  # for auto-indentation

    def _wrap_ssh(self, parsed: ParseResult, append: bool, backup: bool):  # noqa: C901
        """
        Wrap self._fh to handle SSH/SFTP connections and file operations.

        This method establishes an SSH connection using paramiko, opens the specified file via SFTP,
        and wraps it with appropriate compression handlers based on the file extension.

        Parameters
        ----------
        parsed : ParseResult
            The parsed URL containing the SSH/SFTP connection details and file path.
        append : bool
            Whether to open the file in append mode.
        backup : bool
            Whether to create a backup of the file if it exists.

        Returns
        -------
        None
        """
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.connect(parsed.hostname, username=parsed.username, password=parsed.password)
        sftp = client.open_sftp()

        if backup:
            self._ssh_backup_if(sftp, parsed.path)

        try:
            self._fh = sftp.file(parsed.path, 'a' if append else 'w')
        except FileNotFoundError as err:
            print(f"ERROR: No such file found: {self.filename}")
            return exit(1), err
        if self.filename.endswith('.zst'):
            dctx = zstd.ZstdCompressor(level=22)
            self._fh = io.TextIOWrapper(dctx.stream_writer(self._fh), encoding='utf-8')
        elif self.filename.endswith('.bz2'):
            self._fh = bz2.open(self._fh, compresslevel=9, mode='at' if append else 'wt')
        elif self.filename.endswith('.gz'):
            self._fh = gzip.open(self._fh, compresslevel=9, mode='at' if append else 'wt')
        self._sftp = sftp
        pass  # for auto-indentation

    def _wrap_local(self, append: bool, backup: bool):
        """
        Wrap self._fh to handle local file operations with optional compression.

        This method opens the specified local file for writing and wraps it with appropriate
        compression handlers based on the file extension. It also handles file appending and backup creation.

        Parameters
        ----------
        append : bool
            Whether to open the file in append mode.
        backup : bool
            Whether to create a backup of the file if it exists.

        Returns
        -------
        None
        """
        if backup and os.path.exists(self.filename):
            num = 1
            backup_filename = f"{self.filename}.{num:03d}.bu"
            while os.path.exists(backup_filename):
                num += 1
                backup_filename = f"{self.filename}.{num:03d}.bu"
            os.rename(self.filename, backup_filename)

        mode = 'ab' if append else 'wb'
        if self.filename.endswith('.zst'):
            cctx = zstd.ZstdCompressor()
            self._fh = io.TextIOWrapper(cctx.stream_writer(open(self.filename, mode)), encoding='utf-8')
        elif self.filename.endswith('.bz2'):
            self._fh = bz2.open(self.filename, 'at' if append else 'wt')
        elif self.filename.endswith('.gz'):
            self._fh = gzip.open(self.filename, 'at' if append else 'wt')
        else:
            self._fh = open(self.filename, 'a' if append else 'w')
        pass  # for auto-indentation

    def open(self, append: bool = False, backup: bool = True) -> 'PolyWriter':
        """
        Open the file for writing, compressing it on the fly if necessary.

        This method determines the file type and source, and opens the file
        with the appropriate handler and compression method.

        Parameters
        ----------
        append : bool, optional
            Whether to open the file in append mode (default is False).
        backup : bool, optional
            Whether to create a backup of the file if it exists (default is True).

        Returns
        -------
        PolyWriter
            The PolyWriter instance with the file opened for writing.

        Raises
        ------
        ValueError
            If both append and backup are True.
        """
        if append and backup:
            raise ValueError("Cannot have both append and backup set to True.")

        parsed = urlparse(self.filename)

        if parsed.scheme == 'ftp':
            self._wrap_ftp(parsed, append, backup)
        elif parsed.scheme in ('sftp', 'ssh'):
            self._wrap_ssh(parsed, append, backup)
        else:
            self._wrap_local(append, backup)

        return self

    def write(self, data):
        """
        Write data to the file.

        Parameters
        ----------
        data : str
            The data to write to the file.

        Returns
        -------
        None
        """
        self._fh.write(data)
        pass  # for auto-indentation

    def close(self):
        """
        Close the file.

        This method closes the file handle and any associated resources.

        Returns
        -------
        None
        """
        if self._fh is not None:
            self._fh.close()
            if self._ftp is not None:
                self._ftp.close()
            if self._sftp is not None:
                self._sftp.close()
            pass  # for auto-indentation
        pass  # for auto-indentation

    pass  # for auto-indentation


def main():
    """
    Main function, mostly for testing.

    This function serves as the entry point for the script, providing functionality to read from and write to files.
    It supports various compression formats (plain text, gzipped, bzip2, zstandard) and remote sources (HTTP, HTTPS, FTP, SSH, SFTP).
    """
    import time
    from general.constants import CommonFormattingBase

    fmt = CommonFormattingBase()

    def pinfo(preface: str, filename: str, line_count: int, bytes_count: int, seconds: float, fmt: 'CommonFormattingBase'):
        """
        Print information about the file processing.

        Parameters
        ----------
        preface : str
            A preface string for the output message.
        filename : str
            The name of the file being processed.
        line_count : int
            The number of lines processed.
        bytes_count : int
            The number of bytes processed.
        seconds : float
            The total time taken for processing.
        fmt : CommonFormattingBase
            An instance of CommonFormattingBase for formatting the output.
        """
        rate = line_count / seconds
        print(
            f"{preface} {filename}. "
            f"{line_count:,d} lines / {fmt.pbytes(bytes_count)} "
            f"at {fmt.prate(rate)} ({fmt.pbyterate(bytes_count/seconds)}). "
            f"Total time: {fmt.psecs(seconds)})."
        )
        pass  # for auto-indentation

    # Set up argument parser for command-line interface
    parser = argparse.ArgumentParser(description='Test reading of plain text, gzipped, bzip2, or zstandard compressed files locally and remotely.')

    # Add argument for input files to process
    parser.add_argument('files', type=str, nargs='*', default=[], help='The input file(s) to process', metavar="file")

    # Add mutually exclusive group for read/write modes
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--write', '-w', action='store_true', help='Write mode')
    group.add_argument('--read', '-r', action='store_true', help='Read mode')

    # Add argument for specifying input file when in read mode
    parser.add_argument('--input-file', '-i', type=str, help='File to read when testing read mode.')

    # Parse the command-line arguments
    args = parser.parse_args()

    # Validate that input-file is provided when in read mode
    if args.write and not args.input_file:
        parser.error("--input-file/-i is required with --read")
        exit(1)
        pass  # for auto-indentation

    # If read mode is specified
    if args.read:
        for input_file in args.files:
            print(f"TESTING reading {input_file}")
            with PolyReader(input_file) as reader:
                line_count = 0
                t0 = time.monotonic()
                bytes_count = 0
                for line in reader:
                    line_count += 1
                    bytes_count += len(line)
                    pass  # for auto-indentation
                # Print final reading statistics
                pinfo("FINISHED Reading.", reader.filename, line_count, bytes_count, time.monotonic() - t0, fmt)
                pass  # for auto-indentation
            pass  # for auto-indentation
        pass  # for auto-indentation
    else:
        # If write mode is specified
        print(f"Will Read from {args.input_file}")
        for output_file in args.files:
            with PolyReader(args.input_file) as reader:
                with PolyWriter(output_file) as writer:
                    print(f"Writing {writer.filename}")
                    line_count = 0
                    t0 = time.monotonic()
                    bytes_count = 0
                    for line in reader:
                        line_count += 1
                        bytes_count += len(line)
                        writer.write(line)
                        pass  # for auto-indentation
                    # Print final writing statistics
                    pinfo("FINISHED Writing.", writer.filename, line_count, bytes_count, time.monotonic() - t0, fmt)
                    pass  # for auto-indentation
                pass  # for auto-indentation
            pass  # for auto-indentation
        pass  # for auto-indentation
    pass  # for auto-indentation


if __name__ == "__main__":
    main()
