import typing as t

from .interfaces import IAuthorizationRequirement
from .requirements import AuthorizationRequirementType, RequiredClaims, RequiredRole


@t.no_type_check
class _PolicyRequirements(t.Sequence):
    __slots__ = ("_requirements",)

    def __init__(self, *requirements: AuthorizationRequirementType) -> None:
        self._requirements: t.List[AuthorizationRequirementType] = []
        for requirement in requirements:
            self.add(requirement)

    def __len__(self) -> int:
        return self._requirements.__len__()

    @t.no_type_check
    def __getitem__(self, index: int) -> t.Any:
        return self._requirements.__getitem__(index)

    def add(self, requirement: AuthorizationRequirementType) -> None:
        if (
            not isinstance(requirement, type)
            and not isinstance(requirement, IAuthorizationRequirement)
        ) or (
            isinstance(requirement, type)
            and not issubclass(requirement, IAuthorizationRequirement)
        ):
            raise Exception("Only Requirement types or objects are required.")
        self._requirements.append(requirement)


class Policy:
    __slots__ = ("requirements",)

    def __init__(self, *requirements: AuthorizationRequirementType) -> None:
        self.requirements = _PolicyRequirements(*requirements)

    @classmethod
    def add_requirements(cls, *requirements: AuthorizationRequirementType) -> "Policy":
        return cls(*requirements)

    @classmethod
    def required_role(cls, *roles: str) -> "Policy":
        return cls(RequiredRole(*roles))

    @classmethod
    def required_claim(cls, claim_type: str, *claim_values: t.Any) -> "Policy":
        return cls(RequiredClaims(claim_type, *claim_values))
