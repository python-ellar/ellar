import os
import re
import typing

from .exceptions import UnsafeFileOperation


def copy_stream(
    source: typing.IO, target: typing.IO, *, chunk_size: int = 16 * 1024
) -> int:
    length = 0
    while 1:
        buf = source.read(chunk_size)
        if not buf:
            break
        length += len(buf)
        target.write(buf)
    return length


def get_valid_filename(name: str) -> str:
    """
    Return the given string converted to a string that can be used for a clean
    filename. Remove leading and trailing spaces; convert other spaces to
    underscores; and remove anything that is not an alphanumeric, dash,
    underscore, or dot.
    >>> get_valid_filename("john's portrait in 2004.jpg")
    'johns_portrait_in_2004.jpg'
    """
    s = str(name).strip().replace(" ", "_")
    s = re.sub(r"(?u)[^-\w.]", "", s)
    if s in {"", ".", ".."}:
        raise UnsafeFileOperation("Could not derive file name from '%s'" % name)
    return s


def validate_file_name(name: str) -> str:
    # Remove potentially dangerous names
    if os.path.basename(name) in {"", ".", ".."}:
        raise UnsafeFileOperation("Could not derive file name from '%s'" % name)

    if name != os.path.basename(name):
        raise UnsafeFileOperation("File name '%s' includes path elements" % name)

    return name
