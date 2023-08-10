import typing as t

from ellar.common import Identity, IHostContext

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core import HTTPConnection


class BaseAuthenticationHandlerMixin:
    scheme: str = "apiKey"
    run_authentication_check: t.Callable[..., t.Coroutine]

    @t.no_type_check
    async def authenticate(self, context: IHostContext) -> t.Optional[Identity]:
        return await self.run_authentication_check(context)

    def handle_authentication_result(
        self, connection: "HTTPConnection", result: t.Optional[t.Any]
    ) -> t.Any:
        if result:
            return result
        return None

    def handle_invalid_request(self) -> t.Any:
        return None
