# **Testing**
Automated testing is the practice of using software tools to automatically run tests on a software application or system, 
rather than relying on manual testing by humans. It is considered an essential part of software development as it 
helps increase productivity, ensure quality and performance goals are met, and provide faster feedback loops to developers. 
Automated tests can include various types such as unit tests, integration tests, end-to-end tests, and more. 

While setting up automated tests can be tedious, the benefits of increased test coverage and productivity make it an important aspect of software development.
Ellar aims to encourage the use of development best practices, including effective testing, by providing various features to assist developers and teams in creating and automating tests. 
These features include:

- automatically generated default unit tests files for components testing
- offering a util, `Test` Factory class, that constructs an isolated module/application setup
- making the Ellar dependency injection system accessible in the testing environment for convenient component mocking.

Ellar is compatible with `unittest` and `pytest` testing frameworks in python but in this documentation, we will be using `pytest`.

## **Getting started**
You will need to install `pytest`

```shell
pip install pytest
```

## **Unit testing**
In the following example, we test two classes: `CarController` and `CarRepository`. For this we need to use `TestClientFactory` to build
them in isolation from the application since we are writing unit test.

Looking at the `car` module we scaffolded earlier, there is a `tests` folder provided and inside that folder there is `test_controllers.py` module. 
We are going to be writing unit test for `CarController` in there.

```python
# project_name/car/tests/test_controllers.py
from project_name.apps.car.controllers import CarController
from project_name.apps.car.schemas import CreateCarSerializer, CarListFilter
from project_name.apps.car.services import CarRepository


class TestCarController:
    def setup(self):
        self.controller: CarController = CarController(repo=CarRepository())

    async def test_create_action(self, anyio_backend):
        result = await self.controller.create(
            CreateCarSerializer(name="Mercedes", year=2022, model="CLS")
        )

        assert result == {
            "id": "1",
            "message": "This action adds a new car",
            "model": "CLS",
            "name": "Mercedes",
            "year": 2022,
        }
```
In example above, we aren't really testing anything Ellar-specific. Notice that we are not using dependency injection; rather, 
we pass an instance of `CarController` to our `CarRepository`. 
This type of testing, where we manually instantiate the classes being tested, is commonly referred to as **isolated testing** because it is framework-independent

## **Using Test Factory**
**Test** factory function in `ellar.testing` package, is a great tool employ for a quick and better test setup. 
Let's rewrite the previous example using the built-in `Test` class:

```python
# project_name/car/tests/test_controllers.py
from unittest.mock import patch
from ellar.di import ProviderConfig
from ellar.testing import Test
from project_name.apps.car.controllers import CarController
from project_name.apps.car.schemas import CreateCarSerializer, CarListFilter
from project_name.apps.car.services import CarRepository


class TestCarController:
    def setup(self):
        test_module = Test.create_test_module(
            controllers=[CarController,], 
            providers=[ProviderConfig(CarRepository, use_class=CarRepository)]
        )
        self.controller: CarController = test_module.get(CarController)

    async def test_create_action(self, anyio_backend):
        result = await self.controller.create(
            CreateCarSerializer(name="Mercedes", year=2022, model="CLS")
        )

        assert result == {
            "id": "1",
            "message": "This action adds a new car",
            "model": "CLS",
            "name": "Mercedes",
            "year": 2022,
        }

    @patch.object(CarRepository, 'get_all', return_value=[dict(id=2, model='CLS',name='Mercedes', year=2023)])
    async def test_get_all_action(self, mock_get_all, anyio_backend):
        result = await self.controller.get_all(query=CarListFilter(offset=0, limit=10))

        assert result == {
            'cars': [
                {
                    'id': 2, 
                    'model': 'CLS', 
                    'name': 'Mercedes', 
                    'year': 2023
                }
            ], 
            'message': 'This action returns all cars at limit=10, offset=0'
        }
```
With the `Test` class, you can create an application execution context that simulates the entire Ellar runtime, 
providing hooks to easily manage class instances by allowing for mocking and overriding.

The `Test` class has a `create_test_module()` method that takes a module metadata object as its argument (the same object you pass to the `@Module()` decorator).
This method returns a `TestingModule` instance which in turn provides a few methods:

