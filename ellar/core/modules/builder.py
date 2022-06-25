import typing as t

from ellar.constants import (
    EXCEPTION_HANDLERS_KEY,
    MIDDLEWARE_HANDLERS_KEY,
    MODULE_FIELDS,
    ON_REQUEST_SHUTDOWN_KEY,
    ON_REQUEST_STARTUP_KEY,
    TEMPLATE_FILTER_KEY,
    TEMPLATE_GLOBAL_KEY,
)
from ellar.core.events import EventHandler
from ellar.reflect import reflect

from .helper import class_parameter_executor_wrapper

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.middleware.schema import MiddlewareSchema
    from ellar.core.modules.base import ModuleBase, ModuleBaseMeta
    from ellar.core.templating import TemplateFunctionData


class ModuleBaseBuilder:
    __slots__ = ("_cls", "_actions")

    def __init__(self, cls: t.Union[t.Type["ModuleBase"], "ModuleBaseMeta"]) -> None:
        self._cls = cls
        self._cls.__MODULE_FIELDS__ = t.cast(
            t.Dict, getattr(self._cls, MODULE_FIELDS, None) or dict()
        )
        self._actions: t.Dict[str, t.Callable[[t.Any], None]] = dict()
        self._actions.update(
            {
                EXCEPTION_HANDLERS_KEY: self.exception_config,
                MIDDLEWARE_HANDLERS_KEY: self.middleware_config,
                ON_REQUEST_SHUTDOWN_KEY: self.on_request_shut_down_config,
                ON_REQUEST_STARTUP_KEY: self.on_request_startup_config,
                TEMPLATE_GLOBAL_KEY: self.template_global_config,
                TEMPLATE_FILTER_KEY: self.template_filter_config,
            },
        )

    def exception_config(self, exception_dict: t.Dict) -> None:
        for k, v in exception_dict.items():
            func = class_parameter_executor_wrapper(self._cls, v)
            reflect.define_metadata(EXCEPTION_HANDLERS_KEY, {k: func}, self._cls)

    @t.no_type_check
    def middleware_config(self, middleware: "MiddlewareSchema") -> None:
        middleware.dispatch = class_parameter_executor_wrapper(
            self._cls, middleware.dispatch
        )
        reflect.define_metadata(
            MIDDLEWARE_HANDLERS_KEY,
            middleware.create_middleware(),
            self._cls,
            default_value=[],
        )

    def on_request_shut_down_config(self, on_shutdown_event: EventHandler) -> None:
        on_shutdown_event.handler = class_parameter_executor_wrapper(
            self._cls, on_shutdown_event.handler
        )
        reflect.define_metadata(
            ON_REQUEST_SHUTDOWN_KEY,
            on_shutdown_event.handler,
            self._cls,
            default_value=[],
        )

    def on_request_startup_config(self, on_startup_event: EventHandler) -> None:
        on_startup_event.handler = class_parameter_executor_wrapper(
            self._cls, on_startup_event.handler
        )
        reflect.define_metadata(
            ON_REQUEST_STARTUP_KEY,
            on_startup_event.handler,
            self._cls,
            default_value=[],
        )

    def template_filter_config(self, template_filter: "TemplateFunctionData") -> None:
        reflect.define_metadata(
            TEMPLATE_FILTER_KEY,
            {
                template_filter.name: class_parameter_executor_wrapper(
                    self._cls, template_filter.func
                )
            },
            self._cls,
            default_value={},
        )

    def template_global_config(self, template_filter: "TemplateFunctionData") -> None:
        reflect.define_metadata(
            TEMPLATE_GLOBAL_KEY,
            {
                template_filter.name: class_parameter_executor_wrapper(
                    self._cls, template_filter.func
                )
            },
            self._cls,
            default_value={},
        )

    def build(self, namespace: t.Dict) -> None:
        for name, item in namespace.items():
            for k, func in self._actions.items():
                if hasattr(item, k):
                    value = getattr(item, k)
                    func(value)
                    self._cls.__MODULE_FIELDS__[name] = item
