from ellar.core import AppFactory
from ellar.core.templating import Environment


def double_filter(n):
    return n * 2


def double_global(n):
    return n * 2


def test_app_creates_environment_template_globals_and_template_filters():
    app = AppFactory.create_app()
    assert isinstance(app.jinja_environment, Environment)
    assert app.jinja_environment.auto_reload == app.debug
    app.debug = True
    assert app.jinja_environment.auto_reload == app.debug

    app.config.TEMPLATES_AUTO_RELOAD = True
    app.debug = False
    assert app.jinja_environment.auto_reload is True

    app.add_template_filter(double_filter)
    app.add_template_global(double_global)

    app.add_template_filter(double_filter, "double_filter_2")
    app.add_template_global(double_global, "double_global_2")

    @app.template_filter("dec_filter")
    def double_filter_dec(n):
        return n * 2

    @app.template_global("dec_global")
    def double_global_dec(n):
        return n * 2

    @app.template_filter()
    def double_filter_dec_2(n):
        return n * 2

    @app.template_global()
    def double_global_dec_2(n):
        return n * 2

    environment = app.jinja_environment
    for item in [
        "double_filter",
        "double_filter_2",
        "dec_filter",
        "double_filter_dec_2",
    ]:
        assert item in environment.filters

    for item in [
        "double_global",
        "double_global_2",
        "dec_global",
        "double_global_dec_2",
    ]:
        assert item in environment.globals
