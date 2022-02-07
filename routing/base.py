import typing as t
from starlette.routing import Router, Mount
from .operations import Operation, WebsocketOperation
from .route_definitions import RouteDefinitions

__all__ = ['ModuleRouter', 'APIRouter']


class ModuleRouter(Mount):
    def __init__(
            self,
            path: str,
            name: str = None,
    ) -> None:
        super(ModuleRouter, self).__init__(path=path, routes=[], name=name)
        self.app = APIRouter(routes=[])

        self.Get = self.app.Get
        self.Post = self.app.Post

        self.Delete = self.app.Delete
        self.Patch = self.app.Patch

        self.Put = self.app.Put
        self.Options = self.app.Options

        self.Trace = self.app.Trace
        self.Head = self.app.Head

        self.Route = self.app.Route
        self.Websocket = self.app.Websocket


class APIRouter(Router):
    def __init__(self, *args: t.Any, **kwargs: t.Any):
        super().__init__(*args, **kwargs)

        self._route_definitions = RouteDefinitions(Operation, WebsocketOperation, self.routes or [])

        self.Get = self._route_definitions.get
        self.Post = self._route_definitions.post

        self.Delete = self._route_definitions.delete
        self.Patch = self._route_definitions.patch

        self.Put = self._route_definitions.put
        self.Options = self._route_definitions.options

        self.Trace = self._route_definitions.trace
        self.Head = self._route_definitions.head

        self.Route = self._route_definitions.route
        self.Websocket = self._route_definitions.websocket

