# **Module Router**

`ModuleRouter` allows you to define your route handlers as standalone functions, offering an alternative to using classes. 
This can be advantageous for Python developers who prefer using functions. 
Importantly, using `ModuleRouter` does not restrict your access to other features provided by Ellar.

## **Usage**
The Ellar CLI tool automatically generates a `routers.py` file with every `create-module` scaffold command. 
This file serves as a concise guide on utilizing the `ModuleRouter` class.

Now, let's leverage the **routers.py** file generated in our prior project to implement **two** route functions, namely **addition** and **subtraction**.
```python
# project_name/apps/car/routers.py
"""
Define endpoints routes in python function fashion
example:

my_router = ModuleRouter("/cats", tag="Cats", description="Cats Resource description")

@my_router.get('/')
def index(request: Request):
    return {'detail': 'Welcome to Cats Resource'}
"""
from ellar.common import ModuleRouter
from ellar.openapi import ApiTags

math_router = ModuleRouter('/math')
open_api_tag = ApiTags(name='Math')
open_api_tag(math_router)

@math_router.get('/add')
def addition(a: int, b: int):
    return a + b


@math_router.get('/subtract')
def subtraction(a: int, b: int):
    return a - b

```

In the provided example, the `math_router` is created with a prefix `/math` and an OPENAPI tag 'Math'. 
Two routes, `addition(a:int, b:int)` and `subtraction(a:int, b:int)`, are added to the router, each handling two query parameters ('a' and 'b') of integer type. These functions perform the specified mathematical operations and return the results.

To make the `math_router` visible to the application, it is registered with the current injector using `current_injector.register(ModuleRouter, math_router)`. This step ensures that the router is recognized and accessible within the application.

## **Registering Module Router**
Like controllers, ModuleRouters also need to be registered to their root module to be used in a web application. 
In the example provided above, the `math_router` would be registered under the `project_name/apps/car/module.py` file.

This registration process typically involves importing the `math_router` and then adding it to the list of `routers` in the `module.py` file. 
This allows the router to be recognized by the application and its routes to be available to handle requests.

```python

from ellar.common import Module
from ellar.core import ModuleBase
from ellar.di import Container

from .controllers import CarController
from .routers import math_router


@Module(
    controllers=[CarController],
    providers=[],
    routers=[math_router],
)
class CarModule(ModuleBase):
    def register_providers(self, container: Container) -> None:
        # for more complicated provider registrations
        # container.register_instance(...)
        pass
```

![math_router.png](../img/math_router.png)


## **Accessing Other Request Object**
In functional route handle, we can access request object and response object through custom decorators or type annotation as shown below.

### **By Type Annotation**
Let's inject request and response object in `addition` route handler function from our previous example

```python
from ellar.core import Request
from ellar.common import ModuleRouter, Response


math_router = ModuleRouter('/math', name='Math')

@math_router.get('/add')
def addition(request: Request, res: Response, a:int, b:int):
    res.headers['x-operation'] = 'Addition'
    return dict(is_request_object=isinstance(request, Request), is_response_object=isinstance(res, Response), operation_result=a + b)

```

### **By Custom decorators**
You can also achieve the same result by using custom decorator.

```python
from ellar.core import Request
from ellar.common import ModuleRouter,Response, Inject


math_router = ModuleRouter('/math', name='Math')

@math_router.get('/add')
def addition(request:Inject[Request], res:Inject[Response], a:int, b:int):
    res.headers['x-operation'] = 'Addition'
    return dict(is_request_object=isinstance(request, Request), is_response_object=isinstance(res, Response), operation_result=a + b)

```

![math_router_with_request_object.png](../img/math_router_with_request_object.png)

## **Inject Services**
We can also inject service providers just like controller routes using the `Provide` function.

```python
from ellar.core import Config
from ellar.common import ModuleRouter, Response, Inject


math_router = ModuleRouter('/math', name='Math')

@math_router.get('/subtract')
def subtraction(a:int, b:int, res:Response, config:Inject[Config]):
    res.headers['x-operation'] = 'Subtraction'
    return dict(
        is_config=isinstance(config, Config),
        operation_result=a - b
    )

```
