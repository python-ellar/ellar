import inspect
import copy
import re
import sys
import typing as t
from abc import ABC

from injector import is_decorated_with_inject, inject
from starlette.routing import Route
from starletteapi.constants import NOT_SET
from starletteapi.context import ExecutionContext

from starletteapi.shortcuts import fail_silently
from .routing import ControllerMount

if t.TYPE_CHECKING:
    from starletteapi.guard.base import GuardCanActivate
    from starletteapi.routing.operations import Operation, WebsocketOperation


if sys.version_info >= (3, 6):
    def copier(x: t.Any, memo: t.Dict):
        return x
    copy._deepcopy_dispatch[type(re.compile(''))] = copier


class MissingAPIControllerDecoratorException(Exception):
    pass


def get_route_functions(cls: t.Type) -> t.Iterable['Operation']:
    from starletteapi.routing.operations import OperationBase
    for method in cls.__dict__.values():
        if isinstance(method, OperationBase) or (
                isinstance(method, type) and issubclass(method, OperationBase)
        ):
            yield method


def compute_api_route_function(
        base_cls: t.Type, controller_instance: "_ControllerDecorator"
) -> None:
    for cls_route_function in get_route_functions(base_cls):
        controller_instance.add_route(t.cast('Operation', cls_route_function))


class ControllerType(type):
    _mount: ControllerMount

    @t.no_type_check
    def __new__(mcls, name, bases, namespace, **kwargs):
        cls = super().__new__(mcls, name, bases, namespace, **kwargs)  # type: ignore
        cls._mount = None
        return cls

    def controller_class_name(cls) -> str:
        """
        Returns the class name to be used for conventional behavior.
        By default, it returns the lowercase class name.
        """
        return cls.__name__.lower().replace("controller", "")

    def full_view_name(cls, name: str) -> str:
        """
        Returns the full view name for this controller.
        By default, this function concatenates the lowercase class name
        to the view name.

        Therefore, a Home(Controller) will look for templates inside
        /views/home/ folder.
        """
        return f"{cls.controller_class_name()}/{name}"

    def get_route(cls) -> ControllerMount:
        if not cls._mount:
            raise Exception('controller not properly configured')
        return cls._mount


class ControllerBase(metaclass=ControllerType):
    # `context` variable will change based on the route function called on the APIController
    # that way we can get some specific items things that belong the route function during execution
    context: t.Optional[ExecutionContext] = None


class _ControllerDecorator:
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
        self._version: t.Set[str] = set([version] if isinstance(version, str) else version)
        self._meta = dict(
            tag=tag, description=description, external_doc_description=external_doc_description,
            external_doc_url=external_doc_url, path=_prefix, name=name, version=self._version, guards=self._route_guards
        )

        if _controller_class:
            self(_controller_class)

    def __call__(self, cls: t.Type) -> t.Type[ControllerBase]:
        if type(cls) is not ControllerType:
            # We force the cls to inherit from `ControllerBase` by creating another type.
            cls = type(cls.__name__, (cls, ControllerBase), {})

        self._controller_class = t.cast(t.Type[ControllerBase], cls)

        tag = self._controller_class.controller_class_name()
        if not self._meta['tag']:
            self._meta['tag'] = tag

        if self._meta['path'] is NOT_SET:
            self._meta['path'] = f"/{tag}"

        bases = inspect.getmro(cls)
        for base_cls in reversed(bases):
            if base_cls not in [ABC, ControllerBase, object]:
                compute_api_route_function(base_cls, self)

        if not is_decorated_with_inject(cls.__init__):
            fail_silently(inject, constructor_or_class=cls)

        if not self._meta['name']:
            self._meta['name'] = str(cls.__name__).lower().replace("controller", "")
        cls._mount = self.get_route()
        return t.cast(t.Type[ControllerBase], cls)

    def get_route(self) -> ControllerMount:
        return ControllerMount(
            routes=list(self._routes.values()), **self._meta,
        )

    def add_route(self, cls_route_function: 'Operation') -> None:
        route_function = copy.deepcopy(cls_route_function)
        self._routes[cls_route_function.name] = route_function

        operation_meta = route_function.get_meta()
        if not operation_meta.route_versioning:
            operation_meta.update(route_versioning=self._version)
        if not operation_meta.route_guards:
            operation_meta.update(route_guards=self._route_guards)

        if isinstance(route_function, Route):
            tags = [self._meta['tag']]
            if operation_meta.tags:
                tags += operation_meta.tags
            operation_meta.update(tags=tags)
        setattr(route_function.endpoint, 'controller_class', self._controller_class)


@t.overload
def controller(
        prefix: t.Optional[str] = None
) -> t.Union[t.Type[ControllerBase], t.Callable[[t.Type], t.Type[ControllerBase]]]:  # pragma: no cover
    ...


@t.overload
def controller(
        prefix: t.Optional[str] = None,
        *,
        tag: t.Optional[str] = None,
        description: t.Optional[str] = None,
        external_doc_description: t.Optional[str] = None,
        external_doc_url: t.Optional[str] = None,
        name: t.Optional[str] = None,
        version: t.Union[t.List[str], str] = (),
        guards: t.Optional[t.List[t.Union[t.Type['GuardCanActivate'], 'GuardCanActivate']]] = None
) -> t.Union[t.Type[ControllerBase], t.Callable[[t.Type], t.Type[ControllerBase]]]:  # pragma: no cover
    ...


def controller(
        prefix: t.Optional[str] = None,
        *,
        tag: t.Optional[str] = None,
        description: t.Optional[str] = None,
        external_doc_description: t.Optional[str] = None,
        external_doc_url: t.Optional[str] = None,
        name: t.Optional[str] = None,
        version: t.Union[t.List[str], str] = (),
        guards: t.Optional[t.List[t.Union[t.Type['GuardCanActivate'], 'GuardCanActivate']]] = None
) -> t.Union[t.Type[ControllerBase], t.Callable[[t.Type], t.Type[ControllerBase]]]:
    if isinstance(prefix, type):
        return _ControllerDecorator("")(prefix)  # type:ignore

    def _decorator(cls: t.Type):
        _controller = _ControllerDecorator(
            prefix=prefix,
            tag=tag,
            description=description,
            external_doc_description=external_doc_description,
            external_doc_url=external_doc_url,
            name=name,
            version=version,
            guards=guards,
        )
        return _controller(cls)

    return _decorator
