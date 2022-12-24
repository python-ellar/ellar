import typing as t
from collections import OrderedDict, defaultdict

from injector import Injector

from ellar.compatible import asynccontextmanager
from ellar.constants import MODULE_REF_TYPES

from .container import Container
from .request_provider import RequestServiceProvider

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.modules import ModuleBase, ModuleRefBase, ModuleTemplateRef


class EllarInjector(Injector):
    __slots__ = ("_stack", "parent", "container", "_modules")

    def __init__(
        self,
        auto_bind: bool = True,
        parent: "Injector" = None,
    ) -> None:
        self._stack = ()

        self.parent = parent
        # Binder
        self.container = Container(
            self,
            auto_bind=auto_bind,
            parent=parent.binder if parent is not None else None,
        )

        # Bind some useful types
        self.container.register_instance(self, EllarInjector)
        self.container.register_instance(self.binder)
        self._modules: t.DefaultDict = defaultdict(OrderedDict)
        self._modules[MODULE_REF_TYPES.TEMPLATE] = OrderedDict()
        self._modules[MODULE_REF_TYPES.PLAIN] = OrderedDict()

    @property  # type: ignore
    def binder(self) -> Container:  # type: ignore
        return self.container

    @binder.setter
    def binder(self, value: t.Any) -> None:
        """Nothing happens"""

    def get_modules(
        self,
    ) -> t.Dict[t.Type["ModuleBase"], "ModuleRefBase"]:
        modules = dict(
            self._modules[MODULE_REF_TYPES.TEMPLATE],
        )
        modules.update(self._modules[MODULE_REF_TYPES.PLAIN])
        return modules

    def get_module(self, module: t.Type) -> t.Optional["ModuleRefBase"]:
        result: t.Optional["ModuleRefBase"] = None
        if module in self._modules[MODULE_REF_TYPES.TEMPLATE]:
            result = self._modules[MODULE_REF_TYPES.TEMPLATE][module]
            return result

        if module in self._modules[MODULE_REF_TYPES.PLAIN]:
            result = self._modules[MODULE_REF_TYPES.PLAIN][module]
            return result
        return result

    def get_templating_modules(
        self,
    ) -> t.Dict[t.Type["ModuleBase"], "ModuleTemplateRef"]:
        return self._modules.get(MODULE_REF_TYPES.TEMPLATE, {})

    def add_module(self, module_ref: "ModuleRefBase") -> None:
        self._modules[module_ref.ref_type].update({module_ref.module: module_ref})

    @asynccontextmanager
    async def create_request_service_provider(
        self,
    ) -> t.AsyncGenerator[RequestServiceProvider, None]:
        request_provider = RequestServiceProvider(self.container)
        try:
            yield request_provider
        finally:
            request_provider.dispose()
