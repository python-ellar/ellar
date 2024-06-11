import typing as t

from ellar.common import IExecutionContext

from .base import Policy


class RolePolicy(Policy):
    def __init__(self, *role: str):
        self.roles = list(role)

    async def handle(self, context: IExecutionContext) -> bool:
        user_roles = context.user.get("roles", [])
        return all(role in user_roles for role in self.roles)


class ClaimsPolicy(Policy):
    def __init__(self, claim_type: str, *claim_value: t.Any) -> None:
        self.claim_type = claim_type
        self.claim_values = list(claim_value)

    async def handle(self, context: IExecutionContext) -> bool:
        _claim_value = context.user.get(self.claim_type)

        if _claim_value is None:
            return False

        if not isinstance(_claim_value, list):
            _claim_value = [_claim_value]

        return any(claim in _claim_value for claim in self.claim_values)
