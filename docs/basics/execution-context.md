# **Execution Context**
Execution context refers to the current context of execution, or the environment in which a specific piece of code is running. 
It contains information about the current request, the current response in the case of http connection, and the current state of the application.

The execution context is created automatically when a request is received, and it is passed along through the various layers of the application as the request is handled. 
This allows different components of the application like **exception handlers**, **functional middlewares** and **guards** to access information about the current request.

There are two class `HostContext` and `ExecutionContext` which provides set of methods and properties for accessing and manipulating the current context of execution.


## **HostContext**
The `HostContext` class provides a wrapper around `ASGI` app parameters (`scope`, `receive` and `send`) and provides some methods that allows you choosing the appropriate context(e.g., HTTP or WebSockets).

For example, the `catch()` method of an **exception handlers** is called with an IHostContext.

```python
# project_name/apps/custom_exceptions.py
import typing as t
from ellar.common import IExceptionHandler, IHostContext, Response

class MyCustomException(Exception):
    pass


class MyCustomExceptionHandler(IExceptionHandler):
    exception_type_or_code = MyCustomException
    
    async def catch(
        self, ctx: IHostContext, exc: MyCustomException
    ) -> t.Union[Response, t.Any]:
        
        if ctx.get_type() == 'http':
            # do something that is only important in the context of regular HTTP requests (REST)
            pass
        elif  ctx.get_type() == 'websocket':
            # do something that is only important in the context of regular Websocket
            pass
        
        app_config = ctx.get_app().config
        return app_config.DEFAULT_JSON_CLASS(
            {'detail': str(exc)}, status_code=400,
        )

```

## **Switching to other Contexts**

Currently, in Ellar you can only switch between `http` and `websocket` context. And each context has `get_client` method that returns context session.

```python

    async def catch(
        self, ctx: IHostContext, exc: MyCustomException
    ) -> t.Union[Response, t.Any]:
        
        if ctx.get_type() == 'http':
            # do something that is only important in the context of regular HTTP requests (REST)
            http_context = ctx.switch_to_http_connection()
            request: Request = http_context.get_request()
            response: Response = http_context.get_response()
            http_connection: HTTPConnection = http_context.get_client()
            
        elif  ctx.get_type() == 'websocket':
            # do something that is only important in the context of regular Websocket
            websocket_context = ctx.switch_to_websocket()
            websocket_session: WebSocket = websocket_context.get_client()
        
        app_config = ctx.get_app().config
        return app_config.DEFAULT_JSON_CLASS(
            {'detail': str(exc)}, status_code=400,
        )
```

!!! info
    Its good to note that you can't switch to a context that does not match the current context type. 
    Always use the `.get_type()` to verify the type before switching.

### IHostContext Properties
Important properties of `HostContext`

- `get_service_provider`: returns current service provider using in handling the request
- `get_app`: returns current application instance
- `get_type`: gets scope type `http`, `websocket` 
- `get_args`: returns `scope`, `receive` and `send` ASGI parameters
- `switch_to_http_connection`: returns `HTTPConnectionHost` instance
- `switch_to_websocket`: returns `WebSocketConnectionHost` instance

```python
class IHostContext(ABC):
    @abstractmethod
    def get_service_provider(self) -> "RequestServiceProvider":
        """Gets  RequestServiceProvider instance"""

    @abstractmethod
    def switch_to_http_connection(self) -> IHTTPConnectionHost:
        """Returns HTTPConnection instance"""

    @abstractmethod
    def switch_to_websocket(self) -> IWebSocketConnectionHost:
        """Returns WebSocket instance"""

    @abstractmethod
    def get_app(self) -> "App":
        """Gets application instance"""

    @abstractmethod
    def get_type(self) -> str:
        """returns scope type"""

    @abstractmethod
    def get_args(self) -> t.Tuple[TScope, TReceive, TSend]:
        """returns all args passed to asgi function"""
```

`IHTTPConnectionHost` and `IWebSocketConnectionHost` has some methods that maybe of interest.

Here are methods for `IHTTPConnectionHost`:

```python
class IHTTPConnectionHost(ABC):
    @abstractmethod
    def get_response(self) -> Response:
        """Gets response"""

    @abstractmethod
    def get_request(self) -> Request:
        """Returns Request instance"""

    @abstractmethod
    def get_client(self) -> HTTPConnection:
        """Returns HTTPConnection instance"""
```

Following are the methods for `IWebSocketConnectionHost`:

```python
class IWebSocketConnectionHost(ABC):
    @abstractmethod
    def get_client(self) -> WebSocket:
        """Returns WebSocket instance"""
```

