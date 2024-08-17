import pytest
from ellar.common import Module
from ellar.common.constants import MODULE_METADATA, MODULE_WATERMARK
from ellar.common.exceptions import ImproperConfiguration
from ellar.di import has_binding, is_decorated_with_injectable
from ellar.reflect import reflect


@Module(
    name="test",
    static_folder="test",
    controllers=["controllers"],
    routers=["routers"],
    providers=["providers"],
    modules=["modules"],
)
class ModuleDecoratorTest:
    pass


def test_module_decorator_keys_is_complete():
    assert reflect.get_metadata(MODULE_METADATA.ROUTERS, ModuleDecoratorTest) == [
        "routers"
    ]
    assert reflect.get_metadata(MODULE_METADATA.NAME, ModuleDecoratorTest) == "test"
    assert (
        reflect.get_metadata(MODULE_METADATA.STATIC_FOLDER, ModuleDecoratorTest)
        == "test"
    )
    assert reflect.get_metadata(MODULE_METADATA.PROVIDERS, ModuleDecoratorTest) == [
        "providers"
    ]
    assert reflect.get_metadata(MODULE_METADATA.CONTROLLERS, ModuleDecoratorTest) == [
        "controllers"
    ]
    assert reflect.get_metadata(MODULE_METADATA.MODULES, ModuleDecoratorTest) == [
        "modules"
    ]


def test_decorated_class_has_module_watermark():
    assert reflect.get_metadata(MODULE_WATERMARK, ModuleDecoratorTest)


def test_base_directory_is_dynamically_set_when_none():
    base_path = reflect.get_metadata(
        MODULE_METADATA.BASE_DIRECTORY, ModuleDecoratorTest
    )
    assert "/test_decorators" in str(base_path)


def test_cannot_decorate_module_class_twice():
    with pytest.raises(
        ImproperConfiguration, match="is already identified as a Module"
    ):
        Module()(ModuleDecoratorTest)


def test_cannot_decorate_class_instance_as_a_module():
    with pytest.raises(ImproperConfiguration, match="is a class decorator -"):
        Module()(ModuleDecoratorTest())


def test_decorated_class_default_scope_is_singleton():
    assert is_decorated_with_injectable(ModuleDecoratorTest)
    assert not has_binding(ModuleDecoratorTest)  # __init__ is not overridden


def test_module_decorator_does_not_override_module_metadata_if_existing():
    class ExistingModule:
        pass

    reflect.define_metadata(
        MODULE_METADATA.BASE_DIRECTORY, "/path/to/my/base/templates", ExistingModule
    )
    reflect.define_metadata(
        MODULE_METADATA.TEMPLATE_FOLDER, "custom_template", ExistingModule
    )
    reflect.define_metadata(
        MODULE_METADATA.STATIC_FOLDER, "static_custom", ExistingModule
    )

    Module(name="ExistingModule", controllers=["Controller1", "Controller2"])(
        ExistingModule
    )

    data = reflect.get_all_metadata(ExistingModule)
    assert data == {
        "base_directory": "/path/to/my/base/templates",
        "template_folder": "templates",
        "static_folder": "static",
        "MODULE_WATERMARK": True,
        "name": "ExistingModule",
        "controllers": ["Controller1", "Controller2"],
        "routers": [],
        "providers": [],
        "modules": [],
        "commands": [],
        "exports": [],
        "INJECTABLE_WATERMARK": True,
    }


def test_module_decorator_override_module_metadata_if_provided_in_decorator():
    class ExistingModule2:
        pass

    reflect.define_metadata(
        MODULE_METADATA.BASE_DIRECTORY, "/path/to/my/base/templates", ExistingModule2
    )
    reflect.define_metadata(
        MODULE_METADATA.TEMPLATE_FOLDER, "custom_template", ExistingModule2
    )
    reflect.define_metadata(
        MODULE_METADATA.TEMPLATE_FOLDER, "custom_template", ExistingModule2
    )
    reflect.define_metadata(
        MODULE_METADATA.STATIC_FOLDER, "ExistingModule2", ExistingModule2
    )

    Module(
        name="ExistingModule",
        controllers=["Controller1", "Controller2"],
        base_directory="/path/to/another/base",
    )(ExistingModule2)

    data = reflect.get_all_metadata(ExistingModule2)
    assert data == {
        "base_directory": "/path/to/another/base",
        "template_folder": "templates",
        "static_folder": "static",
        "MODULE_WATERMARK": True,
        "name": "ExistingModule",
        "controllers": ["Controller1", "Controller2"],
        "routers": [],
        "providers": [],
        "modules": [],
        "commands": [],
        "exports": [],
        "INJECTABLE_WATERMARK": True,
    }
