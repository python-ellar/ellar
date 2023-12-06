import typing as t

from ellar.cache import BaseCacheBackend
from ellar.pydantic import BaseModel, as_pydantic_validator, field_validator


@as_pydantic_validator("__validate_input__", schema={"type": "object"})
class TBaseCacheBackend:
    @classmethod
    def __validate_input__(
        cls: t.Type["TBaseCacheBackend"], __input: t.Any, _: t.Any
    ) -> t.Any:
        if isinstance(__input, BaseCacheBackend):
            return __input

        raise ValueError(f"Expected BaseCacheBackend, received: {type(__input)}")


class CacheModuleSchemaSetup(BaseModel):
    CACHES: t.Dict[str, TBaseCacheBackend] = {}

    @field_validator("CACHES", mode="before")
    def pre_cache_validate(cls, value: t.Dict) -> t.Any:
        if value and not value.get("default"):
            raise ValueError("CACHES configuration must have a 'default' key")
        return value
