from .base import EventHandler, EventManager

request_context_started_events = EventManager()
request_context_teardown_events = EventManager()

app_context_started_events = EventManager()
app_context_teardown_events = EventManager()

__all__ = [
    "request_context_started_events",
    "request_context_teardown_events",
    "app_context_started_events",
    "app_context_teardown_events",
    "EventHandler",
    "EventManager",
]
