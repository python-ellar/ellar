from ellar.core.conf import ConfigDefaultTypesMixin


class BaseConfig(ConfigDefaultTypesMixin):
    MIDDLEWARE = [
        "ellar.core.middleware.trusted_host:trusted_host_middleware",
        "ellar.core.middleware.cors:cors_middleware",
        "ellar.core.middleware.errors:server_error_middleware",
        "ellar.core.middleware.versioning:versioning_middleware",
        "ellar.auth.middleware.session:session_middleware",
        "ellar.auth.middleware.auth:identity_middleware",
        "ellar.core.middleware.exceptions:exception_middleware",
    ]


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class TestingConfig(BaseConfig):
    DEBUG = False
