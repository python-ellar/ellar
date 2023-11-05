# **Guards**

A **Guard** in Ellar is a way to add **authentication** and **authorization** checks to your application. 
It acts as a middleware and runs before executing the route handler. If the guard returns **false**, the request is rejected and the execution is stopped. 

**Guards** can be used to check for specific roles, permissions, or any other arbitrary condition. 
They can be easily applied to individual routes or groups of routes using `@guard` decorator.

Unlike middleware, a guard have access to the `ExecutionContext` which provides information for the route function to be executed and its controller.

!!! Note
    Guards are executed **after** all middleware

## **Authorization guard**
Authorization is a great example of a guard because some routes should be available only to specific authenticated user and or users that sufficient permissions. 
Let's assume we have a `AuthGard` which checks if a making a request is authenticated.

```python
from ellar.common import GuardCanActivate, IExecutionContext
from ellar.di import injectable

@injectable()
class AuthGuard(GuardCanActivate):
  async def can_activate(self,context: IExecutionContext) -> bool: 
    request = context.switch_to_http_connection().get_request()
    return self.validate_request(request)

  def validate_request(self, request) -> bool:
    ...

```
The implementation of the `validate_request()` function, in the example above, can be simple or complex depending on the use case. 
The primary objective is to demonstrate the integration of guards into the request/response cycle.

Every guard must inherit from `GuardCanActivate` and override `can_activate()` function. 
The `can_activate()` function is required to return a `boolean` value. The return value determines the next action:

- If the function returns **`true`**, the request will be processed.
- If the function returns **`false`**, Ellar will reject the request.

## **Role-based authentication**
Let's build a more functional guard that permits access only to users with a specific role. 
We'll start with a basic guard template, and build on it in the coming sections. 
For now, it allows all requests to proceed:

```python
# project_name/cars/guards.py

from ellar.common import GuardCanActivate, IExecutionContext
from ellar.di import injectable

@injectable()
class RoleGuard(GuardCanActivate):
  async def can_activate(self,context: IExecutionContext) -> bool: 
    return True
```

## **Applying guards**
Guards can be **`controller-scoped`**, **`method-scoped`**, or **`global-scoped`**. We apply guards to controllers or route function by using `@Guards`.
The `@UseGuards` takes a single argument, or a comma-separated list of arguments of `GuardCanActivate` types or instances.

```python
import typing as t

def UseGuards(
    *_guards: t.Type["GuardCanActivate"] | "GuardCanActivate"
) -> t.Callable:
    ...
```

### **Controller-scoped**
We set up controller scoped guards on controller by using `@UseGuards` decorator. For example:
```python
# project_name/cars/controllers.py
from ellar.common import Controller, UseGuards
from .guards import RoleGuard

@Controller()
@UseGuards(RoleGuard)
class CarsController:
    ...

```
The above example attaches the guard to every handler declared by this controller. 
If we wish the guard to apply only to a single method, we apply the `@UseGuards()` decorator at the method level.

### **Method-scoped**
We can also use `@UseGuards()` on route-function when necessary.
```python
# project_name/cars/controllers.py
from ellar.common import Controller, UseGuards, get
from .guards import RoleGuard

@Controller()
@UseGuards(RoleGuard)
class CarsController:
    @UseGuards(RoleGuard())
    @get('/guarded-route')
    def guarded_route(self):
        return "Passed Guard"

```
In the example, we decorated `guarded_route` with `@UseGuards(RoleGuard())` with an instance of `RoleGuard`. 
When request execution for `/guarded-route`, `guarded_route` guard definition will be precedence over `CarsController` guard definitions.

### **Global-scope**
Global guards are used across the whole application, for every controller and every route function but individual controller or route function `@UseGuards` definition can override `global` scoped guards.

Global guards can be applied at application level using `use_global_guards` as shown below:

```python title='project_name/server.py' linenums='1'

import os

from ellar.common.constants import ELLAR_CONFIG_MODULE
from ellar.core.factory import AppFactory
from .apps.cars.guards import RoleGuard
from .root_module import ApplicationModule

application = AppFactory.create_from_app_module(
    ApplicationModule,
    config_module=os.environ.get(
        ELLAR_CONFIG_MODULE, "dialerai.config:DevelopmentConfig"
    )
)
application.use_global_guards(RoleGuard, MoreGuards, ...)
```
Global Guards can also be applied through Dependency Injection. For instance, in `project_name/car/module.py`, we can
register `RoleGuard` in the module `providers` parameter as a Global guards. See illustration below:

