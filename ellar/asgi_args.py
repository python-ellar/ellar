import typing as t

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.di.providers import Provider


class RequestScopeContext:
    __slots__ = ("_injector_scoped_context",)

    def __init__(self) -> None:
        self._injector_scoped_context: t.Dict[t.Type, "Provider"] = {}

    @property
    def context(self) -> t.Dict[t.Type, "Provider"]:
        return self._injector_scoped_context
