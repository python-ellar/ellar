import typing as t

from ellar.common.interfaces import IEllarMiddleware
from ellar.common.types import ASGIApp
from ellar.core.context import current_injector
from ellar.di import injectable
from ellar.utils import build_init_kwargs
from starlette.middleware import Middleware

T = t.TypeVar("T")


class EllarMiddleware(Middleware, IEllarMiddleware):
    _provider_token: t.Optional[str]

    @t.no_type_check
    def __init__(
        self,
        cls: t.Type[T],
        provider_token: t.Optional[str] = None,
        **options: t.Any,
    ) -> None:
        super().__init__(cls, **options)
        injectable()(self.cls)
        self.kwargs = build_init_kwargs(self.cls, self.kwargs)
        self._provider_token = provider_token

    def _register_middleware(self) -> None:
        provider_token = self._provider_token
        if provider_token:
            module_data = next(
                current_injector.tree_manager.find_module(
                    lambda data: data.name == provider_token
                )
            )

            if module_data and module_data.is_ready:
                module_data.value.add_provider(self.cls, export=True)
                return

        current_injector.tree_manager.get_root_module().add_provider(
            self.cls, export=True
        )

    def __iter__(self) -> t.Iterator[t.Any]:
        as_tuple = (self, self.args, self.kwargs)
        return iter(as_tuple)

    @t.no_type_check
    def __call__(self, app: ASGIApp, *args: t.Any, **kwargs: t.Any) -> T:
        self._register_middleware()
        kwargs.update(app=app)
        try:
            return current_injector.create_object(self.cls, additional_kwargs=kwargs)
        except TypeError:  # pragma: no cover
            # TODO: Fix future typing for lower python version.
            return self.cls(*args, **kwargs)
