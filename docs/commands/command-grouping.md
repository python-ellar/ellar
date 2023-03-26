
Ella CLI provides a way by which commands can be grouped.

For instance, a `db` command may have sub-commands like `makemigrations`, `migrate`, `reset-db` etc.

To achieve this use-case, let us create a file `commands.py` in the root level of the project.

```python
from ellar.commands import EllarTyper

db = EllarTyper(name="db")


@db.command(name="make-migrations")
def makemigrations():
    """Create DB Migration """

@db.command()
def migrate():
    """Applies Migrations"""
```

## Register EllarTyper Command

Lets, make the `db` visible on the CLI.

In other for Ellar CLI to identify custom command, its has to be registered to a `@Module` class.

```python
from ellar.common import Module
from ellar.core import ModuleBase
from .commands import db

@Module(commands=[db])
class ApplicationModule(ModuleBase):
    pass
```

open your terminal and navigate to project directory and run the command below
```shell
ellar db --help
```

command output
```shell
Usage: Ellar, Python Web framework db [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  make-migrations  Create DB Migration
  migrate          Applies Migrations

```
