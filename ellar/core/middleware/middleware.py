import inspect
import typing as t

from ellar.common.interfaces import IEllarMiddleware
from ellar.common.types import ASGIApp
from ellar.core.execution_context import current_injector
from ellar.utils.importer import import_from_string
from injector import _infer_injected_bindings
from starlette.middleware import Middleware

T = t.TypeVar("T")


class EllarMiddleware(Middleware, IEllarMiddleware):
    @t.no_type_check
    def __init__(
        self,
        cls_or_import_string: t.Union[t.Type[T], str],
        **options: t.Any,
    ) -> None:
        super().__init__(cls_or_import_string, **options)

    def _ensure_class(self) -> None:
        if isinstance(self.cls, str):
            self.cls = import_from_string(self.cls)

    def __iter__(self) -> t.Iterator[t.Any]:
        self._ensure_class()
        as_tuple = (self, self.args, self.kwargs)
        return iter(as_tuple)

    def create_object(self, **init_kwargs: t.Any) -> t.Any:
        _result = dict(init_kwargs)

        init_method = getattr(self.cls, "__init__", None)
        if init_method is not None:
            spec = inspect.signature(init_method)
            type_hints = _infer_injected_bindings(
                init_method, only_explicit_bindings=False
            )

            for k, annotation in type_hints.items():
                parameter = spec.parameters.get(k)
                if k in _result or (parameter and parameter.default is None):
                    continue

                _result[k] = current_injector.get(annotation)

        return self.cls(**_result)  # type: ignore[call-arg]

    @t.no_type_check
    def __call__(self, app: ASGIApp, *args: t.Any, **kwargs: t.Any) -> T:
        self._ensure_class()
        # kwargs.update(app=app)
        try:
            return self.create_object(**kwargs, app=app)
        except TypeError:  # pragma: no cover
            # TODO: Fix future typing for lower python version.
            return self.cls(*args, **kwargs, app=app)
