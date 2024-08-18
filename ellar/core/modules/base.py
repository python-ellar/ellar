import typing as t

from ellar.common.compatible import AttributeDict
from ellar.common.constants import (
    APP_EXCEPTION_HANDLERS_KEY,
    APP_MIDDLEWARE_HANDLERS_KEY,
    EXCEPTION_HANDLERS_KEY,
    MIDDLEWARE_HANDLERS_KEY,
    MODULE_DECORATOR_ITEM,
    TEMPLATE_CONTEXT_PROCESSOR_KEY,
    TEMPLATE_FILTER_KEY,
    TEMPLATE_GLOBAL_KEY,
)
from ellar.core.exceptions import CallableExceptionHandler
from ellar.core.middleware import FunctionBasedMiddleware
from ellar.core.middleware.middleware import EllarMiddleware
from ellar.core.modules.helper import module_callable_factory
from ellar.di.injector import Container
from ellar.reflect import reflect
from ellar.utils import get_functions_with_tag
from injector import Binder
from injector import Module as _InjectorModule

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.common.templating import TemplateFunctionData
    from ellar.core.modules import ModuleRefBase


class _ModuleBaseBuilder:
    __slots__ = ("_cls", "_actions")

    def __init__(self, cls: t.Union[t.Type["ModuleBase"], "ModuleBaseMeta"]) -> None:
        self._cls = cls
        self._actions: t.Dict[str, t.Callable[[t.Any], None]] = {
            EXCEPTION_HANDLERS_KEY: self.exception_config,
            MIDDLEWARE_HANDLERS_KEY: self.middleware_config,
            TEMPLATE_GLOBAL_KEY: self.template_global_config,
            TEMPLATE_FILTER_KEY: self.template_filter_config,
            TEMPLATE_CONTEXT_PROCESSOR_KEY: self.template_context_processor,
        }

    def exception_config(self, exception_dict: t.Dict) -> None:
        for k, v in exception_dict.items():
            func, global_exc = v
            reflect.define_metadata(
                APP_EXCEPTION_HANDLERS_KEY if global_exc else EXCEPTION_HANDLERS_KEY,
                [
                    CallableExceptionHandler(
                        handler=module_callable_factory(func, self._cls),
                        exc_or_status_code=k,
                    )
                ],
                self._cls,
            )

    @t.no_type_check
    def middleware_config(self, middleware: AttributeDict) -> None:
        dispatch = module_callable_factory(middleware.dispatch, self._cls)
        reflect.define_metadata(
            APP_MIDDLEWARE_HANDLERS_KEY
            if middleware.is_global
            else MIDDLEWARE_HANDLERS_KEY,
            [
                EllarMiddleware(
                    FunctionBasedMiddleware,
                    dispatch=dispatch,
                    **middleware.options,
                )
            ],
            self._cls,
        )

    def template_filter_config(self, template_filter: "TemplateFunctionData") -> None:
        reflect.define_metadata(
            TEMPLATE_FILTER_KEY,
            {
                template_filter.name: module_callable_factory(
                    template_filter.func, self._cls
                )
            },
            self._cls,
        )

    def template_context_processor(self, f: t.Callable) -> None:
        reflect.define_metadata(TEMPLATE_CONTEXT_PROCESSOR_KEY, [f], self._cls)

    def template_global_config(self, template_filter: "TemplateFunctionData") -> None:
        reflect.define_metadata(
            TEMPLATE_GLOBAL_KEY,
            {
                template_filter.name: module_callable_factory(
                    template_filter.func, self._cls
                )
            },
            self._cls,
        )

    def build(self) -> None:
        for _, item in get_functions_with_tag(self._cls, MODULE_DECORATOR_ITEM):
            action_name = getattr(item, MODULE_DECORATOR_ITEM)
            handler = self._actions[action_name]
            handler(item.__dict__[action_name])


class ModuleBaseMeta(type):
    @t.no_type_check
    def __init__(cls, name, bases, namespace) -> None:
        super().__init__(name, bases, namespace)
        _ModuleBaseBuilder(cls).build()


class ModuleBase(_InjectorModule, metaclass=ModuleBaseMeta):
    @classmethod
    def post_build(cls, module_ref: "ModuleRefBase") -> None:
        """Executed after a Subclass build process is done"""

    def register_services(self, container: Container) -> None:
        """Register other services manually"""

    def configure(self, container: Binder) -> None:
        """Injector Module Support. Override register_services instead"""
        self.register_services(t.cast(Container, container))
