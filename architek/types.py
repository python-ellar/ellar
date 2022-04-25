import typing as t

from starlette.types import (
    ASGIApp as ASGIApp,
    Message as TMessage,
    Receive as TReceive,
    Scope as TScope,
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
