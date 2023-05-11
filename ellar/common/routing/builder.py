import typing as t

from starlette.routing import Mount

if t.TYPE_CHECKING:  # pragma: no cover
    from .mount import ModuleMount

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
        raise Exception(
            f"Router Factory Builder was not found.\nUse `ControllerRouterBuilderFactory` "
            f"as an example create a FactoryBuilder for this type: {controller_type}"
        )
    return res


class RouterBuilder:
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
