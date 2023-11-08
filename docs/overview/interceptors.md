# **Interceptors - [(AOP) technique](https://en.wikipedia.org/wiki/Aspect-oriented_programming){target="_blank"}**

An interceptor is a class annotated with the `@injectable()` decorator and implements the EllarInterceptor interface.
During request-response cycle, interceptors are called after middleware execution before route handler execution.

Interceptors have a set of useful capabilities which are inspired by the  [Aspect Oriented Programming (AOP) technique](https://en.wikipedia.org/wiki/Aspect-oriented_programming){target="_blank"} technique. 
They make it possible to:

- bind extra logic before / after method execution
- transform the result returned from a function
- transform the exception thrown from a function
- extend the basic function behavior
- completely override a function depending on specific conditions (e.g., for caching purposes)

## **Basic**
Each interceptor implements the `intercept()` method, which takes two arguments. 
The first one is the `ExecutionContext` instance (exactly the same object as for [guards](guards.md){target="_blank"}) and 
`next_interceptor` awaitable function that executes the next interceptor in the execution chain.

```python
import typing as t
from abc import ABC, abstractmethod
from ellar.common import IExecutionContext


class EllarInterceptor(ABC):
    @abstractmethod
    async def intercept(
        self, context: IExecutionContext, next_interceptor: t.Callable[..., t.Coroutine]
    ) -> t.Any:
        """implementation comes here"""
```
!!! note
    `intercept` function of interceptor class is an asynchronous function.

## **Execution context**
The `ExecutionContext` adds several new helper methods that provide additional details about the current execution process. 
These details can be helpful in building more generic interceptors that can work across a broad set of controllers, methods, and execution contexts. 
Learn more about `ExecutionContext` [here](../basics/execution-context.md){target="_blank"}.

## **Next Interceptor Handler**
The second argument, `next_interceptor`,  in `intercept` of EllarInterceptor class is used to invoke the route handler method at some point in your interceptor.
If you don't call the `next_interceptor` method in your implementation of the `intercept()` method, the route handler method won't be executed at all.

This approach means that the `intercept()` method effectively wraps the request/response cycle. 
As a result, you may implement custom logic **both before and after** the execution of the final route handler. 
It's clear that you can write code in your `intercept()` method that executes before calling `next_interceptor()`, 
but how do you affect what happens afterward? depending on the nature of the data returned by `next_interceptor()`, 
further manipulation can be done before final response to the client.
 
Using Aspect Oriented Programming terminology, the invocation of the route handler 
(i.e., calling `next_interceptor()`) is called a Pointcut, indicating that it's the point at which our 
additional logic is inserted.

Consider, for example, an incoming `POST /car` request. This request is destined for the `create()` handler 
defined inside the `CarController`. If an interceptor which does not call the `next_interceptor()`
method is called anywhere along the way, the `create()` method won't be executed. 
Once `next_interceptor()` is called, the `create()` handler will be triggered. And once the response is returned, 
additional operations can be performed on the data returned, and a final result returned to the client.


## **Aspect interception**
The first use case we'll look at is to use an interceptor to log user interaction (e.g., storing user calls, asynchronously dispatching events or calculating a timestamp). 
We show a simple LoggingInterceptor below:

```python
import typing as t
import logging
import time
from ellar.common import EllarInterceptor, IExecutionContext
from ellar.di import injectable


logger = logging.getLogger('ellar')


@injectable()
class LoggingInterceptor(EllarInterceptor):
    async def intercept(
        self, context: IExecutionContext, next_interceptor: t.Callable[..., t.Coroutine]
    ) -> t.Any:
        logger.info('Before Route Handler Execution...')
        start_time = time.time()
        
        res = await next_interceptor()
        logger.info(f'After Route Handler Execution.... {time.time() - start_time}s')
        return res
```

!!! hint
    Interceptors, like controllers, providers, guards, and so on, can inject dependencies through their `constructor`.

## **Binding interceptors**
In order to set up the interceptor, we use the `@UseInterceptors()` decorator imported from the `ellar.common` package. 
Like **guards**, interceptors can be controller-scoped, method-scoped, or global-scoped.

```python
from ellar.common import UseInterceptors, Controller

@UseInterceptors(LoggingInterceptor)
@Controller()
class CarController:
    ...
```

Note that we passed the LoggingInterceptor type (instead of an instance), leaving responsibility for instantiation to the framework and enabling dependency injection. 
As with guards, we can also pass an in-place instance:

```python
from ellar.common import UseInterceptors, Controller

@UseInterceptors(LoggingInterceptor())
@Controller()
class CarController:
    ...
```

As mentioned, the construction above attaches the interceptor to every handler declared by this controller. 
If we want to restrict the interceptor's scope to a single method, we simply apply the decorator at the method level.

In order to set up a global interceptor, we use the use_global_interceptors() method of the Ellar application instance:

```python
from ellar.app import AppFactory

app = AppFactory.create_from_app_module(ApplicationModule)
app.use_global_interceptors(LoggingInterceptor())
# OR
# app.use_global_interceptors(LoggingInterceptor)
```

## **Exception Handling**
You can also handle exception through on the process of request/response cycle before it gets handled by system exception handlers.

```python
class CustomException(Exception):
    pass


@injectable
class InterceptCustomException(EllarInterceptor):
    async def intercept(
        self, context: IExecutionContext, next_interceptor: t.Callable[..., t.Coroutine]
    ) -> t.Any:
        try:
            return await next_interceptor()
        except CustomException as cex:
            res = context.switch_to_http_connection().get_response()
            res.status_code = 400
            return {"message": str(cex)}
```
