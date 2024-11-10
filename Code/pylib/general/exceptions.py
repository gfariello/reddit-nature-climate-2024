"""A module the contains exceptions."""

__all__ = ['NoUniquePathException', 'NoUniqueDirectoryException', 'NoUniqueFileException']


class NoUniquePathException(Exception):
    """Simple `Exception` for when we can't find a unique path (directory)."""

    pass


class NoUniqueDirectoryException(NoUniquePathException):
    """Simple `Exception` for when we can't find a unique directory name."""

    pass


class NoUniqueFileException(NoUniquePathException):
    """Simple `Exception` for when we can't find a unique filename."""

    pass

# End
