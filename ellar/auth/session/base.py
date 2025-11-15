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
        config: t.Optional[SessionCookieOption] = None,
    ) -> str:
        """
        :param session: Collection ExtraEndpointArg
        :param config: SessionCookieOption
        :return: string
        """

    @abstractmethod
    def deserialize_session(
        self,
        session_data: t.Optional[str],
        config: t.Optional[SessionCookieOption] = None,
    ) -> SessionCookieObject:
        """
        :param session_data:
        :return: SessionCookieObject
        :param config: SessionCookieOption
        """

    def get_cookie_header_value(
        self,
        data: t.Any,
        delete: bool = False,
        config: t.Optional[SessionCookieOption] = None,
    ) -> str:
        session_config = config or self.session_cookie_options
        security_flags = "httponly; samesite=" + session_config.SAME_SITE
        if session_config.SECURE:
            security_flags += "; secure"

        if not delete:
            max_age = (
                f"Max-Age={session_config.MAX_AGE}; " if session_config.MAX_AGE else ""
            )
        else:
            max_age = "Max-Age=0; "

        header_value = "{session_cookie}={data}; path={path}; {max_age}{security_flags}".format(  # E501
            session_cookie=session_config.NAME,
            data=data,
            path=session_config.PATH,
            max_age=max_age,
            security_flags=security_flags,
        )
        return header_value
