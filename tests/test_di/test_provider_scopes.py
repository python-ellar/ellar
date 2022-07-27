import pytest

from ellar.di import EllarInjector, ProviderConfig
from ellar.di.scopes import RequestScope, SingletonScope, TransientScope

from .examples import AnyContext, Foo, IContext


@pytest.mark.parametrize(
    "action, base_type, concrete_type, ref_type, expected_scope",
    [
        ("register_instance", Foo(), None, Foo, SingletonScope),
        ("register_instance", Foo(), Foo, Foo, SingletonScope),
        ("register_singleton", Foo, None, Foo, SingletonScope),
        ("register_singleton", Foo, Foo, Foo, SingletonScope),
        ("register_transient", Foo, None, Foo, TransientScope),
        ("register_transient", Foo, Foo, Foo, TransientScope),
        ("register_scoped", Foo, None, Foo, RequestScope),
        ("register_scoped", Foo, Foo, Foo, RequestScope),
        ("register_exact_singleton", Foo, None, Foo, SingletonScope),
        ("register_exact_transient", Foo, None, Foo, TransientScope),
        ("register_exact_scoped", Foo, None, Foo, RequestScope),
    ],
)
def test_container_scopes(action, base_type, concrete_type, ref_type, expected_scope):
    container = EllarInjector().container
    container_action = getattr(container, action)
    if concrete_type:
        container_action(base_type, concrete_type)
    else:
        container_action(base_type)
    binding = container.get_binding(ref_type)
    assert binding[0].scope is expected_scope


@pytest.mark.asyncio
async def test_request_scope_instance():
    injector = EllarInjector(auto_bind=False)
    ProviderConfig(IContext, use_class=AnyContext).register(injector.container)

    # resolving RequestScope Providers outside RequestServiceProvider will behaves like TransientScope
    assert injector.get(IContext) != injector.get(IContext)
    assert isinstance(injector.get(IContext), AnyContext)
    async with injector.create_request_service_provider() as request_provider:
        # TODO: sync request_provider.get to injector.get during request
        # resolving RequestScope during request will behave like singleton
        assert request_provider.get(IContext) == request_provider.get(IContext)
