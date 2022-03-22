import inspect
import typing as t
from abc import ABC

from injector import is_decorated_with_inject, inject
from starlette.routing import BaseRoute, Route
from starletteapi.constants import NOT_SET
from starletteapi.context import ExecutionContext

from starletteapi.shortcuts import fail_silently
from .routing import ControllerMount
from ..compatible.dict import DataMutableMapper, AttributeDictAccess

if t.TYPE_CHECKING:
    from starletteapi.guard.base import GuardCanActivate
    from starletteapi.routing.operations import Operation, WebsocketOperation


class MissingAPIControllerDecoratorException(Exception):
    pass


class ControllerMeta(DataMutableMapper, AttributeDictAccess):
    pass


def get_route_functions(cls: t.Type) -> t.Iterable['Operation']:
    from starletteapi.routing.operations import OperationBase
    for method in cls.__dict__.values():
        if isinstance(method, OperationBase) or (
                isinstance(method, type) and issubclass(method, OperationBase)
        ):
            yield method


def compute_api_route_function(
        base_cls: t.Type, controller_instance: "Controller"
) -> None:
    for cls_route_function in get_route_functions(base_cls):
        controller_instance.add_route(t.cast('Operation', cls_route_function))


class ControllerBase:
    # `context` variable will change based on the route function called on the APIController
    # that way we can get some specific items things that belong the route function during execution
    context: t.Optional[ExecutionContext] = None

    @classmethod
    def controller_class_name(cls) -> str:
        """
        Returns the class name to be used for conventional behavior.
        By default, it returns the lowercase class name.
        """
        return cls.__name__.lower().replace("controller", "")

    @classmethod
    def full_view_name(cls, name: str) -> str:
        """
        Returns the full view name for this controller.
        By default, this function concatenates the lowercase class name
        to the view name.

        Therefore, a Home(Controller) will look for templates inside
        /views/home/ folder.
        """
        return f"{cls.controller_class_name()}/{name}"


class Controller:
    __slots__ = (
        '_route_guards', '_controller_class', '_routes', '_mount', '_version', '_tag', '_meta', 'guards'
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
            version: t.Union[t.List[str], str] = (),
            guards: t.Optional[t.List[t.Union[t.Type['GuardCanActivate'], 'GuardCanActivate']]] = None
    ) -> None:
        _controller_class = None
        _prefix: t.Optional[t.Any] = prefix or NOT_SET

        if prefix and isinstance(prefix, type):
            _prefix = NOT_SET
            _controller_class = prefix

        if _prefix is not NOT_SET:
            assert _prefix == "" or _prefix.startswith("/"), "Controller Prefix must start with '/'"

        self._route_guards: t.List[t.Union[t.Type['GuardCanActivate'], 'GuardCanActivate']] = guards or []
        # `controller_class`
        self._controller_class: t.Optional[t.Type[ControllerBase]] = None
        # `_path_operations`
        self._routes: t.Dict[str, t.Union['Operation', 'WebsocketOperation']] = {}
        self._mount: t.Optional[ControllerMount] = None
        self._version: t.Set[str] = set([version] if isinstance(version, str) else version)
        self._meta = ControllerMeta(
            tag=tag, description=description, external_doc_description=external_doc_description,
            external_doc_url=external_doc_url, path=_prefix, name=name
        )

        if _controller_class:
            self(_controller_class)

    def get_controller_class(self) -> t.Type[ControllerBase]:
        assert self._controller_class, "Controller Class is not available"
        return self._controller_class

    def __call__(self, cls: t.Type) -> 'Controller':
        if not issubclass(cls, ControllerBase):
            # We force the cls to inherit from `ControllerBase` by creating another type.
            cls = type(cls.__name__, (cls, ControllerBase), {})

        self._controller_class = t.cast(t.Type[ControllerBase], cls)

        tag = self._controller_class.controller_class_name()
        if not self._meta.tag:
            self._meta['tag'] = tag

        if self._meta.path is NOT_SET:
            self._meta['path'] = f"/{tag}"

        bases = inspect.getmro(cls)
        for base_cls in bases:
            if base_cls not in [ABC, ControllerBase, object]:
                compute_api_route_function(base_cls, self)

        if not is_decorated_with_inject(cls.__init__):
            fail_silently(inject, constructor_or_class=cls)

        if not self._meta.name:
            self._meta['name'] = str(cls.__name__).lower().replace("controller", "")

        return self

    def get_route(self) -> ControllerMount:
        if not self._mount:
            self._mount = ControllerMount(
                routes=list(self._routes.values()), **self._meta
            )
        return self._mount

    def __repr__(self) -> str:  # pragma: no cover
        return f"<controller - {self.get_controller_class().__name__}>"

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.get_controller_class().__name__}"

    def add_route(self, cls_route_function: 'Operation') -> None:
        self._routes[cls_route_function.path] = cls_route_function
        operation_meta = cls_route_function.get_meta()
        if not operation_meta.route_versioning:
            operation_meta.update(route_versioning=self._version)
        if not operation_meta.route_guards:
            operation_meta.update(route_guards=self._route_guards)

        if isinstance(cls_route_function, Route):
            tags = [self._meta.tag]
            if operation_meta.tags:
                tags += operation_meta.tags
            operation_meta.update(tags=tags)
        setattr(cls_route_function.endpoint, 'controller_class', self._controller_class)
