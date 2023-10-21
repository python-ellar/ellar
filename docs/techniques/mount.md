# **Mount**
In Starlette, `Mount` is used to mount sub-routes and ASGI apps or WSGI apps. The same is applicable in Ellar.

Let's see how to mount sub-routes in ellar
```python

from starlette.routing import Mount
from ellar.common.routing import RouteOperation
from ellar.core import Request

def users(request:Request):
    return "List of users"

def user(username: str, request:Request):
    return f"Users Profile of {username}"


mount = Mount(
    path='/users', 
    routes=[
        RouteOperation(path='/', endpoint=users, methods=['GET', 'POST'], response={200: str}), 
        RouteOperation(path='/{username}', endpoint=user, methods=['GET', 'POST'], response={200: str})
    ]
)
```
In the construct above, we have created a starlette-like example of `Mount` with a base path `/users` and with two endpoints, 
`/` to get list of users and `/username` to a users profile. 

### **Mount with Ellar**
Now, we have a `mount` instance for the previous code construct, to get it to work in ellar, we need to register it to a **Module**.

For example,
```python
from ellar.common import Module
from .path_to_mount import mount


@Module(routers=[mount])
class ApplicationModule:
    pass

```

## **[Applying Middleware to Mount](https://www.starlette.io/middleware/#applying-middleware-to-mounts){target="_blank"}**
Just like in every other ASGI app, middlewares can be added to `Mount` during its instantiation.

For example,
```python
...
from starlette.middleware import Middleware
from starlette.middleware.gzip import GZipMiddleware


mount = Mount(
    path='/users', 
    routes=[
        RouteOperation(path='/', endpoint=users, methods=['GET', 'POST'], response={200: str}), 
        RouteOperation(path='/{username}', endpoint=user, methods=['GET', 'POST'], response={200: str})
    ],
    middleware=[Middleware(GZipMiddleware)]
)
```
Checkout this [documentation from starlette](https://www.starlette.io/middleware/#applying-middleware-to-mounts){target="_blank"} on some conditions to using `middleware` on Mount
