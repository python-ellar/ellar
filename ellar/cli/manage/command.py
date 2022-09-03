import typer

from ellar.commands import EllarTyper

from .create_module import create_module
from .create_project import create_project
from .runserver import runserver

__all__ = ["manage_commands"]


manage_commands = EllarTyper(name="manage")


@manage_commands.callback()
def manage_command_callback(ctx: typer.Context):
    """- Ellar Management commands -"""


manage_commands.command()(runserver)
manage_commands.command(name="create-project")(create_project)
manage_commands.command(name="create-module")(create_module)
