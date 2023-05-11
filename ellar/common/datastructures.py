import typing as t

from starlette.datastructures import (
    URL as URL,
    Address as Address,
    FormData as FormData,
    Headers as Headers,
    QueryParams as QueryParams,
    State as State,
    UploadFile as StarletteUploadFile,
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
