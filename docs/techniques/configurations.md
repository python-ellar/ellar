# **Application Configurations**

The `config.py` file contains all the configuration necessary in bootstrapping ellar application. 

Lets in this section go through the different configuration available.

## **Configuration Variables**
### **SECRET_KEY**
Default: `' '` _(Empty string)_

A secret key is a unique and unpredictable value.

`ellar new project` command automatically adds a randomly-generated `SECRET_KEY` to each new project.

### **DEBUG**
Default: `False`

A boolean that turns on/off debug mode.

Never deploy a site into production with `DEBUG` turned `on`.

One of the main features of `debug` mode is the display of detailed error pages. 
If your app raises an exception when `DEBUG` is `True`, Ellar will display a detailed traceback.

If `DEBUG` is `False`, you also need to properly set the `ALLOWED_HOSTS` setting. Failing to do so will result in all requests being returned as `“Bad Request (400)”`.

### **INJECTOR_AUTO_BIND**
Default: `False`

A boolean that turns on/off injector `auto_bind` property.

When turned on, `injector` can automatically bind to missing types as `singleton` at the point of resolving object dependencies.
And when turned off, missing types will raise an `UnsatisfiedRequirement` exception.

### **DEFAULT_JSON_CLASS**
Default: `JSONResponse` - (`starlette.common.JSONResponse`)

**DEFAULT_JSON_CLASS** is used when sending JSON response to the client.

There are other options for JSON available in Ellar:

