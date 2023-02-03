
Ellar provides a variety of function decorators in the `ellar.common` python module that can be used to modify the behavior of route functions. 
These decorators can be used to change the response type of a route function, add filters to the response schema, define the OPENAPI context, and more. 
In general, these decorators can help to simplify and streamline the process of creating routes.

## **HTTP Method Decorator**
`@get`, `@post`, `@put`, `@patch`, `@delete`, `@trace`, `@options`, `@head` are decorators that define the standard HTTP methods for a route function. 
They indicate the type of HTTP request that the route function can handle, such as a `GET` request or a `POST` request. 

`@http_route` is a decorator that can be used to define a route that can handle **multiple** HTTP methods at once. 

`@ws_route` is a decorator that is used to define a route that can handle **WebSocket** connections. 

These decorators help to specify which type of request a route function can handle.


## **Route Function Parameters Decorators**
These decorators are Pydantic `ModelField` that can be used to define and validate the dependencies of route function parameters. 
They are used to ensure that the specified parameters are present in the request and are of the correct type. 
If any of the specified parameters are missing or are of an invalid type, the decorators will raise a `422` error code and also provide a clear error message if the input validation fails.
This helps to ensure that the application is receiving valid input and can process the request correctly. 

- `Body(..., embed=False)`
- `Form(..., embed=True)`
- `Query(...)`
- `File(...)`
- `Path(...)`
- `Header(...)`
- `Cookie(...)`

Please refer to the "How-to-Guide" on parsing inputs [here](/ellar/parsing-inputs/) to see how this input decorators work. 

### WsBody(..., embed=False)

`WsBody(...)` is a decorator that defines the message format that should be transmitted from the client in a WebSocket when there is a successful connection. 
This decorator can be used to specify the structure of the message that is sent over the WebSocket, and to validate the message against a specified schema
but for only `use_extra_handler=True`.

For example:
```python
from ellar.common import WsBody, ws_route
from ellar.core import WebSocket
...
@ws_route('/websocket', use_extra_handler=True)
def sample_endpoint_ws(self, websocket: WebSocket, data_schema: str = WsBody()):
    pass

@sample_endpoint_ws.connect
async def on_connect(self, websocket: WebSocket):
    await websocket.accept()

@sample_endpoint_ws.disconnect
async def on_connect(self, websocket: WebSocket, code: int):
    await websocket.close(code)
```

## **Non Route Function Parameters Decorators**
We discussed decorators that are used to define route function parameter dependencies in Ellar. 
These decorators, such as `Query`, `Form`, and `Body`, etc. are pydantic models used to specify the expected parameters for a route function. 
However, there are also some route parameters that are **system** dependent, such as the `request` or `websocket` object, and the `response` object. 
These parameters are resolved by the application and supplied to the route function when needed, and are not specified with pydantic models or user input.

### Provide(Type)
The **Provide(Type)** decorator is used to resolve a service provider and inject it into a route function parameter. 
This can be useful when using the ModuleRouter feature in Ellar. 
It allows for easy injection of services into route functions, making it easier to manage dependencies and improve code organization. 
This can be useful for resolving database connections, external APIs, or other resources that are used by the route function.

For example:
```python
from ellar.common import ModuleRouter, Provide
from ellar.core import App, Config

router = ModuleRouter('/test-provide')

@router.get('/app')
def example_endpoint(app: Provide(App), config: Provide(Config)):
    assert isinstance(app, App)
    assert app.config == config
    assert isinstance(config, Config)
    return {'message': 'injected App and Configuration object to route function'}
```
In the example above, `example_endpoint` function has two parameters `app` and `config` which are decorated with `Provide(Type)` decorator.
This decorator tells the application to resolve the `App` and `Config` service providers and inject them as the `app` and `config` parameters when the endpoint is called.

This allows for easy access to the objects without having to manually import and instantiate them. 
It also makes the code more modular and easier to test.

!!! info
    Only types registered in the application can be resolved, but you can set `INJECTOR_AUTO_BIND = True` in configuration for the injector to register automatically that are not found. 
    please note that this automatic registration will be scoped to singleton by the `EllarInjector`.

### Context
The **Context()** decorator injects the current `IExecutionContext` to route function parameter. See [ExecutionContext](/basics/execution-context)

For example:
```python
from ellar.common import ModuleRouter, Context

router = ModuleRouter('/test-context')

@router.get('/')
def example_endpoint(ctx = Context()):
    http_connection_instance = ctx.switch_to_http_connection().get_client()
    query_params = http_connection_instance.query_params
    return {'message': 'inject execution context', 'query_params': query_params}
```

