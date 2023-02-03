import inspect
import typing as t
from abc import ABC
from types import FunctionType

from ellar.compatible import AttributeDict
from ellar.constants import (
    CONTROLLER_CLASS_KEY,
    CONTROLLER_METADATA,
    CONTROLLER_OPERATION_HANDLER_KEY,
    CONTROLLER_WATERMARK,
    GUARDS_KEY,
    NOT_SET,
    OPERATION_ENDPOINT_KEY,
    REFLECT_TYPE,
    VERSIONING_KEY,
)
from ellar.core import ControllerBase
from ellar.core.controller import ControllerType
from ellar.core.exceptions import ImproperConfiguration
from ellar.core.routing.controller import ControllerRouteOperationBase
from ellar.di import RequestScope, injectable
from ellar.reflect import reflect

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.guard import GuardCanActivate


def get_route_functions(
    cls: t.Type,
) -> t.Iterable[t.Union[t.Callable, ControllerRouteOperationBase]]:
    for method in cls.__dict__.values():
        if hasattr(method, OPERATION_ENDPOINT_KEY) or isinstance(
            method, ControllerRouteOperationBase
        ):
            yield method


def reflect_all_controller_type_routes(cls: t.Type[ControllerBase]) -> None:
    bases = inspect.getmro(cls)

    for base_cls in reversed(bases):
        if base_cls not in [ABC, ControllerBase, object]:
            for item in get_route_functions(base_cls):
                operation = item
                if callable(item) and type(item) == FunctionType:
                    operation = reflect.get_metadata(  # type: ignore
                        CONTROLLER_OPERATION_HANDLER_KEY, item
                    )
                endpoint_func = operation.endpoint  # type:ignore
                if reflect.has_metadata(CONTROLLER_CLASS_KEY, endpoint_func):
                    raise Exception(
                        f"{cls.__name__} Controller route tried to be processed more than once."
                        f"\n-RouteFunction - {endpoint_func}."
                        f"\n-Controller route function can not be reused once its under a `@Controller` decorator."
                    )

                reflect.define_metadata(CONTROLLER_CLASS_KEY, cls, endpoint_func)
                reflect.define_metadata(
                    CONTROLLER_OPERATION_HANDLER_KEY,
                    [operation],
                    cls,
                )


@t.overload
def Controller(
    prefix: t.Optional[str] = None,
) -> t.Union[t.Type[ControllerBase], t.Callable[..., t.Any], t.Any]:  # pragma: no cover
    ...


@t.overload
def Controller(
    prefix: t.Optional[str] = None,
    *,
    tag: str = NOT_SET,
    description: str = None,
    external_doc_description: str = None,
    external_doc_url: str = None,
    name: str = None,
    version: t.Union[t.Tuple, str] = (),
    guards: t.List[t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]] = None,
    include_in_schema: bool = True,
) -> t.Union[t.Type[ControllerBase], t.Callable[..., t.Any], t.Any]:  # pragma: no cover
    """
    ========= CLASS DECORATOR ==============

    Controller Class Decorator
    :param prefix: Route Prefix default=[ControllerName]
    :param tag: OPENAPI tag
    :param description: OPENAPI description
    :param external_doc_description: OPENAPI External Doc Description
    :param external_doc_url: OPENAPI External Document URL
    :param name: route name prefix for url reversing, eg name:route_name default=''
    :param version: default URL versioning for all defined route in a controller
    :param guards: default guard for all routes defined under this controller
    :param include_in_schema: include controller in OPENAPI schema
    :return: t.Type[ControllerBase]
    """
    ...


def Controller(
    prefix: t.Optional[str] = None,
    *,
    tag: str = NOT_SET,
    description: str = None,
    external_doc_description: str = None,
    external_doc_url: str = None,
    name: str = None,
    version: t.Union[t.Tuple, str] = (),
    guards: t.List[t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]] = None,
    include_in_schema: bool = True,
) -> t.Union[t.Type[ControllerBase], t.Callable[..., t.Any], t.Any]:
    """
    Controller Class Decorator
    :param prefix: Route Prefix default=[ControllerName]
    :param tag: OPENAPI tag
    :param description: OPENAPI description
    :param external_doc_description: OPENAPI External Doc Description
    :param external_doc_url: OPENAPI External Document URL
    :param name: route name prefix for url reversing, eg name:route_name default=controller_name
    :param version: default URL versioning for all defined route in a controller
    :param guards: default guard for all routes defined under this controller
    :param include_in_schema: include controller in OPENAPI schema
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
        openapi=AttributeDict(
            tag=tag,
            description=description,
            external_doc_description=external_doc_description,
            external_doc_url=external_doc_url,
        ),
        path=_prefix,
        name=name,
        version=set([version] if isinstance(version, str) else version),
        guards=guards or [],
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

        if not kwargs.openapi.tag:  # type: ignore
            kwargs["openapi"]["tag"] = _tag  # type: ignore

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
            injectable(RequestScope)(cls)

            for key in CONTROLLER_METADATA.keys:
                reflect.define_metadata(key, kwargs[key], _controller_type)

            reflect.define_metadata(VERSIONING_KEY, kwargs.version, _controller_type)
            reflect.define_metadata(GUARDS_KEY, kwargs.guards, _controller_type)

        if new_cls:
            # if we forced cls to inherit from ControllerBase, we need to block it from been processed
            setattr(cls, "__CONTROLLER_WATERMARK__", True)

        return _controller_type

    if callable(prefix):
        return _decorator(prefix)
    return _decorator
