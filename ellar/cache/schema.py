import typing as t

from ellar.cache import BaseCacheBackend
from pydantic import BaseModel, validator


class TBaseCacheBackend:
    @classmethod
    def __get_validators__(
        cls: t.Type["TBaseCacheBackend"],
    ) -> t.Iterable[t.Callable[..., t.Any]]:
        yield cls.validate

    @classmethod
    def validate(cls: t.Type["TBaseCacheBackend"], v: t.Any) -> t.Any:
        if isinstance(v, BaseCacheBackend):
            return v

        raise ValueError(f"Expected BaseCacheBackend, received: {type(v)}")


class CacheModuleSchemaSetup(BaseModel):
    CACHES: t.Dict[str, TBaseCacheBackend] = {}

    @validator("CACHES", pre=True)
    def pre_cache_validate(cls, value: t.Dict) -> t.Any:
        if value and not value.get("default"):
            raise ValueError("CACHES configuration must have a 'default' key")
        return value
