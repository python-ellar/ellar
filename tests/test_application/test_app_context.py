import logging

import pytest
from ellar.app import App, config, current_injector
from ellar.app.context import ApplicationContext
from ellar.common import Body, post
from ellar.core import Config
from ellar.testing import Test


def test_getting_injector_outside_running_fails():
    with pytest.raises(RuntimeError):
        assert current_injector.parent


def test_getting_current_app_outside_running_context_fails():
    with pytest.raises(RuntimeError):
        assert current_injector.get(App)


async def test_current_config_fails_when_there_is_no_ellar_config_module(
    caplog, anyio_backend
):
    with caplog.at_level(logging.WARNING):
        tm = Test.create_test_module()

        async with ApplicationContext.create(tm.create_application()):
            assert current_injector.get(App) is not None
            assert config.DEBUG is False

        assert caplog.text == ""

    with caplog.at_level(logging.WARNING):
        assert config.DEBUG is False
        print(caplog.text)
        assert (
            "You are trying to access app config outside app "
            "context and ELLAR_CONFIG_MODULE is not specified. This may cause differences "
            "in config values with the app"
        ) in caplog.text


async def test_current_injector_works(anyio_backend):
    tm = Test.create_test_module()

    async with ApplicationContext.create(tm.create_application()):
        assert current_injector.get(App) is not None

    with pytest.raises(RuntimeError):
        assert current_injector.parent


async def test_current_app_works(anyio_backend):
    tm = Test.create_test_module()

    async with ApplicationContext.create(tm.create_application()):
        assert isinstance(current_injector.get(Config), Config)

    with pytest.raises(RuntimeError):
        assert current_injector.get(Config)


async def test_current_config_works(anyio_backend):
    tm = Test.create_test_module(config_module={"FRAMEWORK_NAME": "Ellar"})

    async with tm.create_application().application_context():
        app = current_injector.get(App)
        assert app.config.FRAMEWORK_NAME == config.FRAMEWORK_NAME

    with pytest.raises(RuntimeError):
        current_injector.get(App)


async def test_current_config_works_(anyio_backend):
    tm = Test.create_test_module(config_module={"FRAMEWORK_NAME": "Ellar"})

    @post
    def add(a: Body[int], b: Body[int]):
        from ellar.app import current_injector

        config_ = current_injector.get(Config)
        assert config_.FRAMEWORK_NAME == config.FRAMEWORK_NAME
        return a + b

    app = tm.create_application()
    app.router.append(add)

    async with app.application_context():
        res = tm.get_test_client().post("/", json={"a": 1, "b": 4})
        assert res.json() == 5
        config_ = current_injector.get(Config)
        assert config_.FRAMEWORK_NAME == config.FRAMEWORK_NAME

    with pytest.raises(RuntimeError):
        current_injector.get(Config)
