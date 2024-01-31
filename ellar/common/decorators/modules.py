import inspect
import typing as t
from functools import partial
from pathlib import Path

import click
from ellar.common.compatible import AttributeDict
from ellar.common.constants import MODULE_METADATA, MODULE_WATERMARK
from ellar.common.exceptions import ImproperConfiguration
from ellar.common.models import ControllerBase
from ellar.common.operations import ModuleRouter
from ellar.di import ProviderConfig, SingletonScope, injectable
from ellar.reflect import reflect
from ellar.utils.importer import get_main_directory_by_stack
from starlette.routing import Host, Mount


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

    reflect.define_metadata(watermark_key, True, target)
    for key in metadata_keys:
        reflect.define_metadata(key, kwargs[key], target)
    injectable(SingletonScope)(target)
    return target


def Module(
    *,
    name: t.Optional[str] = None,
    controllers: t.Sequence[t.Union[t.Type[ControllerBase], t.Type]] = (),
    routers: t.Sequence[t.Union[ModuleRouter, Mount, Host]] = (),
    providers: t.Sequence[t.Union[t.Type, "ProviderConfig"]] = (),
    template_folder: t.Optional[str] = "templates",
    base_directory: t.Optional[t.Union[Path, str]] = None,
    static_folder: str = "static",
    modules: t.Sequence[t.Union[t.Type, t.Any]] = (),
    commands: t.Sequence[t.Union[click.Command, click.Group, t.Any]] = (),
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

    :param modules: List of Module Types - t.Type[ModuleBase]

    :param commands: List of Command Decorated functions and EllarTyper

    :return: t.TYPE[ModuleBase]
    """
    base_directory = get_main_directory_by_stack(base_directory, stack_level=2)  # type:ignore[arg-type]
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