```python title='project_name/car/module.py' linenums='1'
from ellar.common import Module, GlobalGuard
from ellar.core import ModuleBase
from ellar.di import Container, ProviderConfig

from .services import CarRepository
from .controllers import CarController
from .guards import RoleGuard

@Module(
    controllers=[CarController],
    providers=[CarRepository, ProviderConfig(GlobalGuard, use_class=RoleGuard)]
)
class CarModule(ModuleBase):
    def register_providers(self, container: Container) -> None:
        # for more complicated provider registrations
        # container.register_instance(...)
        pass

```

## **Rounding up RoleGuard**
Our `RolesGuard` is working, but it's not very smart yet. Let's assume we want our `RoleGuard` to manage user role permissions in a more general context
employing the power of `ExecutionContext` and `custom metadata`. In `CarController`, for example, could have different permission schemes for different routes. 
Some might be available only for an admin user, and others could be open for everyone. 

```python
from ellar.common import post, set_metadata

...
@post()
@set_metadata('roles', ['admin'])
async def create(self, payload:Body[CreateCarSerializer]):
    self.repo.create_car(payload)
    return 'This action adds a new car'
...
```
In the above example, we attached the `roles` metadata (roles is a key, while ['admin'] is a particular value) to the `create()` method. 
While this works, it's not good practice to use `@set_metadata()` directly in your routes. So we can refactor that code as shown below:

```python
# project_name/role_decorator.py
import typing
from ellar.common import set_metadata


def roles(*_roles: str) -> typing.Callable:
    return set_metadata('roles', list(_roles))
```

This approach is much cleaner and more readable, and is strongly typed. 
Now that we have a custom `@roles()` decorator, we can use it to decorate the `create()` method.
```python
...
@post()
@role('admin', 'staff')
async def create(self, payload:Body[CreateCarSerializer]):
    self.repo.create_car(payload)
    return 'This action adds a new car'
...
```

Let's now go back and tie this together with our `RolesGuard`. Currently, it simply returns `true` in all cases, allowing every request to proceed. 
We want to make the return value conditional based on the comparing the roles assigned to the current `user` to the actual roles required by the current route being processed. 

In order to access the route's function `role(s)` **(custom metadata)**, we'll use the `Reflector` helper class, which is provided out of the box by the framework.

```python
# project_name/apps/cars/guards.py
import typing as t
from ellar.di import injectable
from ellar.common import GuardCanActivate, IExecutionContext
from ellar.core.services import Reflector


@injectable()
class RoleGuard(GuardCanActivate):
    def __init__(self, reflector: Reflector):
        self.reflector = reflector
    
    def match_roles(self, roles: t.List[str], user_roles: t.List[str]) -> bool:
        for user_role in user_roles:
            if user_role in roles:
                return True
        
        return False
    
    async def can_activate(self, context: IExecutionContext) -> bool:
        roles = self.reflector.get('roles', context.get_handler())
        # request = context.switch_to_http_connection().get_request()
        # check if user in request object has role
        if not roles:
            return True
        
        request = context.switch_to_http_connection().get_request()
        user = request.user
        
        return self.match_roles(roles, user_roles=user.roles)
```
Here, we are assuming an authenticated `user` object exist in request object.

When a user with insufficient privileges requests an endpoint, Ellar automatically returns the following response:
```json
{
  "detail": "Forbidden",
  "status_code": 403
}
```

Note that behind the scenes, when a guard returns `false`, the framework throws a `HTTPException` with status code **403** . 
If you want to return a different error response, you should throw your own specific exception by override `raise_exception` function as shown below:
```python
from ellar.common import APIException, GuardCanActivate
from ellar.di import injectable
from ellar.core import Reflector

@injectable()
class RoleGuard(GuardCanActivate):
    def __init__(self, reflector: Reflector):
        self.reflector = reflector
        
    def raise_exception(self) -> None:
        raise APIException(detail="You don't have the permission to perform this action", status_code=403)
    ...
```
The construct will output the json below when the guard returns `false`
```json
{
  "detail": "You don't have the permission to perform this action"
}
```
