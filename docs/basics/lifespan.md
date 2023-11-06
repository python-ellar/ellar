# **Lifespan**
Ellar applications registers a lifespan manager. The manager handles lifespan handler registered in the configuration under the variable name
**`DEFAULT_LIFESPAN_HANDLER`** and also executes code that needs to run before the application starts up, or when the application is shutting down. 
The lifespan manager must be run before ellar starts serving incoming request.

```python
import uvicorn
import contextlib
from ellar.app import App, AppFactory

@contextlib.asynccontextmanager
async def some_async_resource():
    print("running some-async-resource function")
    yield 
    print("existing some-async-resource function")


@contextlib.asynccontextmanager
async def lifespan(app: App):
    async with some_async_resource():
        print("Run at startup!")
        yield
        print("Run on shutdown!")


application = AppFactory.create_app(config_module=dict(
    DEFAULT_LIFESPAN_HANDLER=lifespan
))

if __name__ == "__main__":
    uvicorn.run(application, port=5000, log_level="info")
```
The construct above will generate the output below:
```shell
INFO:     Started server process [11772]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:5000 (Press CTRL+C to quit)

running some-async-resource function
Run at startup!

INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [11772]

Run on shutdown!
existing some-async-resource function
```

## **Modules and Lifespan**
Any module that wants to engage in application lifespan must inherit `IApplicationStartup` for startup actions or `IApplicationShutdown` for shutdown actions 
or inherit both for startup and shutdown actions. 

`IApplicationStartup` has an abstractmethod `on_startup` function and `IApplicationShutdown` has an abstractmethod `on_shutdown` function.

```python
from abc import abstractmethod


class IApplicationStartup:
    @abstractmethod
    async def on_startup(self, app: "App") -> None:
        ...


class IApplicationShutdown:
    @abstractmethod
    async def on_shutdown(self) -> None:
        ...
```
Let's assume we have a module that extends both `IApplicationStartup` and `IApplicationShutdown` to execute some actions on startup and on shutdown as shown below:

```python
from ellar.common import IApplicationShutdown, IApplicationStartup, Module

@Module()
class SampleModule(IApplicationShutdown, IApplicationStartup):
    
    async def on_startup(self, app) -> None:
        print("Run at startup! in SampleModule")

    async def on_shutdown(self) -> None:
        print("Run on shutdown! in SampleModule")

```

## **Running lifespan in tests**
You should use `TestClient` as a context manager, to ensure that the lifespan is called.

```python
from ellar.testing import Test
from .main import SampleModule

test_module = Test.create_test_module(modules=[SampleModule])

def test_lifespan():
    with test_module.get_test_client() as client:
        # Application's lifespan is called on entering the block.
        response = client.get("/")
        assert response.status_code == 200

    # And the lifespan's teardown is run when exiting the block.

```
