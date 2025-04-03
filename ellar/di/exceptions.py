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


class RequestScopeContextNotFound(Exception):
    pass


__all__ = [
    "CallError",
    "CircularDependency",
    "Error",
    "UnknownProvider",
    "UnknownArgument",
    "UnknownProvider",
    "UnsatisfiedRequirement",
    "DIImproperConfiguration",
    "RequestScopeContextNotFound",
]
