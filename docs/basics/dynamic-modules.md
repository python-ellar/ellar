# **Dynamic Modules**
We have seen in many example given on how to statically configure a [module](../overview/modules.md){_target='blank'}. 
In this section we are going to look at different ways to dynamically set up a module.

Why is this important? Consider a scenario where a general-purpose module needs to behave differently in different use cases, 
it may be useful to use a configuration-based approach to allow customization. This is similar to the concept of a "plugin" in many systems, 
where a generic facility requires some configuration before it can be used by a consumer.

## **Module Dynamic Setup**

To dynamically configure a module, the module should inherit from `IModuleSetup` and provide a `setup` method or `setup_register` method
that performs the necessary actions for setting up the module and then returns a `DynamicModule` or `ModuleSetup` instance.

```python
import typing as t
from ellar.core.modules import DynamicModule, ModuleSetup

class IModuleSetup:
    """Modules that must have a custom setup should inherit from IModuleSetup"""

    @classmethod
    def setup(cls, *args: t.Any, **kwargs: t.Any) -> DynamicModule:
        pass
    
    @classmethod
    def register_setup(cls, *args: t.Any, **kwargs: t.Any) -> ModuleSetup:
        pass

```

Note that `setup` method returns a `DynamicModule` instance, while `register_setup` method returns a `ModuleSetup` instance. 
The `DynamicModule` instance is used when the module requires some configuration before it can be used by a consumer, 
while the `ModuleSetup` instance is used when the module does not require any additional configuration outside the ones provided in the application config.

## **DynamicModule**
`DynamicModule` is a dataclass type that is used to **override** `Module` decorated attributes without having to modify the module code directly.
In other words, it gives you the flexibility to reconfigure module.

For example: Lets look at the code below:
```python
from ellar.common import Module
from ellar.core import DynamicModule
from ellar.di import ProviderConfig

@Module(providers=[ServiceA, ServiceB])
class ModuleA:
    pass

# we can reconfigure ModuleA dynamically using `DynamicModule` as shown below

@Module(
    modules=[
        DynamicModule(
            ModuleA, 
            providers=[
                ProviderConfig(ServiceA, use_class=str),
                ProviderConfig(ServiceB, use_class=dict),
            ]
        )
    ]
)
class ApplicationModule:
    pass
```
`ModuleA` has been defined with some arbitrary providers (`ServiceA` and `ServiceB`), but during registration of `ModuleA` in `ApplicationModule`,
we used `DynamicModule` to **override** its Module attribute `providers` with a new set of data.


## **ModuleSetup**
ModuleSetup is a dataclass type that used to set up a module based on its dependencies. 
It allows you to define the module **dependencies** and allow a **callback factory** function for a module dynamic set up.

**`ModuleSetup` Properties**:

- **`module`:** a required property that defines the type of module to be configured. The value must be a subclass of ModuleBase or IModuleSetup.
- **`inject`:** a sequence property that holds the types to be injected to the factory method. The order of the types will determine the order at which they are injected.
- **`factory`:** a factory function used to configure the module and take `Module` type as first argument and other services as listed in `inject` attribute.

Let's look this `ModuleSetup` example code below with our focus on how we eventually configured `DynamicService` type, 
how we used `my_module_configuration_factory` to dynamically build `MyModule` module.

```python
import typing as t
from ellar.common import Module, IModuleSetup
from ellar.di import ProviderConfig
from ellar.core import DynamicModule, ModuleBase, Config, ModuleSetup, AppFactory


class Foo:
    def __init__(self):
        self.foo = 'foo'


class DynamicService:
    def __init__(self, param1: t.Any, param2: t.Any, foo: str):
        self.param1 = param1
        self.param2 = param2
        self.foo = foo


@Module()
class MyModule(ModuleBase, IModuleSetup):
    @classmethod
    def setup(cls, param1: t.Any, param2: t.Any, foo: Foo) -> DynamicModule:
        return DynamicModule(
            cls,
            providers=[ProviderConfig(DynamicService, use_value=DynamicService(param1, param2, foo.foo))],
        )


def my_module_configuration_factory(module: t.Type[MyModule], config: Config, foo: Foo):
    return module.setup(param1=config.param1, param2=config.param2, foo=foo)


@Module(modules=[ModuleSetup(MyModule, inject=[Config, Foo], factory=my_module_configuration_factory),], providers=[Foo])
class ApplicationModule(ModuleBase):
    pass


app = AppFactory.create_from_app_module(ApplicationModule, config_module=dict(
    param1="param1",
    param2="param2",
))

dynamic_service = app.injector.get(DynamicService)
assert dynamic_service.param1 == "param1"
assert dynamic_service.param2 == "param2"
assert dynamic_service.foo == "foo"
```
In the example, we started by defining a service `DynamicService`, whose parameter depended on some values from application config
and from another service `Foo`. We then set up a `MyModule` and used as **setup** method which takes all parameter needed by 
`DynamicService` after that, we created `DynamicService` as a singleton and registered as a provider in `MyModule` 
for it to be accessible and injectable. 

At this point, looking at the setup function of `MyModule`, its clear `MyModule` depends on `Config` and `Foo` service. And this is where `ModuleSetup` usefulness comes in.

During registration in `ApplicationModule`, we wrapped `MyModule` around a `ModuleSetup` and stated its dependencies in the `inject` property and also
provided a `my_module_configuration_factory` factory that takes in module dependencies and return a `DynamicModule` configuration of `MyModule`.  

When `AppFactory` starts module bootstrapping, `my_module_configuration_factory` will be called with 
all the required **parameters** and returned a `DynamicModule` of `MyModule`.

For more example, checkout [Ellar Throttle Module](https://github.com/eadwinCode/ellar-throttler/blob/master/ellar_throttler/module.py){target="_blank"}
or [Ellar Cache Module](../techniques/caching.md){target="_blank"}
