import email
import re
from abc import abstractmethod
from typing import Any, Set, Optional

from starlette.routing import compile_path

from starletteapi.types import TScope
from starletteapi.constants import NOT_SET
from starletteapi.requests import HTTPConnection
from starletteapi import exceptions


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
        version = self.resolve()

        if version is NOT_SET:
            return True

        return version is not None and version == self.default_version or version in route_versions


class DefaultAPIVersionResolver(BaseAPIVersioningResolver):
    invalid_version_message = 'Invalid API version'

    def resolve_version(self) -> str:
        return NOT_SET


class UrlPathVersionResolver(DefaultAPIVersionResolver):
    invalid_version_message = 'Invalid version in URL path.'

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super(UrlPathVersionResolver, self).__init__(*args, **kwargs)

        prefix = '/{' + self.version_parameter + '}'
        self.path_regex, self.path_format, self.param_convertors = compile_path(
            prefix + "/{path:path}"
        )
        # we expected v[1-9] or (1-9).(1-9) as outcome of the result
        # to tell when a version is part of the url
        self.version_regex = re.compile('(v?[1-9]?(.[0-9]))', re.IGNORECASE)

    def _resolve_url_prefix(self) -> Optional[str]:
        """Since we expect a extra parameter that is not path any router routes,
        there is need to fix the path in order to avoid some unnecessary `Not Found`"""

        scope = self.connection.scope
        path = scope["path"]

        match = self.path_regex.match(path)
        if match:
            matched_params = match.groupdict()
            for key, value in matched_params.items():
                matched_params[key] = self.param_convertors[key].convert(value)

            _version = matched_params.get(self.version_parameter)
            if self.version_regex.match(_version):
                remaining_path = "/" + matched_params.pop("path")
                path_params = dict(scope.get("path_params", {}))
                path_params.update(matched_params)
                _scope_update = {
                    "path_params": path_params,
                    "path": remaining_path,
                }
                scope.update(_scope_update)
                return _version

    def resolve_version(self) -> str:
        version = self._resolve_url_prefix()
        if not version:
            version = self.default_version
        if not version:
            raise exceptions.NotFound(detail=self.invalid_version_message)
        return version


class HeaderVersionResolver(BaseAPIVersioningResolver):
    def __init__(self, header_parameter='accept', **kwargs):
        super(HeaderVersionResolver, self).__init__(**kwargs)
        self.header_parameter = header_parameter

    invalid_version_message = 'Invalid version in "Accept" header.'

    def resolve_version(self) -> str:
        message = email.message.Message()
        message[self.header_parameter] = self.connection.headers.get(self.header_parameter)
        accept = dict(message.get_params(header=self.header_parameter))
        version = accept.get(self.version_parameter, self.default_version)
        if not version:
            raise exceptions.NotAcceptable(detail=self.invalid_version_message)
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
        if not match and self.default_version:
            return self.default_version
        if not match:
            raise exceptions.NotFound(detail=self.invalid_version_message)
        version = match.group(1)
        return version
