import typing as t

import click
from typer import Typer
from typer.models import Default


class EllarTyper(Typer):
    """
    Creates a CLI command group that will be added to ellar cli commands
    Example:
    ---------

    ```python
    db = EllarTyper(name="db")

    @db.commands
    def create_database(ctx):
        # creates database

    @db.commands
    def run_migration(ctx):
        # run database migration


    @Module(commands=[db])
    class ApplicationModule(ModuleBase):
        pass
    ```
    """

    @t.no_type_check
    def __init__(
        self,
        name: str,
        *,
        cls: t.Optional[t.Type[click.Command]] = Default(None),
        invoke_without_command: bool = Default(False),
        no_args_is_help: bool = Default(False),
        subcommand_metavar: t.Optional[str] = Default(None),
        chain: bool = Default(False),
        result_callback: t.Optional[t.Callable[..., t.Any]] = Default(None),
        # Command
        context_settings: t.Optional[t.Dict[t.Any, t.Any]] = Default(None),
        callback: t.Optional[t.Callable[..., t.Any]] = Default(None),
        help: t.Optional[str] = Default(None),
        epilog: t.Optional[str] = Default(None),
        short_help: t.Optional[str] = Default(None),
        options_metavar: str = Default("[OPTIONS]"),
        add_help_option: bool = Default(True),
        hidden: bool = Default(False),
        deprecated: bool = Default(False),
        add_completion: bool = True,
    ) -> None:  # pragma: no cover
        assert name is not None and name != "", "Typer name is required"
        super().__init__(
            name=name,
            cls=cls,
            invoke_without_command=invoke_without_command,
            no_args_is_help=no_args_is_help,
            subcommand_metavar=subcommand_metavar,
            chain=chain,
            result_callback=result_callback,
            context_settings=context_settings,
            callback=callback,
            help=help,
            epilog=epilog,
            short_help=short_help,
            options_metavar=options_metavar,
            add_help_option=add_help_option,
            hidden=hidden,
            deprecated=deprecated,
            add_completion=add_completion,
        )
