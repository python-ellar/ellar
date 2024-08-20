import typing as t

from .base import set_metadata
from .controller import Controller
from .exception import exception_handler
from .extra_args import extra_args
from .file import file
from .guards import UseGuards
from .html import render, template_context, template_filter, template_global
from .interceptor import UseInterceptors
from .middleware import middleware
from .modules import Module
from .serializer import serializer_filter
from .versioning import Version

__all__ = [
    "serializer_filter",
    "Controller",
    "Version",
    "UseGuards",
    "template_filter",
    "template_global",
    "template_context",
    "file",
    "render",
    "exception_handler",
    "set_metadata",
    "middleware",
    "Module",
    "extra_args",
    "UseInterceptors",
]


def __dir__() -> t.List[str]:
    return sorted(__all__)  # pragma: no cover
