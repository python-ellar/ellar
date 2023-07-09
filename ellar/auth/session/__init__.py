import typing as t

from starlette.datastructures import MutableHeaders

from .cookie_dict import SessionCookieObject
from .interface import ISessionService
from .options import SessionCookieOption

__all__ = [
    "SessionCookieObject",
    "SessionCookieOption",
    "ISessionService",
    "SessionServiceBasicStrategy",
]


class SessionServiceBasicStrategy(ISessionService):
    @property
    def session_cookie_options(self) -> SessionCookieOption:
        return SessionCookieOption()

    def load_session(self, session_data: t.Optional[str]) -> SessionCookieObject:
        return SessionCookieObject()

    def save_session(
        self,
        response_headers: MutableHeaders,
        session: t.Union[str, SessionCookieObject],
    ) -> None:
        pass
