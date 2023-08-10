import typing as t
from abc import abstractmethod

from ellar.common.logger import logger
from starlette.routing import Host, Mount

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.common.routing.mount import ModuleMount

_router_builder_factory: t.Dict[t.Type, t.Type["RouterBuilder"]] = {}


def _register_controller_builder(
    controller_type: t.Type, factory: t.Type["RouterBuilder"]
) -> None:
    _router_builder_factory[controller_type] = factory


def get_controller_builder_factory(
    controller_type: t.Type,
) -> t.Type["RouterBuilder"]:
    res = _router_builder_factory.get(controller_type)
    if not res:
        logger.warning(
            f"Router Factory Builder was not found.\nUse `ControllerRouterBuilderFactory` "
            f"as an example create a FactoryBuilder for this type: {controller_type}"
        )
        return _DefaultRouterBuilder
    return res


class RouterBuilder:
    @classmethod
    @abstractmethod
    def build(
        cls, controller_type: t.Union[t.Type, t.Any], **kwargs: t.Any
    ) -> t.Union["ModuleMount", Mount]:
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
    ) -> t.Union["ModuleMount", Mount, t.Any]:
        """Build controller to Mount"""
        return controller_type


_register_controller_builder(Host, _DefaultRouterBuilder)
