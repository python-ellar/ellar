Automated testing is the practice of using software tools to automatically run tests on a software application or system, 
rather than relying on manual testing by humans. It is considered an essential part of software development as it 
helps increase productivity, ensure quality and performance goals are met, and provide faster feedback loops to developers. 
Automated tests can include various types such as unit tests, integration tests, end-to-end tests, and more. 

While setting up automated tests can be tedious, the benefits of increased test coverage and productivity make it an important aspect of software development.
Ellar aims to encourage the use of development best practices, including effective testing, by providing various features to assist developers and teams in creating and automating tests. 
These features include:

- automatically generated default unit tests files for components testing
- offering a util, `TestClientFactory`, that constructs an isolated module/application setup
- making the Ellar dependency injection system accessible in the testing environment for convenient component mocking.

Ellar is compatible with `unittest` and `pytest` testing frameworks in python but in this documentation, we will be using `pytest`.

## Getting started
You will need to install `pytest`

```shell
pip install pytest
```

## Unit testing
In the following example, we test two classes: `CarController` and `CarRepository`. For this we need to use `TestClientFactory` to build
them in isolation from the application since we are writing unit test.

Looking at the `car` module we scaffolded earlier, there is a `tests` folder provided and inside that folder there is `test_controllers.py` module. 
We are going to be writing unit test for `CarController` in there.

```python
# project_name/car/tests/test_controllers.py
from unittest.mock import patch

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
In example above, we aren't really testing anything Ellar-specific. Notice that we are not using dependency injection; rather, 
we pass an instance of `CarController` to our `CarRepository`. This type of testing, where we manually instantiate the classes being tested, is commonly referred to as **isolated testing** because it is framework-independent
## Using TestClientFactory
## Controller Testing
## Module Testing
## Mocking Services
