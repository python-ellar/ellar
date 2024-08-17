import inspect
import typing as t
from abc import abstractmethod

from ellar.common.constants import NOT_SET
from ellar.core.routing.mount import EllarControllerMount
from starlette.routing import BaseRoute, Host, Mount

_router_builder_factory: t.Dict[t.Type, t.Type["RouterBuilder"]] = {}


def _register_controller_builder(
    controller_type: t.Type, factory: t.Type["RouterBuilder"]
) -> None:
    _router_builder_factory[controller_type] = factory


def get_controller_builder_factory(
    controller_type: t.Union[t.Type, t.Any] = NOT_SET,
) -> t.Type["RouterBuilder"]:
    res = _router_builder_factory.get(controller_type)
    if not res:
        return _DefaultRouterBuilder
    return res


class RouterBuilder:
    """
    A factory class that validates and converts a Controllers or ModuleRouter to Starlette Mount or EllarControllerMount.
    """

    @classmethod
    @abstractmethod
    def build(
        cls, controller_type: t.Union[t.Type, t.Any], **kwargs: t.Any
    ) -> t.Union["EllarControllerMount", Mount]:
        """Build controller to Mount"""

    @classmethod
    @abstractmethod
    def check_type(cls, controller_type: t.Union[t.Type, t.Any]) -> None:
        """Check controller type"""

    def __init_subclass__(cls, **kwargs: t.Any) -> None:
        controller_type = kwargs.get("controller_type")
        assert controller_type, "Controller type is required"
        _register_controller_builder(controller_type, cls)


class _DefaultRouterBuilder(RouterBuilder, controller_type=Mount):
    @classmethod
    def check_type(cls, controller_type: t.Union[t.Type, t.Any]) -> None:
        """Do nothing"""

    @classmethod
    def build(
        cls, controller_type: t.Union[t.Type, t.Any], **kwargs: t.Any
    ) -> t.Union["EllarControllerMount", Mount, t.Any]:
        """Build controller to Mount"""
        from ellar.core.router_builders.utils import build_route_handler

        if inspect.isfunction(controller_type):
            operations: t.Any = build_route_handler(controller_type)

            for op in operations or []:
                if not isinstance(op, BaseRoute):
                    raise Exception(f"Unable to build function - {controller_type}")
            return operations

        return controller_type


_register_controller_builder(Host, _DefaultRouterBuilder)
_register_controller_builder(EllarControllerMount, _DefaultRouterBuilder)
_register_controller_builder(NOT_SET, _DefaultRouterBuilder)
