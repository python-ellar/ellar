import typing as t

from ellar.common import IModuleSetup, Module
from ellar.core import Config, DynamicModule, ModuleBase, ModuleSetup
from ellar.di import ProviderConfig

from .interface import ICacheService
from .model import BaseCacheBackend
from .schema import CacheModuleSchemaSetup
from .service import CacheService


@Module()
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
        return ModuleSetup(cls, inject=[Config], factory=cls.register_setup_factory)

    @staticmethod
    def register_setup_factory(
        module: t.Type["CacheModule"], config: Config
    ) -> DynamicModule:
        if config.CACHES:
            schema = CacheModuleSchemaSetup(**{"CACHES": config.CACHES})
            return module._create_dynamic_module(schema)

        cache_service = CacheService()

        return DynamicModule(
            module,
            providers=[
                ProviderConfig(CacheService, use_value=cache_service),
                ProviderConfig(ICacheService, use_value=cache_service),
            ],
        )
