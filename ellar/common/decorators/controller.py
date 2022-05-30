import inspect
import typing as t
from abc import ABC

from ellar.compatible import AttributeDict
from ellar.constants import (
    CONTROLLER_CLASS_KEY,
    CONTROLLER_WATERMARK,
    NOT_SET,
    OPERATION_ENDPOINT_KEY,
    OPERATION_HANDLER_KEY,
    Controller_METADATA,
)
from ellar.core import ControllerBase
from ellar.core.controller import ControllerType
from ellar.exceptions import ImproperConfiguration
from ellar.reflect import reflect

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.guard import GuardCanActivate


def get_route_functions(cls: t.Type) -> t.Iterable[t.Callable]:
    for method in cls.__dict__.values():
        if hasattr(method, OPERATION_ENDPOINT_KEY):
            yield method


@t.overload
def Controller(
    prefix: t.Optional[str] = None,
) -> t.Type[ControllerBase]:  # pragma: no cover
    ...


@t.overload
def Controller(
    prefix: t.Optional[str] = None,
    *,
    tag: t.Optional[str] = None,
    description: t.Optional[str] = None,
    external_doc_description: t.Optional[str] = None,
    external_doc_url: t.Optional[str] = None,
    name: t.Optional[str] = None,
    version: t.Union[t.Tuple, str] = (),
    guards: t.Optional[
        t.List[t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]]
    ] = None,
    include_in_schema: bool = True,
) -> t.Type[ControllerBase]:  # pragma: no cover
    ...


def Controller(
    prefix: t.Optional[str] = None,
    *,
    tag: t.Optional[str] = None,
    description: t.Optional[str] = None,
    external_doc_description: t.Optional[str] = None,
    external_doc_url: t.Optional[str] = None,
    name: t.Optional[str] = None,
    version: t.Union[t.Tuple, str] = (),
    guards: t.Optional[
        t.List[t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]]
    ] = None,
    include_in_schema: bool = True,
) -> t.Union[t.Type[ControllerBase], t.Callable]:
    _prefix: t.Optional[t.Any] = prefix or NOT_SET
    if prefix and isinstance(prefix, type):
        _prefix = NOT_SET

    if _prefix is not NOT_SET:
        assert _prefix == "" or str(_prefix).startswith(
            "/"
        ), "Controller Prefix must start with '/'"

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

        if type(cls) is not ControllerType:
            # We force the cls to inherit from `ControllerBase` by creating another type.
            cls = type(cls.__name__, (cls, ControllerBase), {})

        _controller_type = t.cast(t.Type[ControllerBase], cls)

        _tag = _controller_type.controller_class_name()

        if not kwargs.openapi.tag:
            kwargs.openapi.tag = _tag

        if kwargs.path is NOT_SET:
            kwargs.path = f"/{_tag}"

        if not kwargs.name:
            kwargs.name = (
                str(_controller_type.controller_class_name())
                .lower()
                .replace("controller", "")
            )

        reflect.define_metadata(CONTROLLER_WATERMARK, True, _controller_type)
        bases = inspect.getmro(cls)
        for base_cls in reversed(bases):
            if base_cls not in [ABC, ControllerBase, object]:
                for item in get_route_functions(base_cls):
                    operation = reflect.get_metadata(OPERATION_HANDLER_KEY, item)
                    reflect.define_metadata(
                        CONTROLLER_CLASS_KEY, _controller_type, item
                    )
                    reflect.define_metadata(
                        OPERATION_HANDLER_KEY, operation, _controller_type
                    )

        for key in Controller_METADATA.keys:
            reflect.define_metadata(key, kwargs[key], _controller_type)

        return _controller_type

    if callable(prefix):
        return _decorator(prefix)
    return _decorator
