
The `ExceptionMiddleware` and `ExceptionMiddlewareService` handle all unhandled exceptions throughout an application and provide user-friendly responses.

```json
{
  "status_code": 403,
  "detail": "Forbidden"
}
```

Types of exceptions managed by default:

- **`HTTPException`**: Provided by `Starlette` to handle HTTP errors
- **`WebSocketException`**: Provided by `Starlette` to manage websocket errors
- **`RequestValidationException`**: Provided by `Pydantic` for validation of request data
- **`APIException`**: Handles HTTP errors and provides more context about the error.

## **HTTPException**

The `HTTPException` class provides a base class that you can use for any
handled exceptions.

* `HTTPException(status_code, detail=None, headers=None)`

## **WebSocketException**

You can use the `WebSocketException` class to raise errors inside WebSocket endpoints.

* `WebSocketException(code=1008, reason=None)`

You can set any code valid as defined [in the specification](https://tools.ietf.org/html/rfc6455#section-7.4.1).

## **APIException**
It is a type of exception for REST API based applications. It gives more concept to error and provides a simple interface for creating other custom exception needs in your application without having to create an extra exception handler.

For example,

```python
from ellar.core.exceptions import APIException
from starlette import status

class ServiceUnavailableException(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    code = 'service_unavailable'

```
!!!hint
    You should only raise `HTTPException` and `APIException` inside routing or endpoints. Middleware classes should instead just return appropriate responses directly.

Let's use this `ServiceUnavailableException` in our previous project.

For example, in the `DogsController`, we have a `get_all()` method (a `GET` route handler). 
Let's assume that this route handler throws an exception for some reason. To demonstrate this, we'll hard-code it as follows:

```python
# project_name/apps/dogs/controllers.py

@get()
def get_all(self):
    raise ServiceUnavailableException()

```
Now, when you visit [http://127.0.0.1/dogs/](http://127.0.0.1/dogs/), you will get a JSON response.
```json
{
  "detail": "Service Unavailable"
}
```

When we raise the `ServiceUnavailableException` exception type, it produces a `JSON` response because `Ellar` has implemented an exception handler for any `APIException` exception type. 
We will see how to change the default exception handler later.

There is another error presentation available on the `APIException` instance:
- `.detail`: returns textual description of the error.
- `get_full_details()`: returns both textual description and other information about the error.

```shell
>>> print(exc.detail)
Service Unavailable
>>> print(exc.get_full_details())
{'detail':'Service Unavailable','code':'service_unavailable', 'description': 'The server cannot process the request due to a high load'}
```

## **Creating Custom Exception Handler**

To create an exception handler for your custom exception, you have to make a class that follows the `IExceptionHandler` contract.

At the root project folder, create a file `custom_exceptions.py`,

```python
# project_name/custom_exceptions.py
import typing as t
from ellar.core.exceptions import IExceptionHandler
from ellar.core.context import IHostContext
from starlette.responses import Response


class MyCustomException(Exception):
    pass


class MyCustomExceptionHandler(IExceptionHandler):
    exception_type_or_code = MyCustomException
    
    async def catch(
        self, ctx: IHostContext, exc: MyCustomException
    ) -> t.Union[Response, t.Any]:
        app_config = ctx.get_app().config
        return app_config.DEFAULT_JSON_CLASS(
            {'detail': str(exc)}, status_code=400,
        )

```

**IExceptionHandler** Overview:

- `exception_type_or_code`: defines the `exception class` OR `status code` to target when resolving exception handlers.
- `catch()`: defines the handling code and response to be returned to the client.

### **Creating Exception Handler for status code**
Let's create a handler for `MethodNotAllowedException` which, according to the HTTP code is `405`.
```python
# project_name/apps/custom_exceptions.py
import typing as t
from ellar.core.exceptions import IExceptionHandler
from ellar.core.context import IHostContext
from ellar.core import render_template
from starlette.responses import Response
from starlette.exceptions import HTTPException

class MyCustomException(Exception):
    pass


class MyCustomExceptionHandler(IExceptionHandler):
    exception_type_or_code = MyCustomException
    
    async def catch(
        self, ctx: IHostContext, exc: MyCustomException
    ) -> t.Union[Response, t.Any]:
        app_config = ctx.get_app().config
        return app_config.DEFAULT_JSON_CLASS(
            {'detail': str(exc)}, status_code=400,
        )
    

class ExceptionHandlerAction405(IExceptionHandler):
    exception_type_or_code = 405
    
    async def catch(
        self, ctx: IHostContext, exc: HTTPException
    ) -> t.Union[Response, t.Any]:
        context_kwargs = {}
        return render_template('405.html', request=ctx.switch_to_http_connection().get_request(), **context_kwargs)
```
We have registered a handler for any `HTTP` exception with a `405` status code which we are returning a template `405.html` as a response.

!!!info
    Ellar will look for `405.html` in all registered modules. So `dogs` folder, create a `templates` folder and add `405.html`.

The same way can create Handler for `500` error code.


## **Registering Exception Handlers**
We have successfully created two exception handlers `ExceptionHandlerAction405` and `MyCustomExceptionHandler` but they are not yet visible to the application.

- `config.py`: The config file holds manage application settings. The `EXCEPTION_HANDLERS` variable defines all custom exception handlers registered to `ExceptionMiddlewareService` when bootstrapping the application.

```python
# project_name/config.py
import typing as t
from ellar.core import ConfigDefaultTypesMixin
from ellar.core.exceptions import IExceptionHandler
from .apps.custom_exceptions import MyCustomExceptionHandler, ExceptionHandlerAction405

class BaseConfig(ConfigDefaultTypesMixin):
    EXCEPTION_HANDLERS: t.List[IExceptionHandler] = [
        MyCustomExceptionHandler(),
        ExceptionHandlerAction405()
    ]
```
- `application instance`: You can also add exception through `app` instance.

```python
# project_name/server.py

import os

from ellar.constants import ELLAR_CONFIG_MODULE
from ellar.core.factory import AppFactory
from .root_module import ApplicationModule
from .apps.custom_exceptions import MyCustomExceptionHandler, ExceptionHandlerAction405

application = AppFactory.create_from_app_module(
    ApplicationModule,
    config_module=os.environ.get(
        ELLAR_CONFIG_MODULE, "project_name.config:DevelopmentConfig"
    ),
)

application.add_exception_handler(
    MyCustomExceptionHandler(), 
    ExceptionHandlerAction405()
)
```

## **Override Default Exception Handler**
We have seen how to create an exception handler for status codes and specific exception types.
To override any exception handler, it follows the same pattern and then defines the target to exception type

For example:

```python
# project_name/apps/custom_exceptions.py
import typing as t
from ellar.core.exceptions import IExceptionHandler, APIException
from ellar.core.context import IHostContext
from starlette.responses import Response


class OverrideAPIExceptionHandler(IExceptionHandler):
    exception_type_or_code = APIException
    
    async def catch(
        self, ctx: IHostContext, exc: APIException
    ) -> t.Union[Response, t.Any]:
        app_config = ctx.get_app().config
        return app_config.DEFAULT_JSON_CLASS(
            {'message': exc.detail}, status_code=exc.status_code,
        )
```

Once we register the `OverrideAPIExceptionHandler` exception handler, it will become the default handler for the `APIException` exception type.
