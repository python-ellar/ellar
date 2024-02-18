# **Providers**
A provider is any class or object that can be injected as a dependency when creating an instance of another class. 
These can include services, repository services, factories, and other classes responsible for handling complex tasks. 
Providers are made accessible to controllers, route handlers, or other providers as dependencies, following the principles of Dependency Injection.

In Ellar, creating a provider or injectable class is simplified by decorating the class with the `@injectable()` marker and specifying the desired scope.

```python
from ellar.di import injectable, singleton_scope

@injectable(scope=singleton_scope)
class UserRepository:
    pass
```

For example, we've created a **UserRepository** provider to manage the loading and saving of user data to the database.

Now, let's integrate this service into a controller.

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

We've added the **UserRepository** as a dependency to the **UserController**, 
ensuring that **Ellar** resolves the **UserRepository** instance when creating the **UserController** instance.

Next, let's refactor our CarController and move some actions to a service.

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

We've created a **CarRepository** with a singleton scope to handle car-related operations.

Now, let's wire it up to **CarController** and rewrite some route handlers.

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

By defining CarRepository as a dependency for **CarController**, **Ellar** automatically resolves the CarRepository instance when creating the **CarController** instance.

Note that every class dependency should be defined in the class constructor as a type annotation to ensure that **Ellar** is aware of the dependencies required for object instantiation.

## **Provider Registration**

In order to make the `CarRepository` accessible within the `CarModule`, similar to how we exposed the `CarController`, 
we need to include it in the list of providers within the `CarModule`.

```python
# project_name/apps/car/module.py

from ellar.common import Module
from ellar.core import ModuleBase
from ellar.di import Container
from .services import CarRepository
from .controllers import CarController

@Module(
    controllers=[CarController],
    providers=[CarRepository],  # Include CarRepository in the list of providers
    routers=[],
)
class CarModule(ModuleBase):
    def register_providers(self, container: Container) -> None:
        # for more complicated provider registrations
        # container.register_instance(...)
        pass
```

By adding `CarRepository` to the list of providers, Ellar ensures that it is available for dependency injection within the `CarModule`. 
This allows us to use `CarRepository` within any class or object defined within the `CarModule`, 
providing a seamless integration of services and controllers within the module.

## **Other ways of registering a Provider**

There are two methods available for registering or configuring providers in EllarInjector IoC.

### **1. `ProviderConfig`:**
With `ProviderConfig`, you can register a `base_type` against a `concrete_type` or a `base_type` against a value type.

For instance:
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

In the above example, `ProviderConfig` is used as a value type for `IFooB` and as a concrete type for `IFoo`.

### **2. `register_providers`:**
Another method is by overriding `register_providers` in any Module class.

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


@injectable
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

In this example, the `register_services` method in `AModule` is used to register `IFoo` and `IFooB` with their respective concrete implementations.
