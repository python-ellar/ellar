import inspect
from abc import ABC
from typing import Union, Optional, List, Type, Iterable, cast, Dict, TYPE_CHECKING, Tuple, Any, Set

from injector import is_decorated_with_inject, inject
from starlette.routing import BaseRoute
from starletteapi.constants import NOT_SET
from starletteapi.context import ExecutionContext
from starletteapi.guard import GuardInterface

from starletteapi.shortcuts import fail_silently
from .routing import ControllerMount

if TYPE_CHECKING:
    from starletteapi.guard.base import GuardCanActivate
    from starletteapi.routing.operations import Operation


class MissingAPIControllerDecoratorException(Exception):
    pass


def get_route_functions(cls: Type) -> Iterable['Operation']:
    from starletteapi.routing.operations import OperationBase
    for method in cls.__dict__.values():
        if isinstance(method, OperationBase) or (
                isinstance(method, type) and issubclass(method, OperationBase)
        ):
            yield method


def compute_api_route_function(
        base_cls: Type, controller_instance: "Controller"
) -> None:
    for cls_route_function in get_route_functions(base_cls):
        controller_instance.add_route(cast('Operation', cls_route_function))


class ControllerBase:
    # `context` variable will change based on the route function called on the APIController
    # that way we can get some specific items things that belong the route function during execution
    context: Optional[ExecutionContext] = None


class Controller(GuardInterface):
    def __init__(
            self,
            prefix: Optional[str] = None,
            *,
            tag: Optional[str] = None,
            description: Optional[str] = None,
            external_doc_description: Optional[str] = None,
            external_doc_url: Optional[str] = None,
            name: Optional[str] = None,
            version: Union[List[str], str] = ()
    ) -> None:
        _controller_class = None
        _prefix: Optional[Any] = prefix or NOT_SET

        if prefix and isinstance(prefix, type):
            _prefix = NOT_SET
            _controller_class = prefix

        if _prefix is not NOT_SET:
            assert _prefix == "" or _prefix.startswith("/"), "Controller Prefix must start with '/'"

        self.prefix = _prefix

        self._route_guards: List[Union[Type['GuardCanActivate'], 'GuardCanActivate']] = []
        # `controller_class`
        self._controller_class: Optional[Type[ControllerBase]] = None
        # `_path_operations`
        self._routes: Dict[str, BaseRoute] = {}
        self._mount: Optional[ControllerMount] = None
        self.name = name
        self._version: Set[str] = set([version] if isinstance(version, str) else version)
        self._meta = dict(tag=tag, description=description, external_doc_description=external_doc_description,
                          external_doc_url=external_doc_url)
        self.tag = tag

        if _controller_class:
            self(_controller_class)

    @property
    def version(self) -> Set[str]:
        return self._version

    @property
    def controller_class(self) -> Type[ControllerBase]:
        assert self._controller_class, "Controller Class is not available"
        return self._controller_class

    def __call__(self, cls: Type) -> 'Controller':
        if not issubclass(cls, ControllerBase):
            # We force the cls to inherit from `ControllerBase` by creating another type.
            cls = type(cls.__name__, (cls, ControllerBase), {})

        self._controller_class = cast(Type[ControllerBase], cls)

        tag = self.controller_class_name()
        if not self.tag:
            self.tag = tag

        if self.prefix is NOT_SET:
            self.prefix = f"/{tag}"

        bases = inspect.getmro(cls)
        for base_cls in bases:
            if base_cls not in [ABC, ControllerBase, object]:
                compute_api_route_function(base_cls, self)

        if not is_decorated_with_inject(cls.__init__):
            fail_silently(inject, constructor_or_class=cls)

        if not self.name:
            self.name = str(cls.__name__).lower().replace("controller", "")

        return self

    def controller_class_name(self) -> str:
        """
        Returns the class name to be used for conventional behavior.
        By default, it returns the lowercase class name.
        """
        return self.controller_class.__name__.lower().replace("controller", "")

    def full_view_name(self, name: str) -> str:
        """
        Returns the full view name for this controller.
        By default, this function concatenates the lowercase class name
        to the view name.

        Therefore, a Home(Controller) will look for templates inside
        /views/home/ folder.
        """
        return f"{self.controller_class_name()}/{name}"

    def get_route(self) -> ControllerMount:
        if not self._mount:
            self._mount = ControllerMount(
                self.prefix, routes=list(self._routes.values()), name=self.name, **self._meta
            )
        return self._mount

    def __repr__(self) -> str:  # pragma: no cover
        return f"<controller - {self.controller_class.__name__}>"

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.controller_class.__name__}"

    def get_guards(self) -> List[Union[Type['GuardCanActivate'], 'GuardCanActivate']]:
        return self._route_guards

    def add_guards(self, *guards: Tuple[Union[Type['GuardCanActivate'], 'GuardCanActivate']]) -> None:
        self._route_guards += list(guards)

    def add_route(self, cls_route_function: 'Operation') -> None:
        func_name = f"{cls_route_function.endpoint.__name__}"
        self._routes[func_name] = cls_route_function
        cls_route_function.controller = self
