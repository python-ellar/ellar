import typing as t

from ellar.common.interfaces import IEllarMiddleware
from ellar.common.types import ASGIApp
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

    @t.no_type_check
    def __call__(self, app: ASGIApp, injector: EllarInjector) -> T:
        self.kwargs.update(app=app)
        return injector.create_object(self.cls, additional_kwargs=self.kwargs)
