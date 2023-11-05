import typing as t

from injector import NoScope as TransientScope
from injector import SingletonScope

from .asgi_args import RequestScopeContext
from .constants import (
    INJECTABLE_ATTRIBUTE,
    MODULE_REF_TYPES,
    SCOPED_CONTEXT_VAR,
    AnnotationToValue,
)
from .injector import Container, EllarInjector
from .scopes import (
    RequestORTransientScope,
    RequestScope,
    request_or_transient_scope,
    request_scope,
    singleton_scope,
    transient_scope,
)
from .service_config import (
    ProviderConfig,
    get_scope,
    has_binding,
    injectable,
    is_decorated_with_injectable,
)

__all__ = [
    "Container",
    "EllarInjector",
    "RequestScope",
    "RequestORTransientScope",
    "request_or_transient_scope",
    "SingletonScope",
    "TransientScope",
    "request_scope",
    "singleton_scope",
    "transient_scope",
    "ProviderConfig",
    "injectable",
    "is_decorated_with_injectable",
    "has_binding",
    "get_scope",
    "RequestScopeContext",
    "SCOPED_CONTEXT_VAR",
    "INJECTABLE_ATTRIBUTE",
    "AnnotationToValue",
    "MODULE_REF_TYPES",
]


def __dir__() -> t.List[str]:
    return sorted(__all__)  # pragma: no cover
