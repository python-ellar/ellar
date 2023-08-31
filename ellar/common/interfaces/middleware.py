import typing as t


class IEllarMiddleware:
    @classmethod
    def __get_validators__(
        cls: t.Type["IEllarMiddleware"],
    ) -> t.Iterable[t.Callable[..., t.Any]]:
        # for Pydantic Model Validation
        yield cls.__validate

    @classmethod
    def __validate(cls, v: t.Any) -> t.Any:
        if not isinstance(v, cls):
            raise ValueError(f"Expected EllarMiddleware object, received: {type(v)}")
        return v  # pragma: no cover
