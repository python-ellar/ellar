import os
import sys
import typing as t

import typer
from typer import Typer, echo
from typer.models import CommandInfo

from ellar.commands import EllarTyper
from ellar.constants import CALLABLE_COMMAND_INFO, ELLAR_CONFIG_MODULE, MODULE_METADATA
from ellar.core.factory import AppFactory
from ellar.helper.importer import import_from_string
from ellar.services import Reflector

from .manage import manage_commands
from .manage.utils import get_project_module, import_project_module

__all__ = ["main"]

_typer = Typer(name="ellar")
APPLICATION_STRING_IMPORT_FORMAT = "{setting_module}:APPLICATION_MODULE"


def register_commands(*typer_commands: t.Any) -> None:
    for typer_command in typer_commands:
        _typer.add_typer(typer_command)


def build_typers() -> None:
    dir_basename = get_project_module(os.getcwd())
    if dir_basename:
        import_project_module("exports")
        setting_module = os.environ.get(ELLAR_CONFIG_MODULE)
        if setting_module:

            application_module_settings_import_string = (
                APPLICATION_STRING_IMPORT_FORMAT.format(setting_module=setting_module)
            )
            application_module_import_string = import_from_string(
                application_module_settings_import_string
            )
            application_module = import_from_string(application_module_import_string)
            modules = AppFactory.read_all_module(application_module)

            reflector = Reflector()
            for module in modules.keys():
                typers_commands = reflector.get(MODULE_METADATA.COMMANDS, module) or []
                for typer_command in typers_commands:
                    if isinstance(typer_command, EllarTyper):
                        _typer.add_typer(typer_command)
                    elif hasattr(typer_command, CALLABLE_COMMAND_INFO):
                        command_info: CommandInfo = typer_command.__dict__[
                            CALLABLE_COMMAND_INFO
                        ]
                        _typer.registered_commands.append(command_info)


@_typer.command()
def say_hi(name: str):
    echo(f"Welcome {name}, to Ellar CLI, python web framework")


@_typer.callback()
def root_cli_callback(ctx: typer.Context):
    # TODO: Add some necessary reusable information to `ctx.meta`
    pass


# register all EllarTyper(s) to root typer
register_commands(manage_commands)


def main():
    sys.path.append(os.getcwd())
    build_typers()
    _typer(prog_name="Ellar, Python Web framework")


if __name__ == "__main__":
    main()
