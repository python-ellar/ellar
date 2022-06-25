import typing as t

from ellar.reflect import reflect


class Reflector:
    __slots__ = ()

    def get(self, metadata_key: str, target: t.Union[t.Type, t.Callable]) -> t.Any:
        return reflect.get_metadata(metadata_key, target)

    def get_all(
        self, metadata_key: str, *targets: t.Union[t.Type, t.Callable]
    ) -> t.List[t.Any]:
        pass

    def get_all_and_merge(
        self, metadata_key: str, *targets: t.Union[t.Type, t.Callable]
    ) -> t.List[t.Any]:
        pass

    def get_all_and_override(
        self, metadata_key: str, *targets: t.Union[t.Type, t.Callable]
    ) -> t.List[t.Any]:
        pass
