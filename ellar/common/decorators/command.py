import typing as t

import click
from typer.core import TyperCommand
from typer.models import CommandFunctionType, CommandInfo

from ellar.constants import CALLABLE_COMMAND_INFO


@t.no_type_check
def command(
    name: t.Optional[str] = None,
    cls: t.Optional[t.Type[click.Command]] = None,
    context_settings: t.Optional[t.Dict[t.Any, t.Any]] = None,
    help: t.Optional[str] = None,
    epilog: t.Optional[str] = None,
    short_help: t.Optional[str] = None,
    options_metavar: str = "[OPTIONS]",
    add_help_option: bool = True,
    no_args_is_help: bool = False,
    hidden: bool = False,
    deprecated: bool = False,
) -> t.Callable[[CommandFunctionType], CommandFunctionType]:
    """
    ========= FUNCTION DECORATOR ==============

    Define Application Command which will be available on ellar cli
    """
    if cls is None:
        cls = TyperCommand

    def decorator(f: CommandFunctionType) -> CommandFunctionType:
        command_info = CommandInfo(
            name=name,
            cls=t.cast(t.Type[click.Command], cls),
            context_settings=context_settings,
            callback=f,
            help=help,
            epilog=epilog,
            short_help=short_help,
            options_metavar=options_metavar,
            add_help_option=add_help_option,
            no_args_is_help=no_args_is_help,
            hidden=hidden,
            deprecated=deprecated,
        )
        setattr(f, CALLABLE_COMMAND_INFO, command_info)
        return f

    return decorator
