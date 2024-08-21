# **Authentication Schemes Strategy**

Authentication scheme is another strategy for identifying the user who is using the application. The difference between it and
and Guard strategy is your identification executed at middleware layer when processing incoming request while guard execution
happens just before route function is executed.

Ellar provides `BaseAuthenticationHandler` contract which defines what is required to set up any authentication strategy. 
We are going to make some modifications on the existing project to see how we can achieve the same result and to show how authentication handlers in ellar.

### Creating a JWT Authentication Handler
Just like AuthGuard, we need to create its equivalent. But first we need to create a `auth_scheme.py` at the root level 
of your application for us to define a `JWTAuthentication` handler. 


```python title='prject_name/auth_scheme.py' linenums='1'
import typing as t
from ellar.common.serializer.guard import (
    HTTPAuthorizationCredentials,
)
from ellar.auth import UserIdentity
from ellar.auth.handlers import HttpBearerAuthenticationHandler
from ellar.common import IHostContext
from ellar.di import injectable
from ellar_jwt import JWTService


@injectable
class JWTAuthentication(HttpBearerAuthenticationHandler):
    def __init__(self, jwt_service: JWTService) -> None:
        self.jwt_service = jwt_service

    async def authentication_handler(
        self,
        context: IHostContext,
        credentials: HTTPAuthorizationCredentials,
    ) -> t.Optional[t.Any]:
        # this function will be called by Identity Middleware but only when a `Bearer token` is found on the header request
        try:
            data = await self.jwt_service.decode_async(credentials.credentials)
            return UserIdentity(auth_type=self.scheme, **data)
        except Exception as ex:
            # if we cant identity the user or token has expired, we return None.
            return None
```

Let us make `JWTAuthentication` Handler available for ellar to use as shown below

```python title='project_name.server.py' linenums='1'
import os
from ellar.common.constants import ELLAR_CONFIG_MODULE
from ellar.app import AppFactory, use_authentication_schemes
from ellar.core import LazyModuleImport as lazyLoad
from .auth_scheme import JWTAuthentication


application = AppFactory.create_from_app_module(
    lazyLoad('project_name.root_module:ApplicationModule'),
    config_module=os.environ.get(
        ELLAR_CONFIG_MODULE, "project_name.config:DevelopmentConfig"
    ),
)
use_authentication_schemes(JWTAuthentication)
```
Unlike guards, Authentication handlers are registered global by default as shown in the above illustration. 
Also, we need to remove `GlobalGuard` registration we did in `AuthModule`, 
so that we don't have too user identification checks.

!!!note
    In the above illustration, we added JWTAuthentication as a type.
    This means DI will create JWTAuthentication instance.
    We can use this method because we want `JWTService` to be injected when instantiating `JWTAuthentication`. 
    But if you don't have any need for DI injection, you can use the below.
    ```python
    ...
    application.add_authentication_schemes(JWTAuthentication())
    ## OR
    ## use_authentication_schemes(JWTAuthentication())
    ```

We need
to refactor auth controller and mark `refresh_token` and `sign_in` function as public routes
by using `SkipAuth` decorator from `ellar.auth` package.

```python title='auth/controller.py' linenums='1'
from ellar.common import Controller, ControllerBase, post, Body, get
from ellar.auth import SkipAuth, AuthenticationRequired
from ellar.openapi import ApiTags
from .services import AuthService


@AuthenticationRequired('JWTAuthentication')
@Controller
@ApiTags(name='Authentication', description='User Authentication Endpoints')
class AuthController(ControllerBase):
    def __init__(self, auth_service: AuthService) -> None:
        self.auth_service = auth_service

    @post("/login")
    @SkipAuth()
    async def sign_in(self, username: Body[str], password: Body[str]):
        return await self.auth_service.sign_in(username=username, password=password)

    @get("/profile")
    async def get_profile(self):
        return self.context.user
    
    @SkipAuth()
    @post("/refresh")
    async def refresh_token(self, payload: str = Body(embed=True)):
        return await self.auth_service.refresh_token(payload)


```
In the above illustration,
we decorated AuthController with `@AuthenticationRequired('JWTAuthentication')`
to ensure we have authenticated user before executing any route function and, 
we passed in `JWTAuthentication` as a parameter,
which will be used in openapi doc to define the controller routes security scheme.

It is importance to note that when using `AuthenticationHandler` approach,
that you have
to always use `AuthenticationRequired` decorator on route functions or controller
that needs protected from anonymous users.

But if you have a single form of authentication,
you can register `AuthenticatedRequiredGuard` from `eellar.auth.guard` module globally
just like we did in [applying guard globally](./guard-strategy.md#apply-authguard-globally)

```python title='auth/module.py' linenums='1'
from datetime import timedelta

from ellar.app import use_global_guards
from ellar.auth.guards import AuthenticatedRequiredGuard
from ellar.common import Module
from ellar.core import ModuleBase, LazyModuleImport as lazyLoad
from ellar_jwt import JWTModule

from .controllers import AuthController
from .services import AuthService

## Registers AuthenticatedRequiredGuard to the GLOBAL GUARDS
use_global_guards(AuthenticatedRequiredGuard('JWTAuthentication', []))

@Module(
    modules=[
        lazyLoad('project_name.users.module:UserModule'),
        JWTModule.setup(
            signing_secret_key="my_poor_secret_key_lol", lifetime=timedelta(minutes=5)
        ),
    ],
    controllers=[AuthController],
    providers=[AuthService],
)
class AuthModule(ModuleBase):
    """
    Auth Module
    """
```

Still having the server running, we can test as before

```shell
$ # GET /auth/profile
$ curl http://localhost:8000/auth/profile
{"detail":"Forbidden"} # status_code=403

$ # POST /auth/login
$ curl -X POST http://localhost:8000/auth/login -d '{"username": "john", "password": "password"}' -H "Content-Type: application/json"
{"access_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2OTg3OTE0OTE..."}

$ # GET /profile using access_token returned from previous step as bearer code
$ curl http://localhost:8000/auth/profile -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2Vybm..."
{"exp":1698793558,"iat":1698793258,"jti":"e96e94c5c3ef4fbbbd7c2468eb64534b","sub":1,"user_id":1,"username":"john", "id":null,"auth_type":"bearer"}

```
Source Code to this example is [here](https://github.com/python-ellar/ellar/tree/main/examples/04-auth-with-handlers)
