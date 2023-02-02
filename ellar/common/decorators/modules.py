import inspect
import typing as t
from functools import partial
from pathlib import Path

from starlette.routing import Host, Mount

from ellar.compatible import AttributeDict
from ellar.constants import MODULE_METADATA, MODULE_WATERMARK
from ellar.core import ControllerBase
from ellar.core.exceptions import ImproperConfiguration
from ellar.core.modules.base import ModuleBase, ModuleBaseMeta
from ellar.core.routing import ModuleMount, ModuleRouter
from ellar.di import ProviderConfig, SingletonScope, injectable
from ellar.reflect import reflect

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.commands import EllarTyper


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
    commands: t.Sequence[t.Union[t.Callable, "EllarTyper"]] = tuple(),
) -> t.Callable:
    """
    ========= MODULE DECORATOR ==============

    Defines a class as Module

    :param name: Module name

    :param controllers: List of Module Controllers

    :param routers: List of Module [ModuleRouters, Host, Mount, Router]

    :param providers: List of Module Services or `ProviderConfig`

    :param template_folder: Module template folder name

    :param base_directory: Module base_directory for template folder and static files

    :param static_folder: Module static folder name

    :param modules: List of Module Types - t.Type[MODULEBASE]

    :param commands: List of Command Decorated functions and EllarTyper

    :return: t.TYPE[MODULEBASE]
    """
    kwargs = AttributeDict(
        name=name,
        controllers=list(controllers),
        base_directory=base_directory,
        static_folder=static_folder,
        routers=list(routers),
        providers=list(providers),
        template_folder=template_folder,
        modules=list(modules),
        commands=list(commands),
    )

    return partial(
        _wrapper,
        metadata_keys=MODULE_METADATA.keys,
        watermark_key=MODULE_WATERMARK,
        kwargs=kwargs,
        name="Module",
    )
