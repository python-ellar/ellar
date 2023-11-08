from ellar.app import AppFactory
from ellar.core import Config

ELLAR_DEBUG = True
ELLAR_SECRET_KEY = "your-secret-key-changed"
ELLAR_INJECTOR_AUTO_BIND = True
ELLAR_JINJA_TEMPLATES_OPTIONS = {"auto_reload": True}


def test_config_with_prefix():
    config = Config(
        config_prefix="ellar_", config_module="tests.test_conf:test_config_prefix"
    )

    assert config.DEBUG
    assert config.SECRET_KEY == "your-secret-key-changed"
    assert config.INJECTOR_AUTO_BIND
    assert config.JINJA_TEMPLATES_OPTIONS["auto_reload"]


def test_for_app_factory():
    app = AppFactory.create_app(
        config_module={
            "config_prefix": "ellar_",
            "config_module": "tests.test_conf:test_config_prefix",
        }
    )

    assert app.config.DEBUG
    assert app.config.SECRET_KEY == "your-secret-key-changed"
    assert app.config.INJECTOR_AUTO_BIND
    assert app.config.JINJA_TEMPLATES_OPTIONS["auto_reload"]
