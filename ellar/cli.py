from typer import Typer, echo

_typer = Typer()


@_typer.command()
def init(name: str):
    echo(f"Welcome {name} to Ellar CLI, python web framework")


def main():
    _typer(prog_name="Ellar, Python Web framework")


if __name__ == "__main__":
    main()
