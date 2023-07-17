import typing as t
from abc import ABC, abstractmethod

from .cookie_dict import SessionCookieObject
from .options import SessionCookieOption


class ISessionStrategy(ABC):
    @property
    @abstractmethod
    def session_cookie_options(self) -> SessionCookieOption:
        """
        :return: SessionCookieOption
        """

    @abstractmethod
    def serialize_session(
        self,
        session: t.Union[str, SessionCookieObject],
    ) -> str:
        """
        :param response_headers:
        :param session: Collection ExtraEndpointArg
        :return: None
        """

    @abstractmethod
    def deserialize_session(self, session_data: t.Optional[str]) -> SessionCookieObject:
        """
        :param session_data:
        :return: SessionCookieObject
        """
