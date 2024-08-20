import pytest
from ellar.common import Module
from ellar.common.exceptions import ImproperConfiguration
from ellar.core import ForwardRefModule, ModuleBase
from ellar.di import ProviderConfig
from ellar.di import exceptions as di_exceptions
from ellar.testing import Test
from ellar.utils.importer import get_class_import

from .sample import AnotherUserService, SampleController, UserService


@Module(
    providers=(
        ProviderConfig(UserService, export=True),
        ProviderConfig(AnotherUserService, use_value=AnotherUserService()),
    ),
    name="ModuleToBeReference",
)
class ModuleToBeReference(ModuleBase):
    pass


@Module(controllers=[SampleController])
class ModuleWithoutModuleRef:
    """
    Demos why SampleController won't work unless UserService is configured or registered for it
    UserService, on the other hand, has been registered on ModuleToBeReference and its also exported
    """


@Module(
    controllers=[SampleController],
    modules=[ForwardRefModule(module_name="ModuleToBeReference")],
)
class ModuleWithModuleRefByName:
    """
    Demos how to ref an already registered module by Module name
    """


@Module(
    controllers=[SampleController],
    modules=[ForwardRefModule(module=get_class_import(ModuleToBeReference))],
)
class ModuleWithModuleRefByStringImport:
    """
    Demos how to ref an already registered module by import string
    """


@Module(
    controllers=[SampleController],
    modules=[ForwardRefModule(module=ModuleToBeReference)],
)
class ModuleWithModuleRefByType:
    """
    Demos how to ref an already registered module by import string
    """


def test_sample_controller_fails_for_module_without_module_ref_as_dependency():
    tm = Test.create_test_module(modules=[ModuleToBeReference, ModuleWithoutModuleRef])
    app = tm.create_application()
    tm_module_ref = app.injector.tree_manager.get_module(tm.module).value

    assert ModuleToBeReference in tm_module_ref.modules

    with pytest.raises(
        di_exceptions.UnsatisfiedRequirement,
        match="SampleController has an unsatisfied requirement on UserService",
    ):
        module_ref = app.injector.tree_manager.get_module(ModuleWithoutModuleRef).value
        assert module_ref.get(SampleController)


@pytest.mark.parametrize(
    "module_type",
    [
        ModuleWithModuleRefByName,
        ModuleWithModuleRefByStringImport,
        ModuleWithModuleRefByType,
    ],
)
def test_sample_controller_works_for_module_ref_by_name(module_type, reflect_context):
    app = Test.create_test_module(
        modules=[ModuleToBeReference, module_type]
    ).create_application()
    module_ref = app.injector.tree_manager.get_module(module_type).value

    controller = module_ref.get(SampleController)
    assert controller._user_service.user.full_name == "full_name"


name_error_message = (
    "ForwardRefModule module_name='ModuleToBeReference' defined in "
    "<class 'tests.test_modules.test_forward_ref.ModuleWithModuleRefByName'> "
    "could not be found.\nPlease kindly ensure a @Module(name=ModuleToBeReference) is registered"
)
string_error_message = (
    "ForwardRefModule module='tests.test_modules.test_forward_ref:ModuleToBeReference' "
    "defined in <class 'tests.test_modules.test_forward_ref.ModuleWithModuleRefByStringImport'> "
    "could not be found.\n"
    "Please kindly ensure a tests.test_modules.test_forward_ref:ModuleToBeReference is "
    "decorated with @Module() is registered"
)
type_error_message = (
    "ForwardRefModule module='<class 'tests.test_modules.test_forward_ref.ModuleToBeReference'>' "
    "defined in <class 'tests.test_modules.test_forward_ref.ModuleWithModuleRefByType'> "
    "could not be found.\n"
    "Please kindly ensure a <class 'tests.test_modules.test_forward_ref.ModuleToBeReference'> "
    "is decorated with @Module() is registered"
)


@pytest.mark.parametrize(
    "module_type, error_message",
    [
        (ModuleWithModuleRefByName, name_error_message),
        (ModuleWithModuleRefByStringImport, string_error_message),
        (ModuleWithModuleRefByType, type_error_message),
    ],
)
def test_forward_ref_module_fails_in_absence_of_module_referenced(
    module_type, error_message, reflect_context
):
    with pytest.raises(ImproperConfiguration) as ex:
        Test.create_test_module(modules=[module_type]).create_application()

    assert str(ex.value) == error_message


import_error_message = (
    "Unable to import "
    "'tests.test_modules.test_forward_ref:ModuleToBeReference3' registered in "
    "'<class 'tests.test_modules.test_forward_ref.test_forward_ref_invalid_string_import.<locals>.InvalidStringImport'>'"
)


def test_forward_ref_invalid_string_import():
    @Module(
        controllers=[SampleController],
        modules=[
            ForwardRefModule(
                module="tests.test_modules.test_forward_ref:ModuleToBeReference3"
            )
        ],
    )
    class InvalidStringImport:
        pass

    with pytest.raises(ImproperConfiguration) as ex:
        Test.create_test_module(
            modules=[ModuleToBeReference, InvalidStringImport]
        ).create_application()

    assert str(ex.value) == import_error_message
