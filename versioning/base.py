import re
from abc import ABC
from typing import Any, Set, List, TYPE_CHECKING, Type, Optional

from starletteapi.routing.path import PathModifier
from starletteapi.types import TScope
from starletteapi.constants import NOT_SET
from .resolver import (
    BaseAPIVersioningResolver, DefaultAPIVersionResolver,
    UrlPathVersionResolver, HostNameAPIVersionResolver,
    QueryParameterAPIVersionResolver, HeaderVersionResolver
)

if TYPE_CHECKING:
    from starletteapi.routing import BaseRoute


class BaseAPIVersioning(ABC):
    resolver_class: Type[BaseAPIVersioningResolver] = DefaultAPIVersionResolver

    def __init__(
            self,
            version_parameter: str = 'version',
            default_version: Optional[str] = None,
            **kwargs
    ):
        self.version_parameter = version_parameter or NOT_SET
        self.default_version = default_version or NOT_SET

    def modify_routes(self, routes: List['BaseRoute']) -> None:
        pass

    def get_version_resolver(self, scope: TScope) -> BaseAPIVersioningResolver:
        return self.resolver_class(
            scope=scope, version_parameter=self.version_parameter,
            default_version=self.default_version
        )


class DefaultAPIVersioning(BaseAPIVersioning):
    pass


class UrlPathAPIVersioning(BaseAPIVersioning):
    """
    GET /1.0/something/ HTTP/1.1
    Host: example.com
    Accept: application/json
    """
    resolver_class: Type[BaseAPIVersioningResolver] = UrlPathVersionResolver

    def modify_routes(self, routes: List['BaseRoute']) -> None:
        prefix = '/{' + self.version_parameter + '}'
        for route in routes:
            path_modifier = PathModifier(route)
            path_modifier.prefix(prefix)


class HeaderAPIVersioning(BaseAPIVersioning):
    """
    GET /something/ HTTP/1.1
    Host: example.com
    Accept: application/json; version=1.0
    """
    resolver_class: Type[BaseAPIVersioningResolver] = HeaderVersionResolver

    def __init__(self, header_parameter='accept', **kwargs):
        super().__init__(**kwargs)
        self.header_parameter = header_parameter

    def get_version_resolver(self, scope: TScope) -> BaseAPIVersioningResolver:
        return self.resolver_class(
            scope=scope,
            header_parameter=self.header_parameter,
            version_parameter=self.version_parameter,
            default_version=self.default_version
        )


class QueryParameterAPIVersioning(BaseAPIVersioning):
    """
   GET /something/?version=0.1 HTTP/1.1
   Host: example.com
   Accept: application/json
   """
    resolver_class: Type[BaseAPIVersioningResolver] = QueryParameterAPIVersionResolver


class HostNameAPIVersioning(BaseAPIVersioning):
    """
    GET /something/ HTTP/1.1
    Host: v1.example.com
    Accept: application/json
    """
    resolver_class: Type[BaseAPIVersioningResolver] = HostNameAPIVersionResolver