In this example, the example_endpoint function is decorated with the **Context()** decorator, which injects the current `IExecutionContext` object into the `ctx` parameter of the function. 
The `IExecutionContext` object provides access to various resources and information related to the current execution context, such as the current HTTP connection, query parameters, and more. 
In this example, the `switch_to_http_connection()` method is used to access the current HTTP connection and the `get_client()` method is used to get the client object for the connection. 
The `query_params` attribute of the client object is then accessed and included in the response returned by the endpoint.

### Req
**Req()** decorator injects current `Request` object to route function parameter.

For example:
```python
from ellar.common import ModuleRouter, Req

router = ModuleRouter('/test-req')

@router.get('/')
def example_endpoint(req = Req()):
    headers = req.headers
    query_params = req.query_params
    return {'message': 'injected request object', 'headers': headers, 'query_params': query_params}

```

In this example, the `example_endpoint` function has a parameter req decorated with `Req()`, which will be automatically populated with the current `Request` object at runtime. 
The `headers` and `query_params` attributes of the `req` object can then be accessed and used within the function.

### Res
**Res()** decorator injects current `Response` object to route function parameter.

For example:
```python
from ellar.common import ModuleRouter, Res

router = ModuleRouter('/test-response')

@router.get('/')
def example_endpoint(res = Res()):
    res.headers['x-custom-header'] = 'hello'
    return {'message': 'inject response object'}

```

In this example, the `Res()` decorator injects the current `Response` object to the `res` parameter of the `example_endpoint` function. 
This will allow you to manipulate the headers of the response before it is sent back to the client.

### Ws
**Ws()** decorator injects current `WebSocket` object to route function parameter.

For example:
```python
from ellar.common import ModuleRouter, Ws

router = ModuleRouter('/test-ws')

@router.ws_route('/')
async def example_endpoint(ws = Ws()):
    await ws.accept()
    await ws.send_json({'message': 'injected WebSocket object to route function'})
```
The above code creates a WebSocket route '/test-ws' and when a client connects to this route, 
the `example_endpoint` function is executed. The `Ws` decorator injects the current `WebSocket` object to the `ws` parameter of the function, which can then be used to interact with the WebSocket connection, such as accepting the connection and sending data to the client.

### Host
**Host()** decorator injects current client host address to route function parameter.

### Session
**Session()** decorator injects current Session object to route function parameter.

### Http
**Http()** decorator injects current HTTP connection object to route function parameter.

## **Creating a Custom Parameter Decorators**
You can still create your own route parameter decorators that suits your need. You simply need to follow a contract, `NonParameterResolver`, and override the resolve function.

The `NonParameterResolver` has two attribute, `type_annotation` and `parameter_name`, that are provided automatically when computing route parameter dependencies. 
They are gotten from the application of the NonParameterResolver, like so - `def s(parameter_name:type_annotation = NonParameterResolver())`.

`NonParameterResolver` receives current `IExecutionContext` must return a tuple of dict object of the resulting resolve data with `parameter_name` and list of errors if any. As shown in the return statements in the example below.

For example:
```python
import typing as t
from ellar.core.params import NonParameterResolver
from ellar.core import IExecutionContext
from pydantic.error_wrappers import ErrorWrapper


class UserParam(NonParameterResolver):
    async def resolve(self, ctx: IExecutionContext, **kwargs: t.Any) -> t.Any:
        request = ctx.switch_to_http_connection().get_request()
        user = request.get('user', None)
        if user:
            return {self.parameter_name: user}, []
        return {}, [ErrorWrapper('Authenticated Users Only', loc='system')]
```

This example defines a custom decorator called `UserParam` that inherits from `NonParameterResolver`. 
The `resolve` method is overridden to extract the user from the current `IExecutionContext`'s request. 
If the user is found, it is returned as a dict with the key as the `parameter_name` of the decorator, along with an empty list of errors. 
If no user is found, an empty dict and a list of errors containing an ErrorWrapper object is returned. 

This `UserParam` decorator can then be used to inject the user object to a route function parameter like so:
```python

@router.get('/user')
def example_endpoint(user: UserParam()):
    return {'message': 'injected user object to route function', 'user': user}

```

## **Route Function Decorators**
These decorators are used to modify the output data of a route function, add filtering to the output schema, or add extra OPENAPI information about the route function.

They include:
### RENDER
**@render()** decorator converts a route function response to HTML template response. 

for example: 
```python
from ellar.common import get, render
...
@get('/index-template')
@render(template_name='my_template')
def index(self):
    return {'name': 'Ellar Template'}
```

