# **Exceptions & Exception Handling**
Ellar includes a built-in exceptions middleware, known as `ExceptionMiddleware`, responsible for processing all exceptions 
that occur within an application. When an exception goes unhandled by your application code, 
it is intercepted by this middleware, which then automatically sends an appropriate, user-friendly response.

```json
{
  "status_code": 403,
  "detail": "Forbidden"
}
```
Depending on the application's configuration and the value of `DEBUG`, the exception handling behavior differs. 
When `config.DEBUG` is True, the exception that is raised is shown to the client for easy error debugging. 
However, when `config.DEBUG` is False, a 500 error is returned to the client, as illustrated below:

```json
{
  "statusCode": 500,
  "message": "Internal server error"
}
```

Ellar manages various types of exceptions by default:

- **`HTTPException`**: Provided by `Starlette` to handle HTTP errors.eg. `HTTPException(status_code, detail=None, headers=None)`
- **`WebSocketException`**: Provided by `Starlette` to manage websocket errors. eg `WebSocketException(code=1008, reason=None)`
- **`RequestValidationException`**: Provided by `Pydantic` for validation of request data
- **`APIException`**: It is a type of exception designed for REST API-based applications. It offers a more conceptual approach to handling errors and provides a simple interface for creating other custom exceptions in your application without requiring an additional exception handler.

    For example,

    ```python
    from ellar.common import APIException
    from starlette import status
    
    class ServiceUnavailableException(APIException):
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        code = 'service_unavailable'
    
    ```

### **Built-in APIExceptions**
Ellar offers a set of standard exceptions that inherit from the base `APIException`. 
These exceptions are available within the `ellar.common` package and represent many of the most common HTTP exceptions:

- `AuthenticationFailed`
- `ImproperConfiguration`
- `MethodNotAllowed`
- `NotAcceptable`
- `NotAuthenticated`
- `NotFound`
- `PermissionDenied`
- `UnsupportedMediaType`

## **Throwing standard exceptions**
Let's use the `ServiceUnavailableException` in our previous project.

For example, in the `CarController`, we have a `get_all()` method (a `GET` route handler). 
Let's assume that this route handler throws an exception for some reason. 
To demonstrate this, we'll hard-code it as follows:

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
When we raise the `ServiceUnavailableException`, it produces a `JSON` response because `Ellar` has implemented 
an exception handler for any `APIException` exception type. We will see how to change the default exception handler later.

Another error presentation is available on the APIException instance:

- `.detail`: returns the textual description of the error.
- `get_full_details()`: returns both the textual description and other information about the error.


```shell
>>> print(exc.detail)
Service Unavailable
>>> print(exc.get_full_details())
{'detail':'Service Unavailable','code':'service_unavailable', 'description': 'The server cannot process the request due to a high load'}
```


## **Exception Handlers**
Exception Handlers are classes or functions that handles what response that is returned to the client for specific exception types.

Here is an example of an ExceptionHandler that handles `HTTPException` in the application:

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
In the example above, `HTTPExceptionHandler` will be registered in a key-value data structure of exception handlers.
Where `exception_type_or_code` is the key and the `HTTPExceptionHandler` class is the value. 

During exception handling, `HTTPExceptionHandler.catch` method will be called when `ExceptionMiddleware` detect an exception of type `HTTPException`.
And then, a JSON response is created and returned to the client.


## **Creating Custom Exception Handler**
To create an exception handler for your custom exception, you need to create a class that follows the `IExceptionHandler` contract.

At the root project folder, create a file named `custom_exceptions.py`:

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

- `exception_type_or_code`: defines the `exception class` OR `status code` as a key to identify an exception handler.
- `catch()`: define the exception handling code and response a `Response` object to be returned to the client.

### **Creating Exception Handler for status code**
Let's create a handler for the `MethodNotAllowedException`, which corresponds to the HTTP status code `405`.

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
In this code snippet, we've registered a handler for any `HTTP` exception with a `405` status code, and we return a template, `405.html`, as a response. 
Similarly, you can create an exception handler for the `500` status code that returns an HTML template.

!!!info
    Ellar will search for `405.html` in all registered modules. So, within the `car` folder, create a templates folder and add `405.html`.


## **Registering Exception Handlers**
We have successfully created two exception handlers `ExceptionHandlerAction405` and `MyCustomExceptionHandler` but they are not yet visible to the application.

=== "Using config.py"
    In the `config.py` file, which holds application settings, you can define custom exception handlers to be registered with the `ExceptionMiddlewareService` during the application's bootstrapping process.
    
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
=== "Using Application Instance"
    Alternatively, you can add exception handlers directly through the app instance in your application:

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
We have seen how to create an exception handler for status codes or for a specific exception type. 
The same applies to when we want to override an existing exception handler in Ellar project.

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
Once you register the `OverrideAPIExceptionHandler` exception handler, it will become the default `handler` for the `APIException` exception type.

## **Declaring Exception Handler as a function**
In the previous section, we saw how to create a custom ExceptionHandler from `IExceptionHandler`. In this section, we'll achieve the same result using a plain function.

For example, let's say we have a function `exception_handler_fun` as shown below:

```python
from starlette.responses import PlainTextResponse
from ellar.common import IExecutionContext


def exception_handler_fun(ctx: IExecutionContext, exc: Exception):
    return PlainTextResponse('Bad Request', status_code=400)
```
To make the `exception_handler_fun` work as an ExceptionHandler, you will need to use `CallableExceptionHandler` from the `ellar.common.exceptions` package:

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
In the example above, you have created an `exception_400_handler` Exception Handler to handle HTTP exceptions with a status code of 400. 
You can then register it as an exception handler in your configuration, as we did in the previous section:

Additionally, `exception_handler_fun` can be configured to handle a custom exception type, as shown below:

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
In this example, `exception_custom_handler` is configured to handle a custom exception type, CustomException.
