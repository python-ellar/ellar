import typing as t

from starlette.routing import BaseRoute

from ellar.core.guard import GuardCanActivate

from ..mount import Mount
from .model import ControllerBase


class ControllerMount(Mount):
    def __init__(
        self,
        path: str,
        controller_type: t.Type[ControllerBase],
        routes: t.Sequence[BaseRoute] = None,
        name: str = None,
        tag: t.Optional[str] = None,
        description: t.Optional[str] = None,
        external_doc_description: t.Optional[str] = None,
        external_doc_url: t.Optional[str] = None,
        version: t.Union[t.Tuple, str] = (),
        guards: t.Optional[
            t.List[t.Union[t.Type[GuardCanActivate], GuardCanActivate]]
        ] = None,
        include_in_schema: bool = True,
    ) -> None:
        super(ControllerMount, self).__init__(
            path=path,
            tag=tag,
            name=name,
            description=description,
            external_doc_description=external_doc_description,
            external_doc_url=external_doc_url,
            version=version,
            guards=guards,
            routes=routes,
            include_in_schema=include_in_schema,
        )
        self.controller_type = controller_type

    def build_routes(self) -> None:
        # Not necessary. Route Building is done in ControllerDecorator
        pass
