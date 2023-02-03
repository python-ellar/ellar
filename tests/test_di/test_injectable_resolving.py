import pytest

from ellar.di import (
    EllarInjector,
    injectable,
    request_scope,
    singleton_scope,
    transient_scope,
)
from ellar.di.exceptions import UnsatisfiedRequirement


@injectable(scope=transient_scope)
class SampleInjectableA:
    pass


@injectable(scope=request_scope)
class SampleInjectableB:
    pass


@injectable(scope=singleton_scope)
class SampleInjectableC:
    pass


class MustBeRegisteredToResolve:
    """This class must be registered to resolved or EllarInjector auto_bind must be true"""

    pass


def test_injectable_class_can_be_resolved_at_runtime_without_if_they_are_not_registered():
    injector = EllarInjector(auto_bind=False)

    assert isinstance(injector.get(SampleInjectableA), SampleInjectableA)
    assert isinstance(injector.get(SampleInjectableB), SampleInjectableB)
    assert isinstance(injector.get(SampleInjectableC), SampleInjectableC)

    with pytest.raises(UnsatisfiedRequirement):
        injector.get(MustBeRegisteredToResolve)

    injector.container.register_scoped(MustBeRegisteredToResolve)
    assert isinstance(
        injector.get(MustBeRegisteredToResolve), MustBeRegisteredToResolve
    )

    injector = EllarInjector(auto_bind=True)
    assert isinstance(
        injector.get(MustBeRegisteredToResolve), MustBeRegisteredToResolve
    )


@pytest.mark.asyncio
async def test_injectable_class_uses_defined_scope_during_runtime():
    injector = EllarInjector(auto_bind=True)
    # transient scope
    assert injector.get(SampleInjectableA) != injector.get(SampleInjectableA)
    # request scope outside request
    assert injector.get(SampleInjectableB) != injector.get(SampleInjectableB)
    # singleton scope
    assert injector.get(SampleInjectableC) == injector.get(SampleInjectableC)
    # transient scope by default
    assert injector.get(MustBeRegisteredToResolve) != injector.get(
        MustBeRegisteredToResolve
    )

    async with injector.create_asgi_args():
        # request scope outside request
        assert injector.get(SampleInjectableB) == injector.get(SampleInjectableB)
