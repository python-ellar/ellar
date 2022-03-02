import typing as t
from starlette.routing import Mount

from starletteapi.operation_meta import OperationMeta

if t.TYPE_CHECKING:
    from starletteapi.routing.operations import ControllerOperation, WebsocketOperation

__all__ = ['ControllerMount']


class ControllerMount(Mount):
    def __init__(
            self,
            path: str,
            routes: t.Sequence[t.Union['ControllerOperation', 'WebsocketOperation']] = None,
            name: str = None,
            tag: t.Optional[str] = None,
            description: t.Optional[str] = None,
            external_doc_description: t.Optional[str] = None,
            external_doc_url: t.Optional[str] = None,
    ) -> None:
        super(ControllerMount, self).__init__(path=path, routes=routes, name=name)
        self._meta = OperationMeta() 
        self._meta.update(
            tag=tag, external_doc_description=external_doc_description, description=description,
            external_doc_url=external_doc_url
        )

    def get_meta(self):
        return self._meta
