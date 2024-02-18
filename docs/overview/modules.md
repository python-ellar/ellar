# **Modules**

A **module** in Ellar is essentially a class marked with the `@Module()` decorator. 
This simple yet powerful annotation serves as the cornerstone of defining the architecture and organization of an application.

![Middleware Description](../img/ModuleDescription.png)

Embracing the modular approach, each module encapsulates a specific set of functionalities, ensuring a clear separation of concerns within the application. The `ApplicationModule` typically acts as the root module, orchestrating the composition of various submodules.

This modular structure enables efficient management of dependencies, promotes code reusability, and enhances maintainability 
by facilitating clear boundaries between different components of the application. By structuring the application into modules, 
developers can easily reason about the codebase, foster collaboration among team members, and scale the application seamlessly.

## **Feature modules**
Developing an application as a collection of feature modules grouped together offers several advantages. It helps in managing complexity, maintains a codebase that is both extendable and testable, and promotes adherence to SOLID principles.

A prime example of a feature module is the **car** project. In this project, the `CarModule` encapsulates all the services and controllers responsible for handling the `car` resource. This modular structure simplifies maintenance, extension, and testing of the codebase.

```python
# project_name/apps/car/module.py

from ellar.common import Module
from ellar.core import ModuleBase
from ellar.di import Container
from .services import CarRepository
from .controllers import CarController


@Module(
    controllers=[CarController],
    providers=[CarRepository],
)
class CarModule(ModuleBase):
    def register_providers(self, container: Container) -> None:
        # Additional provider registrations can be done here
        pass
```

## **Module Parameters**
Let's create a Module and take a quick overview of its parameters.

```python
from ellar.common import Module
from ellar.core import ModuleBase

@Module(
    name='', 
    modules=[], 
    providers=[],
    controllers=[],
    routers=[],
    commands=[],
    base_directory=None, 
    static_folder='static', 
    template_folder='templates'
)
class BookModule(ModuleBase):
    pass
```

| Parameter         | Description                                                                                                             |
|-------------------|-------------------------------------------------------------------------------------------------------------------------|
| `name`            | The name of the module. It's relevant for identification purposes.                                                      |
| `modules`         | A list of dependencies required by this module.                                                                         |
| `providers`       | Providers to be instantiated by the Ellar injector, possibly shared across this module.                                 |
| `controllers`     | Controllers defined in this module that need instantiation.                                                             |
| `routers`         | ModuleRouters defined in this module.                                                                                   |
| `commands`        | Functions decorated with `EllarTyper` or `command` that serve as commands.                                              |
| `base_directory`  | The root directory for this module, used to locate `static_folder` and `template_folder`. Default is the module's root. |
| `static_folder`   | The folder for static files within this module. Default is 'static'.                                                    |
| `template_folder` | The folder for templates within this module. Default is 'templates'.                                                    |



## **Additional Module Configurations**
The Ellar framework offers additional module configurations to handle various aspects of the application lifecycle and behavior.

### Module Events
Modules can define `before_init` class method to configure additional initialization parameters before instantiation. This method receives the current application config as a parameter, allowing for further customization.

```python linenums="1"
import typing
from ellar.common import Module
from ellar.core import ModuleBase, Config


@Module()
class ModuleEventSample(ModuleBase):
    @classmethod
    def before_init(cls, config: Config) -> typing.Any:
        """Called before creating Module object"""
```

### Module Application Cycle
Ellar follows a two-phase application lifecycle with `on_startup` and `on_shutdown` events managed by `EllarApplicationLifespan`.

```python
from ellar.common import Module, IApplicationShutdown, IApplicationStartup
from ellar.core import ModuleBase

@Module()
class AModuleSample(ModuleBase, IApplicationStartup):
    async def on_startup(self, app: "App") -> None:
        pass

@Module()
class BModuleSample(ModuleBase, IApplicationShutdown):
    async def on_shutdown(self) -> None:
        pass

@Module()
class CModuleSample(ModuleBase, IApplicationStartup, IApplicationShutdown):
    async def on_startup(self, app: "App") -> None:
        pass

    async def on_shutdown(self) -> None:
        pass
```

### Module Exceptions
Modules can register custom exception handlers for specific HTTP error codes.

