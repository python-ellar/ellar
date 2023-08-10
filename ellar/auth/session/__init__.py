import typing as t

from .cookie_dict import SessionCookieObject
from .interface import ISessionStrategy
from .options import SessionCookieOption

__all__ = [
    "SessionCookieObject",
    "SessionCookieOption",
    "ISessionStrategy",
    "SessionServiceNullStrategy",
]


class SessionServiceNullStrategy(ISessionStrategy):
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
