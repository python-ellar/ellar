import typing as t

from .base import set_metadata
from .command import command
from .controller import Controller
from .exception import exception_handler
from .extra_args import extra_args
from .file import file
from .guards import guards
from .html import render, template_filter, template_global
from .middleware import middleware
from .modules import Module
from .openapi import openapi_info
from .request import on_shutdown, on_startup
from .serializer import serializer_filter
from .versioning import version

__all__ = [
    "serializer_filter",
    "Controller",
    "version",
    "guards",
    "template_filter",
    "template_global",
    "file",
    "render",
    "on_startup",
    "exception_handler",
    "on_shutdown",
    "command",
    "set_metadata",
    "middleware",
    "openapi_info",
    "Module",
    "extra_args",
]


def __dir__() -> t.List[str]:
    return sorted(__all__)  # pragma: no cover
