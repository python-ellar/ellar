import typing as t

from ellar.common.interfaces import IEllarMiddleware
from ellar.common.types import ASGIApp
from ellar.core.context import current_injector
from ellar.di import EllarInjector, injectable
from ellar.utils import build_init_kwargs
from starlette.middleware import Middleware

T = t.TypeVar("T")


class EllarMiddleware(Middleware, IEllarMiddleware):
    @t.no_type_check
    def __init__(self, cls: t.Type[T], **options: t.Any) -> None:
        super().__init__(cls, **options)
        injectable()(self.cls)
        self.kwargs = build_init_kwargs(self.cls, self.kwargs)

    def __iter__(self) -> t.Iterator[t.Any]:
        as_tuple = (self, self.args, self.kwargs)
        return iter(as_tuple)

    @t.no_type_check
    def __call__(self, app: ASGIApp, *args: t.Any, **kwargs: t.Any) -> T:
        kwargs.update(app=app)
        if "ellar_injector" in kwargs:
            injector: EllarInjector = kwargs.pop("ellar_injector")
        else:
            injector = current_injector
        try:
            return injector.create_object(self.cls, additional_kwargs=kwargs)
        except TypeError:  # pragma: no cover
            # TODO: Fix future typing for lower python version.
            return self.cls(*args, **kwargs)
