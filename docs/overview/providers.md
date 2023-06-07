# **Providers**
A provider is any class or object that is **injectable** as a dependency to another class when creating an instance of that class.

Providers are like services, repositories services, factories, etc., classes that manage complex tasks. These providers can be made available to a controller, a route handler, or to another provider as a dependency. 
This concept is commonly known as [Dependency Injection](https://en.wikipedia.org/wiki/Dependency_injection){target="_blank"}

In Ellar, you can easily create a `provider/injectable` class by decorating that class with the `@injectable()` mark and stating the scope.

```python
from ellar.di import injectable, singleton_scope


@injectable(scope=singleton_scope)
class UserRepository:
    pass
```

We have created a `UserRepository` provider that will help manage the loading and saving of user data to the database.

Let's add this service to a controller.

```python
from ellar.di import injectable, singleton_scope
from ellar.common import Controller, ControllerBase


@injectable(scope=singleton_scope)
class UserRepository:
    pass


@Controller()
class UserController(ControllerBase):
    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo
```
Let's refactor our `CarController` and move some actions to a service.

```python
# project_name/apps/car/services.py
import typing as t
from ellar.di import injectable, singleton_scope
from .schemas import CreateCarSerializer, CarSerializer


@injectable(scope=singleton_scope)
class CarRepository:
    def __init__(self):
        self._cars: t.List[CarSerializer] = []

    def create_car(self, data: CreateCarSerializer) -> dict:
        data = CarSerializer(id=len(self._cars) + 1, **data.dict())
        self._cars.append(data)
        return data.dict()


    def get_all(self) -> t.List[CarSerializer]:
        return self._cars

```

We have successfully created a `CarRepository` with a `singleton` scope.

Let's wire it up to `CarController`. And rewrite some route handles.

```python
# project_name/apps/car/controllers.py

from ellar.common import Body, Controller, get, post, Query, ControllerBase
from .schemas import CreateCarSerializer, CarListFilter
from .services import CarRepository


@Controller('/car')
class CarController(ControllerBase):
    def __init__(self, repo: CarRepository):
        self.repo = repo
    
    @post()
    async def create(self, payload: CreateCarSerializer = Body()):
        result = self.repo.create_car(payload)
        result.update(message='This action adds a new car')
        return result

    @get()
    async def get_all(self, query: CarListFilter = Query()):
        res = dict(
            cars=self.repo.get_all(), 
            message=f'This action returns all cars at limit={query.limit}, offset={query.offset}')
        return res

    ...
```

We have defined `CarRepository` as a dependency to `CarController` and Ellar will resolve the `CarRepository` instance when creating the `CarController` instance.

!!! info
    Every class dependency should be defined in the class **constructor**  as a type annotation or Ellar won't be aware of the dependencies required for an object instantiation.

## **Provider Registration**
To get this working, we need to expose the `CarRepository` to the `CarModule` module just like we did for the `CarController`.

```python
# project_name/apps/car/module.py

from ellar.common import Module
from ellar.core import ModuleBase
from ellar.di import Container
from .services import CarRepository
from .controllers import CarController


@Module(
    controllers=[CarController],
    providers=[CarRepository],
    routers=[],
)
class CarModule(ModuleBase):
    def register_providers(self, container: Container) -> None:
        # for more complicated provider registrations
        # container.register_instance(...)
        pass
```

## **Other ways of registering a Provider**
There are two ways we can register/configure providers in EllarInjector IoC.

### **`ProviderConfig`**:
With `ProviderConfig`, we can register a `base_type` against a `concrete_type` OR register a `base_type` against a value type.

For example:
```python
# main.py

from ellar.common import Module
from ellar.core import ModuleBase, Config
from ellar.di import ProviderConfig, injectable, EllarInjector
from ellar.core.modules.ref import create_module_ref_factor

injector = EllarInjector(auto_bind=False)


class IFoo:
    pass


class IFooB:
    pass


@injectable
class AFooClass(IFoo, IFooB):
    pass


a_foo_instance = AFooClass()


@Module(
    providers=[
        ProviderConfig(IFoo, use_class=AFooClass),
        ProviderConfig(IFooB, use_value=a_foo_instance)
    ]
)
class AModule(ModuleBase):
    def __init__(self, ifoo: IFoo, ifoo_b: IFooB):
        self.ifoo = ifoo
        self.ifoo_b = ifoo_b


def validate_provider_config():
    module_ref = create_module_ref_factor(
    AModule, container=injector.container, config=Config(),
    )
    module_ref.run_module_register_services()
    a_module_instance: AModule = injector.get(AModule)
    
    assert isinstance(a_module_instance.ifoo, AFooClass)
    assert isinstance(a_module_instance.ifoo_b, AFooClass)
    assert a_module_instance.ifoo_b == a_foo_instance

    
if __name__ == "__main__":
    validate_provider_config()
```
In above example, we used `ProviderConfig` as a value type as in the case of `IFooB` type and 
as a concrete type as in the case of `IFoo` type.

### **`register_providers`**:
We can also achieve the same by overriding `register_providers` in any Module class.

For example:
```python
# main.py

from ellar.common import Module
from ellar.core import ModuleBase, Config
from ellar.di import Container, EllarInjector, injectable
from ellar.core.modules.ref import create_module_ref_factor

injector = EllarInjector(auto_bind=False)


class IFoo:
    pass


class IFooB:
    pass


@injectable  # default scope=singleton_scope
class AFooClass(IFoo, IFooB):
    pass


a_foo_instance = AFooClass()


@Module()
class AModule(ModuleBase):
    def register_services(self, container: Container) -> None:
        container.register_singleton(IFoo, AFooClass)
        container.register(IFooB, a_foo_instance)


def validate_register_services():
    module_ref = create_module_ref_factor(
    AModule, container=injector.container, config=Config(),
    )
    module_ref.run_module_register_services()
    
    ifoo_b = injector.get(IFooB)
    ifoo = injector.get(IFoo)
    
    assert isinstance(ifoo_b, AFooClass)
    assert isinstance(ifoo, AFooClass)
    assert ifoo_b == a_foo_instance

if __name__ == "__main__":
    validate_register_services()

```
