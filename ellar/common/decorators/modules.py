import inspect
import typing as t
from functools import partial
from pathlib import Path

from starlette.routing import Mount

from ellar.compatible import AttributeDict
from ellar.constants import (
    APP_MODULE_METADATA,
    APP_MODULE_WATERMARK,
    MODULE_METADATA,
    MODULE_WATERMARK,
)
from ellar.core import ControllerBase
from ellar.core.modules.base import ModuleBase, ModuleBaseMeta
from ellar.core.routing import ModuleRouter
from ellar.di import ProviderConfig
from ellar.exceptions import ImproperConfiguration
from ellar.reflect import reflect


def _wrapper(
    target: t.Type,
    watermark_key: str,
    metadata_keys: t.List[str],
    name: str,
    kwargs: AttributeDict,
) -> t.Type:
    if not isinstance(target, type):
        raise ImproperConfiguration(f"{name} is a class decorator - {target}")

    if not kwargs.base_directory:
        kwargs.update(base_directory=Path(inspect.getfile(target)).resolve().parent)

    if type(target) != ModuleBaseMeta:
        attr: t.Dict = {
            item: getattr(target, item) for item in dir(target) if "__" not in item
        }
        target = type(
            target.__name__,
            (target, ModuleBase),
            attr,
        )

    reflect.define_metadata(watermark_key, True, target)
    for key in metadata_keys:
        reflect.define_metadata(key, kwargs[key], target)
    return target


def Module(
    *,
    name: t.Optional[str] = None,
    controllers: t.Sequence[t.Union[t.Type[ControllerBase], t.Type]] = tuple(),
    routers: t.Sequence[t.Union[ModuleRouter, Mount]] = tuple(),
    providers: t.Sequence[t.Union[t.Type, ProviderConfig]] = tuple(),
    template_folder: t.Optional[str] = "templates",
    base_directory: t.Optional[t.Union[Path, str]] = None,
    static_folder: str = "static",
) -> t.Callable:
    kwargs = AttributeDict(
        name=name,
        controllers=controllers,
        base_directory=base_directory,
        static_folder=static_folder,
        routers=routers,
        providers=providers,
        template_folder=template_folder,
    )

    return partial(
        _wrapper,
        metadata_keys=MODULE_METADATA.keys,
        watermark_key=MODULE_WATERMARK,
        kwargs=kwargs,
        name="Module",
    )


def ApplicationModule(
    *,
    modules: t.Sequence[t.Type] = tuple(),
    name: t.Optional[str] = None,
    controllers: t.Sequence[t.Union[t.Type, t.Type[ControllerBase]]] = tuple(),
    routers: t.Sequence[t.Union[ModuleRouter, Mount]] = tuple(),
    providers: t.Sequence[t.Union[t.Type, ProviderConfig]] = tuple(),
    template_folder: t.Optional[str] = "templates",
    base_directory: t.Optional[t.Union[Path, str]] = None,
    static_folder: str = "static",
) -> t.Callable:
    kwargs = AttributeDict(
        modules=modules,
        name=name,
        controllers=controllers,
        base_directory=base_directory,
        static_folder=static_folder,
        routers=routers,
        providers=providers,
        template_folder=template_folder,
    )

    return partial(
        _wrapper,
        metadata_keys=APP_MODULE_METADATA.keys,
        watermark_key=APP_MODULE_WATERMARK,
        kwargs=kwargs,
        name="ApplicationModule",
    )
