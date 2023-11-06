import typing as t

from ellar.common import constants
from ellar.common import set_metadata as set_meta

from .constants import POLICY_KEYS
from .guards import AuthenticatedRequiredGuard
from .interceptor import AuthorizationInterceptor
from .policy import PolicyType


def CheckPolicies(*policies: t.Union[str, PolicyType]) -> t.Callable:
    """
    ========= CONTROLLER AND ROUTE FUNCTION DECORATOR ==============
    Decorates a controller or a route function with specific policy requirements
    :param policies:
    :return:
    """

    def _decorator(target: t.Callable) -> t.Union[t.Callable, t.Any]:
        set_meta(POLICY_KEYS, list(policies))(target)
        return target

    return _decorator


def Authorize() -> t.Callable:
    """
    ========= CONTROLLER AND ROUTE FUNCTION DECORATOR ==============
    Decorates a controller class or route function with  `AuthorizationInterceptor`
    :return:
    """

    return set_meta(constants.ROUTE_INTERCEPTORS, [AuthorizationInterceptor])


def AuthenticationRequired(
    authentication_scheme: t.Optional[str] = None,
    openapi_scope: t.Optional[t.List] = None,
) -> t.Callable:
    """
    ========= CONTROLLER AND ROUTE FUNCTION DECORATOR ==============

    Decorates a controller class or route function with  `IsAuthenticatedGuard`

    @param authentication_scheme: authentication_scheme - Based on the authentication scheme class name or openapi_name used.
    @param openapi_scope: OpenAPi scope
    @return: Callable
    """
    if callable(authentication_scheme):
        return set_meta(constants.GUARDS_KEY, [AuthenticatedRequiredGuard(None, [])])(
            authentication_scheme
        )

    return set_meta(
        constants.GUARDS_KEY,
        [AuthenticatedRequiredGuard(authentication_scheme, openapi_scope or [])],
    )


def SkipAuth() -> t.Callable:
    """
    ========= CONTROLLER AND ROUTE FUNCTION DECORATOR ==============
    Decorates a Class or Route Function with SKIP_AUTH attribute that is checked by `AuthenticationRequiredGuard`
    @return: Callable
    """

    return set_meta(
        constants.SKIP_AUTH,
        True,
    )
