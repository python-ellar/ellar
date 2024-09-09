import inspect
import typing as t
import uuid
from pathlib import Path

from ellar.common.compatible import AttributeDict
from ellar.common.constants import MODULE_METADATA, MODULE_WATERMARK
from ellar.common.exceptions import ImproperConfiguration
from ellar.common.models import ControllerBase
from ellar.common.operations import ModuleRouter
from ellar.di import ProviderConfig, SingletonScope, injectable
from ellar.reflect import reflect
from ellar.utils import get_name
from ellar.utils.importer import get_main_directory_by_stack
from starlette.routing import Host, Mount

if t.TYPE_CHECKING:
    import click

_ModuleClass = t.TypeVar("_ModuleClass", bound=t.Type)


def _wrapper(
    target: _ModuleClass,
    watermark_key: str,
    metadata_keys: t.List[str],
    name: str,
    kwargs: AttributeDict,
) -> _ModuleClass:
    if reflect.get_metadata(watermark_key, target):
        raise ImproperConfiguration(f"{target} is already identified as a Module")

    if not isinstance(target, type):
        raise ImproperConfiguration(f"{name} is a class decorator - {target}")

    if not kwargs.base_directory and not reflect.get_metadata(
        MODULE_METADATA.BASE_DIRECTORY, target
    ):
        kwargs.update(base_directory=Path(inspect.getfile(target)).resolve().parent)

    if not kwargs.name and not reflect.get_metadata(MODULE_METADATA.NAME, target):
        kwargs.name = f"{get_name(target)}{uuid.uuid4().hex[:10]}"

    reflect.define_metadata(watermark_key, True, target)

    for key in metadata_keys:
        if not reflect.get_metadata(key, target) or kwargs[key] is not None:
            reflect.define_metadata(key, kwargs[key], target)

    injectable(SingletonScope)(target)
    return target


def Module(
    *,
    name: t.Optional[str] = None,
    controllers: t.Sequence[t.Union[t.Type[ControllerBase], t.Type]] = (),
    routers: t.Sequence[t.Union[ModuleRouter, Mount, Host, t.Callable]] = (),
    providers: t.Sequence[t.Union[t.Type, "ProviderConfig"]] = (),
    exports: t.Sequence[t.Union[t.Type]] = (),
    template_folder: t.Optional[str] = "templates",
    base_directory: t.Optional[t.Union[Path, str]] = None,
    static_folder: str = "static",
    modules: t.Sequence[t.Union[t.Type, t.Any]] = (),
    commands: t.Sequence[t.Union["click.Command", "click.Group", t.Any]] = (),
) -> t.Callable[[_ModuleClass], _ModuleClass]:
    """
    ========= MODULE DECORATOR ==============

    Defines a class as Module

    :param name: Module name

    :param controllers: List of Module Controllers

    :param routers: List of Module [ModuleRouters, Host, Mount, Router]

    :param providers: List of Module Services or `ProviderConfig`

    :param exports: List of Module Providers that are exposed to the other modules

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
        exports=list(exports),
        template_folder=template_folder,
        modules=list(modules),
        commands=list(commands),
    )

    def _decorator(klass: _ModuleClass) -> _ModuleClass:
        return _wrapper(
            target=klass,
            metadata_keys=MODULE_METADATA.keys,
            watermark_key=MODULE_WATERMARK,
            kwargs=kwargs,
            name="Module",
        )

    return _decorator
