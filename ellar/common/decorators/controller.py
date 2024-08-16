import typing as t

from ellar.common.compatible import AttributeDict
from ellar.common.constants import (
    CONTROLLER_METADATA,
    CONTROLLER_WATERMARK,
    NOT_SET,
)
from ellar.common.exceptions import ImproperConfiguration
from ellar.common.models import ControllerBase, ControllerType
from ellar.di import RequestORTransientScope, injectable
from ellar.reflect import reflect, transfer_metadata
from injector import Scope
from starlette.middleware import Middleware

if t.TYPE_CHECKING:
    from ellar.core.middleware.middleware import EllarMiddleware


@t.no_type_check
def Controller(
    prefix: t.Optional[str] = None,
    *,
    name: t.Optional[str] = None,
    include_in_schema: bool = True,
    middleware: t.Optional[t.Sequence[t.Union[Middleware, "EllarMiddleware"]]] = None,
    scope: t.Optional[t.Union[t.Type[Scope], Scope]] = RequestORTransientScope,
) -> t.Union[t.Type[ControllerBase], t.Callable[..., t.Any], t.Any]:
    """
    ========= CLASS DECORATOR ==============

    Controller Class Decorator
    :param prefix: Route Prefix default=[ControllerName]
    :param name: route name prefix for url reversing, eg name:route_name default=''
    :param include_in_schema: include controller in OPENAPI schema
    :param scope: Controller Instance Lifetime scope
    :param middleware: Controller Middlewares
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
        processed=False,
        middleware=middleware,
    )

    def _decorator(cls: t.Type) -> t.Type[ControllerBase]:
        if not isinstance(cls, type):
            raise ImproperConfiguration(f"Controller is a class decorator - {cls}")

        _controller_type = t.cast(t.Type[ControllerBase], cls)
        new_cls = None

        if type(cls) is not ControllerType:
            # We force the cls to inherit from `ControllerBase` by creating another type.
            attrs = {}
            new_cls = type(cls.__name__, (cls, ControllerBase), attrs)

            transfer_metadata(cls, new_cls)
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

        reflect.define_metadata(CONTROLLER_WATERMARK, True, _controller_type)
        # reflect_all_controller_type_routes(_controller_type)

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
