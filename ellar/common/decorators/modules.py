import inspect
import typing as t
from functools import partial
from pathlib import Path

from starlette.routing import Host, Mount

from ellar.compatible import AttributeDict
from ellar.constants import MODULE_METADATA, MODULE_WATERMARK
from ellar.core import ControllerBase
from ellar.core.modules.base import ModuleBase, ModuleBaseMeta
from ellar.core.routing import ModuleMount, ModuleRouter
from ellar.di import ProviderConfig, SingletonScope, injectable
from ellar.exceptions import ImproperConfiguration
from ellar.reflect import reflect


def _wrapper(
    target: t.Type,
    watermark_key: str,
    metadata_keys: t.List[str],
    name: str,
    kwargs: AttributeDict,
) -> t.Type:
    if reflect.get_metadata(watermark_key, target):
        raise ImproperConfiguration(f"{target} is already identified as a Module")

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
    injectable(SingletonScope)(target)
    return t.cast(t.Type, target)


def Module(
    *,
    name: t.Optional[str] = None,
    controllers: t.Sequence[t.Union[t.Type[ControllerBase], t.Type]] = tuple(),
    routers: t.Sequence[t.Union[ModuleRouter, ModuleMount, Mount, Host]] = tuple(),
    providers: t.Sequence[t.Union[t.Type, ProviderConfig]] = tuple(),
    template_folder: t.Optional[str] = "templates",
    base_directory: t.Optional[t.Union[Path, str]] = None,
    static_folder: str = "static",
    modules: t.Sequence[t.Type] = tuple(),
) -> t.Callable:
    kwargs = AttributeDict(
        name=name,
        controllers=controllers,
        base_directory=base_directory,
        static_folder=static_folder,
        routers=routers,
        providers=providers,
        template_folder=template_folder,
        modules=modules,
    )

    return partial(
        _wrapper,
        metadata_keys=MODULE_METADATA.keys,
        watermark_key=MODULE_WATERMARK,
        kwargs=kwargs,
        name="Module",
    )
