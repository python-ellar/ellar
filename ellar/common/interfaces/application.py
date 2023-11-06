import typing as t
from abc import abstractmethod

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.app import App


class IApplicationStartup:
    @abstractmethod
    async def on_startup(self, app: "App") -> None:
        """Application Startup Actions"""


class IApplicationShutdown:
    @abstractmethod
    async def on_shutdown(self) -> None:
        """Application Shutdown Actions"""
