# **Exceptions & Exception Handling**
Ellar comes with a built-in exceptions middleware, `ExceptionMiddleware`, which is responsible for processing all exceptions across 
an application. When an exception is not handled by your application code, it is caught by this middleware, which 
then automatically sends an appropriate user-friendly response .

```json
{
  "status_code": 403,
  "detail": "Forbidden"
}
```
And based on application config `DEBUG` value, the exception is raised during is `config.DEBUG`
is True but when `config.DEBUG` a 500 error is returned as shown below:
```json
{
  "statusCode": 500,
  "message": "Internal server error"
}
```

Types of exceptions types managed by default:

- **`HTTPException`**: Provided by `Starlette` to handle HTTP errors.eg. `HTTPException(status_code, detail=None, headers=None)`
- **`WebSocketException`**: Provided by `Starlette` to manage websocket errors. eg `WebSocketException(code=1008, reason=None)`
- **`RequestValidationException`**: Provided by `Pydantic` for validation of request data
- **`APIException`**: It is a type of exception for REST API based applications. It gives more concept to error and provides a simple interface for creating other custom exception needs in your application without having to create an extra exception handler.

    For example,

    ```python
    from ellar.common import APIException
    from starlette import status
    
    class ServiceUnavailableException(APIException):
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        code = 'service_unavailable'
    
    ```

### **Built-in APIExceptions**
Ellar provides a set of standard exceptions that inherit from the base `APIException`. 
These are exposed from the `ellar.common` package, and represent many of the most common HTTP exceptions:

- `AuthenticationFailed`
- `ImproperConfiguration`
- `MethodNotAllowed`
- `NotAcceptable`
- `NotAuthenticated`
- `NotFound`
- `PermissionDenied`
- `UnsupportedMediaType`

## **Throwing standard exceptions**
Let's use this `ServiceUnavailableException` in our previous project.

For example, in the `CarController`, we have a `get_all()` method (a `GET` route handler). 
Let's assume that this route handler throws an exception for some reason. To demonstrate this, we'll hard-code it as follows:

```python
# project_name/apps/car/controllers.py

@get()
def get_all(self):
    raise ServiceUnavailableException()

```
Now, when you visit [http://127.0.0.1/car/](http://127.0.0.1/car/){target="_blank"}, you will get a JSON response.
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

!!!hint
    You should only raise `HTTPException` and `APIException` during route function handling. Since exception manager is a 
    middleware and `HTTPException` raised before the `ExceptionMiddleware` will not be managed. Its advice exceptions happening
    inside middleware classes should return appropriate responses directly.


## **Exception Handlers**
Exception Handlers are classes or functions that handles specific exception type response generation.

Below is an example of ExceptionHandler that handles `HTTPException` in the application:
```python
import typing as t

from ellar.common.interfaces import IExceptionHandler, IHostContext
from starlette.exceptions import (
    HTTPException as StarletteHTTPException,
)
from starlette.responses import Response


class HTTPExceptionHandler(IExceptionHandler):
    exception_type_or_code = StarletteHTTPException

    async def catch(
        self, ctx: IHostContext, exc: StarletteHTTPException
    ) -> t.Union[Response, t.Any]:
        assert isinstance(exc, StarletteHTTPException)
        config = ctx.get_app().config

        if exc.status_code in {204, 304}:
            return Response(status_code=exc.status_code, headers=exc.headers)

        if isinstance(exc.detail, (list, dict)):
            data = exc.detail
        else:
            data = {"detail": exc.detail, "status_code": exc.status_code}  # type: ignore[assignment]

        return config.DEFAULT_JSON_CLASS(
            data, status_code=exc.status_code, headers=exc.headers
        )
```
In the example above, `HTTPExceptionHandler.catch` method will be called when `ExeceptionMiddleware` detect exception of type `HTTPException`.
And its return response to the client.


## **Creating Custom Exception Handler**

To create an exception handler for your custom exception, you have to make a class that follows the `IExceptionHandler` contract.

At the root project folder, create a file `custom_exceptions.py`,

```python
# project_name/custom_exceptions.py
import typing as t
from ellar.common import IExceptionHandler, IHostContext
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
from ellar.common import IExceptionHandler, IHostContext, render_template
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
    Ellar will look for `405.html` in all registered modules. So `car` folder, create a `templates` folder and add `405.html`.

The same way can create Handler for `500` error code.


## **Registering Exception Handlers**
We have successfully created two exception handlers `ExceptionHandlerAction405` and `MyCustomExceptionHandler` but they are not yet visible to the application.

- `config.py`: The config file holds manage application settings. The `EXCEPTION_HANDLERS` variable defines all custom exception handlers registered to `ExceptionMiddlewareService` when bootstrapping the application.

```python
# project_name/config.py
import typing as t
from ellar.core import ConfigDefaultTypesMixin
from ellar.common import IExceptionHandler
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

from ellar.common.constants import ELLAR_CONFIG_MODULE
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
from ellar.common import IHostContext, IExceptionHandler, APIException
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

## **Declaring Exception Handler as a function**
In the previous section, we have seen how to create a custom ExceptionHandler from `IExceptionHandler`. In this section we will do the same using a plane function. 

For example, lets say we have a function `exception_handler_fun` as shown below

```python
from starlette.responses import PlainTextResponse
from ellar.common import IExecutionContext


def exception_handler_fun(ctx: IExecutionContext, exc: Exception):
    return PlainTextResponse('Bad Request', status_code=400)
```

To get the `exception_handler_fun` to work as an ExceptionHandler, you will need `CallableExceptionHandler` from `ellar.common.exceptions` package.

```python
from starlette.responses import PlainTextResponse
from ellar.common import IExecutionContext
from ellar.common.exceptions import CallableExceptionHandler


def exception_handler_fun(ctx: IExecutionContext, exc: Exception):
    return PlainTextResponse('Bad Request', status_code=400)


exception_400_handler = CallableExceptionHandler(
    exc_class_or_status_code=400, callable_exception_handler=exception_handler_fun
)
```
In the above example, you have created `exception_400_handler` Exception Handler to handler http exceptions with status code 400.
And then it can be registed as an exception handler as we did in previous section

```python
from .custom_exception_handlers import exception_400_handler


class BaseConfig(ConfigDefaultTypesMixin):
    EXCEPTION_HANDLERS: List[IExceptionHandler] = [
        exception_400_handler
    ]
```

Also, `exception_handler_fun` can be made to handle an custom exception type as shown below.
```python
from starlette.responses import PlainTextResponse
from ellar.common import IExecutionContext
from ellar.common.exceptions import CallableExceptionHandler


class CustomException(Exception):
    pass


def exception_handler_fun(ctx: IExecutionContext, exc: Exception):
    return PlainTextResponse('Bad Request', status_code=400)


exception_custom_handler = CallableExceptionHandler(
    exc_class_or_status_code=CustomException, callable_exception_handler=exception_handler_fun
)
```
In the above example, `exception_custom_handler` 