- [**`override_provider`**](#overriding-providers): Essential for overriding `providers` or `guards` with a mocked type.
- [**`create_application`**](#create-application): This method will return an application instance for the isolated testing module.
- [**`get_test_client`**](#testclient): creates and return a `TestClient` for the application which will allow you to make requests against your application, using the `httpx` library.

## **Automatic Dependency Resolution**
When testing controllers that depend on services from other modules, manually registering all required modules in your test setup can be tedious and error-prone. 
Ellar provides automatic dependency resolution to eliminate this boilerplate.

### **The Problem**
Consider a controller that requires services from multiple modules:

```python
@Controller('/users')
class UserController:
    def __init__(self, auth_service: IAuthService, db: IDatabaseService):
        self.auth_service = auth_service
        self.db = db
```

Without automatic resolution, you must manually register all dependencies:

```python
# Manual approach - error-prone!
test_module = Test.create_test_module(
    controllers=[UserController],
    modules=[AuthModule, DatabaseModule, LoggingModule]  # Must list EVERYTHING
)
```

If you forget to register a module, you get an `UnsatisfiedRequirement` error during test execution.

### **The Solution:**
By providing the `ApplicationModule` in the `Test.create_test_module()` method, Ellar will automatically resolve missing dependencies needed to test the controller.

You can provide the ApplicationModule in two ways:

**1. As a module type (direct import):**
```python
# New approach - automatic!
test_module = Test.create_test_module(
    controllers=[UserController],
    application_module=ApplicationModule  # Automatically resolves dependencies!
)
```

**2. As an import string (avoids circular imports):**
```python
# Using import string - useful to avoid circular imports
test_module = Test.create_test_module(
    controllers=[UserController],
    application_module="app.module:ApplicationModule"  # Import string!
)
```

When you provide `application_module`, Ellar:
1. Analyzes the controller's `__init__` parameters to identify required services
2. Searches the ApplicationModule tree to find modules that provide those services
3. Automatically includes those modules (and their nested dependencies) in the test module

### **How It Works**

#### **Controller Dependency Analysis**
Ellar inspects your controller's `__init__` signature to identify required services:

```python
@Controller()
class AdminController:
    def __init__(self, auth: IAuthService, db: IDatabaseService):
        # Ellar detects: needs IAuthService and IDatabaseService
        self.auth = auth
        self.db = db
```

#### **Recursive Module Resolution**
When a module depends on other modules, all nested dependencies are automatically included:

```python
@Module(
    modules=[LoggingModule],  # Nested dependency
    providers=[ProviderConfig(IDatabaseService, use_class=DatabaseService)],
    exports=[IDatabaseService]
)
class DatabaseModule:
    pass

# When DatabaseModule is needed, LoggingModule is automatically included!
```

#### **ForwardRefModule Support**
`ForwardRefModule` instances are automatically resolved:

```python
@Module(
    modules=[
        DatabaseModule,
        ForwardRefModule(CacheModule)  # Reference without setup
    ]
)
class ApplicationModule:
    pass

# CacheModule is automatically resolved when needed!
test_module = Test.create_test_module(
    controllers=[ProductController],  # Needs ICacheService
    application_module=ApplicationModule  # Resolves ForwardRef automatically
)
```

### **Mocking and Overriding**
You can still override specific modules for mocking - explicitly provided modules take precedence:

```python
class MockAuthService(IAuthService):
    def authenticate(self, token: str):
        return {"user": "test_user"}

@Module(
    providers=[ProviderConfig(IAuthService, use_class=MockAuthService)],
    exports=[IAuthService]
)
class MockAuthModule:
    pass

test_module = Test.create_test_module(
    controllers=[UserController],
    modules=[MockAuthModule],  # Explicitly provided - takes precedence!
    application_module=ApplicationModule  # Still resolves other dependencies
)
# Result: Uses MockAuthModule for IAuthService, but DatabaseModule from ApplicationModule
```

### **Complete Isolation**
When you need complete test isolation, simply omit the `application_module` parameter:

```python
# Full isolation - no automatic resolution
test_module = Test.create_test_module(
    controllers=[UserController],
    modules=[MockAuthModule, MockDatabaseModule],  # Must provide everything
    # No application_module - complete isolation
)
```

### **Using Import Strings (Avoid Circular Imports)**
If importing your ApplicationModule directly causes circular import issues, use an import string:

```python
# In your test file - no direct import needed!
test_module = Test.create_test_module(
    controllers=[UserController],
    application_module="myapp.root_module:ApplicationModule"  # String reference
)
```

This is especially useful when:
- Your test file and ApplicationModule would create circular imports
- You want to keep test files independent of the main application structure
- You're testing across different packages

### **Example: Before and After**

=== "Before (Manual)"

    ```python
    # Must manually register ALL dependencies
    test_module = Test.create_test_module(
        controllers=[AdminController],
        modules=[
            AuthModule,
            DatabaseModule,
            LoggingModule,  # Don't forget nested deps!
            CacheModule
        ]
    )
    ```

=== "After (Automatic)"

    ```python
    # Dependencies automatically resolved!
    test_module = Test.create_test_module(
        controllers=[AdminController],
        application_module=ApplicationModule
    )
    # AuthModule, DatabaseModule, LoggingModule, CacheModule all auto-included!
    ```

### **Tagged Dependencies Support**
When controllers use `InjectByTag` for dependency injection, the resolver automatically finds and registers the appropriate modules:

```python
from ellar.di import InjectByTag, ProviderConfig

# Module with tagged provider
@Module(
    providers=[
        ProviderConfig(IUserRepository, use_class=UserRepository, tag="user_repo")
    ],
    exports=[IUserRepository]
)
class UserModule:
    pass

# Controller using tagged dependency
@Controller()
class UserController:
    def __init__(self, user_repo: InjectByTag('user_repo')):
        self.user_repo = user_repo

# Automatic resolution works with tags!
test_module = Test.create_test_module(
    controllers=[UserController],
    application_module=ApplicationModule
)
# UserModule is automatically included because UserController needs tag 'user_repo'
```

### **Complex Nested Dependencies**
The resolver handles deep dependency trees automatically:

```python
@Module(
    providers=[ProviderConfig(ILogger, use_class=Logger)],
    exports=[ILogger]
)
class LoggingModule:
    pass

@Module(
    modules=[LoggingModule],  # Nested dependency
    providers=[ProviderConfig(IDatabase, use_class=PostgresDB)],
    exports=[IDatabase]
)
class DatabaseModule:
    pass

@Module(
    modules=[DatabaseModule],  # Even deeper nesting
    providers=[ProviderConfig(IUserService, use_class=UserService)],
    exports=[IUserService]
)
class UserModule:
    pass

# Controller only knows about IUserService
@Controller()
class UserController:
    def __init__(self, user_service: IUserService):
        self.user_service = user_service

# All nested dependencies automatically resolved!
test_module = Test.create_test_module(
    controllers=[UserController],
    application_module=ApplicationModule
)
# Result: UserModule, DatabaseModule, and LoggingModule all included
```

### **Error Messages**
When dependencies cannot be resolved, you get clear, actionable error messages:

```python
@Controller()
class OrderController:
    def __init__(self, payment_service: IPaymentService):
        self.payment_service = payment_service

# If IPaymentService isn't provided by any module:
test_module = Test.create_test_module(
    controllers=[OrderController],
    application_module=ApplicationModule
)
# Raises: DependencyResolutionError with suggestions:
#   OrderController requires IPaymentService, but it's not found in ApplicationModule.
#   Please either:
#     1. Register the module providing IPaymentService in ApplicationModule
#     2. Register it explicitly in Test.create_test_module(modules=[...])
#     3. Provide it as a mock in providers=[...]
```

### **Benefits**
- **Zero Boilerplate**: No need to manually track module dependencies
- **Maintainable**: Tests automatically adapt when module structure changes
- **Fail-Fast**: Missing dependencies caught at test setup time, not during execution
- **Supports All Patterns**: Works with regular DI, ForwardRef, and InjectByTag
- **Flexible**: Can still override specific modules for mocking

### **Practical Testing Patterns**

#### **Pattern 1: Integration Testing with Real Dependencies**
Test controllers with actual service implementations:

```python
def test_user_registration_flow():
    """Test full user registration with real services"""
    test_module = Test.create_test_module(
        controllers=[UserController],
        application_module=ApplicationModule
    )
    
    client = test_module.get_test_client()
    response = client.post("/users/register", json={
        "email": "user@example.com",
        "password": "secure123"
    })
    
    assert response.status_code == 201
    assert response.json()["email"] == "user@example.com"
```

#### **Pattern 2: Partial Mocking**
Mock specific services while using real implementations for others:

```python
def test_user_login_with_mock_email():
    """Test login flow with mocked email service"""
    
    class MockEmailService(IEmailService):
        sent_emails = []
        
        def send(self, to: str, subject: str, body: str):
            self.sent_emails.append({"to": to, "subject": subject})
    
    @Module(
        providers=[ProviderConfig(IEmailService, use_class=MockEmailService)],
        exports=[IEmailService]
    )
    class MockEmailModule:
        pass
    
    test_module = Test.create_test_module(
        controllers=[UserController],
        modules=[MockEmailModule],  # Override email service
        application_module=ApplicationModule  # Use real auth, database, etc.
    )
    
    client = test_module.get_test_client()
    response = client.post("/users/login", json={
        "email": "user@example.com",
        "password": "password123"
    })
    
    # Verify email was sent
    email_service = test_module.get(IEmailService)
    assert len(email_service.sent_emails) == 1
    assert "Login successful" in email_service.sent_emails[0]["subject"]
```

#### **Pattern 3: Testing with Tagged Dependencies**
Test controllers that use `InjectByTag` for flexible dependency injection:

```python
def test_payment_processing_with_different_gateways():
    """Test payment with different gateway implementations"""
    
    @Module(
        providers=[
            ProviderConfig(IPaymentGateway, use_class=StripeGateway, tag="stripe"),
            ProviderConfig(IPaymentGateway, use_class=PayPalGateway, tag="paypal"),
        ],
        exports=[IPaymentGateway]
    )
    class PaymentModule:
        pass
    
    @Controller()
    class PaymentController:
        def __init__(self, stripe: InjectByTag('stripe'), paypal: InjectByTag('paypal')):
            self.stripe = stripe
            self.paypal = paypal
    
    test_module = Test.create_test_module(
        controllers=[PaymentController],
        application_module=ApplicationModule
    )
    
    controller = test_module.get(PaymentController)
    assert isinstance(controller.stripe, StripeGateway)
    assert isinstance(controller.paypal, PayPalGateway)
```

#### **Pattern 4: Complete Test Isolation**
For unit tests, provide all dependencies explicitly:

```python
def test_user_service_logic_in_isolation():
    """Unit test UserService without any external dependencies"""
    
    class InMemoryUserRepo(IUserRepository):
        def __init__(self):
            self.users = {}
        
        def save(self, user):
            self.users[user.id] = user
    
    test_module = Test.create_test_module(
        providers=[
            UserService,
            ProviderConfig(IUserRepository, use_class=InMemoryUserRepo)
        ]
        # No application_module - complete isolation
    )
    
    service = test_module.get(UserService)
    user = service.create_user("test@example.com", "password")
    assert user.email == "test@example.com"
```

### **Overriding Providers**
Ellar provides two ways to override providers for testing:

#### **Method 1: Using `override_provider()` on TestingModule**
This is the recommended approach for quickly overriding specific services after creating the test module:

```python
from ellar.testing import Test

class MockAuthService(IAuthService):
    def authenticate(self, token: str):
        return {"user": "test_user", "authenticated": True}

# Create test module with automatic resolution
test_module = Test.create_test_module(
    controllers=[UserController],
    application_module=ApplicationModule
)

# Override specific provider
test_module.override_provider(IAuthService, use_class=MockAuthService)

# Or override with a specific instance
mock_instance = MockAuthService()
test_module.override_provider(IAuthService, use_value=mock_instance)

# Now create the application
app = test_module.create_application()
```

**Key Features:**
- Called on the `TestingModule` instance
- Supports both `use_class` and `use_value` parameters
- Must be called **before** `create_application()`
- Perfect for quick overrides without creating mock modules

#### **Method 2: Providing Mock Modules**
Create a dedicated mock module and pass it in the `modules` parameter. This approach is useful when:
- You want to organize mock implementations into reusable modules
- You need to override multiple related services at once
- You want to share mock modules across multiple tests

```python
from ellar.testing import Test
from ellar.common import Module, ProviderConfig

class MockAuthService(IAuthService):
    def authenticate(self, token: str):
        return {"user": "test_user", "authenticated": True}

# Create a mock module
@Module(
    providers=[ProviderConfig(IAuthService, use_class=MockAuthService)],
    exports=[IAuthService]
)
class MockAuthModule:
    pass

# Pass the mock module explicitly
test_module = Test.create_test_module(
    controllers=[UserController],
    modules=[MockAuthModule],  # Explicitly provided - takes precedence
    application_module=ApplicationModule  # Still resolves other dependencies
)

app = test_module.create_application()
# Result: Uses MockAuthService, but other dependencies (like Database) come from ApplicationModule
```

**Key Features:**
- Mock modules explicitly passed take precedence over ApplicationModule
- Can override multiple related services in one module
- Great for organizing test fixtures
- Reusable across multiple test cases

#### **Choosing Between Methods**

| Use Case | Method 1 (`override_provider`) | Method 2 (Mock Modules) |
|----------|-------------------------------|------------------------|
| **Quick single service override** | ✅ Recommended | ❌ Overkill |
| **Override multiple related services** | ⚠️ Multiple calls needed | ✅ Recommended |
| **Reusable across tests** | ⚠️ Needs duplication | ✅ Recommended |
| **Simple test scenarios** | ✅ Recommended | ⚠️ More setup |
| **Complex mock setup** | ⚠️ Can get verbose | ✅ Recommended |

**Example: Choosing the right method**

```python
# Use Method 1 for simple overrides
test_module = Test.create_test_module(
    controllers=[UserController],
    application_module=ApplicationModule
).override_provider(IAuthService, use_class=MockAuthService)

# Use Method 2 when overriding multiple services
@Module(
    providers=[
        ProviderConfig(IAuthService, use_class=MockAuthService),
        ProviderConfig(IEmailService, use_class=MockEmailService),
        ProviderConfig(ISmsService, use_class=MockSmsService),
    ],
    exports=[IAuthService, IEmailService, ISmsService]
)
class MockNotificationModule:
    pass

test_module = Test.create_test_module(
    controllers=[UserController],
    modules=[MockNotificationModule],
    application_module=ApplicationModule
)
```

### **Overriding Guards**
You can override `UseGuards` used in controllers during testing. For example, let's assume `CarController` has a guard `JWTGuard`

```python
import typing
from ellar.common.compatible import AttributeDict
from ellar.common import UseGuards, Controller, ControllerBase
from ellar.core.guard import HttpBearerAuth
from ellar.di import injectable


@injectable()
class JWTGuard(HttpBearerAuth):
    async def authenticate(self, connection, credentials) -> typing.Any:
        # JWT verification goes here
        return AttributeDict(is_authenticated=True, first_name='Ellar', last_name='ASGI Framework') 


@UseGuards(JWTGuard)
@Controller('/car')
class CarController(ControllerBase):
    ...
```
During testing, we can replace `JWTGuard` with a `MockAuthGuard` as shown below.

```python
from ellar.testing import Test
from .controllers import CarController, JWTGuard

class MockAuthGuard(JWTGuard):
    async def authenticate(self, connection, credentials) -> typing.Any:
        # Jwt verification goes here.
        return dict(first_name='Ellar', last_name='ASGI Framework')


class TestCarController:
    def setup(self):
        test_module = Test.create_test_module(
            controllers=[CarController,]
        ).override_provider(JWTGuard, use_class=MockAuthGuard)
```
### **Create Application**
We can access the application instance after setting up the `TestingModule`. You simply need to call `create_application` method of the `TestingModule`. 

For example:
```python
from ellar.di import ProviderConfig
from ellar.testing import Test

class TestCarController:
    def setup(self):
        test_module = Test.create_test_module(
            controllers=[CarController,], 
            providers=[ProviderConfig(CarRepository, use_class=CarRepository)]
        )
        app = test_module.create_application()
        car_repo = app.injector.get(CarRepository)
        assert isinstance(car_repo, CarRepository)
```

### **Overriding Application Conf During Testing**
Having different application configurations for different environments is a best practice in software development. 
It involves creating different sets of configuration variables, such as database connection details, API keys, and environment-specific settings, 
for different environments such as development, staging, and production.

During testing, there two ways to apply or modify configuration.

=== "In a file"
    In `config.py` file, we can define another configuration for testing eg, `class TestConfiguration` and then we can apply it to `config_module` when creating `TestingModule`.

    For example:

    ```python
    # project_name/config.py
    
    ...
    
    class BaseConfig(ConfigDefaultTypesMixin):
        DEBUG: bool = False
    
    class TestingConfiguration(BaseConfig):
        DEBUG = True
        ANOTHER_CONFIG_VAR = 'Ellar'
        
    ```
    We have created `TestingConfiguration` inside `project_name.config` python module. Lets apply this to TestingModule.
    
    ```python
    # project_name/car/tests/test_controllers.py
    
    class TestCarController:
        def setup(self):
            test_module = Test.create_test_module(
                controllers=[CarController,], 
                providers=[ProviderConfig(CarRepository, use_class=CarRepository)],
                config_module='project_name.config:TestingConfiguration'
            )
            self.controller: CarController = test_module.get(CarController)
    ```
    Also, we can expose the testing config to environment for more global scope, for example:
    
    ```python
    # project_name/tests/conftest.py
    import os
    from ellar.constants import ELLAR_CONFIG_MODULE
    os.environ.setdefault(ELLAR_CONFIG_MODULE, 'project_name.config:TestingConfiguration')
    ```

=== "Inline"
    This method doesn't require configuration file, we simply go ahead and define the configuration variables in a dictionary type set to `config_module`. 

    For instance:
    
    ```python
    # project_name/car/tests/test_controllers.py
    
    class TestCarController:
        def setup(self):
            test_module = Test.create_test_module(
                controllers=[CarController,], 
                providers=[ProviderConfig(CarRepository, use_class=CarRepository)],
                config_module=dict(DEBUG=True, ANOTHER_CONFIG_VAR='Ellar')
            )
            self.controller: CarController = test_module.get(CarController)
    ```


## **End-to-End Test**
**End-to-end (e2e)** testing operates on a higher level of abstraction than unit testing, assessing the interaction between 
classes and modules in a way that approximates user behavior with the production system. 

As an application expands, manual e2e testing of every API endpoint becomes increasingly difficult, 
which is where automated e2e testing becomes essential in validating that the system's overall behavior is correct and 
aligned with project requirements. 

To execute e2e tests, we adopt a similar configuration to that of unit testing, 
and Ellar's use of **TestClient**, a tool provided by Starlette, to facilitates the simulation of HTTP requests

### **TestClient**
Starlette provides a [TestClient](https://www.starlette.io/testclient/){target="_blank"} for making requests ASGI Applications, and it's based on [httpx](https://www.python-httpx.org/) library similar to requests.
```python
from starlette.responses import HTMLResponse
from starlette.testclient import TestClient


async def app(scope, receive, send):
    assert scope['type'] == 'http'
    response = HTMLResponse('<html><body>Hello, world!</body></html>')
    await response(scope, receive, send)


def test_app():
    client = TestClient(app)
    response = client.get('/')
    assert response.status_code == 200
```
In example above, `TestClient` needs an `ASGI` Callable. It exposes the same interface as any other `httpx` session. 
In particular, note that the calls to make a request are just standard function calls, not awaitable.

Let's see how we can use `TestClient` in writing e2e testing for `CarController` and `CarRepository`.

```python
# project_name/car/tests/test_controllers.py
from ellar.di import ProviderConfig
from ellar.testing import Test, TestClient
from project_name.apps.car.controllers import CarController
from project_name.apps.car.services import CarRepository


class MockCarRepository(CarRepository):
    def get_all(self):
        return [dict(id=2, model='CLS',name='Mercedes', year=2023)]


class TestCarControllerE2E:
    def setup(self):
        test_module = Test.create_test_module(
            controllers=[CarController,],
            providers=[ProviderConfig(CarRepository, use_class=MockCarRepository)],
            config_module=dict(
                REDIRECT_SLASHES=True
            )
        )
        self.client: TestClient = test_module.get_test_client()

    def test_create_action(self):
        res = self.client.post('/car', json=dict(
            name="Mercedes", year=2022, model="CLS"
        ))
        assert res.status_code == 200
        assert res.json() == {
            "id": "1",
            "message": "This action adds a new car",
            "model": "CLS",
            "name": "Mercedes",
            "year": 2022,
        }

    def test_get_all_action(self):
        res = self.client.get('/car?offset=0&limit=10')
        assert res.status_code == 200
        assert res.json() == {
            'cars': [
                {
                    'id': 2,
                    'model': 'CLS',
                    'name': 'Mercedes',
                    'year': 2023
                }
            ],
            'message': 'This action returns all cars at limit=10, offset=0'
        }
```

In the construct above, `test_module.get_test_client()` created an isolated application instance and used it to instantiate a `TestClient`.
And with we are able to simulate request behaviour on `CarController`.
