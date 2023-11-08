import functools
import typing as t

from ellar.di import injectable
from ellar.reflect import reflect


@injectable()
class Reflector:
    __slots__ = ()

    def get(self, metadata_key: str, target: t.Union[t.Type, t.Callable]) -> t.Any:
        return reflect.get_metadata(metadata_key, target)

    def get_all(
        self, metadata_key: str, *targets: t.Union[t.Type, t.Callable, t.Any]
    ) -> t.List[t.Any]:
        results = []
        for target in targets:
            value = self.get(metadata_key, target)
            results.append(value)
        return results

    def get_all_and_merge(
        self, metadata_key: str, *targets: t.Union[t.Type, t.Callable, t.Any]
    ) -> t.Any:
        metadata_collection = [
            item for item in self.get_all(metadata_key, *targets) if item
        ]

        if len(metadata_collection) == 0:
            return []

        if len(metadata_collection) == 1:
            return [metadata_collection[0]]

        @t.no_type_check
        def inline_function(previous_item: t.Any, next_item: t.Any) -> t.Any:
            if isinstance(previous_item, (list, tuple, set)):
                previous_item.extend(
                    list(next_item)
                    if isinstance(next_item, (list, tuple, set))
                    else [next_item]
                )
                return previous_item

            if isinstance(previous_item, dict) and isinstance(next_item, dict):
                previous_item.update(next_item)
                return previous_item

            return [previous_item, next_item]

        return functools.reduce(inline_function, metadata_collection)

    def get_all_and_override(
        self, metadata_key: str, *targets: t.Union[t.Type, t.Callable, t.Any]
    ) -> t.Optional[t.Any]:
        for target in targets:
            value = self.get(metadata_key, target)
            if value is not None:
                return value
        return None


reflector = Reflector()
