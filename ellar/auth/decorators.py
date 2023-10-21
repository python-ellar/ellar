import typing as t

from ellar.common import set_metadata as set_meta
from ellar.common.constants import ROUTE_INTERCEPTORS

from .constants import POLICY_KEYS
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

    return set_meta(ROUTE_INTERCEPTORS, [AuthorizationInterceptor])
