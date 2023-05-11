import typing as t

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.modules import DynamicModule, ModuleSetup


class IModuleSetup:
    """Modules that must have a custom setup should inherit from IModuleSetup"""

    @classmethod
    @t.no_type_check
    def setup(cls, *args: t.Any, **kwargs: t.Any) -> "DynamicModule":
        """
        Provides Dynamic set up for a module.

        Usage:

        class MyModule(ModuleBase, IModuleSetup):
            @classmethod
            def setup(cls, param1: Any, param2: Any) -> DynamicModule:
                :return DynamicModule(module, provider=[], controllers=[], routers=[])


        @Module(modules=[MyModule.setup(param1='xyz', param2='abc')])
        class ApplicationModule(ModuleBase):
            pass
        """

    @classmethod
    @t.no_type_check
    def register_setup(cls, *args: t.Any, **kwargs: t.Any) -> "ModuleSetup":
        """
        The module defines all the dependencies its needs for its setup.
        Allowing parameters needed for setting up the module to come from app Config.

        Usage:

        class MyModule(ModuleBase, IModuleSetup):
            @classmethod
            def register_setup(cls) -> ModuleSetup:
                :return ModuleSetup(cls, inject=[Config, OtherServices], factory=cls.setup_module_factory)

            @staticmethod
            def setup_module_factory(module: t.Type['MyModule'], config: Config, others: OtherServices) -> DynamicModule:
                param1 = config.param1
                param2 = config.param2

                :return DynamicModule(module, provider=[], controllers=[], routers=[])


        @Module(modules=[MyModule.register_setup()])
        class ApplicationModule(ModuleBase):
            pass

        """
