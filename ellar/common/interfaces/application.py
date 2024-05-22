import typing as t
from abc import abstractmethod

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.app import App


class IApplicationStartup:
    """
    Module Interface called during application LifeSpan starts up
    """

    @abstractmethod
    async def on_startup(self, app: "App") -> None:
        """Application Startup Actions"""


class IApplicationShutdown:
    """
    Module Interface called during application LifeSpan shutdown
    """

    @abstractmethod
    async def on_shutdown(self) -> None:
        """Application Shutdown Actions"""


class IApplicationReady:
    """
    Module Interface called when all modules have been registered just before lifespan execution starts
    """

    @abstractmethod
    def on_ready(self, app: "App") -> None:
        """Application Shutdown Actions"""