- **UJSONResponse**(`ellar.common.UJSONResponse`):  renders JSON response using [ujson](https://pypi.python.org/pypi/ujson){target="_blank"}. 
- **ORJSONResponse**(`ellar.common.ORJSONResponse`):  renders JSON response using [orjson](https://pypi.org/project/orjson/){target="_blank"}. 

### **JINJA_TEMPLATES_OPTIONS**
Default: `{}`

Default is an empty dictionary object. It defines options used when creating `Jinja2` Environment for templating.

Different keys available:

- `block_start_string` (str) –
- `block_end_string` (str) –
- `variable_start_string` (str) –
- `variable_end_string` (str) –
- `comment_start_string` (str) –
- `comment_end_string` (str) –
- `line_statement_prefix` (Optional[str]) –
- `line_comment_prefix` (Optional[str]) –
- `trim_blocks` (bool) –
- `lstrip_blocks` (bool) –
- `newline_sequence` (te.Literal['\n', '\r\n', '\r']) –
- `keep_trailing_newline` (bool) –
- `extensions` (Sequence[Union[str, Type[Extension]]]) –
- `optimized` (bool) –
- `undefined` (Type[jinja2.runtime.Undefined]) –
- `finalize` (Optional[Callable[[...], Any]]) –
- `autoescape` (Union[bool, Callable[[Optional[str]], bool]]) –
- `loader` (Optional[BaseLoader]) –
- `cache_size` (int) –
- `auto_reload` (bool) –
- `bytecode_cache` (Optional[BytecodeCache]) –
- `enable_async` (bool)

!!! info
    Check Jinja2 [environment option](https://jinja.palletsprojects.com/en/3.0.x/api/#high-level-api){target="_blank"} for more information.

### **VERSIONING_SCHEME**
Default: `DefaultAPIVersioning()`

**VERSIONING_SCHEME** defined the versioning scheme for the application.  
The **DefaultAPIVersioning** is placeHolder object for versioning scheme.

Other Options includes:

- **UrlPathAPIVersioning** - for url versioning. eg `https://example.com/v1` or `https://example.com/v2`
- **HostNameAPIVersioning** - for host versioning. eg `https://v1.example.com` or `https://v2.example.com`
- **HeaderAPIVersioning** - for request header versioning. eg `Accept: application/json; version=1.0`
- **QueryParameterAPIVersioning** - for request query versioning. eg `/something/?version=0.1`

### **REDIRECT_SLASHES**
Default: `False`

A boolean that turns on/off router `redirect_slashes` property.

When **REDIRECT_SLASHES** is turned on, the Application Router creates a redirect with a `/` to complete a URL path.
This only happens when the URL was not found but may exist when  `/` is appended to the URL.

For example, a route to the user profile goes like this `http://localhost:8000/user/profile/`. If a path like this is passed `http://localhost:8000/user/profile`, it will be redirected to `http://localhost:8000/user/profile` automatically.

This approach may be complex depending on the application size because ApplicationRouter has to loop through its routes twice.

When **REDIRECT_SLASHES** is turned off, URL paths have to be an exact match, or a `404` exception is raised.

### **STATIC_FOLDER_PACKAGES**
Default: `[]`

It is used to apply static files that exist in installed python package.

For example:

```python
STATIC_FOLDER_PACKAGES = [('boostrap4', 'statics')]
```
`'boostrap4'` is the package, and `'statics'` is the static folder.

### **STATIC_DIRECTORIES**
Default: `[]`

It is used to apply static files that project level

For example:

```python
STATIC_DIRECTORIES = ['project_name/staticfiles', 'project_name/path/to/static/files']
```

### **MIDDLEWARE**
Default: `[]`

**MIDDLEWARE** defines a list of user-defined ASGI Middleware to be applied to the application alongside default application middleware.

### **EXCEPTION_HANDLERS**
Default: `[]`

It defines a list of `IExceptionHandler` objects used in handling custom exceptions or any exception.

### **STATIC_MOUNT_PATH**
Default: `/static`

It configures the root path to serve static files.
For example, if there is a `stylesheet.css` in a **static** folder, and `STATIC_MOUNT_PATH=/static`,
`stylesheet.css` can be reached through the link
`http://localhost:8000/static/stylesheet.css` assuming you are on local development server.

Also, if `STATIC_MOUNT_PATH=None`, static route handler would not be registered to application routes.

### **SERIALIZER_CUSTOM_ENCODER**
Default: `ENCODERS_BY_TYPE` (`ellar.pydantic.ENCODERS_BY_TYPE`)

**SERIALIZER_CUSTOM_ENCODER** is a key-value pair of a type and function. Default is a pydantic JSON encode type.
It is used when serializing objects to JSON format.

### **DEFAULT_NOT_FOUND_HANDLER**
Default: `not_found` (`not_found(scope: TScope, receive: TReceive, send: TSend)`)

Default is an ASGI function. **DEFAULT_NOT_FOUND_HANDLER** is used by the application router as a callback function to a resource not found.

```python
from ellar.common.types import TScope, TReceive, TSend
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.websockets import WebSocketClose
from ellar.common import PlainTextResponse


async def _not_found(scope: TScope, receive: TReceive, send: TSend) -> None:
    if scope["type"] == "websocket":
        websocket_close = WebSocketClose()
        await websocket_close(scope, receive, send)
        return

    # If we're running inside a starlette application then raise an
    # exception, so that the configurable exception handler can deal with
    # returning the response. For plain ASGI apps, just return the response.
    if "app" in scope:
        raise StarletteHTTPException(status_code=404)
    else:
        response = PlainTextResponse("Not Found", status_code=404)
    await response(scope, receive, send)
```

### **DEFAULT_LIFESPAN_HANDLER**
Default: `None`

**DEFAULT_LIFESPAN_HANDLER** is a function that returns `AsyncContextManager`  used to manage `startup` and `shutdown`
together instead of having a separate handler for `startup` and `shutdown` events.

```python
import contextlib
from ellar.core import ConfigDefaultTypesMixin
from ellar.app import App


@contextlib.asynccontextmanager
async def lifespan(app: App):
    async with some_async_resource():
        yield

        
class BaseConfig(ConfigDefaultTypesMixin):
    DEFAULT_LIFESPAN_HANDLER = lifespan
```

Consider using `anyio.create_task_group()` for managing asynchronous tasks.

### **CORS_ALLOW_ORIGINS**
Default: `[]`

A list of origins that should be permitted to make cross-origin requests. e.g. `['https://example.org', 'https://www.example.org']`. 

You can use `['*']` to allow any origin.

### **CORS_ALLOW_METHODS: t.List[str]**
Default: `["GET"]`

A list of HTTP methods that should be allowed for cross-origin requests.

You can use `['*']` to allow all standard methods.

### **CORS_ALLOW_HEADERS**:
Default: `[]`

A list of HTTP request headers that should be supported for cross-origin requests. 

You can use `['*']` to allow all headers. The `Accept`, `Accept-Language`, `Content-Language` and `Content-Type` headers are always allowed for CORS requests.

### **CORS_ALLOW_CREDENTIALS**
Default: `False`

Indicate that cookies should be supported for cross-origin requests.

### **CORS_ALLOW_ORIGIN_REGEX**:
Default: `None`

A regex string to match against origins that should be permitted to make cross-origin requests. eg. `'https://.*\.example\.org'`.

### **CORS_EXPOSE_HEADERS**:
Default: `None`

Indicate any response headers that should be made accessible to the browser.

### **CORS_MAX_AGE:**
Defaults: `600`

Sets a maximum time in seconds for browsers to cache CORS responses.

### **ALLOWED_HOSTS**
Default: `["*"]`

A list of domain names that should be allowed as hostnames in `TrustedHostMiddleware`.
Wildcard domains such as `*.example.com` are supported for matching subdomains. 

To allow any hostname either use `allowed_hosts=["*"]` or omit the middleware.

### **REDIRECT_HOST**
Default: `True`

Indicates whether to append `www.` when redirecting host in `TrustedHostMiddleware`


## **Configuration with prefix**
Ellar configuration module also support loading of its configurations with appended prefix. for instance,
we can have a file `my_settings.py` with some ellar's configurations set to it with some prefix `API_` as shown below.

```python
# my_settings.py
API_DEBUG = True
API_SECRET_KEY = "your-secret-key-changed"
API_INJECTOR_AUTO_BIND = True
API_JINJA_TEMPLATES_OPTIONS = {"auto_reload": True}

OTHER_XYZ_CONFIGS_1 ='whatever'
OTHER_XYZ_CONFIGS_2 ='whatever2'
```
To apply these configurations without having to load everything, you have to provide the prefix to be used to load configurations that
belongs to ellar. For example,

```python
from ellar.app import AppFactory
from .root_module import ApplicationModule

application = AppFactory.create_from_app_module(ApplicationModule, config_module=dict(
    config_module='project_name:my_settings',
    config_prefix='api_',
))
```
In the above construct, we used a dict object to define the configuration module(`'project_name:my_settings'`) and prefix `api_`. 
This will be applied to the configuration instance when the application is ready.

## **Defining Configurations directly**
During application bootstrapping with `AppFactory`, you can define app configurations directly under `config_module` as a dict object as some below.

```python
from ellar.app import AppFactory
from .root_module import ApplicationModule

application = AppFactory.create_from_app_module(
    ApplicationModule, 
    config_module=dict(
        SECRET_KEY = "your-secret-key-changed",
        INJECTOR_AUTO_BIND = True,
        MIDDLEWARE=[],
        EXCEPTION_HANDLERS=[]
    )
)
```

## **Complete Configuration Example**

Below is a complete configuration example showing all available configuration options with their default values:

```python
import typing as t

from ellar.common import IExceptionHandler, JSONResponse
from ellar.core import ConfigDefaultTypesMixin
from ellar.core.versioning import BaseAPIVersioning, DefaultAPIVersioning
from ellar.pydantic import ENCODERS_BY_TYPE as encoders_by_type
from starlette.middleware import Middleware
from starlette.requests import Request


class BaseConfig(ConfigDefaultTypesMixin):
    DEBUG: bool = False

    DEFAULT_JSON_CLASS: t.Type[JSONResponse] = JSONResponse
    SECRET_KEY: str = "your-secret-key-here"

    # injector auto_bind = True allows you to resolve types that are not registered on the container
    # For more info, read: https://injector.readthedocs.io/en/latest/index.html
    INJECTOR_AUTO_BIND = False

    # jinja Environment options
    # https://jinja.palletsprojects.com/en/3.0.x/api/#high-level-api
    JINJA_TEMPLATES_OPTIONS: t.Dict[str, t.Any] = {}

    # Injects context to jinja templating context values
    TEMPLATES_CONTEXT_PROCESSORS: t.List[
        t.Union[str, t.Callable[[t.Union[Request]], t.Dict[str, t.Any]]]
    ] = [
        "ellar.core.templating.context_processors:request_context",
        "ellar.core.templating.context_processors:user",
        "ellar.core.templating.context_processors:request_state",
    ]

    # Application route versioning scheme
    VERSIONING_SCHEME: BaseAPIVersioning = DefaultAPIVersioning()

    # Enable or Disable Application Router route searching by appending backslash
    REDIRECT_SLASHES: bool = False

    # Define references to static folders in python packages.
    # eg STATIC_FOLDER_PACKAGES = [('boostrap4', 'statics')]
    STATIC_FOLDER_PACKAGES: t.Optional[t.List[t.Union[str, t.Tuple[str, str]]]] = []

    # Define references to static folders defined within the project
    STATIC_DIRECTORIES: t.Optional[t.List[t.Union[str, t.Any]]] = []

    # static route path
    STATIC_MOUNT_PATH: str = "/static"

    CORS_ALLOW_ORIGINS: t.List[str] = ["*"]
    CORS_ALLOW_METHODS: t.List[str] = ["*"]
    CORS_ALLOW_HEADERS: t.List[str] = ["*"]
    ALLOWED_HOSTS: t.List[str] = ["*"]

    # Application middlewares
    MIDDLEWARE: t.List[t.Union[str, Middleware]] = [
        "ellar.core.middleware.trusted_host:trusted_host_middleware",
        "ellar.core.middleware.cors:cors_middleware",
        "ellar.core.middleware.errors:server_error_middleware",
        "ellar.core.middleware.versioning:versioning_middleware",
        "ellar.auth.middleware.session:session_middleware",
        "ellar.auth.middleware.auth:identity_middleware",
        "ellar.core.middleware.exceptions:exception_middleware",
    ]

    # A dictionary mapping either integer status codes,
    # or exception class types onto callables which handle the exceptions.
    # Exception handler callables should be of the form
    # `handler(context:IExecutionContext, exc: Exception) -> response`
    # and may be either standard functions, or async functions.
    EXCEPTION_HANDLERS: t.List[t.Union[str, IExceptionHandler]] = [
        "ellar.core.exceptions:error_404_handler"
    ]

    # Object Serializer custom encoders
    SERIALIZER_CUSTOM_ENCODER: t.Dict[t.Any, t.Callable[[t.Any], t.Any]] = (
        encoders_by_type
    )
```

!!! tip
    You can copy this configuration as a starting point and modify only the values you need to change for your application.
