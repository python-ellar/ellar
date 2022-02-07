from enum import Enum

from .base import (
    BaseAPIVersioning,
    DefaultAPIVersioning,
    UrlPathAPIVersioning,
    QueryParameterAPIVersioning,
    HeaderAPIVersioning,
    HostNameAPIVersioning
)


class VERSIONING(Enum):
    URL = UrlPathAPIVersioning
    QUERY = QueryParameterAPIVersioning
    HEADER = HeaderAPIVersioning
    HOST = HostNameAPIVersioning
