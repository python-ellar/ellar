"""
Tag Registry for managing global tag-to-interface mappings
"""

import typing as t

from ellar.di.exceptions import UnsatisfiedRequirement


class TagRegistry:
    """
    Centralized registry for managing tag-to-interface mappings.

    This ensures that all tagged providers are registered globally and accessible
    across the entire injector hierarchy, rather than being scoped to individual containers.
    """

    def __init__(self) -> None:
        self._bindings_by_tag: t.Dict[str, t.Type[t.Any]] = {}

    def register(self, tag: str, interface: t.Type[t.Any]) -> None:
        """
        Register a tag-to-interface mapping.

        :param tag: The tag string
        :param interface: The interface/type associated with this tag
        """
        self._bindings_by_tag[tag] = interface

    def get_interface(self, tag: str) -> t.Type[t.Any]:
        """
        Get the interface associated with a tag.

        :param tag: The tag string to lookup
        :return: The interface/type associated with the tag
        :raises UnsatisfiedRequirement: If the tag is not registered
        """
        interface = self._bindings_by_tag.get(tag)
        if interface:
            return interface

        raise UnsatisfiedRequirement(None, t.cast(t.Any, tag))

    def has_tag(self, tag: str) -> bool:
        """
        Check if a tag is registered.

        :param tag: The tag string to check
        :return: True if the tag is registered, False otherwise
        """
        return tag in self._bindings_by_tag

    def clear(self) -> None:
        """Clear all tag registrations. Useful for testing."""
        self._bindings_by_tag.clear()

    def get_all_tags(self) -> t.Dict[str, t.Type[t.Any]]:
        """Get a copy of all tag-to-interface mappings."""
        return self._bindings_by_tag.copy()

    def __repr__(self) -> str:
        return f"TagRegistry(tags={list(self._bindings_by_tag.keys())})"
