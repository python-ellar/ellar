from enum import Enum

from .base import (  # noqa
    BaseAPIVersioning as BaseAPIVersioning,
    DefaultAPIVersioning as DefaultAPIVersioning,
    HeaderAPIVersioning as HeaderAPIVersioning,
    HostNameAPIVersioning as HostNameAPIVersioning,
    QueryParameterAPIVersioning as QueryParameterAPIVersioning,
    UrlPathAPIVersioning as UrlPathAPIVersioning,
)


class VERSIONING(Enum):
    URL = UrlPathAPIVersioning
    QUERY = QueryParameterAPIVersioning
    HEADER = HeaderAPIVersioning
    HOST = HostNameAPIVersioning
    NONE = DefaultAPIVersioning
