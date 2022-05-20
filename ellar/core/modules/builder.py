import typing as t

from ellar.constants import (
    EXCEPTION_HANDLERS_KEY,
    MIDDLEWARE_HANDLERS_KEY,
    ON_APP_INIT,
    ON_APP_STARTED,
    ON_SHUTDOWN_KEY,
    ON_STARTUP_KEY,
    TEMPLATE_FILTER_KEY,
    TEMPLATE_GLOBAL_KEY,
)
from ellar.core.events import ApplicationEventHandler, EventHandler

from .helper import class_parameter_executor_wrapper

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.middleware.schema import MiddlewareSchema
    from ellar.core.modules.base import ModuleBase, ModuleBaseMeta
    from ellar.core.templating import TemplateFunctionData


class ModuleBaseBuilder:
    __slots__ = ("_cls", "_actions")

    def __init__(self, cls: t.Union[t.Type["ModuleBase"], "ModuleBaseMeta"]) -> None:
        self._cls = cls
        self._actions: t.Dict[str, t.Callable[[t.Any], None]] = dict()
        self._actions.update(
            {
                EXCEPTION_HANDLERS_KEY: self.exception_config,
                MIDDLEWARE_HANDLERS_KEY: self.middleware_config,
                ON_APP_INIT: self.on_app_init_config,
                ON_APP_STARTED: self.on_app_started_config,
                ON_SHUTDOWN_KEY: self.on_shut_down_config,
                ON_STARTUP_KEY: self.on_startup_config,
                TEMPLATE_GLOBAL_KEY: self.template_global_config,
                TEMPLATE_FILTER_KEY: self.template_filter_config,
            },
        )

    def exception_config(self, exception_dict: t.Dict) -> None:
        for k, v in exception_dict.items():
            func = class_parameter_executor_wrapper(self._cls, v)
            self._cls.get_exceptions_handlers().update({k: func})

    @t.no_type_check
    def middleware_config(self, middleware: "MiddlewareSchema") -> None:
        middleware.dispatch = class_parameter_executor_wrapper(
            self._cls, middleware.dispatch
        )
        self._cls.get_middleware().append(middleware.create_middleware())

    def on_app_init_config(self, on_app_init_event: ApplicationEventHandler) -> None:
        on_app_init_event.handler = class_parameter_executor_wrapper(
            self._cls, on_app_init_event.handler
        )
        self._cls.get_before_initialisation()(on_app_init_event.handler)

    def on_app_started_config(
        self, on_app_started_event: ApplicationEventHandler
    ) -> None:
        on_app_started_event.handler = class_parameter_executor_wrapper(
            self._cls, on_app_started_event.handler
        )
        self._cls.get_after_initialisation()(on_app_started_event.handler)

    def on_shut_down_config(self, on_shutdown_event: EventHandler) -> None:
        on_shutdown_event.handler = class_parameter_executor_wrapper(
            self._cls, on_shutdown_event.handler
        )
        self._cls.get_on_shutdown()(on_shutdown_event.handler)

    def on_startup_config(self, on_startup_event: EventHandler) -> None:
        on_startup_event.handler = class_parameter_executor_wrapper(
            self._cls, on_startup_event.handler
        )
        self._cls.get_on_startup()(on_startup_event.handler)

    def template_filter_config(self, template_filter: "TemplateFunctionData") -> None:
        module_decorator = self._cls.get_module_decorator()
        if module_decorator:
            module_decorator.jinja_environment.filters[
                template_filter.name
            ] = class_parameter_executor_wrapper(self._cls, template_filter.func)

    def template_global_config(self, template_filter: "TemplateFunctionData") -> None:
        module_decorator = self._cls.get_module_decorator()
        if module_decorator:
            module_decorator.jinja_environment.globals[
                template_filter.name
            ] = class_parameter_executor_wrapper(self._cls, template_filter.func)

    def build(self, namespace: t.Dict) -> None:
        for item in namespace.values():
            for k, func in self._actions.items():
                if hasattr(item, k):
                    value = getattr(item, k)
                    func(value)
