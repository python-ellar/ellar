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
from ellar.di import ProviderConfig, injectable, register_request_scope_context
from ellar.reflect import reflect
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
    worked = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.instantiated = True
        self.worked = True


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
            operation_handler_type=operation.router_reflect_key,
            reflector=self.reflector,
        )

        reflect.define_metadata(
            "NewExecutionContext", i_execution_context, NewExecutionContext
        )

        return i_execution_context


@injectable()
class NewHostContextFactory(IHostContextFactory):
    def create_context(self, scope, receive=None, send=None) -> IHostContext:
        host_context = NewHostContext(scope=scope, receive=receive, send=send)
        register_request_scope_context(IHostContext, host_context)
        return host_context


class NewHostContext(HostContext):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.instantiated = True
        self.__class__.worked = True


@injectable()
class NewExceptionMiddlewareService(ExceptionMiddlewareService):
    worked = False

    def lookup_status_code_exception_handler(self, status_code: int):
        reflect.define_metadata(
            "NewExceptionMiddlewareService", self, NewExceptionMiddlewareService
        )
        self.worked = True
        return self._status_handlers.get(status_code)


def test_can_replace_host_context():
    tm = Test.create_test_module(controllers=[ExampleController]).override_provider(
        IHostContextFactory, use_class=NewHostContextFactory, core=True
    )

    assert hasattr(NewHostContext, "worked") is False
    client = tm.get_test_client()
    res = client.get("/example/exception")
    assert res.json() == {"detail": "Bad Request", "status_code": 400}

    assert hasattr(NewHostContext, "worked") is True
    assert NewHostContext.worked is True


def test_can_replace_exception_service(reflect_context):
    @Module(
        controllers=[ExampleController],
        providers=[
            ProviderConfig(
                IExceptionMiddlewareService,
                use_class=NewExceptionMiddlewareService,
                core=True,
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
    client = tm.get_test_client()
    assert NewExceptionMiddlewareService.worked is False

    res = client.get("/example/exception")
    assert res.status_code == 200
    assert res.text == "Exception 400 handled by ExampleModule.exception_400"

    new_exc_instance = reflect.get_metadata(
        "NewExceptionMiddlewareService", NewExceptionMiddlewareService
    )
    assert new_exc_instance.worked is True


def test_can_replace_execution_context():
    tm = Test.create_test_module(controllers=[ExampleController]).override_provider(
        IExecutionContextFactory, use_class=NewExecutionHostFactory, core=True
    )

    assert NewExecutionContext.worked is False
    client = tm.get_test_client()

    res = client.get("/example/")
    assert res.status_code == 200

    assert res.text == '"NewExecutionContext"'
    new_ctx_instance = reflect.get_metadata("NewExecutionContext", NewExecutionContext)
    assert new_ctx_instance.worked is True
