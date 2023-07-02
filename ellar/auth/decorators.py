import typing as t

from ellar.common import set_metadata as set_meta

from .constants import POLICY_KEYS
from .policy import BasePolicyHandler

_PolicyType = t.Union[BasePolicyHandler, t.Type[BasePolicyHandler]]


def CheckPolicies(*policies: t.Union[str, _PolicyType]) -> t.Callable:
    """
    ========= CONTROLLER AND ROUTE FUNCTION DECORATOR ==============

    :param policies:
    :return:
    """

    def _decorator(target: t.Callable) -> t.Union[t.Callable, t.Any]:
        set_meta(POLICY_KEYS, list(policies))(target)
        return target

    return _decorator
