from unittest.mock import Mock

import pytest
from ellar.auth import BasePolicyHandler, BasePolicyHandlerWithRequirement
from ellar.common import IExecutionContext
from ellar.di import EllarInjector

injector = EllarInjector()
mock_context = Mock()
mock_context.get_service_provider = lambda: injector


class MyRequirement:
    def __init__(self, a: str, b: str):
        self.a = a
        self.b = b


class EllarPolicy(BasePolicyHandlerWithRequirement):
    requirement_type = MyRequirement

    async def handle(
        self, context: IExecutionContext, requirement: MyRequirement
    ) -> bool:
        return requirement.a == "ellar" and requirement.b == "policy"


class AnyPolicy(BasePolicyHandlerWithRequirement):
    async def handle(self, context: IExecutionContext, requirement=None) -> bool:
        if requirement:
            return requirement.arg_1 == requirement.arg_2
        return requirement is None


class TruePolicyHandler(BasePolicyHandler):
    async def handle(self, context: IExecutionContext) -> bool:
        return True


class FalsePolicyHandler(BasePolicyHandler):
    async def handle(self, context: IExecutionContext) -> bool:
        return False


@pytest.mark.asyncio
class TestPolicyHandlerLogics:
    async def test_and_false(self):
        composed_policy = TruePolicyHandler & FalsePolicyHandler
        assert await composed_policy.handle(mock_context) is False

    async def test_and_true(self):
        composed_policy = TruePolicyHandler & TruePolicyHandler
        assert await composed_policy.handle(mock_context) is True

    async def test_or_false(self):
        composed_policy = FalsePolicyHandler | FalsePolicyHandler
        assert await composed_policy.handle(mock_context) is False

    async def test_or_true(self):
        composed_policy = FalsePolicyHandler | TruePolicyHandler
        assert await composed_policy.handle(mock_context) is True

    async def test_not_false(self):
        composed_policy = ~FalsePolicyHandler
        assert await composed_policy.handle(mock_context) is True
        composed_policy = ~TruePolicyHandler
        assert await composed_policy.handle(mock_context) is False

    async def test_several_levels_without_negation(self):
        composed_policy = (
            TruePolicyHandler
            & TruePolicyHandler
            & TruePolicyHandler
            & TruePolicyHandler
        )
        assert await composed_policy.handle(mock_context) is True

    async def test_several_levels_and_precedence_with_negation(self):
        composed_policy = (
            TruePolicyHandler
            & ~FalsePolicyHandler
            & TruePolicyHandler
            & ~(TruePolicyHandler & FalsePolicyHandler)
        )
        assert await composed_policy.handle(mock_context) is True

    async def test_several_levels_and_precedence(self):
        composed_policy = (
            TruePolicyHandler & TruePolicyHandler
            | TruePolicyHandler & TruePolicyHandler
        )
        assert await composed_policy.handle(mock_context) is True


@pytest.mark.asyncio
class TestPolicyHandlerWithRequirement:
    async def test_and_false(self):
        composed_policy = EllarPolicy["ellar", "policy"] & FalsePolicyHandler
        assert await composed_policy.handle(mock_context) is False

    async def test_and_true(self):
        composed_policy = AnyPolicy & TruePolicyHandler
        assert await composed_policy.handle(mock_context) is True

    async def test_or_false(self):
        composed_policy = EllarPolicy["ellar", "whatever"] | EllarPolicy["ellar", "and"]
        assert await composed_policy.handle(mock_context) is False

    async def test_or_true(self):
        composed_policy = FalsePolicyHandler | EllarPolicy["ellar", "policy"]
        assert await composed_policy.handle(mock_context) is True

    async def test_not_false(self):
        composed_policy = ~EllarPolicy["ellar", "whatever"]
        assert await composed_policy.handle(mock_context) is True
        composed_policy = ~AnyPolicy
        assert await composed_policy.handle(mock_context) is False

    async def test_several_levels_and_precedence_with_negation(self):
        composed_policy = (
            EllarPolicy["ellar", "policy"]
            & ~AnyPolicy["ellar", "false"]
            & EllarPolicy["ellar", "policy"]
            & ~(EllarPolicy["ellar", "policy"] & AnyPolicy["ellar", "false"])
        )
        assert await composed_policy.handle(mock_context) is True

    async def test_several_levels_and_precedence(self):
        composed_policy = (
            EllarPolicy["ellar", "policy"] & EllarPolicy["ellar", "false"]
            | EllarPolicy["ellar", "policy"] & AnyPolicy
        )
        assert await composed_policy.handle(mock_context) is True

    def test_same_requirement_returns_same_policy_object(self):
        assert EllarPolicy["a", "b"] == EllarPolicy["a", "b"]
        assert EllarPolicy["c", "d"] != EllarPolicy["e", "f"]

        assert EllarPolicy["c", "d"] == EllarPolicy["c", "d"]
        assert (
            EllarPolicy[EllarPolicy, AnyPolicy] == EllarPolicy[EllarPolicy, AnyPolicy]
        )
