import typing as t
from starlette.routing import Mount

if t.TYPE_CHECKING:
    from starletteapi.routing.operations import ControllerOperation, WebsocketOperation

__all__ = ['ControllerMount']


class ControllerMount(Mount):
    def __init__(
            self,
            path: str,
            routes: t.Sequence[t.Union['ControllerOperation', 'WebsocketOperation']] = None,
            name: str = None,
    ) -> None:
        super(ControllerMount, self).__init__(path=path, routes=routes, name=name)
