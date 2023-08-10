import typing as t

from starlette.types import (
    ASGIApp as ASGIApp,
)
from starlette.types import (
    Message as TMessage,
)
from starlette.types import (
    Receive as TReceive,
)
from starlette.types import (
    Scope as TScope,
)
from starlette.types import (
    Send as TSend,
)

__all__ = [
    "TScope",
    "TMessage",
    "TReceive",
    "TSend",
    "ASGIApp",
    "TemplateFilterCallable",
    "TemplateGlobalCallable",
    "T",
    "KT",
    "VT",
    "TCallable",
]

TemplateFilterCallable = t.Callable[..., t.Any]
TemplateGlobalCallable = t.Callable[..., t.Any]
T = t.TypeVar("T")
KT = t.TypeVar("KT")
VT = t.TypeVar("VT")

TCallable = t.TypeVar("TCallable", bound=t.Callable[..., t.Any])
