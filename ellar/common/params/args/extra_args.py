import inspect
import typing as t

from ellar.common.types import T


class ExtraEndpointArg(t.Generic[T]):
    """
    Add more route function parameters programmatically.
    For example,
    let's add `limit` and `offset` to a route function.

    def limit(func):
        limit_args = ExtraEndpointArg(name='limit', annotation=int, default_value=10)

        Offset_args = ExtraEndpointArg(name='offset', annotation=int, default_value=0)

        extra_args = [limit_args, offset_args]

        Set_metadata(EXTRA_ROUTE_ARGS_KEY, extra_args)(func)

        @wraps(func)
        def _wrapper(*args, **kwargs):
            # RESOLVING EXTRA ARGS

            Resolved_limit_args = limit_args.resolve(kwargs)

            resolved_offset_args = offset_args.resolve(kwargs)

            response = func(*args, **kwargs)

            response = response[resolved_offset_args: resolved_limit_args]

            Return response

        Return _wrapper

    Router = ModuleRouter('/testing')

    @router.get('/list')
    @limit
    def route(request: Request):

        return [i=1 for i in range(40)]
    """

    __slots__ = ("name", "annotation", "default")

    empty = inspect.Parameter.empty

    def __init__(
        self, *, name: str, annotation: t.Type[T], default_value: t.Any = None
    ):
        self.name = name
        self.annotation = annotation
        self.default = default_value or self.empty

    def resolve(self, kwargs: t.Dict) -> T:
        if self.name in kwargs:
            return t.cast(T, kwargs.pop(self.name))
        raise AttributeError(
            f"{self.name} ExtraOperationArg not found"
        )  # pragma: no cover
