import inspect
import typing as t
from abc import ABC

from starlette.routing import BaseRoute, Route

from architek.constants import NOT_SET
from architek.core.context import ExecutionContext
from architek.di import RequestScope, injectable
from architek.helper import get_name

if t.TYPE_CHECKING:
    from architek.core.guard import GuardCanActivate
    from architek.core.routing.controller.method_decorators import (
        RouteMethodDecoratorBase,
    )
    from architek.core.routing.controller.mount import ControllerMount


class MissingAPIControllerDecoratorException(Exception):
    pass


def get_route_functions(cls: t.Type) -> t.Iterable["RouteMethodDecoratorBase"]:
    from architek.core.routing.controller.method_decorators import (
        RouteMethodDecoratorBase,
    )

    for method in cls.__dict__.values():
        if isinstance(method, RouteMethodDecoratorBase):
            yield method


def compute_api_route_function(
    base_cls: t.Type, controller_instance: "ControllerDecorator"
) -> None:
    for cls_route_function in get_route_functions(base_cls):
        controller_instance.add_route(cls_route_function)


class ControllerType(type):
    _controller_name: t.Optional[str]

    @t.no_type_check
    def __new__(mcls, name, bases, namespace, **kwargs):
        cls = super().__new__(mcls, name, bases, namespace, **kwargs)
        cls._controller_name = None
        return cls

    def controller_class_name(cls) -> str:
        """ """
        if cls._controller_name:
            return cls._controller_name
        return cls.__name__.lower().replace("controller", "")

    def full_view_name(cls, name: str) -> str:
        """ """
        return f"{cls.controller_class_name()}/{name}"


class ControllerBase(metaclass=ControllerType):
    # `context` variable will change based on the route function called on the APIController
    # that way we can get some specific items things that belong the route function during execution
    context: t.Optional[ExecutionContext] = None


class ControllerDecorator:
    __slots__ = (
        "_route_guards",
        "_controller_class",
        "_routes",
        "_mount",
        "_version",
        "_tag",
        "_meta",
        "guards",
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

        self._route_guards: t.List[
            t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]
        ] = (guards or [])
        # `controller_class`
        self._controller_class: t.Optional[t.Type[ControllerBase]] = None
        # `_path_operations`
        self._routes: t.Dict[str, BaseRoute] = {}
        self._version: t.Set[str] = set(
            [version] if isinstance(version, str) else version
        )
        self._meta = dict(
            tag=tag,
            description=description,
            external_doc_description=external_doc_description,
            external_doc_url=external_doc_url,
            path=_prefix,
            name=name,
            version=self._version,
            guards=self._route_guards,
        )
        self._mount: t.Optional[ControllerMount] = None

        if _controller_class:
            self(_controller_class)

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

        bases = inspect.getmro(cls)
        for base_cls in reversed(bases):
            if base_cls not in [ABC, ControllerBase, object]:
                compute_api_route_function(base_cls, self)

        cls = injectable(RequestScope)(cls)

        if not self._meta["name"]:
            self._meta["name"] = str(cls.__name__).lower().replace("controller", "")
        return self

    def get_controller_type(self) -> t.Type[ControllerBase]:
        assert self._controller_class, "Controller not properly initialised"
        return self._controller_class

    def get_route(self) -> "ControllerMount":
        from architek.core.routing.controller.mount import ControllerMount

        if not self._mount:
            self._mount = ControllerMount(
                routes=list(self._routes.values()),
                **self._meta,  # type: ignore
                controller_type=self.get_controller_type(),
            )
        return self._mount

    def add_route(self, cls_route_function: "RouteMethodDecoratorBase") -> None:
        operation = cls_route_function.create_operation(self.get_controller_type())
        self._routes[get_name(operation.endpoint)] = operation

        operation_meta = operation.get_meta()
        if not operation_meta.route_versioning:
            operation_meta.update(route_versioning=self._version)
        if not operation_meta.route_guards:
            operation_meta.update(route_guards=self._route_guards)

        if isinstance(operation, Route):
            tags = {self._meta["tag"]}
            if operation_meta.openapi.tags:
                tags.update(set(operation_meta.openapi.tags))
            operation_meta.openapi.update(tags=list(tags))
