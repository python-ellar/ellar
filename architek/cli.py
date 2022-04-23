from typer import Typer, echo

app = Typer()


@app.command()
def init(name: str):
    echo(f"Welcome {name} to Architek, python web framework")


def main():
    app(prog_name="Architek Python Web framework")


if __name__ == "__main__":
    main()
