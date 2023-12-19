import typing as t
from io import BytesIO, StringIO

from ellar.pydantic import as_pydantic_validator
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
from typing_extensions import Annotated, Doc

__all__ = [
    "URL",
    "Address",
    "FormData",
    "Headers",
    "QueryParams",
    "UploadFile",
    "URLPath",
    "State",
    "ContentFile",
]


@as_pydantic_validator(
    "__validate_input__", schema={"type": "string", "format": "binary"}
)
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
    def __validate_input__(cls, __input_value: t.Any, _: t.Any) -> "UploadFile":
        if not isinstance(__input_value, StarletteUploadFile):
            raise ValueError(f"Expected UploadFile, received: {type(__input_value)}")
        return cls(
            __input_value.file,
            size=__input_value.size,
            filename=__input_value.filename,
            headers=__input_value.headers,
        )


class ContentFile(UploadFile):
    """
    A File-like object that takes just raw content, rather than an actual file.
    """

    def __init__(
        self, content: t.Union[str, bytes], name: t.Optional[str] = None
    ) -> None:
        stream_class = StringIO if isinstance(content, str) else BytesIO
        headers = Headers({"content-type": "text/plain"})
        super().__init__(
            stream_class(content), filename=name, size=len(content), headers=headers
        )
