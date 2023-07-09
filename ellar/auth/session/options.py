import sys
import typing as t

from pydantic import BaseModel

if sys.version_info >= (3, 8):  # pragma: no cover
    from typing import Literal
else:  # pragma: no cover
    from typing_extensions import Literal


class SessionCookieOption(BaseModel):
    NAME: str = "connect.sid"
    DOMAIN: t.Optional[str] = None
    PATH: str = "/"
    HTTPONLY: bool = True
    SECURE: bool = False
    SAME_SITE: Literal["lax", "strict", "none"] = "lax"
    MAX_AGE: int = 14 * 24 * 60 * 60  # 14 days, in seconds
