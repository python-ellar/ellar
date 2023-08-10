import typing as t

from ellar.common.interfaces import IAPIVersioning
from ellar.common.types import TScope

from .resolver import (
    BaseAPIVersioningResolver,
    DefaultAPIVersionResolver,
    HeaderVersionResolver,
    HostNameAPIVersionResolver,
    QueryParameterAPIVersionResolver,
    UrlPathVersionResolver,
)


class BaseAPIVersioning(IAPIVersioning):
    resolver_class: t.Type[BaseAPIVersioningResolver] = DefaultAPIVersionResolver

    def __init__(
        self,
        version_parameter: str = "version",
        default_version: t.Optional[str] = None,
        **kwargs: t.Any,
    ):
        self.version_parameter = version_parameter
        self.default_version = default_version

    def get_version_resolver(self, scope: TScope) -> BaseAPIVersioningResolver:
        return self.resolver_class(
            scope=scope,
            version_parameter=self.version_parameter,
            default_version=self.default_version,
        )


class DefaultAPIVersioning(BaseAPIVersioning):
    """
    A PlaceHolder Versioning Scheme.
    """


class UrlPathAPIVersioning(BaseAPIVersioning):
    """
    GET /1.0/something/ HTTP/1.1
    Host: example.com
    Accept: application/json
    """

    resolver_class: t.Type[BaseAPIVersioningResolver] = UrlPathVersionResolver


class HeaderAPIVersioning(BaseAPIVersioning):
    """
    GET /something/ HTTP/1.1
    Host: example.com
    Accept: application/json; version=1.0
    """

    resolver_class: t.Type[BaseAPIVersioningResolver] = HeaderVersionResolver

    def __init__(self, header_parameter: str = "accept", **kwargs: t.Any) -> None:
        super().__init__(**kwargs)
        self.header_parameter = header_parameter

    def get_version_resolver(self, scope: TScope) -> BaseAPIVersioningResolver:
        resolver_class = t.cast(t.Type[HeaderVersionResolver], self.resolver_class)
        return resolver_class(
            scope=scope,
            header_parameter=self.header_parameter,
            version_parameter=self.version_parameter,
            default_version=self.default_version,
        )


class QueryParameterAPIVersioning(BaseAPIVersioning):
    """
    GET /something/?version=0.1 HTTP/1.1
    Host: example.com
    Accept: application/json
    """

    resolver_class: t.Type[BaseAPIVersioningResolver] = QueryParameterAPIVersionResolver


class HostNameAPIVersioning(BaseAPIVersioning):
    """
    GET /something/ HTTP/1.1
    Host: v1.example.com
    Accept: application/json
    """

    resolver_class: t.Type[BaseAPIVersioningResolver] = HostNameAPIVersionResolver
