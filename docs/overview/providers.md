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
    pass
```

By adding `CarRepository` to the list of providers, Ellar ensures that it is available for dependency injection within the `CarModule`. 
This allows us to use `CarRepository` within any class or object defined within the `CarModule`, 
providing a seamless integration of services and controllers within the module.

## **Other ways of registering a Provider/Services**

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
        ProviderConfig(IFooB, use_value=a_foo_instance),
        ProviderConfig(IFoo, use_class="path.to:AFooClass")
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
    a_module_instance = injector.get(AModule)
    
    assert isinstance(a_module_instance.ifoo, AFooClass)
    assert isinstance(a_module_instance.ifoo_b, AFooClass)
    assert a_module_instance.ifoo_b == a_foo_instance

    
if __name__ == "__main__":
    validate_provider_config()
```

In the above example, `ProviderConfig` is used as a value type for `IFooB` and as a concrete type for `IFoo`. Also, the `use_class` argument can be used to specify the path to the class to be used as the provider which is useful when you want to lazy load the provider class.

## **Tagging Registered Providers**

There are situations where you want to **tag** a service with a name and also resolve the service with the tag.

For example:

```python
from ellar.di import EllarInjector

injector = EllarInjector(auto_bind=False)


class Foo:
    pass


class FooB:
    pass


@Module(
    providers=[
        ProviderConfig(Foo, tag="first_foo"),
        ProviderConfig(FooB, tag="second_foo"),
    ]
)
class AModule(ModuleBase):
    def __init__(self, foo: InjectByTag("first_foo"), foo_b: InjectByTag("second_foo")):
        self.foo = foo
        self.foo_b = foo_b

        assert isinstance(self.foo, Foo)
        assert isinstance(self.foo_b, FooB)
```

In the above example, we are tagging `Foo` as `first_foo` and `FooB` as `second_foo`. By doing this, we can resolve both services using their tag names, thus providing the possibility of resolving services by tag name or type.

Also, services can be injected as a dependency by using tags. To achieve this, the `InjectByTag` decorator is used as a `**constructor**` argument.
This allows for more flexibility in managing dependencies and resolving services based on tags.
