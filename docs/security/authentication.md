# **Authentication**
Authentication is an **essential** part of most applications. It refers to the methods and techniques used to verify the identity of users interacting with your application. There are many different approaches and strategies to handle authentication. The approach taken for any project depends on its particular application requirements.
In this section, we shall go through different approaches to authentication in Ellar and how it will suit your authentication requirements.

There are two ways in which user authentication and identification are processed in Ellar:

- [Using Guards](#1-guard-authentication)
- [Using Authentication Schemes](#2-authentication-schemes)

## **1. Guard Authentication**
We have discussed in detail how Guards are used to protect a route and check for user authorizations, but we never really addressed how they can be used for authentication purposes. For this, we are going to illustrate JWT authentication using Guard

!!!note 
    Read more on [Guards](../overview/guards.md){target=_blank}

Let's flesh out our requirements. For this use case, clients will start by authenticating with a username and password. 
Once authenticated, the server will issue a JWT that can be sent as a bearer token in an authorization header on subsequent requests to prove authentication. 
Then, we create a protected route that is accessible only to requests that contain a valid JWT.

Let's start with the first requirement: authenticating a user, then extend that by issuing a JWT. 
And finally, we'll create a protected route that checks for a valid JWT on the request.

### **Creating an authentication module**
We´ll start by scaffolding an `AuthModule` with the Ellar CLI tool followed by `AuthService` and `AuthController` implementations.
We´ll use the `AuthService` to implement the authentication logic and the `AuthController` to expose the authentication endpoints.

```shell
ellar create-module auth
```

Also, the AuthService would need UserService, which encapsulates user operations. Let's also scaffold a user module.

```shell
ellar create-module user
```

Now, let's add some implementations to the generated files. For this application, the `UserService` will be working with a hard-coded list of users with a retrieve one-by-email method. 
In a real application, you´d build your user model and persistence layer using a library of your choice like SQLAlchemy, Django ORM, Peewee, PonyORM, etc.

```python title='user.services.py' linenums="1"

from ellar.common import Serializer
from ellar.common.serializer import SerializerFilter
from ellar.di import injectable
from ellar.core.security.hashers import make_password


class UserModel(Serializer):
    _filter = SerializerFilter(exclude={'password'})

    user_id: int
    username: str
    password: str


@injectable()
class UsersService:
    users = [
        {
            'user_id': 1,
            'username': 'john',
            'password': make_password('password'),
        },
        {
            'user_id': 2,
            'username': 'clara',
            'password': make_password('guess'),
        },
    ]

    async def get_user_by_username(self, username: str) -> UserModel | None:
        filtered_list = filter(lambda item: item["username"] == username, self.users)
        found_user = next(filtered_list)
        if found_user:
            return UserModel(**found_user)

```

In the above example, we have used `make_password` to hash the password. It is strictly advised you don't save passwords as plain text.
In the `UsersModule`, we need to register the `UserService` we just created so that it will be injectable in `AuthService`

```python title='user.module.py' linenums="1"
from ellar.common import Module
from ellar.core import ModuleBase

from .services import UsersService


@Module(
    providers=[UsersService],
)
class UserModule(ModuleBase):
    """
    User Module
    """

```

### **Implementing the "Sign in" endpoint**
The `AuthService` has the job of retrieving a user and verifying the password. 
Let's create a `sign_in` function for this purpose.

```python title="auth.services.py" linenums='1'
import typing as t

from ellar.core.security.hashers import check_password
from ellar.di import injectable
from ellar.common import exceptions
from ..user.services import UsersService


@injectable()
class AuthService:
    def __init__(self, users_service: UsersService) -> None:
        self.users_service = users_service

    async def sign_in(self, username: str, password: str) -> t.Any:
        user_model = await self.users_service.get_user_by_username(username)
        if not user_model:
            raise exceptions.AuthenticationFailed()

        if not check_password(user_model.password, password):
            raise exceptions.AuthenticationFailed()

        return user_model.serialize()
```

Next, we create the AuthController and add a sign_in endpoint

```python title="auth.controllers.py" linenums="1"
from ellar.common import Controller, ControllerBase, post, Body
from .services import AuthService


@Controller
class AuthController(ControllerBase):
    def __init__(self, auth_service: AuthService) -> None:
        self.auth_service = auth_service

    @post("/login")
    async def sign_in(self, username: Body[str], password: Body[str]):
        return await self.auth_service.sign_in(username=username, password=password)
```

At this junction, the `AuthService` returns a Python dictionary object of the user retrieved if the password is correct. 
But in the real sense, we need a token returned to the client. 

For this, we need to install the `ellar-jwt` package

```shell
pip install ellar-jwt
```

Let us review and refine our requirements once again:

- Allow users to authenticate with username/password, returning a JWT for use in subsequent calls to protected API endpoints. This is almost done. What is left is to write the code that issues a JWT.
- Create API routes that are protected based on the presence of a valid JWT as a bearer token

EllarJWT comes with `JWTModule` and `JWTService` for encoding and decoding tokens. 
Let us configure the JWTModule inside AuthModule. 

!!!hint
    You can also see docs on how to use the [EllarJWT](https://github.com/python-ellar/ellar-jwt){target=_blank}

```python title="auth.module.py" linenums="1"
from datetime import timedelta

from ellar.common import Module
from ellar.core import ModuleBase
from ellar_jwt import JWTModule

from .controllers import AuthController
from ..user.module import UserModule
from .services import AuthService


@Module(
    modules=[
        UserModule,
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

In the above example, we configured `JWTModule` with very minimal configurations and registered it as a module dependency
together with `UserModule`. Also we have registered `AuthController` and `AuthService` to `AuthModule` as well. 
With that done, we have completed the `AuthModule` setup. 

Now, let us finish the `AuthService` by returning a token using `JWTService`.

```python title="auth.services.py" linenums='1'
import typing as t

from ellar.core.security.hashers import check_password
from ellar.di import injectable
from ellar.common import exceptions
from ellar_jwt import JWTService

from ..user.services import UsersService


@injectable()
class AuthService:
    def __init__(self, users_service: UsersService, jwt_service: JWTService) -> None:
        self.users_service = users_service
        self.jwt_service = jwt_service

    async def sign_in(self, username: str, password: str) -> t.Any:
        user_model = await self.users_service.get_user_by_username(username)
        if not user_model:
            raise exceptions.AuthenticationFailed()

        if not check_password(user_model.password, password):
            raise exceptions.AuthenticationFailed()

        result = {"access_token": await self.jwt_service.sign_async(dict(user_model.serialize(), sub=user_model.user_id))}
        return result
```

At this point, we can run the application to test what we have done so far. 
To do that, we need to register `AuthModule` to the `ApplicationModule`.

```python title="project_name.root_module.py" linenums="1"
from ellar.common import Module, exception_handler
from ellar.common import IExecutionContext, JSONResponse, Response
from ellar.core import ModuleBase
from ellar.samples.modules import HomeModule
from .apps.car.module import CarModule
from .apps.auth.module import AuthModule


@Module(
    modules=[HomeModule, CarModule, AuthModule],
)
class ApplicationModule(ModuleBase):
    @exception_handler(404)
    def exception_404_handler(cls, ctx: IExecutionContext, exc: Exception) -> Response:
        return JSONResponse(dict(detail="Resource not found."))
```

Then restart the server if it is not running.
```shell
ellar runserver --reload
```
Let us make some requests to the server. Open a terminal window and run the code below:
```shell
$ # POST to /auth/login
$ curl -X POST http://localhost:8000/auth/login -d '{"username": "john", "password": "password"}' -H "Content-Type: application/json"
{"access_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2OTg3OTE0OTE..."}
$ # Note: above JWT truncated
```

### **Implementing the authentication guard**

At this point, we can now comfortably address our final requirement: protecting endpoints by requiring a valid JWT to be 
present on the request. We will do this by creating an AuthGuard that will be used to guard our routes. 

```python title='auth.guards.py' linenums='1'
import typing as t

from ellar.auth import UserIdentity
from ellar.common.serializer.guard import (
    HTTPAuthorizationCredentials,
)
from ellar.auth.guards import GuardHttpBearerAuth
from ellar.di import injectable
from ellar_jwt import JWTService
from ellar.common import logger, IExecutionContext


@injectable
class AuthGuard(GuardHttpBearerAuth):
    def __init__(self, jwt_service: JWTService) -> None:
        self.jwt_service = jwt_service

    async def authentication_handler(
        self,
        context: IExecutionContext,
        credentials: HTTPAuthorizationCredentials,
    ) -> t.Optional[t.Any]:
        try:
            data = await self.jwt_service.decode_async(credentials.credentials)
            return UserIdentity(auth_type=self.scheme, **data)
        except Exception as ex:
            logger.logger.error(f"[AuthGuard] Exception: {ex}")
            self.raise_exception()
```

We can now implement our protected route and register our AuthGuard to guard it.

```python title='auth.controllers.py' linenums='1'
from ellar.common import Controller, ControllerBase, post, Body, get, UseGuards
from .services import AuthService
from .guards import AuthGuard


@Controller
class AuthController(ControllerBase):
    def __init__(self, auth_service: AuthService) -> None:
        self.auth_service = auth_service

    @post("/login")
    async def sign_in(self, username: Body[str], password: Body[str]):
        return await self.auth_service.sign_in(username=username, password=password)

    @get("/profile")
    @UseGuards(AuthGuard)
    async def get_profile(self):
        return self.context.user
```

Ensure the app is running, and test the routes using `cURL`.

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

Note in the `AuthModule` configuration, we configured the JWT to have an expiration of 5 minutes. 
If you wait 5 minutes after authenticating before attempting a `GET` `/auth/profile` request, 
you'll receive a `401` Unauthorized response. 
This is because the `EllarJWT` package automatically checks the JWT for its expiration time, 
saving you the trouble of doing so in your application.

### **Refresh Token**

This was not included in the requirement, but it might be useful to some developers. 
So, let us address token refresh using EllarJWT. Depending your application, this illustration may vary.

To get this done, we need to edit the `sign_in` in `AuthService` to return `access_token` and `refresh_token`.
We also need to add a `refresh_token` endpoint to our `AuthController`.

```python title='auth.services.py' linenums='1'
import typing as t
from datetime import timedelta

from ellar.core.security.hashers import check_password
from ellar.di import injectable
from ellar.common import exceptions
from ellar_jwt import JWTService

from ..user.services import UsersService


@injectable()
class AuthService:
    def __init__(self, users_service: UsersService, jwt_service: JWTService) -> None:
        self.users_service = users_service
        self.jwt_service = jwt_service

    async def sign_in(self, username: str, password: str) -> t.Any:
        user_model = await self.users_service.get_user_by_username(username)
        if user_model is None:
            raise exceptions.AuthenticationFailed()

        if not check_password(password, user_model.password):
            raise exceptions.AuthenticationFailed()

        result = {
            "access_token": await self.jwt_service.sign_async(
                payload=dict(user_model.serialize(), sub=user_model.user_id)
            ),
            "refresh_token": await self.jwt_service.sign_async(
                payload=dict(sub=user_model.username),
                lifetime=timedelta(days=30)
            ),
        }
        return result
    
    async def refresh_token(self, refresh_token: str) -> t.Dict:
        try:
            payload = await self.jwt_service.decode_async(refresh_token)
        except Exception:
            raise exceptions.AuthenticationFailed()

        user_model = await self.users_service.get_user_by_username(payload['username'])
        if user_model is None:
            raise exceptions.AuthenticationFailed()

        return {
            "access_token": await self.jwt_service.sign_async(
                payload=dict(user_model.serialize(), sub=user_model.user_id)
            ),
        }
```

We have modified the sign_in method and added the refresh_token method to handle refresh token actions. 
The `sign_in` method return `access_token` and `refresh_token` that expires in 30days.

```python title='auth.controllers.py' linenums='1'
from ellar.common import Controller, ControllerBase, post, Body, get, UseGuards
from ellar.openapi import ApiTags
from .services import AuthService
from .guards import AuthGuard


@Controller
@ApiTags(name='Authentication', description='User Authentication Endpoints')
class AuthController(ControllerBase):
    def __init__(self, auth_service: AuthService) -> None:
        self.auth_service = auth_service

    @post("/login")
    async def sign_in(self, username: Body[str], password: Body[str]):
        return await self.auth_service.sign_in(username=username, password=password)

    @get("/profile")
    @UseGuards(AuthGuard)
    async def get_profile(self):
        return self.context.user
    
    @post("/refresh")
    async def refresh_token(self, payload: str = Body(embed=True)):
        return await self.auth_service.refresh_token(payload)
```
With the above illustration refresh token mechanism is complete. 

!!!note
    There are ways of refreshing tokens. This was to illustrate how you can achieve it using ellar-jwt package.

You can also vist [http://localhost:8000/docs](http://localhost:8000/docs)
![Swagger UI](../img/auth_image.png)

## **Apply AuthGuard Globally**

In situations when you need to protect all your endpoints, you can register `AuthGuard` as a global guard instead of 
using the `@UseGuards` decorator in all your controllers or route functions. 
However, you also need to implement a mechanism to skip the auth guard for certain route functions 
that don't require it, such as the `sign_in` route function.

First, let us register `AuthGuard` a global guard in `AuthModule`.

```python title="auth.module.py" linenums="1"
from datetime import timedelta

from ellar.common import GlobalGuard, Module
from ellar.core import ModuleBase
from ellar.di import ProviderConfig
from ellar_jwt import JWTModule

from .controllers import AuthController
from ..user.module import UserModule
from .services import AuthService
from .guards import AuthGuard

@Module(
    modules=[
        UserModule,
        JWTModule.setup(
            signing_secret_key="my_poor_secret_key_lol", lifetime=timedelta(minutes=5)
        ),
    ],
    controllers=[AuthController],
    providers=[AuthService, ProviderConfig(GlobalGuard, use_class=AuthGuard)],
)
class AuthModule(ModuleBase):
    """
    Auth Module
    """
```

With this, `AuthGuard` will be available to all endpoints.

### **Anonymous Route Function Mechanism**
Let us define a mechanism for declaring routes as anonymous or public. 

=== "Using Route Function MetaData"
    One way to achieve this, is by using the `set_metadata` decorator.
    We can set some metadata on those functions, and it can be read in AuthGuard. 
    If the metadata is present, we exit the authentication verification and allow the execution to continue.
    
    ```python title='auth.guards.py' linenums='1'
    import typing as t
    
    from ellar.auth import UserIdentity
    from ellar.common.serializer.guard import (
        HTTPAuthorizationCredentials,
    )
    from ellar.common import IExecutionContext, set_metadata, logger
    from ellar.auth.guards import GuardHttpBearerAuth
    from ellar.core import Reflector
    from ellar.di import injectable
    from ellar_jwt import JWTService
    
    IS_ANONYMOUS = 'is_anonymous'
    
    
    def allow_any() -> t.Callable:
        return set_metadata(IS_ANONYMOUS, True)    


    @injectable
    class AuthGuard(GuardHttpBearerAuth):
        def __init__(self, jwt_service: JWTService, reflector: Reflector) -> None:
            self.jwt_service = jwt_service
            self.reflector = reflector
    
        async def authentication_handler(
            self,
            context: IExecutionContext,
            credentials: HTTPAuthorizationCredentials,
        ) -> t.Optional[t.Any]:
            is_anonymous = self.reflector.get_all_and_override(IS_ANONYMOUS, context.get_handler(), context.get_class())
            
            if is_anonymous:
                return True
            
            try:
                data = await self.jwt_service.decode_async(credentials.credentials)
                return UserIdentity(auth_type=self.scheme, **data)
            except Exception as ex:
                logger.error(f"[AuthGuard] Exception: {ex}")
                self.raise_exception()
    ```
    
    We have defined the `allow_any` metadata decorator in the above illustration and have used Ellar's built-in class `Reflector` to read the metadata defined at the controller or route function.

=== "Using GuardCanActivate"
    We can create an `allow_any` decorator function that defines a guard metadata on the decorated function to override the global guard
    
    ```python title='auth.guards.py' linenums='1'
    import typing as t
    
    from ellar.auth import UserIdentity
    from ellar.common.serializer.guard import (
        HTTPAuthorizationCredentials,
    )
    from ellar.common import IExecutionContext, set_metadata, constants, GuardCanActivate, logger
    from ellar.auth.guards import GuardHttpBearerAuth
    from ellar.di import injectable
    from ellar_jwt import JWTService
    
    
    def allow_any() -> t.Callable:
        return set_metadata(constants.GUARDS_KEY, [AllowAny])
    
    
    class AllowAny(GuardCanActivate):
        async def can_activate(self, context: IExecutionContext) -> bool:
            return True
    
    
    @injectable
    class AuthGuard(GuardHttpBearerAuth):
        def __init__(self, jwt_service: JWTService) -> None:
            self.jwt_service = jwt_service
    
        async def authentication_handler(
            self,
            context: IExecutionContext,
            credentials: HTTPAuthorizationCredentials,
        ) -> t.Optional[t.Any]:
            try:
                data = await self.jwt_service.decode_async(credentials.credentials)
                return UserIdentity(auth_type="bearer", **data)
            except Exception as ex:
                logger.logger.error(f"[AuthGuard] Exception: {ex}")
                self.raise_exception()
    ```

#### Using allow_any decorator function
We have seen from above how to get `allow_any` decorator function.
Now we use it on the `refresh` and `sign in` endpoints as shown below:

```python title='auth.controllers.py' linenums='1'
from ellar.common import Controller, ControllerBase, post, Body, get
from ellar.openapi import ApiTags
from .services import AuthService
from .guards import AuthGuard, allow_any


@Controller
@ApiTags(name='Authentication', description='User Authentication Endpoints')
class AuthController(ControllerBase):
    def __init__(self, auth_service: AuthService) -> None:
        self.auth_service = auth_service

    @post("/login")
    @allow_any()
    async def sign_in(self, username: Body[str], password: Body[str]):
        return await self.auth_service.sign_in(username=username, password=password)

    @get("/profile")
    async def get_profile(self):
        return self.context.user
    
    @allow_any()
    @post("/refresh")
    async def refresh_token(self, payload: str = Body(embed=True)):
        return await self.auth_service.refresh_token(payload)
```
Source Code to this example is [here](https://github.com/python-ellar/ellar/tree/main/examples/03-auth-with-guards)

## **2. Authentication Schemes**

Authentication scheme is another strategy for identifying the user who is using the application. The difference between it and
and Guard strategy is your identification executed at middleware layer when processing incoming request while guard execution
happens just before route function is executed.

Ellar provides `BaseAuthenticationHandler` contract which defines what is required to set up any authentication strategy. 
We are going to make some modifications on the existing project to see how we can achieve the same result and to show how authentication handlers in ellar.

### Creating a JWT Authentication Handler
Just like AuthGuard, we need to create its equivalent. But first we need to create a `auth_scheme.py` at the root level 
of your application for us to define a `JWTAuthentication` handler. 


```python title='prject_name.auth_scheme.py' linenums='1'
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
from ellar.core.factory import AppFactory
from .root_module import ApplicationModule
from .auth_scheme import JWTAuthentication

application = AppFactory.create_from_app_module(
    ApplicationModule,
    config_module=os.environ.get(
        ELLAR_CONFIG_MODULE, "project_name.config:DevelopmentConfig"
    ),
)
application.add_authentication_schemes(JWTAuthentication)

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
    ```

We need
to refactor auth controller and mark `refresh_token` and `sign_in` function as public routes
by using `SkipAuth` decorator from `ellar.auth` package.

```python title='auth.controller.py' linenums='1'
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
just like we did in [applying guard globally](#apply-authguard-globally)

```python title='auth.module.py' linenums='1'
from datetime import timedelta
from ellar.auth.guard import AuthenticatedRequiredGuard
from ellar.common import GlobalGuard, Module
from ellar.core import ModuleBase
from ellar.di import ProviderConfig
from ellar_jwt import JWTModule

from ..users.module import UsersModule
from .controllers import AuthController
from .services import AuthService


@Module(
    modules=[
        UsersModule,
        JWTModule.setup(
            signing_secret_key="my_poor_secret_key_lol", lifetime=timedelta(minutes=5)
        ),
    ],
    controllers=[AuthController],
    providers=[AuthService, ProviderConfig(GlobalGuard, use_value=AuthenticatedRequiredGuard('JWTAuthentication', []))],
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