In the example, the index function is decorated with the `render` decorator, 
which will return a 200 status code and HTML content from my_template. 
The return object from the index function will be used as the templating context for `my_template` during the template rendering process. 
This allows the function to pass data to the template and have it rendered with the provided context, the rendered template will be the response body.

See [HTML Templating](/ellar/templating/templating) for more information on `render` and HTML templating with Ellar.

### FILE
**@file()** decorator converts a route function response to file or streaming response type. 
Based on the value of `streaming` parameter, file decorator creates `FileResponseModel` or `StreamingResponseModel`.

#### FileResponseModel as file(streaming=False)
When `streaming` parameter in `@file(streaming=False)` decorator is set to `False`, a `FileResponseModel` is created as the response model for the decorated route function. 
And the route function is required to return a dictionary object that follows a `FileResponseModelSchema` format:

```python
import typing as t
from enum import Enum
from ellar.serializer import Serializer


class ContentDispositionType(str, Enum):
    inline = "inline"
    attachment = "attachment"

    
class FileResponseModelSchema(Serializer):
    path: str
    media_type: t.Optional[str] = None
    filename: t.Optional[str] = None
    method: t.Optional[str] = None
    content_disposition_type: ContentDispositionType = ContentDispositionType.attachment
```

- `path`: This is a required key whose value defines the path to the file to attach to the response.
- `filename`: when specified, it will be used as the attached file's filename. The default value is computed from the file referenced.
- `content_disposition_type`: defines the content disposition type, can be either inline or attachment. The default is attachment.
- `media_type`: states the `MIME` type of the file to be attached. The default value is computed from the file referenced.
- `method`: HTTP method, defaults: `HEAD`

for example:
```python
from ellar.common import get, file
...
@get()
@file(media_type='text/html', streaming=False)
def file_download(self):
    return {'path': 'path/to/file.html', 'filename': 'code.html', 'content_disposition_type': 'attachment'}
```
In the example, an additional parameter media_type is added to the @file(streaming=False) decorator to define the content-type of the file returned. This is helpful for creating the route function's OPENAPI documentation, as it allows the content-type to be defined upfront. Without this parameter, the content-type will be computed during runtime when returning a response for a request.
It is a way to explicitly define the content-type of the file which will be returned.

#### StreamingResponseModel as file(streaming=True)
On the other hand, when `streaming` parameter in `@file(streaming=True)` decorator is set to `True`, a `StreamingResponseModel` is created as the response model for the decorated route function. 
And the route function is required to return an `ContentStream`. `ContentStream` is an synchronous or asynchronous iterator of string or bytes. 
Type definition is shown below.

```python
import typing
import asyncio
from ellar.common import get, file

Content = typing.Union[str, bytes]
SyncContentStream = typing.Iterator[Content]
AsyncContentStream = typing.AsyncIterable[Content]
ContentStream = typing.Union[AsyncContentStream, SyncContentStream]

async def slow_numbers(minimum: int, maximum: int):
    yield ("<html><body><ul>")
    for number in range(minimum, maximum + 1):
        yield "<li>%d</li>" % number
        await asyncio.sleep(0.01)
    yield ("</ul></body></html>")
    
...
@get('/stream')
@file(media_type='text/html', streaming=True)
def file_stream(self):
    # file_stream function must return ContentStream
    return slow_numbers(1, 4)
```

### OPENAPI-INFO
**@openapi_info()** decorator adds extra route function OPENAPI properties to route function OPENAPI documentation. They include:

Parameters:

- `tags`: adds more OPENAPI tags to route function OPENAPI docs.
- `deprecated`: marks route function as deprecated. Default is false
- `descriptions`: adds description to route function OPENAPI docs
- `operation_id`: modifies operationid for the route function OPENAPI docs
- `summary`: adds summary to route function OPENAPI docs

For example:
```python
from ellar.common import get, openapi_info

...
@get("/open-api-info")
@openapi_info(
    tags=['query'], 
    deprecated=False, 
    description='open api info testing', 
    operation_id='some-operation-id', 
    summary='some summary'
)
def openapi_info_function(self, query: str):
    return f"foo bar {query}"
```

### SERIALIZER-FILTER
**@serializer_filter()** decorator provides Pydantic filtering options to decorated route function output schema.

Parameters:

- `include`: fields to include in the returned dictionary
- `exclude`: fields to exclude from the returned dictionary
- `by_alias`: whether field aliases should be used as keys in the returned dictionary; default `False`
- `exclude_unset`: whether fields which were not explicitly set when creating the model should be excluded from the returned dictionary; default `False`.
- `exclude_defaults`: whether fields which are equal to their default values (whether set or otherwise) should be excluded from the returned dictionary; default `False`
- `exclude_none`: whether fields which are equal to None should be excluded from the returned dictionary; default `False`

