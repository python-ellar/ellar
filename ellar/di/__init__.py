import typing as t

from injector import NoScope as TransientScope
from injector import SingletonScope

from .asgi_args import RequestScopeContext
from .constants import (
    INJECTABLE_ATTRIBUTE,
    MODULE_REF_TYPES,
    AnnotationToValue,
    request_context_var,
)
from .injector import (
    Container,
    EllarInjector,
    ModuleTreeManager,
    register_request_scope_context,
)
from .scopes import (
    RequestORTransientScope,
    RequestScope,
    request_or_transient_scope,
    request_scope,
    singleton_scope,
    transient_scope,
)
from .service_config import (
    InjectByTag,
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
    "request_context_var",
    "INJECTABLE_ATTRIBUTE",
    "AnnotationToValue",
    "MODULE_REF_TYPES",
    "InjectByTag",
    "ModuleTreeManager",
    "register_request_scope_context",
]


def __dir__() -> t.List[str]:
    return sorted(__all__)  # pragma: no cover
