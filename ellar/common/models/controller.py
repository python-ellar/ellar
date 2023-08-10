import typing as t

from ..interfaces import IExecutionContext


class ControllerType(type):
    _controller_name: t.Optional[str]

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
    context: t.Optional[IExecutionContext] = None

    @t.no_type_check
    def __init_subclass__(cls, controller_name: str = None) -> None:
        cls._controller_name = controller_name
