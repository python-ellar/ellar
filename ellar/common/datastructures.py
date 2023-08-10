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
    @classmethod
    def __get_validators__(
        cls: t.Type["UploadFile"],
    ) -> t.Iterable[t.Callable[..., t.Any]]:
        yield cls.validate

    @classmethod
    def validate(cls: t.Type["UploadFile"], v: t.Any) -> t.Any:
        if not isinstance(v, StarletteUploadFile):
            raise ValueError(f"Expected UploadFile, received: {type(v)}")
        return v
