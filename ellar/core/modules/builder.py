import typing as t

from ellar.common.compatible import AttributeDict
from ellar.common.constants import (
    EXCEPTION_HANDLERS_KEY,
    MIDDLEWARE_HANDLERS_KEY,
    MODULE_DECORATOR_ITEM,
    MODULE_METADATA,
    TEMPLATE_FILTER_KEY,
    TEMPLATE_GLOBAL_KEY,
)
from ellar.common.exceptions import CallableExceptionHandler
from ellar.core.middleware import FunctionBasedMiddleware, Middleware
from ellar.reflect import reflect

from ...utils import get_functions_with_tag
from .helper import module_callable_factory

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.common.templating import TemplateFunctionData
    from ellar.core.modules import ModuleBase, ModuleBaseMeta


class ModuleBaseBuilder:
    __slots__ = ("_cls", "_actions")

    def __init__(self, cls: t.Union[t.Type["ModuleBase"], "ModuleBaseMeta"]) -> None:
        self._cls = cls
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
            self._cls.MODULE_FIELDS.setdefault(EXCEPTION_HANDLERS_KEY, []).append(
                CallableExceptionHandler(
                    callable_exception_handler=module_callable_factory(v, self._cls),
                    exc_class_or_status_code=k,
                )
            )

    @t.no_type_check
    def middleware_config(self, middleware: AttributeDict) -> None:
        dispatch = module_callable_factory(middleware.dispatch, self._cls)
        self._cls.MODULE_FIELDS.setdefault(MIDDLEWARE_HANDLERS_KEY, []).append(
            Middleware(
                FunctionBasedMiddleware,
                dispatch=dispatch,
                **middleware.options,
                provider_token=reflect.get_metadata(MODULE_METADATA.NAME, self._cls),
            )
        )

    def template_filter_config(self, template_filter: "TemplateFunctionData") -> None:
        self._cls.MODULE_FIELDS.setdefault(TEMPLATE_FILTER_KEY, {}).update(
            {
                template_filter.name: module_callable_factory(
                    template_filter.func, self._cls
                )
            }
        )

    def template_global_config(self, template_filter: "TemplateFunctionData") -> None:
        self._cls.MODULE_FIELDS.setdefault(TEMPLATE_GLOBAL_KEY, {}).update(
            {
                template_filter.name: module_callable_factory(
                    template_filter.func, self._cls
                )
            }
        )

    def build(self) -> None:
        self._cls.MODULE_FIELDS = {}

        for _, item in get_functions_with_tag(self._cls, MODULE_DECORATOR_ITEM):
            action_name = getattr(item, MODULE_DECORATOR_ITEM)
            handler = self._actions[action_name]
            handler(item.__dict__[action_name])
