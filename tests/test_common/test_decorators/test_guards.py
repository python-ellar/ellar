from ellar.common import guards
from ellar.constants import GUARDS_KEY
from ellar.core import ExecutionContext
from ellar.core.guard import GuardCanActivate
from ellar.reflect import reflect


class SomeGuard(GuardCanActivate):
    async def can_activate(self, context: ExecutionContext) -> bool:
        return True


class SomeGuard2(SomeGuard):
    async def can_activate(self, context: ExecutionContext) -> bool:
        return False


@guards(SomeGuard)
def endpoint(request):
    return "foo"


@guards(SomeGuard, SomeGuard2)
def endpoint2(request):
    return "foo"


def test_guard_decorator_applies_guards_key_to_reflect():
    guard_info = reflect.get_metadata(GUARDS_KEY, endpoint)
    assert guard_info
    assert len(guard_info) == 1
    assert guard_info == [
        SomeGuard,
    ]

    guard_info = reflect.get_metadata(GUARDS_KEY, endpoint2)
    assert guard_info
    assert len(guard_info) == 2
    assert guard_info == [SomeGuard, SomeGuard2]
