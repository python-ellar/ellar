from ellar.auth.session import ISessionStrategy, SessionServiceNullStrategy
from ellar.core.conf import Config
from starlette.datastructures import MutableHeaders
from starlette.requests import HTTPConnection
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class SessionMiddleware:
    def __init__(
        self, app: ASGIApp, session_strategy: ISessionStrategy, config: Config
    ) -> None:
        config.setdefault("SESSION_DISABLED", False)
        self.app = app
        self._session_strategy = session_strategy
        self._is_active = not isinstance(session_strategy, SessionServiceNullStrategy)
        self._is_disabled = config.SESSION_DISABLED

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (
            scope["type"] not in ("http", "websocket")
            or not self._is_active
            or self._is_disabled
        ):  # pragma: no cover
            await self.app(scope, receive, send)
            return

        connection = HTTPConnection(scope)
        session_service_config = self._session_strategy.session_cookie_options

        if session_service_config.NAME in connection.cookies:
            data = connection.cookies[session_service_config.NAME]
            scope["session"] = self._session_strategy.deserialize_session(data)
        else:
            scope["session"] = self._session_strategy.deserialize_session(None)

        async def _send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                if scope["session"]:
                    # We have session data to persist.
                    headers = MutableHeaders(scope=message)
                    headers.append(
                        "Set-Cookie",
                        self._session_strategy.serialize_session(scope["session"]),
                    )
                else:
                    # The session has been cleared.
                    headers = MutableHeaders(scope=message)
                    headers.append(
                        "Set-Cookie", self._session_strategy.serialize_session("null")
                    )

            await send(message)

        await self.app(scope, receive, _send_wrapper)
