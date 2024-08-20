import contextvars
from typing import List, Optional, no_type_check

from .asgi_args import RequestScopeContext

INJECTABLE_ATTRIBUTE = "__DI_SCOPE__"


request_context_var: contextvars.ContextVar[Optional[RequestScopeContext]] = (
    contextvars.ContextVar("ellar.di.request_context_var")
)
request_context_var.set(None)
INJECTABLE_WATERMARK = "INJECTABLE_WATERMARK"


class Tag(str):
    """Tag Placeholder Type"""


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
            if type(v) is type(str):
                value = str(k).lower()
                setattr(cls, k, value)
                cls.keys.append(value)
        return cls


class MODULE_REF_TYPES(metaclass=AnnotationToValue):
    PLAIN: str
    TEMPLATE: str
    DYNAMIC: str
    FORWARD_REF: str
    APP_DEPENDENT: str
