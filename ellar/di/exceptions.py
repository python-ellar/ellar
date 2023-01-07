from injector import (
    CallError,
    CircularDependency,
    Error,
    UnknownArgument,
    UnknownProvider,
    UnsatisfiedRequirement,
)


class DIImproperConfiguration(Exception):
    pass


class ServiceUnavailable(Exception):
    default_message = "Service Unavailable at the current context."

    def __init__(self, message: str = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


__all__ = [
    "CallError",
    "CircularDependency",
    "Error",
    "UnknownProvider",
    "UnknownArgument",
    "UnknownProvider",
    "UnsatisfiedRequirement",
    "DIImproperConfiguration",
    "ServiceUnavailable",
]
