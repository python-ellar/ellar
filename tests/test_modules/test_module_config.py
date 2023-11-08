from abc import ABC
from unittest.mock import patch

import pytest
from ellar.app import App
from ellar.common import (
    Controller,
    ControllerBase,
    IModuleSetup,
    Module,
    ModuleRouter,
    get,
)
from ellar.common.constants import MODULE_METADATA
from ellar.core import Config, DynamicModule, ModuleBase, ModuleSetup
from ellar.core.services import Reflector
from ellar.di import EllarInjector, ProviderConfig
from ellar.reflect import reflect
from ellar.testing import Test

from ..main import router


class IDynamic(ABC):
    a: int
    b: float


class SampleController(ControllerBase):
    @get("/sample")
    def sample_example(self):
        return {"message": 'You have reached "sample_example" home route'}


@Module(routers=(router,))
class DynamicInstantiatedModule(ModuleBase, IModuleSetup):
    @classmethod
    def setup(cls, a: int, b: int) -> DynamicModule:
        dynamic_type = type("DynamicSample", (IDynamic,), {"a": a, "b": b})
        dynamic_router = ModuleRouter("/dynamic")

        @dynamic_router.get("/index")
        async def home():
            return {"message": 'You have reached "dynamic" home route'}

        dynamic_controller = Controller("/dynamic-controller")(SampleController)

        return DynamicModule(
            cls,
            providers=[ProviderConfig(IDynamic, use_class=dynamic_type)],
            routers=[
                dynamic_router,
            ],
            controllers=[dynamic_controller],
        )


@Module()
class DynamicModuleSetupRegisterModule(ModuleBase, IModuleSetup):
    @classmethod
    def setup(cls, a: int, b: int) -> DynamicModule:
        dynamic_type = type("DynamicSample", (IDynamic,), {"a": a, "b": b})
        return DynamicModule(
            cls,
            providers=[ProviderConfig(IDynamic, use_class=dynamic_type)],
        )

    @classmethod
    def setup_register(cls) -> ModuleSetup:
        return ModuleSetup(cls, inject=[Config], factory=cls.setup_register_factory)

    @staticmethod
    def setup_register_factory(
        module: "DynamicModuleSetupRegisterModule", config: Config
    ) -> DynamicModule:
        return module.setup(config.a, config.b)


def test_dynamic_module_haves_routes():
    routers = reflect.get_metadata(MODULE_METADATA.ROUTERS, DynamicInstantiatedModule)
    assert len(routers) == 1
    assert len(routers[0].routes) == 39
    tm = Test.create_test_module(
        modules=(DynamicInstantiatedModule.setup(a=233, b=344),)
    )
    tm.create_application()
    routers = reflect.get_metadata(MODULE_METADATA.ROUTERS, DynamicInstantiatedModule)
    assert len(routers) == 1
    assert len(routers[0].routes) == 1


def test_dynamic_module_setup_providers_works():
    test_module = Test.create_test_module(
        modules=(DynamicInstantiatedModule.setup(a=233, b=344),)
    )
    dynamic_object = test_module.get(IDynamic)
    assert dynamic_object.a == 233 and dynamic_object.b == 344


def test_dynamic_module_setup_router_controllers_works():
    test_module = Test.create_test_module(
        modules=(DynamicInstantiatedModule.setup(a=233, b=344),)
    )
    assert len(test_module.create_application().routes) == 2
    client = test_module.get_test_client()

    res = client.get("/dynamic/index")
    assert res.status_code == 200
    assert res.json() == {"message": 'You have reached "dynamic" home route'}

    res = client.get("/dynamic-controller/sample")
    assert res.status_code == 200
    assert res.json() == {"message": 'You have reached "sample_example" home route'}


def test_dynamic_module_setup_register_works():
    with reflect.context():
        test_module = Test.create_test_module(
            modules=(DynamicModuleSetupRegisterModule.setup_register(),),
            config_module={"a": 24555, "b": 8899900},
        )
        assert len(test_module.create_application().routes) == 0
        dynamic_instance = test_module.get(IDynamic)
        assert dynamic_instance.a == 24555
        assert dynamic_instance.b == 8899900


@pytest.mark.parametrize(
    "name, dependencies",
    [
        ("depends on nothing but has factory", []),
        ("depends only on config", [Config]),
        ("depends on other services", [Config, Reflector]),
        (
            "depends on other services and Application instance",
            [Config, Reflector, App],
        ),
    ],
)
def test_module_setup_with_factory_works(name, dependencies):
    def dynamic_instantiate_factory(module: DynamicInstantiatedModule, *args):
        for _type, instance in zip(dependencies, args):
            assert isinstance(instance, _type)
        return module.setup(a=233, b=344)

    test_module = Test.create_test_module(
        modules=[
            ModuleSetup(
                DynamicInstantiatedModule,
                factory=dynamic_instantiate_factory,
                inject=dependencies,
            )
        ]
    )

    dynamic_object = test_module.get(IDynamic)
    assert dynamic_object.a == 233 and dynamic_object.b == 344
    client = test_module.get_test_client()

    res = client.get("/dynamic/index")
    assert res.status_code == 200
    assert res.json() == {"message": 'You have reached "dynamic" home route'}


def test_invalid_module_setup():
    config = Config()
    injector = EllarInjector()

    def dynamic_instantiate_factory(module: DynamicInstantiatedModule, *args):
        return ModuleSetup(DynamicInstantiatedModule)

    with pytest.raises(Exception) as ex:
        ModuleSetup(module=IDynamic)
    assert str(ex.value) == "IDynamic is not a valid Module"

    module_setup = ModuleSetup(
        DynamicInstantiatedModule, factory=dynamic_instantiate_factory
    )

    with pytest.raises(Exception) as ex:
        module_setup.get_module_ref(config, injector.container)
    assert (
        str(ex.value)
        == "Factory function for DynamicInstantiatedModule module configuration must return `DynamicModule` instance"
    )


def test_invalid_dynamic_module_setup():
    with pytest.raises(Exception) as ex:
        DynamicModule(module=IDynamic)
    assert str(ex.value) == "IDynamic is not a valid Module"


def test_can_not_apply_dynamic_module_twice():
    dynamic_type = type("DynamicSample", (IDynamic,), {"a": "1222", "b": "121212"})
    with patch.object(reflect.__class__, "define_metadata") as mock_define_metadata:
        dynamic_module = DynamicModule(
            module=DynamicInstantiatedModule,
            providers=[ProviderConfig(IDynamic, use_class=dynamic_type)],
        )
        dynamic_module.apply_configuration()
        assert mock_define_metadata.called

    with patch.object(reflect.__class__, "define_metadata") as mock_define_metadata:
        dynamic_module.apply_configuration()
        assert mock_define_metadata.called is False
