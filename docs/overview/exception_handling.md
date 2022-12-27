
Ellar `ExceptionMiddleware` together with `ExceptionMiddlewareService` are responsible for processing all unhandled exception
across the application and provides an appropriate user-friendly response.

```json
{
  "status_code": 403,
  "detail": "Forbidden"
}
```

Default exceptions types Managed by default:

- **`HTTPException`**: Default exception class provided by `Starlette` for HTTP client
- **`WebSocketException`**: Default websocket exception class also provided by `Starlette` for websocket connection
- **`RequestValidationException`**: Request data validation exception provided by `Pydantic`
- **`APIException`**: Custom exception created for typical REST API based application to provides more concept about the exception raised.

## **HTTPException**

The `HTTPException` class provides a base class that you can use for any
handled exceptions.

* `HTTPException(status_code, detail=None, headers=None)`

## **WebSocketException**

You can use the `WebSocketException` class to raise errors inside WebSocket endpoints.

* `WebSocketException(code=1008, reason=None)`

You can set any code valid as defined [in the specification](https://tools.ietf.org/html/rfc6455#section-7.4.1).

## **APIException**
As stated earlier, its an exception type for typical REST API based application. Its gives more concept to error and provides a
simple interface for creating other custom exception need in your application.

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

We have a JSON response because Ellar has an exception handler for `APIException`. This handler can be change to return some different. 
We shall how to do that on Overriding Default Exception Handlers.

There is other error presentation available on `APIException` instance:
- `.detail`: returns textual description of the error.
- `get_full_details()`: returns both textual description and other information about the error.

```shell
>>> print(exc.detail)
Service Unavailable
>>> print(exc.get_full_details())
{'detail':'Service Unavailable','code':'service_unavailable', 'description': 'The server cannot process the request due to a high load'}
```

## **Creating Custom Exception Handler**

To create an exception handler for your custom exception, you have to create a class that follow `IExceptionHandler` contract.

At the root project folder, create a file `custom_exceptions.py`,

```python
# project_name/custom_exceptions.py
import typing as t
from ellar.core.exceptions import IExceptionHandler
from ellar.core.context import IExecutionContext
from starlette.responses import Response


class MyCustomException(Exception):
    pass


class MyCustomExceptionHandler(IExceptionHandler):
    exception_type_or_code = MyCustomException
    
    async def catch(
        self, ctx: IExecutionContext, exc: MyCustomException
    ) -> t.Union[Response, t.Any]:
        app_config = ctx.get_app().config
        return app_config.DEFAULT_JSON_CLASS(
            {'detail': str(exc)}, status_code=400,
        )

```
- `exception_type_or_code`: defines the `exception class` OR `status code` to target when resolving exception handlers.
- `catch()`: defines the handling code and response to be returned to the client.

### **Creating Exception Handler for status code**
Let's create a handler for `MethodNotAllowedException` which, according to HTTP code is `405`.

```python
# project_name/apps/custom_exceptions.py
import typing as t
from ellar.core.exceptions import IExceptionHandler
from ellar.core.context import IExecutionContext
from ellar.core import render_template
from starlette.responses import Response
from starlette.exceptions import HTTPException

class MyCustomException(Exception):
    pass


class MyCustomExceptionHandler(IExceptionHandler):
    exception_type_or_code = MyCustomException
    
    async def catch(
        self, ctx: IExecutionContext, exc: MyCustomException
    ) -> t.Union[Response, t.Any]:
        app_config = ctx.get_app().config
        return app_config.DEFAULT_JSON_CLASS(
            {'detail': str(exc)}, status_code=400,
        )
    

class ExceptionHandlerAction405(IExceptionHandler):
    exception_type_or_code = 405
    
    async def catch(
        self, ctx: IExecutionContext, exc: HTTPException
    ) -> t.Union[Response, t.Any]:
        context_kwargs = {}
        return render_template('405.html', request=ctx.switch_to_request(), **context_kwargs)
```
We have registered a handler for any `HTTPException` with status code `405` and we have chosen to return a template `405.html` as response.

!!!info
    Ellar will look for `405.html` in all registered module. So `dogs` folder, create a `templates` folder and add `405.html`.

The same way can create Handler for `500` error code.


## **Registering Exception Handlers**
We have successfully created two exception handlers `ExceptionHandlerAction405` and `MyCustomExceptionHandler` but they are not yet visible to the application.

- `config.py`: The config file holds manage application settings including `EXCEPTION_HANDLERS` fields which defines all custom exception handlers used in the application.

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
We have gone through how to create an exception handler for status code and specific exception type. 
So, override any exception handler follows the same pattern with a target to exception class

for example:

```python
# project_name/apps/custom_exceptions.py
import typing as t
from ellar.core.exceptions import IExceptionHandler, APIException
from ellar.core.context import IExecutionContext
from starlette.responses import Response


class OverrideAPIExceptionHandler(IExceptionHandler):
    exception_type_or_code = APIException
    
    async def catch(
        self, ctx: IExecutionContext, exc: APIException
    ) -> t.Union[Response, t.Any]:
        app_config = ctx.get_app().config
        return app_config.DEFAULT_JSON_CLASS(
            {'message': exc.detail}, status_code=exc.status_code,
        )
```

Once we register `OverrideAPIExceptionHandler` exception handler, it will become the default handler for `APIException` exception type.