```python linenums="1"
from ellar.common import Module, exception_handler, JSONResponse, Response, IHostContext
from ellar.core import ModuleBase

@Module()
class ModuleExceptionSample(ModuleBase):
    @exception_handler(404)
    def exception_404_handler(cls, context: IHostContext, exc: Exception) -> Response:
        return JSONResponse(dict(detail="Resource not found."))
```

### Module Templating Filters
Define Jinja2 templating filters within modules, which are then added to the Jinja2 environment instance during template loading.

```python
from ellar.common import Module, template_global, template_filter
from ellar.core import ModuleBase

@Module()
class ModuleTemplateFilterSample(ModuleBase):
    @template_filter()
    def double_filter(cls, n):
        return n * 2

    @template_global()
    def double_global(cls, n):
        return n * 2

    @template_filter(name="dec_filter")
    def double_filter_dec(cls, n):
        return n * 2
```

These configurations enhance the flexibility and functionality of Ellar modules, 
allowing for greater control over application behavior and lifecycle events.


## **Dependency Injection**
A module class can inject providers, such as configuration objects, for various purposes. Let's consider an example from our sample project where we inject `Config` into the `CarModule`.

```python linenums="1"
# project_name/apps/car/module.py

from ellar.common import Module
from ellar.core import Config, ModuleBase
from ellar.di import Container
from .services import CarRepository
from .controllers import CarController


@Module(
    controllers=[CarController],
    providers=[CarRepository],
)
class CarModule(ModuleBase):
    def __init__(self, config: Config):
        self.config = config
    
    def register_providers(self, container: Container) -> None:
        # Additional provider registrations can be performed here
        pass
```

In this example, the `CarModule` class accepts a `Config` object in its constructor. 
This allows us to access configuration parameters within the module. 
Additionally, the `register_providers` method can be utilized for more advanced provider registrations within the container.

## **Module Middleware**
Middleware functions can be defined at the module level using the `@middleware()` function decorator. Let's illustrate this with an example:

```python linenums="1"
from ellar.common import Module, middleware, IHostContext, PlainTextResponse
from ellar.core import ModuleBase


@Module()
class ModuleMiddlewareSample(ModuleBase):
    @middleware()
    async def my_middleware_function_1(cls, context: IHostContext, call_next):
        request = context.switch_to_http_connection().get_request() # for HTTP response only
        request.state.my_middleware_function_1 = True
        await call_next()
    
    @middleware()
    async def my_middleware_function_2(cls, context: IHostContext, call_next):
        if context.get_type() == 'websocket':
            websocket = context.switch_to_websocket().get_client()
            websocket.state.my_middleware_function_2 = True
        await call_next()

    @middleware()
    async def my_middleware_function_3(cls, context: IHostContext, call_next):
        connection = context.switch_to_http_connection().get_client() # for HTTP response only
        if connection.headers['somekey']:
            # response = context.get_response() -> use the `response` to add extra definitions to things you want to see on
            return PlainTextResponse('Header is not allowed.')
        await call_next()
```

Key points to remember:
- Middleware functions must be asynchronous (`async`).
- Middleware functions can return a response or modify a response returned.
- Middleware functions must call `call_next()` and await its actions as demonstrated above.

## **Injector Module**
The `EllarInjector` module, built on top of the Python library `injector`, offers similar features to the `injector` 
library, with some additional capabilities. One such feature is the ability to create or reuse modules from `injector` 
Modules for configuring bindings and providers for dependency injection.

```python linenums="1"
from ellar.core import ModuleBase
from ellar.di import Container
from injector import provider


class Name(str):
    pass


class Description(str):
    pass


class ExampleModule(ModuleBase):
    def register_services(self, container: Container) -> None:
        container.bind(Name, to='Sherlock')

    @provider
    def describe(self, name: Name) -> Description:
        return Description('%s is a man of astounding insight' % name)
```

In this example, the `ExampleModule` registers the `Description` and `Name` types with the injector. 
These can then be resolved if required by any object in the application.

For more details on the use cases of the `injector` module, 
you can refer to the documentation [here](https://injector.readthedocs.io/en/latest/terminology.html#module).
