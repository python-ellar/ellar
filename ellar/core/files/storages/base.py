import os
import pathlib
from abc import ABC

from .exceptions import UnsafeFileOperation
from .interface import Storage
from .utils import get_valid_filename, validate_file_name


class BaseStorage(ABC, Storage):
    DEFAULT_CHUNK_SIZE = 64 * 2**10

    def validate_file_name(self, filename: str) -> None:
        """
        Return an alternative filename, by adding an underscore and a random 7-character alphanumeric string
        (before the file extension, if one exists) to the filename.
        """
        validate_file_name(name=filename)

    def generate_filename(self, filename: str) -> str:
        """
        Validate the filename by calling get_valid_name() and return a filename
        to be passed to the save() method.
        """
        filename = str(filename).replace("\\", "/")
        # `filename` may include a path as returned by FileField.upload_to.
        dirname, filename = os.path.split(filename)
        if ".." in pathlib.PurePath(dirname).parts:
            raise UnsafeFileOperation(
                "Detected path traversal attempt in '%s'" % dirname
            )
        return os.path.normpath(os.path.join(dirname, get_valid_filename(filename)))
