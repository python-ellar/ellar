import typing as t
from starlette.routing import Mount

from starletteapi.compatible import DataMapper
from starletteapi.operation_meta import OperationMeta

if t.TYPE_CHECKING:
    from starletteapi.routing.operations import ControllerOperation, WebsocketOperation
    from starletteapi.guard.base import GuardCanActivate

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
            version: t.Set[str] = (),
            guards: t.Optional[t.List[t.Union[t.Type['GuardCanActivate'], 'GuardCanActivate']]] = None
    ) -> None:
        super(ControllerMount, self).__init__(path=path, routes=routes, name=name)
        self._meta = DataMapper(
            tag=tag, external_doc_description=external_doc_description, description=description,
            external_doc_url=external_doc_url
        )
        self.route_guards: t.List[t.Union[t.Type['GuardCanActivate'], 'GuardCanActivate']] = guards or []
        self.version = version

    def get_meta(self) -> DataMapper:
        return self._meta
