# **JWT Authentication in Ellar****

This guide demonstrates how to implement JWT (JSON Web Token) authentication in an Ellar application using both Guard and Authentication Handler strategies.

## **Prerequisites**

- Ellar application setup
- `ellar-jwt` package installed:
  ```bash
  pip install ellar-jwt
  ```

## **Basic Setup**

First, let's set up the basic structure with user management:

```python
# user/services.py
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
    # For demonstration. In production, use a proper database
    users = [
        {
            'user_id': 1,
            'username': 'john',
            'password': make_password('password'),
        }
    ]

    async def get_user_by_username(self, username: str) -> UserModel | None:
        filtered_list = filter(lambda item: item["username"] == username, self.users)
        found_user = next(filtered_list, None)
        if found_user:
            return UserModel(**found_user)
```

## **Method 1: Using Authentication Handler**

The Authentication Handler approach processes authentication at the middleware layer:

```python
# auth/auth_scheme.py
import typing as t
from ellar.auth import UserIdentity
from ellar.auth.handlers import HttpBearerAuthenticationHandler
from ellar.common import IHostContext
from ellar.common.serializer.guard import HTTPAuthorizationCredentials
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
        try:
            data = await self.jwt_service.decode_async(credentials.credentials)
            return UserIdentity(auth_type=self.scheme, **data)
        except Exception:
            return None
```

Register the authentication handler in your application:

```python
# server.py
from ellar.app import AppFactory, use_authentication_schemes

application = AppFactory.create_from_app_module(
    lazyLoad('project_name.root_module:ApplicationModule'),
    config_module="project_name.config:DevelopmentConfig"
)
use_authentication_schemes(JWTAuthentication)
```

## **Method 2: Using Guard Strategy**

The Guard strategy processes authentication at the route handler level:

```python
# auth/guards.py
from ellar.auth import UserIdentity
from ellar.auth.guards import GuardHttpBearerAuth
from ellar.di import injectable
from ellar_jwt import JWTService


@injectable
class JWTGuard(GuardHttpBearerAuth):
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
        except Exception:
            self.raise_exception()
```

## **Authentication Service**

Implement the authentication service:

```python
# auth/services.py
from datetime import timedelta
from ellar.di import injectable
from ellar.common import exceptions
from ellar_jwt import JWTService
from ..user.services import UsersService


@injectable()
class AuthService:
    def __init__(self, users_service: UsersService, jwt_service: JWTService) -> None:
        self.users_service = users_service
        self.jwt_service = jwt_service

    async def sign_in(self, username: str, password: str) -> dict:
        user = await self.users_service.get_user_by_username(username)
        if not user or not check_password(password, user.password):
            raise exceptions.AuthenticationFailed()

        return {
            "access_token": await self.jwt_service.sign_async(
                dict(user.serialize(), sub=user.user_id)
            ),
            "refresh_token": await self.jwt_service.sign_async(
                dict(sub=user.username),
                lifetime=timedelta(days=30)
            )
        }

    async def refresh_token(self, refresh_token: str) -> dict:
        try:
            payload = await self.jwt_service.decode_async(refresh_token)
            user = await self.users_service.get_user_by_username(payload['sub'])
            if not user:
                raise exceptions.AuthenticationFailed()

            return {
                "access_token": await self.jwt_service.sign_async(
                    dict(user.serialize(), sub=user.user_id)
                )
            }
        except Exception:
            raise exceptions.AuthenticationFailed()
```

## **Controller Implementation**

```python
# auth/controllers.py
from ellar.common import Controller, post, Body, get
from ellar.auth import SkipAuth, AuthenticationRequired
from ellar.openapi import ApiTags
from .services import AuthService


@AuthenticationRequired('JWTAuthentication')
@Controller
@ApiTags(name='Authentication')
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
    
    @post("/refresh")
    @SkipAuth()
    async def refresh_token(self, payload: str = Body(embed=True)):
        return await self.auth_service.refresh_token(payload)
```

## **Module Configuration**

Configure the authentication module:

```python
# auth/module.py
from datetime import timedelta
from ellar.common import Module
from ellar.core import ModuleBase
from ellar_jwt import JWTModule
from .controllers import AuthController
from .services import AuthService


@Module(
    modules=[
        JWTModule.setup(
            signing_secret_key="your-secret-key",
            lifetime=timedelta(minutes=5)
        ),
    ],
    controllers=[AuthController],
    providers=[AuthService],
)
class AuthModule(ModuleBase):
    pass
```

## **Testing the Implementation**

```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "john", "password": "password"}'

# Access protected route
curl http://localhost:8000/auth/profile \
  -H "Authorization: Bearer <your-jwt-token>"

# Refresh token
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"payload": "<your-refresh-token>"}'
```

## **Security Considerations**

1. **Secret Key**: 
    - Use a strong, environment-specific secret key
    - Never commit secrets to version control

2. **Token Lifetime**:
    - Set appropriate expiration times
    - Implement token refresh mechanism
    - Consider using sliding sessions

3. **Error Handling**:
    - Provide secure, non-revealing error messages
    - Implement proper logging
    - Handle token expiration gracefully

## **Best Practices**

1. **Token Storage**:
    - Store tokens securely (e.g., HttpOnly cookies for web apps)
    - Implement proper token revocation
    - Consider token rotation strategies

2. **Refresh Token Handling**:
    - Use longer expiration for refresh tokens
    - Implement proper refresh token rotation
    - Consider implementing a token blacklist

3. **API Security**:
    - Use HTTPS in production
    - Implement rate limiting
    - Consider implementing CSRF protection

## **Complete Example**

Find a complete working example in the [Ellar GitHub repository](https://github.com/python-ellar/ellar/tree/main/examples/04-auth-with-handlers). 
