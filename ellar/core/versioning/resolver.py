import email
import re
import typing as t
from abc import abstractmethod

from ellar.common.constants import NOT_SET
from ellar.common.exceptions import NotAcceptable, NotFound
from ellar.common.interfaces import IAPIVersioningResolver
from ellar.common.types import TScope
from ellar.core.connection import HTTPConnection
from starlette.routing import compile_path


class BaseAPIVersioningResolver(IAPIVersioningResolver):
    def __init__(
        self, *, scope: TScope, version_parameter: str, default_version: t.Optional[str]
    ) -> None:
        self.version_parameter = version_parameter
        self.default_version = default_version
        self.connection = HTTPConnection(scope)
        self._resolved_version: t.Optional[str] = None
        self.matched_any_route = False

    def resolve(self) -> t.Optional[str]:
        if not self._resolved_version:
            self._resolved_version = self.resolve_version()
        return self._resolved_version

    @abstractmethod
    def resolve_version(self) -> t.Optional[str]:
        """resolve versions for an incoming request"""

    @abstractmethod
    def raise_exception(self) -> None:
        """raise exception defined by the resolver"""

    def can_activate(self, route_versions: t.Set[t.Union[int, float, str]]) -> bool:
        self.matched_any_route = True

        version = self.resolve()

        if str(version) == str(NOT_SET):
            return True

        if route_versions and version not in route_versions:
            return False

        return (
            version is not None
            and version == str(self.default_version)
            or version in route_versions
        )


class DefaultAPIVersionResolver(BaseAPIVersioningResolver):
    invalid_version_message = "Invalid API version"

    def raise_exception(self) -> None:
        raise NotFound(self.invalid_version_message)

    def resolve_version(self) -> str:
        return str(NOT_SET)


class UrlPathVersionResolver(DefaultAPIVersionResolver):
    invalid_version_message = "Invalid version in URL path."

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        super(UrlPathVersionResolver, self).__init__(*args, **kwargs)

        prefix = "/{" + self.version_parameter + "}"
        self.path_regex, self.path_format, self.param_convertors = compile_path(
            prefix + "/{path:path}"
        )
        # we expected v[1-9] or (1-9).(1-9) as outcome of the result
        # to tell when a version is part of the url
        self.version_regex = re.compile("(/?(v)?[1-9]?(.[0-9]))", re.IGNORECASE)

    def _resolve_url_prefix(self) -> t.Optional[str]:
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
            if _version and self.version_regex.match(f"/{_version}"):
                remaining_path = "/" + matched_params.pop("path")
                path_params = dict(scope.get("path_params", {}))
                path_params.update(matched_params)
                _scope_update = {
                    "path_params": path_params,
                    "path": remaining_path,
                }
                scope.update(_scope_update)
                return str(_version).replace("v", "")
        return None

    def resolve_version(self) -> str:
        version = self._resolve_url_prefix()
        if not version:
            version = self.default_version
        return str(version)


class HeaderVersionResolver(BaseAPIVersioningResolver):
    def __init__(self, header_parameter: str = "accept", **kwargs: t.Any) -> None:
        super(HeaderVersionResolver, self).__init__(**kwargs)
        self.header_parameter = header_parameter

    invalid_version_message = 'Invalid version in "{parameter}" header.'

    def raise_exception(self) -> None:
        raise NotAcceptable(
            self.invalid_version_message.format(parameter=self.header_parameter)
        )

    def resolve_version(self) -> str:
        message = email.message.Message()
        message[self.header_parameter] = self.connection.headers.get(
            self.header_parameter
        )
        accept = dict(message.get_params(header=self.header_parameter))  # type: ignore[arg-type]
        version = accept.get(self.version_parameter, self.default_version)
        return str(version)


class QueryParameterAPIVersionResolver(DefaultAPIVersionResolver):
    invalid_version_message = "Invalid version in query parameter."

    def resolve_version(self) -> str:
        version = (
            self.connection.query_params.get(self.version_parameter)
            or self.default_version
        )
        return str(version)


class HostNameAPIVersionResolver(HeaderVersionResolver):
    hostname_regex = re.compile(r"^([a-zA-Z0-9]+)\.[a-zA-Z0-9]+\.[a-zA-Z0-9]+$")
    invalid_version_message = "Invalid version in hostname."

    def __init__(self, **kwargs: t.Any) -> None:
        super(HostNameAPIVersionResolver, self).__init__(**kwargs)
        self.version_parameter = (
            "v" if self.version_parameter == "version" else self.version_parameter
        )
        self.header_parameter = "Host"

    def raise_exception(self) -> None:
        raise NotFound(self.invalid_version_message)

    def resolve_version(self) -> str:
        host_value = self.connection.headers.get(self.header_parameter)
        hostname, separator, port = str(host_value).partition(":")
        match = self.hostname_regex.match(hostname)
        if not match and self.default_version:
            return str(self.default_version)
        if match:
            version = match.group(1)
            return str(version).replace(self.version_parameter, "")
        return str(None)
