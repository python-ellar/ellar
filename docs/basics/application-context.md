# **Application Context**

In the complex web of dependencies within Ellar, 
accessing the application instance without triggering circular import errors can be a daunting task. 

To address this challenge, Ellar introduces the concept of an application context, 
a powerful mechanism that facilitates smooth access to the application instance throughout various parts of the codebase.

## **Understanding the Application Context**

The application context serves as a bridge between different components of the application, making the application object 
readily available through the application Dependency Injection (DI) container. This ensures that you can access the 
application instance without encountering import issues, whether it's during request handling, execution of CLI commands, 
or manual invocation of the context.

Two key elements of the application context are:

- **current_injector**: This proxy variable refers to the current application **injector**, providing access to any service or the application instance itself.
- **config**: A lazy loader for application configuration, which is based on the `ELLAR_CONFIG_MODULE` reference or accessed through `application.config` when the application context is active.

## **Integration with Click Commands**

By decorating Click commands with `click.with_app_context`, you can effortlessly incorporate the application context 
into their CLI workflows. This allows them to leverage the full power of the application context when executing commands.

For instance, consider the following example:

```python
import ellar_cli.click as click
from ellar.app import current_injector
from ellar.di import injectable

@injectable
class MyService:
    def do_something(self) -> None:
        pass

@click.command()
@click.argument('name')
@click.with_app_context
def my_command(name: str):
    my_service = current_injector.get(MyService)
    my_service.do_something()
```

Here, the `click.with_app_context` decorator ensures that the application context is available within the `my_command` function, 
allowing seamless access to application resources.

## **Lifecycle of the Application Context**

The application context operates as an asynchronous context manager, automatically created at 
the beginning of request handling and gracefully torn down upon completion of the request. 

## **Handling Application Context Events**

Additionally, the application context offers event hooks that you can leverage to perform custom actions at 
specific points in the context's lifecycle. 

Two such events are `app_context_started` and `app_context_teardown`, 
which are triggered at the beginning and end of the context, respectively.

For example, consider the following event handling setup:

```python
from ellar.events import app_context_teardown, app_context_started
from ellar.app import App, AppFactory, current_injector
from ellar.threading import run_as_async

@app_context_started.connect
async def on_context_started():
    print('=======> Context Started <=======')

@app_context_teardown.connect
def on_context_ended():
    print('=======> Context ended <=========')

app = AppFactory.create_app()

@run_as_async
async def run_app_context():
    async with app.application_context() as ctx:
        print("-----> Context is now available <------")

        app_instance = ctx.injector.get(App)
        app_instance_2 = current_injector.get(App)

        assert app_instance == app == app_instance_2
    print("-----> Context is now destroyed <------")

if __name__ == '__main__':
    run_app_context()
```

In this example, event handlers are registered to execute custom logic when the application context starts and ends. 
This allows you to perform initialization or cleanup tasks as needed.
