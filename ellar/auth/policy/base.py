import typing as t
from abc import ABC, ABCMeta, abstractmethod

from ellar.common import IExecutionContext
from ellar.common.compatible import AttributeDict


class DefaultRequirementType(AttributeDict):
    def __init__(self, *args: t.Any) -> None:
        kwargs_args = {f"arg_{idx+1}": value for idx, value in enumerate(args)}
        super().__init__(kwargs_args)


class _PolicyOperandMixin:
    @t.no_type_check
    def __and__(
        cls: t.Union["BasePolicyHandler", t.Type["BasePolicyHandler"]],
        other: t.Union["BasePolicyHandler", t.Type["BasePolicyHandler"]],
    ) -> "BasePolicyHandler":
        return _ANDPolicy(cls, other)

    @t.no_type_check
    def __rand__(
        cls: t.Union["BasePolicyHandler", t.Type["BasePolicyHandler"]],
        other: t.Union["BasePolicyHandler", t.Type["BasePolicyHandler"]],
    ) -> "BasePolicyHandler":
        return _ANDPolicy(cls, other)

    @t.no_type_check
    def __or__(
        cls: t.Union["BasePolicyHandler", t.Type["BasePolicyHandler"]],
        other: t.Union["BasePolicyHandler", t.Type["BasePolicyHandler"]],
    ) -> "BasePolicyHandler":
        return _ORPolicy(cls, other)

    @t.no_type_check
    def __ror__(
        cls: t.Union["BasePolicyHandler", t.Type["BasePolicyHandler"]],
        other: t.Union["BasePolicyHandler", t.Type["BasePolicyHandler"]],
    ) -> "BasePolicyHandler":
        return _ORPolicy(cls, other)

    @t.no_type_check
    def __invert__(
        cls: t.Union["BasePolicyHandler", t.Type["BasePolicyHandler"]]
    ) -> "BasePolicyHandler":
        return _NOTPolicy(cls)


class BasePolicyHandlerMetaclass(_PolicyOperandMixin, ABCMeta):
    pass


class BasePolicyHandler(ABC, metaclass=BasePolicyHandlerMetaclass):
    @abstractmethod
    async def handle(self, context: IExecutionContext) -> bool:
        """Run Policy Actions and return true or false"""


class BasePolicyHandlerWithRequirement(
    BasePolicyHandler,
    ABC,
):
    requirement_type: t.Type = DefaultRequirementType

    @abstractmethod
    @t.no_type_check
    async def handle(self, context: IExecutionContext, requirement: t.Any) -> bool:
        pass

    def __class_getitem__(
        cls, parameters: t.Union[str, t.Tuple[str]]
    ) -> "BasePolicyHandler":
        _parameters = parameters if isinstance(parameters, tuple) else (parameters,)
        return _PolicyHandlerWithRequirement(cls, cls.requirement_type(*_parameters))


PolicyType = t.Union[
    BasePolicyHandler,
    t.Type[BasePolicyHandler],
    BasePolicyHandlerWithRequirement,
    t.Type[BasePolicyHandlerWithRequirement],
]


class _OperandResolvers:
    def _get_policy_object(
        self, context: IExecutionContext, policy: PolicyType
    ) -> t.Union[BasePolicyHandler, BasePolicyHandlerWithRequirement]:
        if isinstance(policy, type):
            return context.get_service_provider().get(policy)  # type: ignore[no-any-return]
        return policy


class _ORPolicy(BasePolicyHandler, _OperandResolvers):
    def __init__(self, policy_1: PolicyType, policy_2: PolicyType) -> None:
        self._policy_1 = policy_1
        self._policy_2 = policy_2

    async def handle(self, context: IExecutionContext) -> bool:
        _policy_1 = self._get_policy_object(context, self._policy_1)
        _policy_2 = self._get_policy_object(context, self._policy_2)

        _policy_1_result = await _policy_1.handle(context)
        _policy_2_result = await _policy_2.handle(context)

        return _policy_1_result or _policy_2_result


class _NOTPolicy(BasePolicyHandler, _OperandResolvers):
    def __init__(self, policy_1: PolicyType) -> None:
        self._policy_1 = policy_1

    async def handle(self, context: IExecutionContext) -> bool:
        _policy_1 = self._get_policy_object(context, self._policy_1)

        _policy_1_result = await _policy_1.handle(context)

        return not _policy_1_result


class _ANDPolicy(_ORPolicy):
    async def handle(self, context: IExecutionContext) -> bool:
        _policy_1 = self._get_policy_object(context, self._policy_1)
        _policy_2 = self._get_policy_object(context, self._policy_2)

        _policy_1_result = await _policy_1.handle(context)
        _policy_2_result = await _policy_2.handle(context)

        return _policy_1_result and _policy_2_result


class _PolicyHandlerWithRequirement(
    BasePolicyHandler, _OperandResolvers, _PolicyOperandMixin
):
    def __init__(self, policy_1: PolicyType, requirement: t.Any) -> None:
        self._policy_1 = policy_1
        self.requirement = requirement

    async def handle(self, context: IExecutionContext) -> bool:
        _policy_1 = self._get_policy_object(context, self._policy_1)
        return await _policy_1.handle(context, requirement=self.requirement)  # type: ignore[call-arg]
