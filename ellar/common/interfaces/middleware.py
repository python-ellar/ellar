import typing as t

from ellar.pydantic import as_pydantic_validator


@as_pydantic_validator("__validate_input__", schema={"type": "object"})
class IEllarMiddleware:
    @classmethod
    def __validate_input__(cls, v: t.Any, _: t.Any) -> t.Any:
        if not isinstance(v, cls):
            raise ValueError(f"Expected EllarMiddleware object, received: {type(v)}")
        return v  # pragma: no cover
