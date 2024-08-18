# **Custom Commands**
In this section, we will guide you through the process of creating a command and explain why you 
should utilize `ellar_cli.click` as your primary Click package when working with Ellar.


## **Command Options Arguments**
The `ellar_cli.click` package offers comprehensive help messages and documentation for command options and arguments 
without compromising the fundamental functionality of the command. 
For instance:

```python
import ellar_cli.click as click

@click.command()
@click.argument("arg1", required=True, help="Arg1 description")
@click.argument("arg2", required=False, help="Arg2 description")
@click.option("-op1", required=False, help="option1 description")
@click.option("-op2", required=False, help="option2 description")
def my_command(arg1, arg2, op1, op2):
    print(f"ARG1={arg1} ARG2={arg2}; op1={op1} op2={op2}")
```

When you register `my_command` to a `@Module` class, you can then execute it in your terminal with the following command:
```shell
ellar my-command --help 

## OUTPUT

Usage: ellar my-command <arg1> [<arg2>] [OPTIONS]

ARGUMENTS:
  arg1: <arg1>    Arg1 description  [required]
  arg2: [<arg2>]  Arg2 description

[OPTIONS]:
  -op1 TEXT  option1 description
  -op2 TEXT  option2 description
  --help     Show this message and exit.
```

## **With Injector Context Decorator**
The `ellar_cli.click` module includes a command decorator function called `with_injector_context`. 
This decorator ensures that a click command is executed within the application context, 
allowing `current_injector`, and `current_config` to have values.

For instance:

```python
import ellar_cli.click as click
from ellar.core import Config, current_injector

@click.command()
@click.argument("arg1", required=True, help="Arg1 description")
@click.with_injector_context
def command_context(arg1):
    config = current_injector.get(Config) 
    print("ALLOWED_HOSTS:", config.ALLOWED_HOSTS, ";ELLAR_CONFIG_MODULE:", config.config_module)

@click.command()
@click.argument("arg1", required=True, help="Arg1 description")
def command_woc(arg1):
    config = current_injector.get(Config) 
    print("ALLOWED_HOSTS:", config.ALLOWED_HOSTS, ";ELLAR_CONFIG_MODULE:", config.config_module)
```

In this example, `command_context` is wrapped with `with_injector_context`, while `command_woc` is not. 
When executing both commands, `command_context` will run successfully, and `command_wc` will raise a RuntimeError 
because it attempts to access a value outside the context.

## **AppContextGroup**
`AppContextGroup` extended from `click.Group` to wrap all its commands with `with_injector_context` decorator.


```python
import ellar_cli.click as click
from ellar.core import Config, current_injector

cm = click.AppContextGroup(name='cm')

@cm.command()
@click.argument("arg1", required=True, help="Arg1 description")
def command_context(arg1):
    config = current_injector.get(Config) 
    print("ALLOWED_HOSTS:", config.ALLOWED_HOSTS, ";ELLAR_CONFIG_MODULE:", config.config_module)


@cm.command()
@click.argument("arg1", required=True, help="Arg1 description")
def command_wc(arg1):
    config = current_injector.get(Config) 
    print("ALLOWED_HOSTS:", config.ALLOWED_HOSTS, ";ELLAR_CONFIG_MODULE:", config.config_module)
```
All commands registered under `cm` will be executed under within the context of the application. 

### **Disabling `with_injector_context` in AppContextGroup**
There are some cases where you may want to execute a command under `AppContextGroup` outside application context.
This can be done by setting `with_injector_context=False` as command parameter.

```python
import ellar_cli.click as click

cm = click.AppContextGroup(name='cm')

@cm.command(with_injector_context=False)
@click.argument("arg1", required=True, help="Arg1 description")
def command_wc(arg1):
    # config = current_injector.get(Config) 
    print("ALLOWED_HOSTS:Unavailable;ELLAR_CONFIG_MODULE:Unavailable")
```

## Async Command
The `ellar_cli.click` package provides a utility decorator function, `run_as_sync`, 
specifically designed to execute coroutine commands. 
This is useful when you want to define asynchronous commands using the `click` package. 
Here's an example:

```python
import ellar_cli.click as click
from ellar.core import Config,current_injector

@click.command()
@click.argument("arg1", required=True, help="Arg1 description")
@click.with_injector_context
@click.run_as_sync
async def command_context(arg1):
    config = current_injector.get(Config) 
    print("ALLOWED_HOSTS:", config.ALLOWED_HOSTS, ";ELLAR_CONFIG_MODULE:", config.config_module)
```

In this example, the `run_as_async` decorator enables the `command_context` coroutine 
command to be executed appropriately during execution.

## **Custom Command With Ellar**
Let's create a command group `db` which contains sub-commands such as `makemigrations`, `migrate`, `reset-db`, and so on.

To implement this scenario, let's create a file `commands.py` at the root level of the project and add the code below.
```python
from ellar_cli.click import AppContextGroup

db = AppContextGroup(name="db")


@db.command(name="make-migrations")
def makemigrations():
    """Create DB Migration """

@db.command()
async def migrate():
    """Applies Migrations"""
```

### **Registering Command**

To make the `db` command visible on the CLI, it **must** be registered within a `@Module` class. 
This ensures that the Ellar CLI can recognize and identify custom commands.

```python
from ellar.common import Module
from ellar.core import ModuleBase
from .commands import db

@Module(commands=[db])
class ApplicationModule(ModuleBase):
    pass
```
Open your terminal and navigate to the project directory and run the command below
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

Having explored various methods for crafting commands and understanding the roles of `with_injector_context` and `run_as_sync` decorators, 
you now possess the knowledge to create diverse commands for your Ellar application. 

It's crucial to keep in mind that any custom command you develop needs to be registered within a `@Module` class, which, 
in turn, should be registered with the `ApplicationModule`.
This ensures that your commands are recognized and integrated into the Ellar application's command-line interface. 
