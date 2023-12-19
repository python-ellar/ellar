import os
import typing as t

from .base import BaseStorage
from .utils import copy_stream


class FileSystemStorage(BaseStorage):
    def service_name(self) -> str:
        return "local"

    def __init__(
        self, location: str, chunk_size: int = BaseStorage.DEFAULT_CHUNK_SIZE
    ) -> None:
        self.root_path = os.path.abspath(location)
        self.chunk_size = chunk_size

    def _get_physical_path(self, filename: str) -> str:
        name = os.path.join(self.root_path, filename)
        self.validate_file_name(filename)
        return self.generate_filename(name)

    def put(self, filename: str, stream: t.IO) -> int:
        physical_path = self._get_physical_path(filename)
        physical_directory = os.path.dirname(physical_path)

        if not os.path.exists(physical_directory):
            os.makedirs(physical_directory, exist_ok=True)

        stream.seek(0)

        with open(physical_path, mode="wb") as target_file:
            return copy_stream(stream, target_file, chunk_size=self.chunk_size)

    def delete(self, filename: str) -> None:
        physical_path = self._get_physical_path(filename)
        os.remove(physical_path)

    def open(self, filename: str, mode: str = "rb") -> t.IO:
        return open(self._get_physical_path(filename), mode=mode)

    def locate(self, filename: str) -> str:
        return f"{self.root_path}/{filename}"
