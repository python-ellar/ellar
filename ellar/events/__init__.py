from .base import EventHandler, EventManager

app_context_started_events = EventManager()
app_context_teardown_events = EventManager()

__all__ = [
    "app_context_started_events",
    "app_context_teardown_events",
    "EventHandler",
    "EventManager",
]
