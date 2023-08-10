import contextvars
from typing import List, Optional, no_type_check

from .asgi_args import RequestScopeContext

INJECTABLE_ATTRIBUTE = "__DI_SCOPE__"


SCOPED_CONTEXT_VAR: contextvars.ContextVar[
    Optional[RequestScopeContext]
] = contextvars.ContextVar("SCOPED-CONTEXT-VAR")
SCOPED_CONTEXT_VAR.set(None)


class AnnotationToValue(type):
    keys: List[str]

    @no_type_check
    def __new__(mcls, name, bases, namespace):
        cls = super().__new__(mcls, name, bases, namespace)
        annotations = {}
        for base in reversed(bases):  # pragma: no cover
            annotations.update(getattr(base, "__annotations__", {}))
        annotations.update(namespace.get("__annotations__", {}))
        cls.keys = []
        for k, v in annotations.items():
            if type(v) == type(str):
                value = str(k).lower()
                setattr(cls, k, value)
                cls.keys.append(value)
        return cls


class MODULE_REF_TYPES(metaclass=AnnotationToValue):
    PLAIN: str
    TEMPLATE: str
    DYNAMIC: str
    APP_DEPENDENT: str
