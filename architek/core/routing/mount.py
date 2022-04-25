import typing as t

from starlette.routing import BaseRoute, Mount as StarletteMount, Route

from architek.compatible import DataMapper
from architek.core.routing.base import RouteOperationBase

from .operation_definitions import OperationDefinitions

if t.TYPE_CHECKING:
    from architek.core.guard import GuardCanActivate


__all__ = ["Mount", "ModuleRouter"]


class Mount(StarletteMount):
    def __init__(
        self,
        path: str,
        routes: t.Sequence[BaseRoute] = None,
        name: str = None,
        tag: t.Optional[str] = None,
        description: t.Optional[str] = None,
        external_doc_description: t.Optional[str] = None,
        external_doc_url: t.Optional[str] = None,
        version: t.Union[t.Tuple, str] = (),
        guards: t.Optional[
            t.List[t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]]
        ] = None,
    ) -> None:
        super(Mount, self).__init__(path=path, routes=routes or [], name=name)
        self._meta: t.Mapping = DataMapper(
            tag=tag,
            external_doc_description=external_doc_description,
            description=description,
            external_doc_url=external_doc_url,
        )
        self._route_guards: t.List[
            t.Union[t.Type["GuardCanActivate"], "GuardCanActivate", t.Any]
        ] = (guards or [])
        self._version = set(version or [])

    def get_meta(self) -> t.Mapping:
        return self._meta


class ModuleRouter(Mount):
    operation_definition_class: t.Type[OperationDefinitions] = OperationDefinitions

    def __init__(
        self,
        path: str,
        name: str = None,
        tag: t.Optional[str] = None,
        description: t.Optional[str] = None,
        external_doc_description: t.Optional[str] = None,
        external_doc_url: t.Optional[str] = None,
        version: t.Union[t.Tuple, str] = (),
        guards: t.Optional[
            t.List[t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]]
        ] = None,
    ) -> None:
        super(ModuleRouter, self).__init__(
            path=path,
            tag=tag,
            name=name,
            description=description,
            external_doc_description=external_doc_description,
            external_doc_url=external_doc_url,
            version=version,
            guards=guards,
        )

        _route_definitions = self.operation_definition_class(t.cast(list, self.routes))

        self.Get = _route_definitions.get
        self.Post = _route_definitions.post

        self.Delete = _route_definitions.delete
        self.Patch = _route_definitions.patch

        self.Put = _route_definitions.put
        self.Options = _route_definitions.options

        self.Trace = _route_definitions.trace
        self.Head = _route_definitions.head

        self.HttpRoute = _route_definitions.http_route
        self.WsRoute = _route_definitions.ws_route

    def build_routes(self) -> None:
        for route in self.routes:
            _route: RouteOperationBase = t.cast("RouteOperationBase", route)
            operation_meta = _route.get_meta()

            if not operation_meta.route_versioning:
                operation_meta.update(route_versioning=self._version)
            if not operation_meta.route_guards:
                operation_meta.update(route_guards=self._route_guards)

            if isinstance(_route, Route) and self._meta.get("tag"):
                tags = {self._meta["tag"]}
                if operation_meta.openapi.tags:
                    tags.update(set(operation_meta.openapi.tags))
                operation_meta.openapi.update(tags=list(tags))
