from .base import EventHandler, EventManager

app_context_started = EventManager()
app_context_teardown = EventManager()

request_started = EventManager()
request_teardown = EventManager()

__all__ = [
    "app_context_started",
    "app_context_teardown",
    "request_started",
    "request_teardown",
    "EventHandler",
    "EventManager",
]