For example:
```python
import typing as t
from ellar.common import serializer_filter, get
from ellar.serializer import Serializer

class UserSchema(Serializer):
    username: str
    password: str
    first_name: t.Optional[str]
    last_name: t.Optional[str]

...
@get("/serialize-filter-1", response=UserSchema)
@serializer_filter(exclude_none=True, exclude={'password'})
def serialized_output_1(self):
    return dict(username='python', password='secret', first_name='ellar')

```
In example, `serializer_filter` to filter values that are `None` and also excluded `password` property from been returned.
See [Pydantic Model Export](https://docs.pydantic.dev/usage/exporting_models/#modeldict) for more examples.

### VERSION
**@version()**  is a decorator that provides endpoint versioning for a route function. 
This decorator allows you to specify the version of the endpoint that the function is associated with. 
Based on the versioning scheme configuration in the application, versioned route functions are called. This can be useful for maintaining backward compatibility, or for rolling out new features to different versions of an application. 
More information on how to use this decorator can be found in the [Versioning documentation]()

A quick example on how to use `version` decorator:
```python
from ellar.common import post, version

@post("/create", name='v2_v3_list')
@version('2', '3')
async def get_item_v2_v3(self):
    return {'message': 'for v2 and v3 request'}
```

The `version` decorator takes a list of values as an argument, for example `@version('2', '3')`. 
This indicates that the `get_item_v2_v3` route function will handle version 2 and version 3 requests of the /create endpoint. 
This allows for multiple versions of the same endpoint to be handled by different route functions, each with their own logic and implementation.

### GUARDS
**@guards()**  is a decorator that applies a protection class of type GuardCanActivate to a route function. 
These protection classes have a can_execute function that is called to determine whether a route function should be executed. 
This decorator allows you to apply certain conditions or checks before a route function is executed, such as authentication or authorization checks. 
This can help to ensure that only authorized users can access certain resources. 
More information on how to use this decorator can be found in the [Guard Documentation]()

A quick example on how to use `guards` decorator:
```python
import typing as t
from ellar.common import get, guards
from ellar.core.guard import APIKeyQuery
from ellar.core.connection import HTTPConnection


class MyAPIKeyQuery(APIKeyQuery):
    async def authenticate(self, connection: HTTPConnection, key: t.Optional[t.Any]) -> t.Optional[t.Any]:
        if key == 'supersecret':
            return True
        return False


@get("/")
@guards(MyAPIKeyQuery(), )
async def get_guarded_items(self):
    return {'message': 'worked fine with `key`=`supersecret`'}
```
The `guards` decorator, like the `version` decorator, takes a list of values as an argument. 
During a request, the provided guards are called in the order in which they are provided. 
This allows you to apply multiple guards to a single route function and have them executed in a specific order. 
This is useful for applying multiple levels of security or access control to a single endpoint. 
Each guard class has a `can_execute` function that is called in the order specified by the decorator, if any of the guard's `can_execute` function returns False, the route function will not be executed.

## **Command Decorators**
The `command` decorator is used to convert a decorated function into a command that can be executed through the Ellar command-line interface (CLI) actions. 
This allows you to define custom commands that can be run from the command-line, which can be useful for tasks such as running database migrations, generating code, or other tasks that can be automated.

See [Ellar-CLI Custom Commands](https://eadwincode.github.io/ellar-cli/custom-commands/)

## **Module Function Decorators**

- `@exception_handler`: This decorator is used to register a function as an exception handler. This function will be called when an unhandled exception occurs during a request. It should take the exception instance as its only argument and return a response object.

- `@middleware`: This decorator is used to register a function as a middleware. Middlewares are called for each incoming request and can be used to modify the request or response, or perform any other actions before or after the request is handled.

- `@template_filter`: This decorator is used to register a function as a Jinja2 template filter. The function should take one or more arguments and return a modified value.

- `@template_global`: This decorator is used to register a function as a global variable available in all Jinja2 templates. The function can be called without any arguments and should return a value.

- `@on_shutdown`: This decorator is used to register a function that will be called when the application is shutting down.

- `@on_startup`: This decorator is used to register a function that will be called when the application is starting up.

These decorators can be used to define functions that will be executed at specific points in the application's lifecycle. 
They provide a way to separate and organize the different parts of an application. See [Module Additional Configuration](../modules/#additional-module-configurations) for examples on how these decorator functions are used.
