import typing as t

from .base import SessionStrategy
from .cookie_dict import SessionCookieObject
from .options import SessionCookieOption

__all__ = [
    "SessionCookieObject",
    "SessionCookieOption",
    "SessionStrategy",
    "SessionServiceNullStrategy",
]


class SessionServiceNullStrategy(SessionStrategy):
    """
    A Null implementation ISessionService. This is used as a placeholder for ISSessionService when there is no
    ISSessionService implementation registered.
    """

    @property
    def session_cookie_options(self) -> SessionCookieOption:  # pragma: no cover
        return SessionCookieOption()

    def deserialize_session(
        self, session_data: t.Optional[str]
    ) -> SessionCookieObject:  # pragma: no cover
        return SessionCookieObject()

    def serialize_session(
        self,
        session: t.Union[str, SessionCookieObject],
    ) -> str:  # pragma: no cover
        return ""
