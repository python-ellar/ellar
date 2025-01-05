# **API Key Authentication in Ellar**

This guide demonstrates how to implement API Key authentication in Ellar using both header-based and query parameter-based approaches.

## **Overview**

API Key authentication is a simple yet effective way to secure your APIs. Ellar provides built-in support for three types of API Key authentication:

1. Header-based API Key
2. Query Parameter-based API Key
3. Cookie-based API Key

## **Implementation Methods**

### 1. **Using Authentication Handler**

```python
# auth/api_key_scheme.py
from ellar.auth import UserIdentity
from ellar.auth.handlers import (
    HeaderAPIKeyAuthenticationHandler,
    QueryAPIKeyAuthenticationHandler,
    CookieAPIKeyAuthenticationHandler
)
from ellar.common import IHostContext
from ellar.di import injectable


@injectable
class HeaderAPIKeyAuth(HeaderAPIKeyAuthenticationHandler):
    api_key = "your-secret-api-key"  # In production, use secure storage
    api_key_name = "X-API-Key"

    async def authentication_handler(
        self,
        context: IHostContext,
        api_key: str,
    ) -> UserIdentity | None:
        if api_key == self.api_key:
            return UserIdentity(auth_type="api_key", api_key=api_key)
        return None


@injectable
class QueryAPIKeyAuth(QueryAPIKeyAuthenticationHandler):
    api_key = "your-secret-api-key"
    api_key_name = "api_key"

    async def authentication_handler(
        self,
        context: IHostContext,
        api_key: str,
    ) -> UserIdentity | None:
        if api_key == self.api_key:
            return UserIdentity(auth_type="api_key", api_key=api_key)
        return None
```

Register the authentication handlers:

```python
# server.py
from ellar.app import AppFactory, use_authentication_schemes

application = AppFactory.create_from_app_module(
    lazyLoad('project_name.root_module:ApplicationModule'),
    config_module="project_name.config:DevelopmentConfig"
)
use_authentication_schemes([HeaderAPIKeyAuth, QueryAPIKeyAuth])
```

### 2. **Using Guard Strategy**

```python
# auth/guards.py
from ellar.auth import UserIdentity
from ellar.auth.guards import (
    GuardAPIKeyHeader,
    GuardAPIKeyQuery
)
from ellar.di import injectable


@injectable
class HeaderAPIKeyGuard(GuardAPIKeyHeader):
    api_key = "your-secret-api-key"
    api_key_name = "X-API-Key"

    async def authentication_handler(
        self,
        context: IExecutionContext,
        api_key: str,
    ) -> UserIdentity | None:
        if api_key == self.api_key:
            return UserIdentity(auth_type="api_key", api_key=api_key)
        self.raise_exception()


@injectable
class QueryAPIKeyGuard(GuardAPIKeyQuery):
    api_key = "your-secret-api-key"
    api_key_name = "api_key"

    async def authentication_handler(
        self,
        context: IExecutionContext,
        api_key: str,
    ) -> UserIdentity | None:
        if api_key == self.api_key:
            return UserIdentity(auth_type="api_key", api_key=api_key)
        self.raise_exception()
```

## **Controller Implementation**

```python
from ellar.common import Controller, get
from ellar.auth import AuthenticationRequired


@Controller('/api')
@AuthenticationRequired(['HeaderAPIKeyAuth', 'QueryAPIKeyAuth'])
class APIController:
    @get('/data')
    async def get_data(self):
        return {"message": "Protected data"}
```

## **Testing the Implementation**

```bash
# Using Header-based API Key
curl http://localhost:8000/api/data \
  -H "X-API-Key: your-secret-api-key"

# Using Query Parameter-based API Key
curl "http://localhost:8000/api/data?api_key=your-secret-api-key"
```

## **Security Best Practices**

1. **API Key Storage**:
    - Never hardcode API keys in source code
    - Use environment variables or secure key management systems
    - Rotate API keys periodically

2. **Transport Security**:
    - Always use HTTPS in production
    - Consider implementing rate limiting
    - Log and monitor API key usage

3. **Key Management**:
    - Implement API key rotation
    - Maintain an audit trail of API key usage
    - Implement key revocation mechanisms

## **Advanced Implementation**

### **API Key with Scopes**

```python
from typing import List
from ellar.auth import UserIdentity
from ellar.auth.handlers import HeaderAPIKeyAuthenticationHandler


@injectable
class ScopedAPIKeyAuth(HeaderAPIKeyAuthenticationHandler):
    api_keys = {
        "key1": ["read"],
        "key2": ["read", "write"],
    }
    api_key_name = "X-API-Key"

    async def authentication_handler(
        self,
        context: IHostContext,
        api_key: str,
    ) -> UserIdentity | None:
        if api_key in self.api_keys:
            return UserIdentity(
                auth_type="api_key",
                api_key=api_key,
                scopes=self.api_keys[api_key]
            )
        return None
```

## **Manual OpenAPI Integration**

Ellar automatically generates OpenAPI documentation when you use and class in `ellar.auth.handlers` and `ellar.auth.guards`. But if you want to manually add it, you can do so by using the `OpenAPIDocumentBuilder` class.

```python
from ellar.openapi import ApiTags, OpenAPIDocumentBuilder

@Controller
@ApiTags(name='API', security=[{"ApiKeyAuth": []}])
class APIController:
    pass

# In your OpenAPI configuration
document_builder = OpenAPIDocumentBuilder()
document_builder.add_security_scheme(
    "ApiKeyAuth",
    {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key"
    }
)
```

## **Custom Error Handling**

```python
from ellar.common import IExecutionContext
from ellar.common.responses import JSONResponse
from ellar.core.exceptions import as_exception_handler


@as_exception_handler(401)
def invalid_api_key_exception_handler(ctx: IExecutionContext, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={
            "message": "Invalid API key",
            "error": "unauthorized"
        }
    )
```
See [Custom Error Handling](../../overview/exception_handling.md) for more information.

## **Complete Examples**

For a complete working example of API Key authentication, visit the [Ellar examples repository](https://github.com/python-ellar/ellar/tree/main/examples). 
