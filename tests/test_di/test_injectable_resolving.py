import pytest
from ellar.di import (
    EllarInjector,
    injectable,
    request_or_transient_scope,
    singleton_scope,
    transient_scope,
)


@injectable(scope=transient_scope)
class SampleInjectableA:
    pass


@injectable(scope=request_or_transient_scope)
class SampleInjectableB:
    pass


@injectable(scope=singleton_scope)
class SampleInjectableC:
    pass


class MustBeRegisteredToResolve:
    """This class must be registered to resolved or EllarInjector auto_bind must be true"""

    pass


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
