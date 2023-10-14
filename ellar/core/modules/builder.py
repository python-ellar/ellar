import typing as t

from ellar.common.compatible import AttributeDict
from ellar.common.constants import (
    EXCEPTION_HANDLERS_KEY,
    MIDDLEWARE_HANDLERS_KEY,
    MODULE_FIELDS,
    TEMPLATE_FILTER_KEY,
    TEMPLATE_GLOBAL_KEY,
)
from ellar.common.exceptions import CallableExceptionHandler
from ellar.core.middleware import FunctionBasedMiddleware, Middleware
from ellar.reflect import reflect

from .helper import module_callable_factory

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.common.templating import TemplateFunctionData
    from ellar.core.modules import ModuleBase, ModuleBaseMeta


class ModuleBaseBuilder:
    __slots__ = ("_cls", "_actions")

    def __init__(self, cls: t.Union[t.Type["ModuleBase"], "ModuleBaseMeta"]) -> None:
        self._cls = cls
        self._cls.__MODULE_FIELDS__ = t.cast(
            t.Dict, getattr(self._cls, MODULE_FIELDS, None) or {}
        )
        self._actions: t.Dict[str, t.Callable[[t.Any], None]] = {}
        self._actions.update(
            {
                EXCEPTION_HANDLERS_KEY: self.exception_config,
                MIDDLEWARE_HANDLERS_KEY: self.middleware_config,
                TEMPLATE_GLOBAL_KEY: self.template_global_config,
                TEMPLATE_FILTER_KEY: self.template_filter_config,
            },
        )

    def exception_config(self, exception_dict: t.Dict) -> None:
        for k, v in exception_dict.items():
            func = CallableExceptionHandler(
                self._cls, callable_exception_handler=v, exc_class_or_status_code=k
            )
            reflect.define_metadata(EXCEPTION_HANDLERS_KEY, [func], self._cls)

    @t.no_type_check
    def middleware_config(self, middleware: AttributeDict) -> None:
        dispatch = module_callable_factory(middleware.dispatch, self._cls)
        reflect.define_metadata(
            MIDDLEWARE_HANDLERS_KEY,
            [
                Middleware(
                    FunctionBasedMiddleware, dispatch=dispatch, **middleware.options
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

    def build(self, namespace: t.Dict) -> None:
        for name, item in namespace.items():
            for k, func in self._actions.items():
                if hasattr(item, k):
                    value = item.__dict__.pop(k)
                    func(value)
                    self._cls.__MODULE_FIELDS__[name] = item
