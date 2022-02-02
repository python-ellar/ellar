from .base import ControllerBase, Controller
from .routing import ControllerMount
from starletteapi.routing.operations import ControllerOperation, ControllerWebsocketOperation
from starletteapi.routing.route_definitions import RouteDefinitions

__all__ = [
    'Get',
    'Put',
    'Post',
    'Delete',
    'Patch', 'Head',
    'Options',
    'Trace',
    'Route',
    'Websocket',
    'ControllerBase',
    'Controller',
    'ControllerMount'
]

_route_definitions = RouteDefinitions(ControllerOperation, ControllerWebsocketOperation)

Get = _route_definitions.get
Post = _route_definitions.post

Delete = _route_definitions.delete
Patch = _route_definitions.patch

Put = _route_definitions.put
Options = _route_definitions.options

Trace = _route_definitions.trace
Head = _route_definitions.head

Route = _route_definitions.route
Websocket = _route_definitions.websocket
