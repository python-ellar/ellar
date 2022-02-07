import email
import re
from abc import abstractmethod, ABC
from typing import Any, Set, List, TYPE_CHECKING
from starletteapi.types import TScope
from starletteapi.constants import NOT_SET
from starletteapi.requests import HTTPConnection
from starletteapi import exceptions

if TYPE_CHECKING:
    from starletteapi.routing import BaseRoute


class BaseAPIVersioningResolver:
    def __init__(
            self, *, scope: TScope,
            version_parameter: str,
            default_version: str
    ):
        self.version_parameter = version_parameter
        self.default_version = default_version
        self.connection = HTTPConnection(scope)
        self._resolved_version = None
        self.find_route_with_wrong_version = False

    def resolve(self) -> str:
        if not self._resolved_version:
            self._resolved_version = self.resolve_version()
        return self._resolved_version

    @abstractmethod
    def resolve_version(self) -> str:
        pass

    def can_activate(self, route_versions: Set[str]) -> bool:
        is_version_allowed = self.is_version_allowed(route_versions=route_versions)
        self.find_route_with_wrong_version = not is_version_allowed
        return is_version_allowed

    def is_version_allowed(self, route_versions: Set[str]) -> bool:
        version = self.resolve()

        if version is NOT_SET:
            return True

        return version is not None and version == self.default_version or version in route_versions

    @abstractmethod
    def raise_exception_from(self, ex: Exception) -> bool:
        pass


class DefaultAPIVersionResolver(BaseAPIVersioningResolver):
    invalid_version_message = 'Invalid API version'

    def raise_exception_from(self, ex: Exception) -> None:
        if self.find_route_with_wrong_version:
            raise exceptions.NotFound(detail=self.invalid_version_message)
        raise ex

    def resolve_version(self) -> str:
        return NOT_SET


class UrlPathVersionResolver(DefaultAPIVersionResolver):
    invalid_version_message = 'Invalid version in URL path.'

    def resolve_version(self) -> str:
        version = self.connection.path_params.get(self.version_parameter, self.default_version)
        return version


class HeaderVersionResolver(BaseAPIVersioningResolver):
    def __init__(self, header_parameter='accept', **kwargs):
        super(HeaderVersionResolver, self).__init__(**kwargs)
        self.header_parameter = header_parameter

    invalid_version_message = 'Invalid version in "Accept" header.'

    def raise_exception_from(self, ex: Exception) -> None:
        if self.find_route_with_wrong_version:
            raise exceptions.NotAcceptable(detail=self.invalid_version_message)
        raise ex

    def resolve_version(self) -> str:
        message = email.message.Message()
        message[self.header_parameter] = self.connection.headers.get(self.header_parameter)
        accept = dict(message.get_params(header=self.header_parameter))
        version = accept.get(self.version_parameter, self.default_version)
        return version


class QueryParameterAPIVersionResolver(DefaultAPIVersionResolver):
    invalid_version_message = 'Invalid version in query parameter.'

    def resolve_version(self) -> str:
        version = self.connection.query_params.get(self.version_parameter, self.default_version)
        return version


class HostNameAPIVersionResolver(DefaultAPIVersionResolver):
    hostname_regex = re.compile(r'^([a-zA-Z0-9]+)\.[a-zA-Z0-9]+\.[a-zA-Z0-9]+$')
    invalid_version_message = 'Invalid version in hostname.'

    def resolve_version(self) -> str:
        host_value = self.connection.headers.get('Host')
        hostname, separator, port = str(host_value).partition(':')
        match = self.hostname_regex.match(hostname)
        if not match:
            return self.default_version
        version = match.group(1)
        return version
