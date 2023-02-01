import functools
import typing as t

from ellar.reflect import reflect


class Reflector:
    __slots__ = ()

    def get(self, metadata_key: str, target: t.Union[t.Type, t.Callable]) -> t.Any:
        return reflect.get_metadata(metadata_key, target)

    def get_all(
        self, metadata_key: str, *targets: t.Union[t.Type, t.Callable]
    ) -> t.List[t.Any]:
        results = []
        for target in targets:
            value = self.get(metadata_key, target)
            results.append(value)
        return results

    def get_all_and_merge(
        self, metadata_key: str, *targets: t.Union[t.Type, t.Callable]
    ) -> t.Any:
        metadata_collection = [
            item for item in self.get_all(metadata_key, *targets) if item
        ]

        if len(metadata_collection) == 0:
            return None

        if len(metadata_collection) == 1:
            return metadata_collection[0]

        def inline_function(previous_item: t.Any, next_item: t.Any) -> t.Any:
            if isinstance(previous_item, list):
                return previous_item.append(next_item)

            if isinstance(previous_item, dict) and isinstance(next_item, dict):
                return previous_item.update(next_item)

            if isinstance(previous_item, (tuple, set)):
                return list(previous_item) + [next_item]

            return [previous_item, next_item]

        results = functools.reduce(inline_function, metadata_collection)
        return results

    def get_all_and_override(
        self, metadata_key: str, *targets: t.Union[t.Type, t.Callable]
    ) -> t.Optional[t.Any]:
        for target in targets:
            value = self.get(metadata_key, target)
            if value is not None:
                return value
        return None
