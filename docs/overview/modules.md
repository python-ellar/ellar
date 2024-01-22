# **Modules**

A module is represented by a class with the `@Module()` decorator. 
This decorator provides essential metadata, offering a `Module` data structure that outlines the module's architecture.

![middleware description image](../img/ModuleDescription.png)

Organizing components within projects as `Modules` is considered a best practice. 
The `ApplicationModule` serves as the starting point or root module for constructing the application module tree. 
This internal data structure facilitates the resolution of relationships, dependencies, and interactions between modules and providers.

Consequently, the typical architecture of applications involves multiple modules, each encapsulating closely related functionality.

## **Feature modules**
Building an application as a group of feature modules bundled together helps manage complexity, 
maintain a codebase that is both extendable and testable, and encourages development using SOLID principles.

A typical example of a feature module is the **car** project. 
The `CarModule` wraps all the services and controllers responsible for managing the `car` resource, 
making it easy to maintain, extend, and test.

```python title='project_name/apps/car/module.py' linenums="1"
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
        # for more complicated provider registrations
        # container.register_instance(...)
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

|                   |                                                                                                                              |
|-------------------|------------------------------------------------------------------------------------------------------------------------------|
| `name`            | name of the module - it's irrelevant at the moment.                                                                          |
| `modules`         | List of Module dependencies                                                                                                  |
| `providers`       | the providers that will be instantiated by the Ellar injector and that may be shared at least across this module             |
| `controllers`     | the set of controllers defined in this module which have to be instantiated                                                  |
| `routers`         | the set of `ModuleRouter` defined in this module                                                                             |
| `commands`        | the set of `EllarTyper` or `command` decorated functions                                                                     |
| `base_directory`  | root directory for this module to read `static_folder` and `template_folder`. Default is the root folder of the Module Class |
| `static_folder`   | defines the static folder for this module - default: `static`                                                                |
| `template_folder` | defines the template folder for this module - default: `templates`                                                           |


## **Additional Module Configurations**

### **Module Events**
Before a Module is instantiated, the `before_init` class method is invoked with an application config object. 
This allows for the configuration of additional initialization parameters that need to be supplied to the `__init__` 
function, originating from the application config.

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
`before_init` receives current app `Config` as a parameter for further configurations before `ModuleEventSample` is initiated.
It's important to note that returned values from `before_init` will be passed to the constructor of `ModuleEventSample` during instantiation.

### **Module Application Cycle**
The Ellar application follows a two-phase lifecycle, consisting of `on_startup` and `on_shutdown`, which are managed by `EllarApplicationLifespan`.

- `on_startup`: Triggered when the ASGI server initiates a lifespan request on the application instance.
- `on_shutdown`: Activated when the ASGI server is in the process of shutting down the application.

Modules can subscribe to these events by inheriting from `IApplicationStartup` for startup actions and `IApplicationShutdown` for shutdown actions.

For instance:
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

In the provided example:
- `AModuleSample` subscribes to `IApplicationStartup` and will be called only during startup.
- `BModuleSample` subscribes to `IApplicationShutdown` and will be called only during application shutdown.
- `CModuleSample` subscribes to both `IApplicationStartup` and `IApplicationShutdown`, thus being invoked during both startup and shutdown phases.

This modular approach enables modules to actively engage in the application's life-cycle events, allowing developers 
to organize and execute code efficiently during specific stages. 
This not only enhances flexibility but also contributes to the overall maintainability of the application.

### **Module Exceptions**
Custom exception handlers can be registered through modules.

```python linenums="1"
from ellar.common import Module, exception_handler, JSONResponse, Response, IHostContext
from ellar.core import ModuleBase

@Module()
class ModuleExceptionSample(ModuleBase):
    @exception_handler(404)
    def exception_404_handler(cls, context: IHostContext, exc: Exception) -> Response:
        return JSONResponse(dict(detail="Resource not found."))
```
`exception_404_handler` will be register to the application at runtime during `ModuleExceptionSample` computation.

### **Module Templating Filters**
In addition, we can define `Jinja2` templating filters within project Modules or any module annotated with `@Module()`.
The specified filters are then passed down to the `Jinja2` **environment** instance alongside the `template_folder` 
value when creating the **TemplateLoader**.

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


## **Dependency Injection**
A module class can inject providers as well (e.g., for configuration purposes):

For example, from our sample project, we can inject `Config` to the `CarModule`

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
        # for more complicated provider registrations
        # container.register_instance(...)
        pass
```

## **Module Middleware**

Middlewares functions can be defined at Module level with `@middleware()` function decorator.

For example:

```python linenums="1"
from ellar.common import Module, middleware, IHostContext, PlainTextResponse
from ellar.core import ModuleBase


@Module()
class ModuleMiddlewareSample(ModuleBase):
    @middleware()
    async def my_middleware_function_1(cls, context: IHostContext, call_next):
        request = context.switch_to_http_connection().get_request() # for http response only
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
        connection = context.switch_to_http_connection().get_client() # for http response only
        if connection.headers['somekey']:
            # response = context.get_response() -> use the `response` to add extra definitions to things you want to see on
            return PlainTextResponse('Header is not allowed.')
        await call_next()
```
Things to note:

- middleware functions must be `async`.
- middleware functions can return a `response` or modify a `response` returned
- middleware functions must call `call_next` and `await` its actions as shown above.

## **Injector Module**
`EllarInjector` is based on a python library [injector](https://injector.readthedocs.io/en/latest/index.html). Both share similar `Module` features with few distinct features. 

As an added support, you can create or reuse modules from `injector` Modules.

!!! info
    This type of module is used to configure `injector` **bindings** and **providers** for dependency injection purposes.

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
The `ExampleModule` has registered `Description` and `Name` type to the injector and can be resolved respectively if required by any object.

Read more on injector module use cases - [Here](https://injector.readthedocs.io/en/latest/terminology.html#module).
