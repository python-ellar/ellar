# **Injector Scopes**
There are 3 different scopes which defines ways a service/provider is instantiated.

- [TRANSIENT SCOPE](#transientscope-)
- [SINGLETON SCOPE](#singletonscope-)
- [REQUEST SCOPE](#requestscope-)

## **`transient_scope`**: 
Whenever a transient scoped provider is required, a new instance of the provider is created

```python
# main.py

from ellar.di import EllarInjector, transient_scope, injectable

injector = EllarInjector(auto_bind=False)


@injectable(scope=transient_scope)
class ATransientClass:
    pass

injector.container.register(ATransientClass)
# OR
# injector.container.register_transient(ATransientClass)

def validate_transient_scope():
    a_transient_instance_1 = injector.get(ATransientClass)
    a_transient_instance_2 = injector.get(ATransientClass)
    
    assert a_transient_instance_2 != a_transient_instance_1 # True

    
if __name__ == "__main__":
    validate_transient_scope()
```

## **`singleton_scope`**: 
A singleton scoped provider is created once throughout the lifespan of the Container instance.

For example:
```python
# main.py

from ellar.di import EllarInjector, singleton_scope, injectable

injector = EllarInjector(auto_bind=False)
# OR

@injectable(scope=singleton_scope)
class ASingletonClass:
    pass

injector.container.register(ASingletonClass)
# OR
# injector.container.register_singleton(ASingletonClass)

def validate_singleton_scope():
    a_singleton_instance_1 = injector.get(ASingletonClass)
    a_singleton_instance_2 = injector.get(ASingletonClass)

    assert a_singleton_instance_2 == a_singleton_instance_1 # True

if __name__ == "__main__":
    validate_singleton_scope()
```

## **`request_scope`**: 
A request scoped provider is instantiated once during the scope of the request. And it's destroyed once the request is complete.
It is important to note that `request_scope` behaves like a `singleton_scope` during HTTPConnection mode and behaves like a `transient_scope` outside HTTPConnection mode.

```python
# main.py

import uvicorn
from ellar.di import EllarInjector, request_scope, injectable

injector = EllarInjector(auto_bind=False)


@injectable(scope=request_scope)
class ARequestScopeClass:
    pass


injector.container.register(ARequestScopeClass)


async def scoped_request(scope, receive, send):
    async with injector.create_asgi_args(scope, receive, send) as request_injector:
        request_instance_1 = request_injector.get(ARequestScopeClass)
        request_instance_2 = request_injector.get(ARequestScopeClass)
        assert request_instance_2 == request_instance_1

    request_instance_1 = injector.get(ARequestScopeClass)
    request_instance_2 = injector.get(ARequestScopeClass)

    assert request_instance_2 != request_instance_1


if __name__ == "__main__":
    uvicorn.run("main:scoped_request", port=5000, log_level="info")

```
