from threading import RLock
from typing import Callable, Any, Optional

from starletteapi.helper import cached_property

try:
    import jinja2

    # @contextfunction renamed to @pass_context in Jinja 3.0, to be removed in 3.1
    if hasattr(jinja2, "pass_context"):
        pass_context = jinja2.pass_context
    else:  # pragma: nocover
        pass_context = jinja2.contextfunction
except ImportError:  # pragma: nocover
    jinja2 = None  # type: ignore


class locked_cached_property(cached_property):
    """A :func:`property` that is only evaluated once. Like
    :class:`werkzeug.utils.cached_property` except access uses a lock
    for thread safety.
    """

    def __init__(
        self,
        fget: Callable[[Any], Any],
        name: Optional[str] = None,
        doc: Optional[str] = None,
    ) -> None:
        super().__init__(fget, name=name, doc=doc)
        self.lock = RLock()

    def __get__(self, obj: object, type: type = None) -> Any:  # type: ignore
        if obj is None:
            return self

        with self.lock:
            return super().__get__(obj, type=type)

    def __set__(self, obj: object, value: Any) -> None:
        with self.lock:
            super().__set__(obj, value)

    def __delete__(self, obj: object) -> None:
        with self.lock:
            super().__delete__(obj)
