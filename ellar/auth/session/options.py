import typing as t
from typing import Literal

from ellar.pydantic import BaseModel


class SessionCookieOption(BaseModel):
    NAME: str = "session"
    DOMAIN: t.Optional[str] = None
    PATH: str = "/"
    HTTPONLY: bool = True
    SECURE: bool = False
    SAME_SITE: Literal["lax", "strict", "none"] = "lax"
    MAX_AGE: t.Optional[int] = 14 * 24 * 60 * 60  # 14 days, in seconds
