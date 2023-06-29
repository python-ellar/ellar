import typing as t

from ellar.common import UseGuards, set_metadata as set_meta

from .constants import POLICY_KEYS
from .guard import AuthorizationGuard
from .policy import Policy

_PolicyType = t.Union[Policy, t.Type[Policy]]


def Authorization(*policies: t.Union[str, _PolicyType]) -> t.Callable:
    """
    =========CONTROLLER AND ROUTE FUNCTION DECORATOR ==============

    :param policies:
    :return:
    """

    def _decorator(target: t.Callable) -> t.Union[t.Callable, t.Any]:
        set_meta(POLICY_KEYS, list(policies))(target)
        return UseGuards(AuthorizationGuard)(target)

    return _decorator
