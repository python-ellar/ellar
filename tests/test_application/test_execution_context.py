from ellar.common import (
    Controller,
    IExceptionMiddlewareService,
    IExecutionContext,
    IExecutionContextFactory,
    IHostContext,
    IHostContextFactory,
    Module,
    exception_handler,
    get,
)
from ellar.core import ModuleBase
from ellar.core.exceptions.service import ExceptionMiddlewareService
from ellar.core.execution_context import ExecutionContext, HostContext
from ellar.core.services import Reflector
from ellar.di import ProviderConfig, injectable
from ellar.testing import Test
from starlette.exceptions import HTTPException
from starlette.responses import PlainTextResponse


@Controller
class ExampleController:
    @get()
    def index(self):
        return self.context.__class__.__name__

    @get("/exception")
    def exception(self):
        raise HTTPException(status_code=400)


class NewExecutionContext(ExecutionContext):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.instantiated = True
        self.__class__.worked = True


@injectable()
class NewExecutionHostFactory(IExecutionContextFactory):
    def __init__(self, reflector: Reflector):
        self.reflector = reflector

    def create_context(
        self, operation, scope, receive=None, send=None
    ) -> IExecutionContext:
        i_execution_context = NewExecutionContext(
            scope=scope,
            receive=receive,
            send=send,
            operation_handler=operation.endpoint,
            operation_handler_type=operation.get_controller_type(),
            reflector=self.reflector,
        )

        return i_execution_context


@injectable()
class NewHostContextFactory(IHostContextFactory):
    def create_context(self, scope, receive=None, send=None) -> IHostContext:
        host_context = NewHostContext(scope=scope, receive=receive, send=send)
        host_context.get_service_provider().update_scoped_context(
            IHostContext, host_context
        )
        return host_context


class NewHostContext(HostContext):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.instantiated = True
        self.__class__.worked = True


@injectable()
class NewExceptionMiddlewareService(ExceptionMiddlewareService):
    def lookup_status_code_exception_handler(self, status_code: int):
        self.__class__.worked = True
        return self._status_handlers.get(status_code)


def test_can_replace_host_context():
    tm = Test.create_test_module(controllers=[ExampleController]).override_provider(
        IHostContextFactory, use_class=NewHostContextFactory
    )

    assert hasattr(NewHostContext, "worked") is False
    client = tm.get_test_client()
    res = client.get("/example/exception")
    assert res.json() == {"detail": "Bad Request", "status_code": 400}

    assert hasattr(NewHostContext, "worked") is True
    assert NewHostContext.worked is True


def test_can_replace_exception_service():
    @Module(
        controllers=[ExampleController],
        providers=[
            ProviderConfig(
                IExceptionMiddlewareService, use_class=NewExceptionMiddlewareService
            )
        ],
    )
    class ExampleModule(ModuleBase):
        @exception_handler(400)
        def exception_400(self, context: IHostContext, exc: Exception):
            return PlainTextResponse(
                "Exception 400 handled by ExampleModule.exception_400"
            )

    tm = Test.create_test_module(modules=[ExampleModule])

    assert hasattr(NewExceptionMiddlewareService, "worked") is False
    client = tm.get_test_client()
    res = client.get("/example/exception")
    assert res.status_code == 200
    assert res.text == "Exception 400 handled by ExampleModule.exception_400"

    assert hasattr(NewExceptionMiddlewareService, "worked") is True
    assert NewExceptionMiddlewareService.worked is True


def test_can_replace_execution_context():
    tm = Test.create_test_module(controllers=[ExampleController]).override_provider(
        IExecutionContextFactory, use_class=NewExecutionHostFactory
    )

    assert hasattr(NewExecutionContext, "worked") is False
    client = tm.get_test_client()
    res = client.get("/example/")
    assert res.status_code == 200
    assert res.text == '"NewExecutionContext"'

    assert hasattr(NewExecutionContext, "worked") is True
    assert NewExecutionContext.worked is True
