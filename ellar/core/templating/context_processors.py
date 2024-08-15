import typing as t

from ellar.core.connection import Request


def request_context(request: Request) -> t.Dict[str, t.Any]:
    return {"request": request}


def user(request: Request) -> t.Dict[str, t.Any]:
    """
    Return context variables for current request user. This could be AnonymousIdentity or a real user Identity
    """

    return {
        "user": request.user,
    }


def request_state(request: Request) -> t.Dict[str, t.Any]:
    """Adds request state variable to template context"""

    return {
        "request_state": request.state,
    }
