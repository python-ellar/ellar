import typing as t

from .conf import Config, ConfigDefaultTypesMixin
from .connection import HTTPConnection, Request, WebSocket
from .execution_context import (
    ExecutionContext,
    HostContext,
    HttpRequestConnectionContext,
    current_config,
    current_connection,
    current_injector,
    injector_context,
)
from .guards import GuardConsumer
from .interceptors import EllarInterceptorConsumer
from .modules import (
    DynamicModule,
    ForwardRefModule,
    LazyModuleImport,
    ModuleBase,
    ModuleSetup,
)
from .services import Reflector, reflector
from .shortcuts import host, mount
from .templating import TemplateRenderingService
from .versioning import VersioningSchemes

__all__ = [
    "HTTPConnection",
    "ExecutionContext",
    "HostContext",
    "ConfigDefaultTypesMixin",
    "EllarInterceptorConsumer",
    "ModuleBase",
    "Config",
    "Request",
    "WebSocket",
    "ModuleSetup",
    "DynamicModule",
    "Reflector",
    "reflector",
    "GuardConsumer",
    "LazyModuleImport",
    "VersioningSchemes",
    "mount",
    "host",
    "current_injector",
    "current_config",
    "ForwardRefModule",
    "TemplateRenderingService",
    "HttpRequestConnectionContext",
    "current_connection",
    "injector_context",
]


def __dir__() -> t.List[str]:
    return sorted(__all__)  # pragma: no cover
