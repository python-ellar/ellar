import typing as t

from click.testing import Result
from typer import Typer
from typer.testing import CliRunner

from ellar.cli._main import _typer, typer_callback


class EllarCliRunner(CliRunner):
    def invoke_command(
        self,
        command: t.Callable,
        args: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        input: t.Optional[t.Union[bytes, t.Text, t.IO[t.Any]]] = None,
        env: t.Optional[t.Mapping[str, str]] = None,
        catch_exceptions: bool = True,
        color: bool = False,
        **extra: t.Any,
    ):
        app: Typer = Typer()
        app.command()(command)
        app.callback()(typer_callback)
        return super().invoke(
            app,
            args=args,
            input=input,
            env=env,
            catch_exceptions=catch_exceptions,
            color=color,
            **extra,
        )

    def invoke_ellar_command(  # type: ignore
        self,
        args: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        input: t.Optional[t.Union[bytes, t.Text, t.IO[t.Any]]] = None,
        env: t.Optional[t.Mapping[str, str]] = None,
        catch_exceptions: bool = True,
        color: bool = False,
        **extra: t.Any,
    ) -> Result:
        return super().invoke(
            _typer,
            args=args,
            input=input,
            env=env,
            catch_exceptions=catch_exceptions,
            color=color,
            **extra,
        )
