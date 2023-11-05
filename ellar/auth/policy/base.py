import typing as t
from abc import ABC, ABCMeta, abstractmethod

from ellar.common import IExecutionContext
from ellar.common.compatible import AttributeDict


class DefaultRequirementType(AttributeDict):
    """
    Stores Policy Requirement Arguments in `arg_[n]` value
    example:
        class MyPolicyHandler(BasePolicyHandlerWithRequirement):
            ...

        policy = MyPolicyHandler['req1', 'req2', 'req2']
        policy.requirement.arg_1 = 'req1'
        policy.requirement.arg_2 = 'req2'
        policy.requirement.arg_3 = 'req2'
    """

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
    def __or__(
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


class BasePolicyHandler(ABC, _PolicyOperandMixin, metaclass=BasePolicyHandlerMetaclass):
    @abstractmethod
    async def handle(self, context: IExecutionContext) -> bool:
        """Run Policy Actions and return true or false"""


class BasePolicyHandlerWithRequirement(
    BasePolicyHandler,
    ABC,
):
    __requirements__: t.Dict[int, "BasePolicyHandler"] = {}

    requirement_type: t.Type = DefaultRequirementType

    @abstractmethod
    @t.no_type_check
    async def handle(self, context: IExecutionContext, requirement: t.Any) -> bool:
        """Handle Policy Action"""

    def __class_getitem__(cls, parameters: t.Any) -> "BasePolicyHandler":
        _parameters = parameters if isinstance(parameters, tuple) else (parameters,)
        hash_id = hash(_parameters)
        if hash_id not in cls.__requirements__:
            cls.__requirements__[hash_id] = _PolicyHandlerWithRequirement(
                cls, cls.requirement_type(*_parameters)
            )
        return cls.__requirements__[hash_id]


PolicyType = t.Union[
    BasePolicyHandler,
    t.Type[BasePolicyHandler],
    BasePolicyHandlerWithRequirement,
    t.Type[BasePolicyHandlerWithRequirement],
]


class _OperandResolversMixin:
    def _get_policy_object(
        self, context: IExecutionContext, policy: PolicyType
    ) -> t.Union[BasePolicyHandler, BasePolicyHandlerWithRequirement]:
        if isinstance(policy, type):
            # resolve instance from EllarInjector, we assume the policy hand been decorated with @injector decorator.
            return context.get_service_provider().get(policy)  # type: ignore[no-any-return]
        return policy


class _ORPolicy(BasePolicyHandler, _OperandResolversMixin):
    def __init__(self, policy_1: PolicyType, policy_2: PolicyType) -> None:
        self._policy_1 = policy_1
        self._policy_2 = policy_2

    async def handle(self, context: IExecutionContext) -> bool:
        _policy_1 = self._get_policy_object(context, self._policy_1)
        _policy_2 = self._get_policy_object(context, self._policy_2)

        _policy_1_result = await _policy_1.handle(context)
        _policy_2_result = await _policy_2.handle(context)

        return _policy_1_result or _policy_2_result


class _NOTPolicy(BasePolicyHandler, _OperandResolversMixin):
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


class _PolicyHandlerWithRequirement(BasePolicyHandler, _OperandResolversMixin):
    def __init__(self, policy_1: PolicyType, requirement: t.Any) -> None:
        self._policy_1 = policy_1
        self.requirement = requirement

    @t.no_type_check
    def __call__(
        self, *args: t.Any, **kwargs: t.Any
    ) -> "_PolicyHandlerWithRequirement":
        self._policy_1 = self._policy_1(*args, **kwargs)
        return self

    async def handle(self, context: IExecutionContext) -> bool:
        _policy_1 = self._get_policy_object(context, self._policy_1)
        return await _policy_1.handle(context, requirement=self.requirement)  # type: ignore[call-arg]
