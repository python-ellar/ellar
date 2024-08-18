import typing as t
from types import TracebackType

from ellar.common import IHostContext
from ellar.common.logging import logger
from ellar.di import (
    RequestScopeContext,
    register_request_scope_context,
    request_context_var,
)
from ellar.events import request_started, request_teardown
from ellar.utils.functional import SimpleLazyObject, empty


def _clear_lazy_objects() -> None:
    current_connection._wrapped = empty  # type:ignore[attr-defined]


class HttpRequestConnectionContext(RequestScopeContext):
    def __init__(self, host_context: IHostContext) -> None:
        super().__init__()
        self._reset_token: t.Optional[t.Any] = None
        self.host_context = host_context

    async def __aenter__(self) -> "HttpRequestConnectionContext":
        self._reset_token = request_context_var.set(self)

        register_request_scope_context(IHostContext, self.host_context)

        _clear_lazy_objects()

        await request_started.run(context=self.host_context)
        return self

    @t.no_type_check
    async def __aexit__(
        self,
        exc_type: t.Optional[t.Any],
        exc_value: t.Optional[BaseException],
        tb: t.Optional[TracebackType],
    ) -> None:
        try:
            request_context_var.reset(self._reset_token)
            await request_teardown.run(context=self.host_context)
        except ValueError as vex:
            logger.exception(vex)
        finally:
            _clear_lazy_objects()


def _get_connection() -> IHostContext:
    request_context: t.Union[HttpRequestConnectionContext, t.Any] = (
        request_context_var.get(empty)
    )
    if request_context is empty:
        raise RuntimeError("HTTPHostContext is only available during request.")

    return request_context.host_context


current_connection: IHostContext = t.cast(
    IHostContext, SimpleLazyObject(func=_get_connection)
)
