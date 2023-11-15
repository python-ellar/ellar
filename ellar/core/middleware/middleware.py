import typing as t

from ellar.common.interfaces import IEllarMiddleware
from ellar.common.types import ASGIApp
from ellar.common.utils import build_init_kwargs
from ellar.di import EllarInjector, injectable
from starlette.middleware import Middleware

T = t.TypeVar("T")


class EllarMiddleware(Middleware, IEllarMiddleware):
    def __init__(self, cls: t.Type[T], **options: t.Any) -> None:
        super().__init__(cls, **options)
        injectable()(self.cls)
        self.options = build_init_kwargs(self.cls, self.options)

    def __call__(
        self, app: ASGIApp, injector: EllarInjector
    ) -> T:  # type:ignore[type-var]
        self.options.update(app=app)
        return injector.create_object(self.cls, additional_kwargs=self.options)
