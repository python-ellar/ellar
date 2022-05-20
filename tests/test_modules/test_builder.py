import pytest

from ellar.core.modules import ModuleDecoratorBuilder

from .sample import ModuleBaseExample, ModuleBaseExample2, SampleModule


def test_module_decorator_build_for_unknown_type():
    module_decorator_build = ModuleDecoratorBuilder(type("Unknown", (), {}))
    build_data = module_decorator_build.build()
    assert build_data == ModuleDecoratorBuilder.default()


@pytest.mark.parametrize(
    "module_instance_or_type, value, routes",
    [
        (ModuleBaseExample, 0, 0),
        (ModuleBaseExample(), 0, 0),
        (
            ModuleBaseExample2,
            1,
            4,
        ),  # presence of decorator, builds class special attributes
        (
            ModuleBaseExample2(),
            1,
            4,
        ),  # presence of decorator, builds class special attributes
        (SampleModule, 1, 4),
    ],
)
def test_module_decorator_build_for_module_base(module_instance_or_type, value, routes):
    module_decorator_build = ModuleDecoratorBuilder(module_instance_or_type)
    build_data = module_decorator_build.build()
    assert len(build_data.before_init) == value
    assert len(build_data.after_init) == value

    assert len(build_data.shutdown_event) == value
    assert len(build_data.startup_event) == value

    assert len(build_data.exception_handlers) == value

    assert len(build_data.middleware) == value
    assert len(build_data.routes) == routes
