A provider is any class or object that is **injectable** as a dependency to another class, and it's required when creating an instance of that class.
So, in a way, providers are like services, repositories, factories etc., classes that can manage complex tasks.
This concept of class injection is known as [Dependency Injector](https://de.wikipedia.org/wiki/Dependency_Injection)

You can easily create a provider class by decorating that class with the `@injectable()` mark
```python
from ellar.di import injectable, singleton_scope


@injectable(scope=singleton_scope)
class UserRepository:
    pass
```
We have created a `UserRepository` provider that will help manage load and saving of user data to the database. Now
Let's add this service to a controller.

```python
from ellar.di import injectable, singleton_scope
from ellar.core import ControllerBase


@injectable(scope=singleton_scope)
class UserRepository:
    pass


class UserController(ControllerBase):
    def __init__(self, user_repo: UserRepository) -> None:
        self.userRepo = user_repo
```
In our previous `Dogs` module, we can refactor the `DogsController` and move some actions to a service.

```python
# project_name/apps/dogs/services.py
import uuid
import typing as t
from ellar.di import injectable, singleton_scope
from .schemas import CreateDogSerializer, DogSerializer


@injectable(scope=singleton_scope)
class DogsRepository:
    def __init__(self):
        self._dogs: t.List[DogSerializer] = []

    def create_dog(self, data: CreateDogSerializer) -> None:
        self._dogs.append(
            DogSerializer(id=str(uuid.uuid4()), **data.dict())
        )
    
    def get_all(self) -> t.List[DogSerializer]:
        return self._dogs

```

We have successfully created a `DogsRepository` with a `singleton` scope.

Let's wire it up to `DogsController`. And rewrite some route handles.

```python
# project_name/apps/dogs/controllers.py

from ellar.common import Body, Controller, delete, get, post, put, Query
from ellar.core import ControllerBase, Request
from .schemas import CreateDogSerializer, DogListFilter
from .services import DogsRepository


@Controller('/dogs')
class DogsController(ControllerBase):
    def __init__(self, dog_repo: DogsRepository):
        self.dog_repo = dog_repo
    
    @post()
    async def create(self, payload: CreateDogSerializer = Body()):
        self.dog_repo.create_dog(payload)
        return 'This action adds a new dog'

    @get()
    async def get_all(self, query: DogListFilter = Query()):
        res = dict(
            dogs=self.dog_repo.get_all(), 
            message=f'This action returns all dogs at limit={query.limit}, offset={query.offset}')
        return res

    ...
```
We have defined `DogsRepository` as a dependency to `DogsController` which means Ellar will resolve `DogsRepository` instance when creating `DogsController` instance.
This was made possible by type definition on `dog_repo` parameter and with the type defined, Ellar knows the provider to look for.

!!info
    Every class dependencies should be defined in the class **constructor**, that way Ellar will resolve all the dependencies needed for an object instantiation.

## Provider registration
To get this working, we need to expose the `DogsRepository` to the `DogsModule` module just like we did for the `DogsController`.

```python
# project_name/apps/dogs/module.py

from ellar.common import Module
from ellar.core import ModuleBase
from ellar.di import Container
from .services import DogsRepository
from .controllers import DogsController


@Module(
    controllers=[DogsController],
    providers=[DogsRepository],
    routers=[],
)
class DogsModule(ModuleBase):
    def register_providers(self, container: Container) -> None:
        # for more complicated provider registrations
        # container.register_instance(...)
        pass
```

## Provider Scopes
There are different scope which defines different ways a service is instantiated.
- `transient_scope`: Whenever a transient scoped provider is required, a new instance of the provider is created
```python
from ellar.di import EllarInjector, transient_scope, injectable

injector = EllarInjector(auto_bind=False)


@injectable(scope=transient_scope)
class ATransientClass:
    pass

injector.container.register(ATransientClass)
# OR
# injector.container.register_transient(ATransientClass)

a_transient_instance_1 = injector.get(ATransientClass)
a_transient_instance_2 = injector.get(ATransientClass)

assert a_transient_instance_2 != a_transient_instance_1 # True
```
- `singleton_scope`: A singleton scoped provider is created once throughout the lifespan of the Container instance. For example
```python
from ellar.di import EllarInjector, singleton_scope, injectable

injector = EllarInjector(auto_bind=False)
# OR

@injectable(scope=singleton_scope)
class ASingletonClass:
    pass

injector.container.register(ASingletonClass)
# OR
# injector.container.register_singleton(ASingletonClass)

a_singleton_instance_1 = injector.get(ASingletonClass)
a_singleton_instance_2 = injector.get(ASingletonClass)

assert a_singleton_instance_2 == a_singleton_instance_1 # True
```

- `request_scope`: A request scoped provider is instantiated once during the scope of the request. And its destroyed once the request is complete.
It is important to noted that `request_scope` behaves like a `singleton_scope` during HTTPConnection mode and behaves like a `transient_scope` outside a HTTPConnection mode.
```python
from ellar.di import EllarInjector, request_scope, injectable, RequestServiceProvider

injector = EllarInjector(auto_bind=False)


@injectable(scope=request_scope)
class ARequestScopeClass:
    pass


injector.container.register(ARequestScopeClass)
request_injector = RequestServiceProvider(injector.container)

request_instance_1 = request_injector.get(ARequestScopeClass)
request_instance_2 = request_injector.get(ARequestScopeClass)
assert request_instance_2 == request_instance_1

request_instance_1 = injector.get(ARequestScopeClass)
request_instance_2 = injector.get(ARequestScopeClass)

assert request_instance_2 != request_instance_1

```

## Provider Configurations
There are two ways we can configure providers that are required in EllarInjector IoC.
- `ProviderConfig`:
With `ProviderConfig` we can register `base_type` against a `concrete_type` or register a `base_type` against a value type.

For example:
```python
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


module_ref = create_module_ref_factor(
    AModule, container=injector.container, config=Config(),
)
module_ref.run_module_register_services()
a_module_instance: AModule = injector.get(AModule)

assert isinstance(a_module_instance.ifoo, AFooClass)
assert isinstance(a_module_instance.ifoo_b, AFooClass)
assert a_module_instance.ifoo_b == a_foo_instance
```
In above example, we used `ProviderConfig` as a value type as in the case of `IFooB` type and 
as a concrete type as in the case of `IFoo` type.

- `register_providers`:
We can also achieve the same by overriding `register_providers` in any Module class.

For example:
```python
from ellar.common import Module
from ellar.core import ModuleBase, Config
from ellar.di import Container, EllarInjector, injectable, ProviderConfig
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


module_ref = create_module_ref_factor(
    AModule, container=injector.container, config=Config(),
)
module_ref.run_module_register_services()

ifoo_b = injector.get(IFooB)
ifoo = injector.get(IFoo)

assert isinstance(ifoo_b, AFooClass)
assert isinstance(ifoo, AFooClass)
assert ifoo_b == a_foo_instance
```
