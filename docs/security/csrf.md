# **CSRF or XSRF**
CSRF or XSRF is a security vulnerability and attack method in web applications. It involves tricking a user's browser 
into sending unauthorized requests to a website where the user is authenticated, allowing attackers to perform actions on behalf of the user.

## **Available ASGI CSRF Middlewares**

- [Piccolo CSRF Middleware](https://piccolo-api.readthedocs.io/en/latest/csrf/usage.html)
- [Starlette CSRF](https://pypi.org/project/starlette-csrf/)

These middlewares can be configured as every other asgi middleware as shown in middleware [docs](../overview/middleware.md#applying-middleware) to work in Ellar

For example, using [Starlette CSRF](https://pypi.org/project/starlette-csrf/) Middleware
```python
# config.py
import typing as t
from ellar.core.middleware import Middleware
from starlette_csrf import CSRFMiddleware

class Development(BaseConfig):
    DEBUG: bool = True
    # Application middlewares
    MIDDLEWARE: t.Sequence[Middleware] = [
        Middleware(
            CSRFMiddleware, 
            secret="__CHANGE_ME__", 
            cookie_name='csrftoken', 
            safe_methods={"GET", "HEAD", "OPTIONS", "TRACE"}
        )
    ]

```

## **CORS**
Cross-origin resource sharing (CORS) is a mechanism that allows resources to be requested from another domain. 
Under the hood, Ellar registers CORS Middleware and provides CORS options in application for CORS customization.
See how to configure **CORS** [here](../overview/middleware.md#corsmiddleware)
