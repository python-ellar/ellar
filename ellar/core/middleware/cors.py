from ellar.common.types import ASGIApp
from ellar.core.conf import Config
from starlette.middleware.cors import CORSMiddleware as BaseCORSMiddleware

from .middleware import EllarMiddleware


class CORSMiddleware(BaseCORSMiddleware):
    def __init__(self, app: ASGIApp, config: Config) -> None:
        super().__init__(
            app,
            allow_origins=config.CORS_ALLOW_ORIGINS,
            allow_credentials=config.CORS_ALLOW_CREDENTIALS,
            allow_methods=config.CORS_ALLOW_METHODS,
            allow_headers=config.CORS_ALLOW_HEADERS,
            allow_origin_regex=config.CORS_ALLOW_ORIGIN_REGEX,
            expose_headers=config.CORS_EXPOSE_HEADERS,
            max_age=config.CORS_MAX_AGE,
        )


# CORSMiddleware Configuration
cors_middleware = EllarMiddleware(CORSMiddleware)
