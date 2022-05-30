import typing as t

from starlette.routing import BaseRoute

from ellar.core.events import EventHandler


class ModuleData(t.NamedTuple):
    startup_event: t.List[EventHandler]
    shutdown_event: t.List[EventHandler]
    flattened_routes: t.List[BaseRoute]

    @classmethod
    def default(cls) -> "ModuleData":
        return ModuleData(
            startup_event=[],
            shutdown_event=[],
            flattened_routes=[],
        )

    def extend(self, other: "ModuleData") -> "ModuleData":
        return ModuleData(
            shutdown_event=self.shutdown_event + other.shutdown_event,
            startup_event=self.startup_event + other.startup_event,
            flattened_routes=self.flattened_routes + other.flattened_routes,
        )
