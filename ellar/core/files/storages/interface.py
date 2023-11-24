import typing as t
from abc import abstractmethod


class Storage:
    """The abstract base class for all stores."""

    @abstractmethod
    def service_name(self) -> str:
        pass

    @abstractmethod
    def put(self, filename: str, stream: t.IO) -> int:
        """
        Puts the file object as the given filename in the store.

        :param filename: target filename.
        :param stream: source file-like object
        :return: length of the stored file.
        """

    @abstractmethod
    def delete(self, filename: str) -> None:
        """
        deletes a given file.

        :param filename: The filename to delete
        """

    @abstractmethod
    def open(self, filename: str, mode: str = "rb") -> t.IO:
        """
        Return a file object representing the file in the store.
        :param filename: The filename to open.
        :param mode: same as the `mode` in famous :func:`.open` function.
        """

    @abstractmethod
    def locate(self, filename: str) -> str:
        """
        Returns a shareable public link to the filename.

        :param filename: The filename to locate.
        """
