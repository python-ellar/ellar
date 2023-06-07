In this section, we are going to go over how to create a custom command and throw more light on how Ella CLI works.

## Create Custom Command
Let's create a file called `commands.py` at the root level of the project.

```python
# project_name/commands.py

from ellar.common import command

@command
def my_new_command():
    """my_new_command cli description """
```

## Custom Command with Context

Ellar CLI tools is a wrapper round [typer](https://typer.tiangolo.com/).
So, therefore, we can easily get the command context by adding a parameter with the annotation of `typer.Context`

Ellar CLI adds some meta-data CLI context that provides an interface for interaction with the Ellar project.

For example:

```python
import typing as t
import typer
from ellar.common import command
from ellar_cli.service import EllarCLIService
from ellar_cli.constants import ELLAR_META

@command
def my_new_command(ctx:typer.Context):
    """my_new_command CLI Description """
    ellar_cli_service = t.cast(t.Optional[EllarCLIService], ctx.meta.get(ELLAR_META))
    app = ellar_cli_service.import_application()
```
`EllarCLIService` is an Ellar CLI meta-data for interacting with Ellar project.

Some important method that may be of interest:

- `import_application`: returns application instance.
- `get_application_config`: gets current application config.

## Register a Custom Command

Lets, make the `my_new_command` visible on the CLI.
In other for Ellar CLI to identify custom command, its has to be registered to a `@Module` class.

For example:

```python
# project_name/root_module.py
from ellar.common import Module
from ellar.core import ModuleBase
from .commands import my_new_command

@Module(commands=[my_new_command])
class ApplicationModule(ModuleBase):
    pass
```

open your terminal and navigate to project directory and run the command below
```shell
ellar --help
```

command output
```shell
Usage: Ellar, Python Web framework [OPTIONS] COMMAND [ARGS]...

Options:
  -p, --project TEXT              Run Specific Command on a specific project
  --install-completion [bash|zsh|fish|powershell|pwsh]
                                  Install completion for the specified shell.
  --show-completion [bash|zsh|fish|powershell|pwsh]
                                  Show completion for the specified shell, to
                                  copy it or customize the installation.
  --help                          Show this message and exit.

Commands:
  create-module   - Scaffolds Ellar Application Module -
  create-project  - Scaffolds Ellar Application -
  my-new-command  - my_new_command cli description
  new             - Runs a complete Ellar project scaffold and creates...
  runserver       - Starts Uvicorn Server -
  say-hi 
```
