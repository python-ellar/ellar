import typing as t

from ellar.core.context import ExecutionContext

if t.TYPE_CHECKING:
    from ellar.core.routing.base import RouteOperationBase
    from ellar.core.routing.controller.decorator import ControllerDecorator


class MissingAPIControllerDecoratorException(Exception):
    pass


def get_route_functions(cls: t.Type) -> t.Iterable["RouteOperationBase"]:
    from ellar.core.routing.base import RouteOperationBase

    for method in cls.__dict__.values():
        if isinstance(method, RouteOperationBase):
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
