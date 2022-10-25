import getopt
import sys
import typing as t

import typer
from typer import Typer
from typer.models import CommandInfo

from ellar.commands import EllarTyper
from ellar.constants import CALLABLE_COMMAND_INFO, ELLAR_META, MODULE_METADATA
from ellar.core.factory import AppFactory
from ellar.services import Reflector

from .manage_commands import create_module, create_project, runserver
from .service import EllarCLIService

__all__ = ["build_typers", "_typer", "typer_callback"]

_typer = Typer(name="ellar")

_typer.command()(runserver)
_typer.command(name="create-project")(create_project)
_typer.command(name="create-module")(create_module)


@_typer.callback()
def typer_callback(
    ctx: typer.Context,
    project: t.Optional[str] = typer.Option(
        None,
        "-p",
        "--project",
        show_default=True,
        exists=True,
        help="Run Specific Command on a specific project",
    ),
) -> None:
    meta_: EllarCLIService = EllarCLIService.import_project_meta(project)
    ctx.meta[ELLAR_META] = meta_


def build_typers() -> None:
    try:
        options, args = getopt.getopt(
            sys.argv[1:],
            "p:",
            ["project=", "help"],
        )
        app_name: t.Optional[str] = None

        for k, v in options:
            if k in ["-p", "--project"] and v:
                app_name = v
    except Exception:
        raise typer.Abort()

    meta_: EllarCLIService = EllarCLIService.import_project_meta(app_name)

    if meta_ and meta_.has_meta:
        modules = AppFactory.get_all_modules(meta_.import_root_module())
        reflector = Reflector()

        for module in modules:
            typers_commands = reflector.get(MODULE_METADATA.COMMANDS, module) or []
            for typer_command in typers_commands:
                if isinstance(typer_command, EllarTyper):
                    _typer.add_typer(typer_command)
                elif hasattr(typer_command, CALLABLE_COMMAND_INFO):
                    command_info: CommandInfo = typer_command.__dict__[
                        CALLABLE_COMMAND_INFO
                    ]
                    _typer.registered_commands.append(command_info)
