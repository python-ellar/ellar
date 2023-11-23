import typing as t

from starlette.datastructures import (
    URL as URL,
)
from starlette.datastructures import (
    Address as Address,
)
from starlette.datastructures import (
    FormData as FormData,
)
from starlette.datastructures import (
    Headers as Headers,
)
from starlette.datastructures import (
    QueryParams as QueryParams,
)
from starlette.datastructures import (
    State as State,
)
from starlette.datastructures import (
    UploadFile as StarletteUploadFile,
)
from starlette.datastructures import (
    URLPath,
)
from typing_extensions import Annotated, Doc  # type: ignore[attr-defined]

__all__ = [
    "URL",
    "Address",
    "FormData",
    "Headers",
    "QueryParams",
    "UploadFile",
    "URLPath",
    "State",
]


class UploadFile(StarletteUploadFile):
    """
    A file uploaded in a request.

    Define it as a *path operation function* (or dependency) parameter.

    ## Example

    ```python

    from ellar.common import ModuleRouter, File, UploadFile

    router = ModuleRouter()


    @router.post("/files/")
    async def create_file(file: File[bytes]):
        return {"file_size": len(file)}


    @router.post("/uploadfile/")
    async def create_upload_file(file: UploadFile):
        return {"filename": file.filename}
    ```
    """

    file: Annotated[
        t.BinaryIO,
        Doc("The standard Python file object (non-async)."),
    ]
    filename: Annotated[t.Optional[str], Doc("The original file name.")]
    size: Annotated[t.Optional[int], Doc("The size of the file in bytes.")]
    headers: Annotated[Headers, Doc("The headers of the request.")]
    content_type: Annotated[
        t.Optional[str], Doc("The content type of the request, from the headers.")
    ]

    @classmethod
    def __modify_schema__(cls, field_schema: t.Dict[str, t.Any]) -> None:
        field_schema.update({"type": "string", "format": "binary"})

    @classmethod
    def __get_validators__(
        cls: t.Type["UploadFile"],
    ) -> t.Iterable[t.Callable[..., t.Any]]:
        yield cls.validate

    @classmethod
    def validate(cls: t.Type["UploadFile"], v: t.Any) -> t.Any:
        if not isinstance(v, StarletteUploadFile):
            raise ValueError(f"Expected UploadFile, received: {type(v)}")
        return cls(v.file, size=v.size, filename=v.filename, headers=v.headers)
