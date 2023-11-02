import inspect
import typing as t
from abc import ABC

from ellar.common.compatible import AttributeDict
from ellar.common.constants import (
    CONTROLLER_CLASS_KEY,
    CONTROLLER_METADATA,
    CONTROLLER_OPERATION_HANDLER_KEY,
    CONTROLLER_WATERMARK,
    NOT_SET,
    OPERATION_ENDPOINT_KEY,
    ROUTE_OPERATION_PARAMETERS,
)
from ellar.common.exceptions import ImproperConfiguration
from ellar.common.logger import logger
from ellar.common.models import ControllerBase, ControllerType
from ellar.di import RequestORTransientScope, injectable
from ellar.reflect import REFLECT_TYPE, reflect
from injector import Scope

from ..routing.controller import (
    ControllerRouteOperation,
    ControllerWebsocketRouteOperation,
)
from ..routing.schema import RouteParameters, WsRouteParameters


def get_route_functions(
    cls: t.Type,
) -> t.Iterable[t.Callable]:
    for method in cls.__dict__.values():
        if hasattr(method, OPERATION_ENDPOINT_KEY):
            yield method


def reflect_all_controller_type_routes(cls: t.Type[ControllerBase]) -> None:
    bases = inspect.getmro(cls)

    for base_cls in reversed(bases):
        if base_cls not in [ABC, ControllerBase, object]:
            for item in get_route_functions(base_cls):
                if reflect.has_metadata(CONTROLLER_CLASS_KEY, item):
                    raise Exception(
                        f"{cls.__name__} Controller route tried to be processed more than once."
                        f"\n-RouteFunction - {item}."
                        f"\n-Controller route function can not be reused once its under a `@Controller` decorator."
                    )
                reflect.define_metadata(CONTROLLER_CLASS_KEY, cls, item)

                parameter = item.__dict__[ROUTE_OPERATION_PARAMETERS]
                operation: t.Union[
                    ControllerRouteOperation, ControllerWebsocketRouteOperation
                ]
                if isinstance(parameter, RouteParameters):
                    operation = ControllerRouteOperation(**parameter.dict())
                elif isinstance(parameter, WsRouteParameters):
                    operation = ControllerWebsocketRouteOperation(**parameter.dict())
                else:  # pragma: no cover
                    logger.warning(
                        f"Parameter type is not recognized. {type(parameter) if not isinstance(parameter, type) else parameter}"
                    )
                    continue

                del item.__dict__[ROUTE_OPERATION_PARAMETERS]

                reflect.define_metadata(
                    CONTROLLER_OPERATION_HANDLER_KEY,
                    [operation],
                    cls,
                )


@t.no_type_check
def Controller(
    prefix: t.Optional[str] = None,
    *,
    name: t.Optional[str] = None,
    include_in_schema: bool = True,
    scope: t.Optional[t.Union[t.Type[Scope], Scope]] = RequestORTransientScope,
) -> t.Union[t.Type[ControllerBase], t.Callable[..., t.Any], t.Any]:
    """
    ========= CLASS DECORATOR ==============

    Controller Class Decorator
    :param prefix: Route Prefix default=[ControllerName]
    :param name: route name prefix for url reversing, eg name:route_name default=''
    :param include_in_schema: include controller in OPENAPI schema
    :param scope: Controller Instance Lifetime scope
    :return: t.Type[ControllerBase]
    """
    _prefix: t.Optional[t.Any] = prefix if prefix is not None else NOT_SET
    if prefix and isinstance(prefix, type):
        _prefix = NOT_SET

    if _prefix is not NOT_SET:
        assert _prefix == "" or str(_prefix).startswith(
            "/"
        ), "Controller Prefix must start with '/'"
    # TODO: replace with a ControllerTypeDict and OpenAPITypeDict
    kwargs = AttributeDict(
        path=_prefix,
        name=name,
        include_in_schema=include_in_schema,
    )

    def _decorator(cls: t.Type) -> t.Type[ControllerBase]:
        if not isinstance(cls, type):
            raise ImproperConfiguration(f"Controller is a class decorator - {cls}")

        _controller_type = t.cast(t.Type[ControllerBase], cls)
        new_cls = None

        if type(cls) is not ControllerType:
            # We force the cls to inherit from `ControllerBase` by creating another type.
            attrs = {}
            if hasattr(cls, REFLECT_TYPE):
                attrs.update({REFLECT_TYPE: cls.__dict__[REFLECT_TYPE]})
            new_cls = type(cls.__name__, (cls, ControllerBase), attrs)

            _controller_type = t.cast(t.Type[ControllerBase], new_cls)

        _tag = _controller_type.controller_class_name()

        if kwargs["path"] is NOT_SET:
            kwargs["path"] = f"/{_tag}"

        if not kwargs["name"]:
            kwargs["name"] = (
                str(_controller_type.controller_class_name())
                .lower()
                .replace("controller", "")
            )

        if not reflect.has_metadata(
            CONTROLLER_WATERMARK, _controller_type
        ) and not hasattr(cls, "__CONTROLLER_WATERMARK__"):
            reflect.define_metadata(CONTROLLER_WATERMARK, True, _controller_type)
            reflect_all_controller_type_routes(_controller_type)

            injectable(scope or RequestORTransientScope)(cls)

            for key in CONTROLLER_METADATA.keys:
                reflect.define_metadata(key, kwargs[key], _controller_type)

        if new_cls:
            # if we forced cls to inherit from ControllerBase, we need to block it from been processed
            cls.__CONTROLLER_WATERMARK__ = True

        return _controller_type

    if callable(prefix):
        return _decorator(prefix)
    return _decorator
