import os
import sys
import typing as t

from typer import echo

from ._main import _typer, build_typers

__all__ = ["main"]


def register_commands(*typer_commands: t.Any) -> None:
    for typer_command in typer_commands:
        _typer.add_typer(typer_command)


@_typer.command()
def say_hi(name: str):
    echo(f"Welcome {name}, to Ellar CLI, python web framework")


# register all EllarTyper(s) to root typer
# register_commands(*other_commands)


def main():
    sys.path.append(os.getcwd())
    build_typers()
    _typer(prog_name="Ellar, Python Web framework")


if __name__ == "__main__":
    main()
