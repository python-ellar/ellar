import typing as t

from ellar.common import IModuleSetup, Module
from ellar.core.conf import Config
from ellar.core.modules import DynamicModule, ModuleBase, ModuleRefBase, ModuleSetup
from ellar.di import ProviderConfig

from .interface import ICacheService
from .model import BaseCacheBackend
from .schema import CacheModuleSchemaSetup
from .service import CacheService


@Module(exports=[ICacheService])
class CacheModule(ModuleBase, IModuleSetup):
    @classmethod
    def _create_dynamic_module(cls, schema: CacheModuleSchemaSetup) -> DynamicModule:
        cache_service = CacheService(
            t.cast(t.Dict[str, BaseCacheBackend], dict(schema.CACHES))
        )

        return DynamicModule(
            cls,
            providers=[
                ProviderConfig(CacheService, use_value=cache_service),
                ProviderConfig(ICacheService, use_value=cache_service),
            ],
        )

    @classmethod
    def setup(
        cls, default: BaseCacheBackend, **kwargs: BaseCacheBackend
    ) -> DynamicModule:
        args = {"default": default}
        args.update(kwargs)

        schema = CacheModuleSchemaSetup(**{"CACHES": args})  # type: ignore[arg-type]
        return cls._create_dynamic_module(schema)

    @classmethod
    def register_setup(cls) -> ModuleSetup:
        return ModuleSetup(cls, inject=[Config], factory=cls.__register_setup_factory)

    @staticmethod
    def __register_setup_factory(
        module_ref: "ModuleRefBase", config: Config
    ) -> DynamicModule:
        if config.CACHES:
            schema = CacheModuleSchemaSetup(**{"CACHES": config.CACHES})
            module = t.cast(t.Type[CacheModule], module_ref.module)
            return module._create_dynamic_module(schema)

        cache_service = CacheService()

        return DynamicModule(
            module_ref.module,
            providers=[
                ProviderConfig(CacheService, use_value=cache_service),
                ProviderConfig(ICacheService, use_value=cache_service),
            ],
        )
