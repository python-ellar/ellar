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

### **Overriding Providers**
`TestingModule` `override_provider` method allows you to provide an alternative for a provider type or a guard type. For example:

```python
from ellar.testing import Test

class MockCarRepository(CarRepository):
    pass

class TestCarController:
    def setup(self):
        test_module = Test.create_test_module(
            controllers=[CarController,]
        ).override_provider(
            CarRepository, use_class=MockCarRepository
        )
```
`override_provider` takes the same arguments as `ellar.di.ProviderConfig` and in fact, it builds to `ProvideConfig` behind the scenes.
In example above, we created a `MockCarRepository` for `CarRepository` and applied it as shown above. 
We can also create an instance of `MockCarRepository` and have it behave as a singleton within the scope of `test_module` instance.

```python
from ellar.testing import Test

class MockCarRepository(CarRepository):
    pass

class TestCarController:
    def setup(self):
        test_module = Test.create_test_module(
            controllers=[CarController,]
        ).override_provider(CarRepository, use_value=MockCarRepository())
```
We this, anywhere `CarRepository` is needed, a `MockCarRepository()` instance will be applied.

In same way, we can override `UseGuards` used in controllers during testing. For example, lets assume `CarController` has a guard `JWTGuard`

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
