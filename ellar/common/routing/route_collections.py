import typing as t
import uuid
from collections import OrderedDict

from ellar.common.logger import logger
from ellar.common.utils import generate_controller_operation_unique_id
from starlette.routing import BaseRoute, Host, Mount


class RouteCollection(t.Sequence[BaseRoute]):
    __slots__ = ("_routes", "_served_routes")

    def __init__(self, routes: t.Optional[t.Sequence[BaseRoute]] = None) -> None:
        self._routes: t.Dict[int, BaseRoute] = OrderedDict()
        self._served_routes: t.List[BaseRoute] = []
        self.extend([] if routes is None else list(routes))

    @t.no_type_check
    def __getitem__(self, i: int) -> BaseRoute:
        return self._served_routes.__getitem__(i)

    def __setitem__(self, i: int, o: BaseRoute) -> None:
        self._add_operation(o)
        self.sort_routes()

    def __len__(self) -> int:
        return len(self._routes)

    def __iter__(self) -> t.Iterator[BaseRoute]:
        return iter(self._served_routes)

    def append(self, __item: t.Any) -> None:
        self._add_operation(__item)
        self.sort_routes()

    def get_routes(self) -> t.List[BaseRoute]:
        return self._served_routes.copy()

    def extend(self, routes: t.Sequence[BaseRoute]) -> "RouteCollection":
        for item in routes:
            self._add_operation(item)
        self.sort_routes()
        return self

    def sort_routes(self) -> None:
        # TODO: flatten the routes for faster look up
        self._served_routes = list(self._routes.values())
        self._served_routes.sort(
            key=lambda e: e.host if isinstance(e, Host) else e.path  # type: ignore
        )

    def _add_operation(self, operation: t.Union[BaseRoute]) -> None:
        if not isinstance(operation, BaseRoute):
            logger.warning("Tried Adding an operation that is not supported.")
            return

        _methods = getattr(operation, "methods", {"WS"})
        _versioning = list(
            operation.get_allowed_version()
            if hasattr(operation, "get_allowed_version")
            else {}
        )
        path = operation.host if isinstance(operation, Host) else operation.path  # type: ignore

        if isinstance(operation, (Mount, Host)):
            _methods = {
                operation.name or operation.__class__.__name__,
                operation.__class__.__name__,
            }

        _hash = generate_controller_operation_unique_id(
            path=path,
            methods=list(_methods),
            versioning=_versioning or ["no_versioning"],
        )
        if _hash in self._routes:
            _hash = generate_controller_operation_unique_id(
                path=path,
                methods=list(_methods),
                versioning=_versioning or ["no_versioning"],
                extra_string=f"{uuid.uuid4().hex:5}",
            )

            # TODO: log warning to user when operations with the same route is found
        self._routes[_hash] = operation
