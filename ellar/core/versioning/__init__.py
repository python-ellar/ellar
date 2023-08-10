from enum import Enum

from .base import (  # noqa
    BaseAPIVersioning as BaseAPIVersioning,
)
from .base import (
    DefaultAPIVersioning as DefaultAPIVersioning,
)
from .base import (
    HeaderAPIVersioning as HeaderAPIVersioning,
)
from .base import (
    HostNameAPIVersioning as HostNameAPIVersioning,
)
from .base import (
    QueryParameterAPIVersioning as QueryParameterAPIVersioning,
)
from .base import (
    UrlPathAPIVersioning as UrlPathAPIVersioning,
)


class VersioningSchemes(Enum):
    URL = UrlPathAPIVersioning
    QUERY = QueryParameterAPIVersioning
    HEADER = HeaderAPIVersioning
    HOST = HostNameAPIVersioning
    NONE = DefaultAPIVersioning
