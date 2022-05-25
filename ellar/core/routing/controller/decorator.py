import inspect
import typing as t
from abc import ABC

from starlette.routing import BaseRoute

from ellar.constants import NOT_SET
from ellar.di import RequestScope, injectable

from .model import ControllerBase, ControllerType
from .router import ControllerRouter

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.guard import GuardCanActivate
    from ellar.core.routing.base import RouteOperationBase


def get_route_functions(cls: t.Type) -> t.Iterable["RouteOperationBase"]:
    from ellar.core.routing.base import RouteOperationBase

    for method in cls.__dict__.values():
        if isinstance(method, RouteOperationBase):
            yield method


class ControllerDecorator:
    __slots__ = (
        "_controller_class",
        "_meta",
        "_router",
    )

    def __init__(
        self,
        prefix: t.Optional[str] = None,
        *,
        tag: t.Optional[str] = None,
        description: t.Optional[str] = None,
        external_doc_description: t.Optional[str] = None,
        external_doc_url: t.Optional[str] = None,
        name: t.Optional[str] = None,
        version: t.Union[t.Tuple, str] = (),
        guards: t.Optional[
            t.List[t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]]
        ] = None,
        include_in_schema: bool = True,
    ) -> None:
        _controller_class = None
        _prefix: t.Optional[t.Any] = prefix or NOT_SET

        if prefix and isinstance(prefix, type):
            _prefix = NOT_SET
            _controller_class = prefix

        if _prefix is not NOT_SET:
            assert _prefix == "" or str(_prefix).startswith(
                "/"
            ), "Controller Prefix must start with '/'"

        # `controller_class`
        self._controller_class: t.Optional[t.Type[ControllerBase]] = None

        self._meta = dict(
            tag=tag,
            description=description,
            external_doc_description=external_doc_description,
            external_doc_url=external_doc_url,
            path=_prefix,
            name=name,
            version=set([version] if isinstance(version, str) else version),
            guards=guards or [],
            include_in_schema=include_in_schema,
        )
        self._router: t.Optional["ControllerRouter"] = None

        if _controller_class:
            self(_controller_class)

    def get_meta(self) -> t.Dict:
        return self._meta

    def __call__(self, cls: t.Type) -> "ControllerDecorator":
        if type(cls) is not ControllerType:
            # We force the cls to inherit from `ControllerBase` by creating another type.
            cls = type(cls.__name__, (cls, ControllerBase), {})

        self._controller_class = t.cast(t.Type[ControllerBase], cls)

        tag = self._controller_class.controller_class_name()
        if not self._meta["tag"]:
            self._meta["tag"] = tag

        if self._meta["path"] is NOT_SET:
            self._meta["path"] = f"/{tag}"

        if not self._meta["name"]:
            self._meta["name"] = (
                str(self._controller_class.controller_class_name())
                .lower()
                .replace("controller", "")
            )

        self._router = ControllerRouter(
            **self._meta,  # type: ignore
            controller_type=self.get_controller_type(),
        )
        bases = inspect.getmro(cls)
        for base_cls in reversed(bases):
            if base_cls not in [ABC, ControllerBase, object]:
                self.compute_api_route_function(base_cls)

        injectable(RequestScope)(cls)

        return self

    def compute_api_route_function(self, base_cls: t.Type) -> None:
        for cls_route_function in get_route_functions(base_cls):
            self.get_router().routes.append(cls_route_function)

    def get_controller_type(self) -> t.Type[ControllerBase]:
        assert self._controller_class, "Controller not properly initialised"
        return self._controller_class

    def get_router(self) -> "ControllerRouter":
        assert self._router, "Controller not properly initialised"
        return self._router

    def build_routes(self) -> t.List[BaseRoute]:
        router = self.get_router()
        return router.build_routes()
