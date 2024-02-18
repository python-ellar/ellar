# **Interceptors - [(AOP) technique](https://en.wikipedia.org/wiki/Aspect-oriented_programming){target="_blank"}**

An interceptor is a class marked with the `@injectable()` decorator and adhering to the **`EllarInterceptor`** interface. 
They execute additional logic before or after method invocation.

Inspired by the principles of [Aspect-Oriented Programming (AOP)](https://en.wikipedia.org/wiki/Aspect-oriented_programming){target="_blank"}, 
interceptors offer several functionalities:

- Pre- and post-processing of method executions.
- Transformation of return values.
- Handling exceptions thrown during execution.
- Extension of method behavior.
- Conditional method override, useful for tasks like caching.

## **Basic**
Each interceptor class includes an `intercept()` method, accepting two parameters. 
The first parameter is an instance of the `ExecutionContext` class, which is identical to the object used for [guards](guards.md). 
The second parameter is a callable asynchronous function called `next_interceptor`, 
responsible for executing the subsequent interceptor in the execution sequence.

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
    The `intercept()` method within an interceptor class is an asynchronous function.

## **Execution context**
The `ExecutionContext` introduces several auxiliary methods that offer further insights into the ongoing execution process. 
This additional information can be valuable for creating more versatile interceptors capable of functioning across various controllers, methods, and execution contexts. 
For further details on `ExecutionContext`, refer to the documentation [here](../basics/execution-context.md).

## **Next Interceptor Handler**
The `next_interceptor` parameter in the `intercept()` method of the `EllarInterceptor` class serves a crucial role in invoking the route handler method within your interceptor. Omitting the invocation of `next_interceptor` within your implementation of `intercept()` will result in the route handler method not being executed.

This mechanism essentially encapsulates the request/response cycle within the `intercept()` method. Consequently, you have the flexibility to incorporate custom logic both before and after the execution of the final route handler. While it's evident how to include code before calling `next_interceptor()`, influencing the behavior afterward depends on the data returned by `next_interceptor()`.

From the perspective of Aspect-Oriented Programming, the invocation of the route handler (i.e., calling `next_interceptor()`) represents a Pointcut, denoting the point at which additional logic is injected.

For instance, consider an incoming `POST /car` request targeting the `create()` handler in the `CarController`. If an interceptor fails to call `next_interceptor()` at any point, the `create()` method won't execute. However, once `next_interceptor()` is invoked, the `create()` handler proceeds. Subsequently, upon receiving the response, additional operations can be performed on the returned data before delivering the final result to the client.


## **Aspect interception**
Here's a simple example demonstrating the use of an interceptor to log user interactions. The **LoggingInterceptor** intercepts requests before and after the route handler execution to log relevant information such as start time, end time, and duration of execution.

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
        
        # Invoke the next interceptor in the chain (or the route handler)
        res = await next_interceptor()
        
        # Log after route handler execution
        logger.info(f'After Route Handler Execution.... {time.time() - start_time}s')
        
        return res
```

This interceptor captures the timing of the request execution by recording the start time before invoking the route handler and calculating the duration after execution. It utilizes the logging module to output the relevant information.

Remember, like other components such as controllers and providers, interceptors can also inject dependencies through their constructor, enabling seamless integration with other parts of the application.

## **Binding interceptors**
To set up an interceptor, we utilize the `@UseInterceptors()` decorator from the `ellar.common` package. Similar to guards, interceptors can be scoped at the controller level, method level, or globally.

```python
from ellar.common import UseInterceptors, Controller

@UseInterceptors(LoggingInterceptor)
@Controller()
class CarController:
    ...
```

In the above code snippet, we apply the `UseInterceptors()` decorator to the `CarController` class, specifying `LoggingInterceptor` as the interceptor to be used. Note that we pass the type of the interceptor (not an instance), allowing the framework to handle instantiation and enabling dependency injection. Alternatively, we can directly pass an instance:

```python
from ellar.common import UseInterceptors, Controller

@UseInterceptors(LoggingInterceptor())
@Controller()
class CarController:
    ...
```

This construction attaches the interceptor to every handler declared within the controller. If we want to limit the scope of the interceptor to a specific method, we apply the decorator at the method level.

For setting up a global interceptor, we utilize the `use_global_interceptors()` method of the Ellar application instance:

```python
from ellar.app import AppFactory

app = AppFactory.create_from_app_module(ApplicationModule)
app.use_global_interceptors(LoggingInterceptor())
# OR
# app.use_global_interceptors(LoggingInterceptor)
```

This approach ensures that the interceptor is applied to every request processed by the Ellar application, regardless of the controller or method handling the request.

## **Exception Handling**
You can also manage exceptions during the request/response cycle before they are handled by system exception handlers.

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
            # Access the response object from the context
            res = context.switch_to_http_connection().get_response()
            # Set the status code to 400 for a custom exception
            res.status_code = 400
            # Return a JSON response with the exception message
            return {"message": str(cex)}
```

In the above code, the `InterceptCustomException` interceptor catches any `CustomException` raised during the execution of the request/response cycle. It then modifies the response object to set the status code to 400 and returns a JSON response containing the exception message. This allows for custom handling of exceptions within the interceptor before they are propagated to the system's exception handlers.
