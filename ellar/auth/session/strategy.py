import json
import typing as t
from base64 import b64decode, b64encode

import itsdangerous
from itsdangerous import BadSignature
from starlette.datastructures import MutableHeaders

from ellar.core import Config
from ellar.di import injectable

from .cookie_dict import SessionCookieObject
from .interface import ISessionService
from .options import SessionCookieOption


@injectable
class SessionClientStrategy(ISessionService):
    def __init__(self, config: Config) -> None:
        self._signer = itsdangerous.TimestampSigner(str(config.SECRET_KEY))
        self.config = config
        self._session_config = SessionCookieOption(
            NAME=config.SESSION_COOKIE_NAME or "connect.sid",
            DOMAIN=config.SESSION_COOKIE_DOMAIN,
            PATH=config.SESSION_COOKIE_PATH or "/",
            HTTPONLY=config.SESSION_COOKIE_HTTPONLY or True,
            SECURE=config.SESSION_COOKIE_SECURE or False,
            SAME_SITE=config.SESSION_COOKIE_SAME_SITE or "lax",
            MAX_AGE=config.SESSION_COOKIE_MAX_AGE
            or 14 * 24 * 60 * 60,  # 14 days, in seconds
        )

    @property
    def session_cookie_options(self) -> SessionCookieOption:
        return self._session_config

    def _get_header_value(self, data: t.Any, max_age: str) -> str:
        security_flags = "httponly; samesite=" + self._session_config.SAME_SITE
        if self._session_config.SECURE:
            security_flags += "; secure"

        header_value = "{session_cookie}={data}; path={path}; {max_age}{security_flags}".format(  # E501
            session_cookie=self._session_config.NAME,
            data=data,
            path=self._session_config.PATH,
            max_age=max_age,
            security_flags=security_flags,
        )
        return header_value

    def save_session(
        self,
        response_headers: MutableHeaders,
        session: t.Union[str, SessionCookieObject],
    ) -> None:
        if isinstance(session, SessionCookieObject):
            data = b64encode(json.dumps(dict(session)).encode("utf-8"))
            data = self._signer.sign(data)
            header_value = self._get_header_value(
                data,
                max_age=f"Max-Age={self._session_config.MAX_AGE}; "
                if self._session_config.MAX_AGE
                else "",
            )
        else:
            header_value = self._get_header_value(session, max_age="Max-Age=0; ")

        response_headers.append("Set-Cookie", header_value)

    def load_session(self, session_data: t.Optional[str]) -> SessionCookieObject:
        if session_data:
            data = session_data.encode("utf-8")
            try:
                data = self._signer.unsign(data, max_age=self._session_config.MAX_AGE)
                return SessionCookieObject(json.loads(b64decode(data)))
            except BadSignature:
                pass

        return SessionCookieObject()
