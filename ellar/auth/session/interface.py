import typing as t
from abc import ABC, abstractmethod

from starlette.datastructures import MutableHeaders

from .cookie_dict import SessionCookieObject
from .options import SessionCookieOption


class ISessionService(ABC):
    @property
    @abstractmethod
    def session_cookie_options(self) -> SessionCookieOption:
        """
        :return: SessionCookieOption
        """

    @abstractmethod
    def save_session(
        self,
        response_headers: MutableHeaders,
        session: t.Union[str, SessionCookieObject],
    ) -> None:
        """
        :param response_headers:
        :param session: Collection ExtraEndpointArg
        :return: None
        """

    @abstractmethod
    def load_session(self, session_data: t.Optional[str]) -> SessionCookieObject:
        """
        :param session_data:
        :return: SessionCookieObject
        """
