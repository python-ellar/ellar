import typing as t

from starlette.routing import Mount

from architek.compatible import DataMapper

if t.TYPE_CHECKING:
    from architek.guard.base import GuardCanActivate
    from architek.routing.operations import ControllerOperation, WebsocketOperation

__all__ = ["ControllerMount"]


class ControllerMount(Mount):
    def __init__(
        self,
        path: str,
        routes: t.Sequence[t.Union["ControllerOperation", "WebsocketOperation"]] = None,
        name: str = None,
        tag: t.Optional[str] = None,
        description: t.Optional[str] = None,
        external_doc_description: t.Optional[str] = None,
        external_doc_url: t.Optional[str] = None,
        version: t.Set[str] = None,
        guards: t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"] = None,
    ) -> None:
        super(ControllerMount, self).__init__(path=path, routes=routes, name=name)
        self._meta: t.Mapping = DataMapper(
            tag=tag,
            external_doc_description=external_doc_description,
            description=description,
            external_doc_url=external_doc_url,
        )
        self.route_guards: t.List[
            t.Union[t.Type["GuardCanActivate"], "GuardCanActivate", t.Any]
        ] = (
            guards or []  # type: ignore
        )
        self.version = set(version or [])

    def get_meta(self) -> t.Mapping:
        return self._meta
