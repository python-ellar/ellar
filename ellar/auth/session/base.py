import typing as t
from abc import ABC, abstractmethod

from .cookie_dict import SessionCookieObject
from .options import SessionCookieOption


class SessionStrategy(ABC):
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
        :param session: Collection ExtraEndpointArg
        :return: string
        """

    @abstractmethod
    def deserialize_session(self, session_data: t.Optional[str]) -> SessionCookieObject:
        """
        :param session_data:
        :return: SessionCookieObject
        """

    def get_cookie_header_value(self, data: t.Any, delete: bool = False) -> str:
        security_flags = "httponly; samesite=" + self.session_cookie_options.SAME_SITE
        if self.session_cookie_options.SECURE:
            security_flags += "; secure"

        if not delete:
            max_age = (
                f"Max-Age={self.session_cookie_options.MAX_AGE}; "
                if self.session_cookie_options.MAX_AGE
                else ""
            )
        else:
            max_age = "Max-Age=0; "

        header_value = "{session_cookie}={data}; path={path}; {max_age}{security_flags}".format(  # E501
            session_cookie=self.session_cookie_options.NAME,
            data=data,
            path=self.session_cookie_options.PATH,
            max_age=max_age,
            security_flags=security_flags,
        )
        return header_value
