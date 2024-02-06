from .base import EventHandler, EventManager

app_context_started = EventManager()
app_context_teardown = EventManager()

__all__ = [
    "app_context_started",
    "app_context_teardown",
    "EventHandler",
    "EventManager",
]
