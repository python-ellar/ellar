import typing as t

from ..base import ModuleBase, ModuleBaseMeta
from ..schema import ModuleData
from .base import BaseModuleDecorator


class ModuleDecoratorBuilder:
    __slots__ = ("module",)

    def __init__(
        self, module: t.Union[t.Type[ModuleBase], ModuleBase, BaseModuleDecorator]
    ) -> None:
        self.module = module

    @classmethod
    def default(cls) -> ModuleData:
        return ModuleData(
            before_init=[],
            after_init=[],
            startup_event=[],
            shutdown_event=[],
            exception_handlers=dict(),
            middleware=[],
            routes=[],
        )

    def _build_module_base(self, module: t.Type[ModuleBase]) -> ModuleData:
        on_startup_events = list(module.get_on_startup())
        on_shutdown_events = list(module.get_on_shutdown())
        before_init_events = list(module.get_before_initialisation())
        after_init_events = list(module.get_after_initialisation())
        exception_handlers = dict(module.get_exceptions_handlers())
        middleware = list(module.get_middleware())

        return ModuleData(
            before_init=before_init_events,
            after_init=after_init_events,
            startup_event=on_startup_events,
            shutdown_event=on_shutdown_events,
            middleware=middleware,
            exception_handlers=exception_handlers,
            routes=[],
        )

    def _build_module_decorator(self, module: BaseModuleDecorator) -> ModuleData:
        module_data = self._build_module_base(module.get_module())

        return ModuleData(
            before_init=module_data.before_init,
            after_init=module_data.after_init,
            startup_event=module_data.startup_event,
            shutdown_event=module_data.shutdown_event,
            middleware=module_data.middleware,
            exception_handlers=module_data.exception_handlers,
            routes=module.get_routes(),
        )

    def build(self) -> ModuleData:
        if type(self.module) == ModuleBaseMeta:
            module_base = t.cast(t.Type[ModuleBase], self.module).get_module_decorator()
            if module_base:
                return self._build_module_decorator(module_base)
            return self._build_module_base(self.module)

        if isinstance(self.module, ModuleBase):
            module_base = type(self.module).get_module_decorator()
            if module_base:
                return self._build_module_decorator(module_base)
            return self._build_module_base(type(self.module))

        if isinstance(self.module, BaseModuleDecorator):
            return self._build_module_decorator(self.module)

        return self.default()

    @classmethod
    def extend(
        cls,
        data: ModuleData,
        module: t.Union[t.Type[ModuleBase], ModuleBase, BaseModuleDecorator],
    ) -> None:
        module_data = ModuleDecoratorBuilder(module).build()
        data.before_init.extend(module_data.before_init)
        data.after_init.extend(module_data.after_init)
        data.shutdown_event.extend(module_data.shutdown_event)
        data.startup_event.extend(module_data.startup_event)
        data.exception_handlers.update(module_data.exception_handlers)
        data.middleware.extend(module_data.middleware)
        data.routes.extend(module_data.routes)
