import typing as t

from starlette.routing import Mount

if t.TYPE_CHECKING:
    from ellar.core.routing import ModuleMount

_controller_build_factory: t.Dict[t.Type, t.Type["ControllerRouterBuilder"]] = {}


def _register_controller_builder(
    controller_type: t.Type, factory: t.Type["ControllerRouterBuilder"]
) -> None:
    _controller_build_factory[controller_type] = factory


def get_controller_builder_factory(
    controller_type: t.Type,
) -> t.Type["ControllerRouterBuilder"]:
    return _controller_build_factory[controller_type]


class ControllerRouterBuilder:
    @classmethod
    def build(
        cls, controller_type: t.Union[t.Type, t.Any]
    ) -> t.Union["ModuleMount", Mount]:
        """Build controller to Mount"""

    @classmethod
    def check_type(cls, controller_type: t.Union[t.Type, t.Any]) -> None:
        """Check controller type"""

    def __init_subclass__(cls, **kwargs: t.Any) -> None:
        controller_type = kwargs.get("controller_type")
        assert controller_type, "Controller type is required"
        _register_controller_builder(controller_type, cls)