## **ExecutionContext Class**
`ExecutionContext` extends `HostContext` and provides extra information like `Controller` class and controller `function` 
that will handler the current request.

```python
import typing
from ellar.common import ControllerBase
from ellar.core import HostContext


class ExecutionContext(HostContext):
    # Returns the type of the controller class which the current handler belongs to.
    def get_class(self) -> typing.Type[ControllerBase]:
        pass
    
    # Returns a reference to the handler (method) that will be handler the current request.
    def get_handler(self) -> typing.Callable:
        pass

```

These extra information are necessary for reading `metadata` properties set on controllers or the route handler function.

### **How to access the current execution context**
You can access the current execution context using the `Inject[ExecutionContext]` annotation. 
This decorator can be applied to a parameter of a controller or service method, 
and it will inject the current `ExecutionContext` object into the method.

For example, consider the following controller method:
```python
from ellar.common import get, Controller, IExecutionContext, Inject

@Controller('/users')
class UserController:
    @get('/{user_id}')
    async def get_user(self, user_id: str, ctx:Inject[IExecutionContext]):
        # Use the ctx object to access the current execution context
        res = ctx.switch_to_http_connection().get_response()
        res.status_code = 200
        res.body = f"Request to get user with id={user_id}".encode("utf-8")
        scope, receive, send = ctx.get_args()
        await res(scope, receive, send) # sends response

```

In this example, the `get_user` method is decorated with the `@get` decorator to handle a GET request to the /users/:id route. 
The `Inject[ExecutionContext]` annotation is applied to the second parameter of the method, which will inject the current `ExecutionContext` object into the method.

Once you have access to the `ExecutionContext` object, you can use its methods and properties to access information about the current request.

## **Reflector and Metadata**
Ellar provides the ability to attach **custom metadata** to route handlers through the `@set_metadata()` decorator. 
We can then access this metadata from within our class to make certain decisions.

```python
# project_name/apps/cars/controllers.py

from ellar.common import Body, Controller, post, set_metadata, ControllerBase
from .schemas import CreateCarSerializer


@Controller('/car')
class CarController(ControllerBase):
    @post()
    @set_metadata('role', ['admin'])
    async def create(self, payload: CreateCarSerializer = Body()):
        result = payload.dict()
        result.update(message='This action adds a new car')
        return result
```

With the construction above, we attached the `roles` metadata (roles is a metadata key and ['admin'] is the associated value) 
to the `create()` method. While this works, it's not good practice to use `@set_metadata()` directly in your routes. 
Instead, create your own decorators, as shown below:

```python
# project_name/apps/cars/controllers.py
import typing
from ellar.common import Body, Controller, post, set_metadata, ControllerBase
from .schemas import CreateCarSerializer


def roles(*_roles: str) -> typing.Callable:
    return set_metadata('roles', list(_roles))


@Controller('/car')
class CarController(ControllerBase):
    @post()
    @roles('admin', 'is_staff')
    async def create(self, payload: CreateCarSerializer = Body()):
        result = payload.dict()
        result.update(message='This action adds a new car')
        return result
```

!!! info
    It's important to note that `ExecutionContext` becomes available when there is route handler found to handle the current request.

To access the route's role(s) (custom metadata), we'll use the `Reflector` helper class, which is provided out of the box by the framework. 
`Reflector` can be injected into a class in the normal way:

```python
# project_name/apps/cars/guards.py
from ellar.di import injectable
from ellar.common import GuardCanActivate, IExecutionContext
from ellar.core.services import Reflector


@injectable()
class RoleGuard(GuardCanActivate):
    def __init__(self, reflector: Reflector):
        self.reflector = reflector

    async def can_activate(self, context: IExecutionContext) -> bool:
        roles = self.reflector.get('roles', context.get_handler())
        # request = context.switch_to_http_connection().get_request()
        # check if user in request object has role
        if not roles:
            return True
        return 'user' in roles
```

Next, we apply the `RoleGuard` to `CarController`

```python
# project_name/apps/cars/controllers.py
import typing
from ellar.common import Body, Controller, post, set_metadata, UseGuards, ControllerBase
from .schemas import CreateCarSerializer
from .guards import RoleGuard

def roles(*_roles: str) -> typing.Callable:
    return set_metadata('roles', list(_roles))


@Controller('/car')
@UseGuards(RoleGuard)
class CarController(ControllerBase):
    @post()
    @roles('admin', 'is_staff')
    async def create(self, payload: CreateCarSerializer = Body()):
        result = payload.dict()
        result.update(message='This action adds a new car')
        return result
```

Also, since `RoleGuard` is marked as `injectable`, EllarInjector service will be able to resolve `RoleGuard` without `RoleGuard` registered as a provider.
