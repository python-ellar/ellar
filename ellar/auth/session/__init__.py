import typing as t

from .cookie_dict import SessionCookieObject
from .interface import ISessionService
from .options import SessionCookieOption

__all__ = [
    "SessionCookieObject",
    "SessionCookieOption",
    "ISessionService",
    "SessionServiceNullStrategy",
]


class SessionServiceNullStrategy(ISessionService):
    @property
    def session_cookie_options(self) -> SessionCookieOption:
        return SessionCookieOption()

    def deserialize_session(self, session_data: t.Optional[str]) -> SessionCookieObject:
        return SessionCookieObject()

    def serialize_session(
        self,
        session: t.Union[str, SessionCookieObject],
    ) -> str:
        return ""
