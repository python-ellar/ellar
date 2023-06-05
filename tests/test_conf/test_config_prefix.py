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
