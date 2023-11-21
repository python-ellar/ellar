import pytest
from ellar.app import App, current_app, current_config, current_injector
from ellar.app.context import ApplicationContext
from ellar.core import Config
from ellar.testing import Test


def test_getting_injector_outside_running_fails():
    with pytest.raises(RuntimeError):
        assert current_injector.parent


def test_getting_current_app_outside_running_context_fails():
    with pytest.raises(RuntimeError):
        assert current_app.config


def test_current_config_fails_when_there_is_no_ellar_config_module():
    with pytest.raises(RuntimeError):
        assert current_config.DEBUG is False


def test_current_injector_works():
    tm = Test.create_test_module()

    with ApplicationContext.create(tm.create_application()):
        assert current_injector.get(App) is not None

    with pytest.raises(RuntimeError):
        assert current_injector.parent


def test_current_app_works():
    tm = Test.create_test_module()

    with ApplicationContext.create(tm.create_application()):
        assert isinstance(current_app.config, Config)

    with pytest.raises(RuntimeError):
        assert current_app.config


def test_current_config_works():
    tm = Test.create_test_module(config_module={"FRAMEWORK_NAME": "Ellar"})

    with ApplicationContext.create(tm.create_application()):
        assert current_app.config.FRAMEWORK_NAME == current_config.FRAMEWORK_NAME

    with pytest.raises(RuntimeError):
        assert current_app.config.FRAMEWORK_NAME
