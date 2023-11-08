# **Quick Project**
This section will guide on how to quickly setup ellar project to just have a glimpse of its features.

## **Ellar CLI**
Ellar CLI helps in quick project scaffolding.
```shell
pip install ellar-cli
```
or 
```shell
poetry add ellar-cli
```

## **Creating a project**
To create an ellar project, you need to have a `pyproject.toml` available on your root directory.
This is necessary for ellar to store some `metadata` about your project. 

If you are using `Poetry`, you might have to run `poetry init` first before running the command below:
```shell
ellar create-project carsite
```

For Pip Users
```shell
ellar new carsite
```
This will create the `pyproject.toml` and add all other necessary files for ellar project.

In the scaffolded project, you will see the following:

- `server.py`: is the entry point of the application. 
- `config.py`: hold all application configuration
- `root_module.py`: hold reference to all registered Application Modules
- `core`: directory to add core business logics
- `domain`: directory to add domain models

## **Run your project**
Ellar runs [UVICORN - ASGI Server](https://www.uvicorn.org/) under the hood.
```shell
ellar runserver --reload
```
`--reload` is to watch for file changes

OR, if you want to use a different ASGI server, it's allowed.
```shell
uvicorn run server:application --reload
```

Now go to [http://127.0.0.1:8000](http://127.0.0.1:8000)
![Swagger UI](https://python-ellar.github.io/ellar/img/ellar_framework.png)

For more info on Ellar CLI, click [here](https://github.com/python-ellar/ellar-cli)

## **Adding a project module**
A project module is a like project app defining a group of controllers or services including templates and static files.
So, we shall be adding a `car` module to our `carsite` project just to handle some logic like creating and retrieving car data.

```shell
ellar create-module car carsite
```
This will add some files like:

- `controllers.py`: where we can add different controllers for car module
- `schemas.py`: place to define various pydantic schemas for both controller and service use.
- `routers.py`: an alternative to controller class if you enjoy defining endpoint in functions 
- `module.py`: an export for our car module that will be registered in `root_module.py` of the project
- `services.py`: place where we can define services for managing data and others for our car module
- `tests`: place to add unit test or E2E test for out car module

## **Add Schema**
In `car/schema.py`, lets add some serializer for car input and output data
```python
from ellar.common import Serializer

class CarSerializer(Serializer):
    name: str
    model: str
    brand: str


class RetrieveCarSerializer(CarSerializer):
    pk: str
```

## **Add Services**
In `car/services.py`, lets create a dummy repository `CarDummyDB` to manage our car data.
```python
"""
Create a provider and declare its scope

@injectable
class AProvider
    pass

@injectable(scope=transient_scope)
class BProvider
    pass
"""
import typing as t
import uuid
from ellar.di import injectable, singleton_scope


class DummyDBItem:
    pk: str

    def __init__(self, **data: t.Dict) -> None:
        self.__dict__ = data

    def __eq__(self, other):
        if isinstance(other, DummyDBItem):
            return self.pk == other.pk
        return self.pk == str(other)


@injectable(scope=singleton_scope)
class CarDummyDB:
    def __init__(self) -> None:
        self._data: t.List[DummyDBItem] = []

    def add_car(self, data: t.Dict) -> str:
        pk = uuid.uuid4()
        _data = dict(data)
        _data.update(pk=str(pk))
        item = DummyDBItem(**_data)
        self._data.append(item)
        return item.pk

    def list(self) -> t.List[DummyDBItem]:
        return self._data

    def update(self, car_id: str, data: t.Dict) -> t.Optional[DummyDBItem]:
        if car_id in self._data:
            idx = self._data.index(car_id)
            _data = dict(data)
            _data.update(pk=str(car_id))
            self._data[idx] = DummyDBItem(**_data)
            return self._data[idx]

    def get(self, car_id: str) -> t.Optional[DummyDBItem]:
        if car_id in self._data:
            idx = self._data.index(car_id)
            return self._data[idx]


    def remove(self, car_id: str) -> t.Optional[DummyDBItem]:
        if car_id in self._data:
            idx = self._data.index(car_id)
            return self._data.pop(idx)

```
## **Add Controller**
In `car/controllers.py`, lets create `CarController`

```python
import typing as t
from ellar.common import Controller, delete, get, put, post, ControllerBase
from ellar.common.exceptions import NotFound
from .schemas import CarSerializer, RetrieveCarSerializer
from .services import CarDummyDB


@Controller
class CarController(ControllerBase):
    def __init__(self, db: CarDummyDB) -> None:
        self.car_db = db

    @post("/create", response={200: str})
    async def create_cat(self, payload: CarSerializer):
        pk = self.car_db.add_car(payload.dict())
        return pk

    @put("/{car_id:str}", response={200: RetrieveCarSerializer})
    async def update_cat(self, car_id: str, payload: CarSerializer):
        car = self.car_db.update(car_id, payload.dict())
        if not car:
            raise NotFound("Item not found")
        return car

    @get("/{car_id:str}", response={200: RetrieveCarSerializer})
    async def get_car_by_id(self, car_id: str):
        car = self.car_db.get(car_id)
        if not car:
            raise NotFound('Item not found.')
        return car

    @delete("/{car_id:str}", response={204: dict})
    async def deleted_cat(self, car_id: str):
        car = self.car_db.remove(car_id)
        if not car:
            raise NotFound('Item not found.')
        return 204, {}

    @get("/", response={200: t.List[RetrieveCarSerializer]})
    async def list(self):
        return self.car_db.list()

```
## **Register Service and Controller**
In `car/module.py`, lets register `CarController` and `CarDummyDB`

```python
from ellar.common import Module
from ellar.core import ModuleBase
from ellar.di import Container

from .controllers import CarController
from .services import CarDummyDB


@Module(
    controllers=[CarController],
    providers=[CarDummyDB],
    routers=[],
)
class CarModule(ModuleBase):
    def register_providers(self, container: Container) -> None:
        # for more complicated provider registrations
        # container.register_instance(...)
        pass
```

## **Registering Module**
Ellar is not aware of `CarModule` yet, so we need to add it to the `modules` list of `ApplicationModule` at the `carsite/root_module.py`.
```python
from ellar.common import Module, exception_handler, JSONResponse, Response, IHostContext
from ellar.core import ModuleBase

from ellar.samples.modules import HomeModule
from .car.module import CarModule


@Module(modules=[HomeModule, CarModule])
class ApplicationModule(ModuleBase):
    @exception_handler(404)
    def exception_404_handler(cls, context: IHostContext, exc: Exception) -> Response:
        return JSONResponse(dict(detail="Resource not found."))

```
## **Enabling OpenAPI Docs**
To start up openapi, we need to go back to project folder in the `server.py`
then add the following below.
```python
import os

from ellar.common.constants import ELLAR_CONFIG_MODULE
from ellar.app import AppFactory
from ellar.openapi import OpenAPIDocumentModule, OpenAPIDocumentBuilder, SwaggerDocumentGenerator
from .root_module import ApplicationModule

application = AppFactory.create_from_app_module(
    ApplicationModule,
    config_module=os.environ.get(
        ELLAR_CONFIG_MODULE, "carsite.config:DevelopmentConfig"
    ),
)

document_builder = OpenAPIDocumentBuilder()
document_builder.set_title('CarSite API') \
    .set_version('1.0.0') \
    .set_contact(name='Author', url='https://www.yahoo.com', email='author@gmail.com') \
    .set_license('MIT Licence', url='https://www.google.com')

document = document_builder.build_document(application)
module = OpenAPIDocumentModule.setup(
    document=document,
    document_generator=SwaggerDocumentGenerator(),
    guards=[]
)
application.install_module(module)
```

Now we can test our API at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs#/)
Please ensure your server is running
![Swagger UI](https://python-ellar.github.io/ellar/img/car_api.png)

## **Source Code**
You can find this example source code [here](https://github.com/python-ellar/ellar/tree/main/examples/quick-project)
