from ellar.app import AppFactory
from ellar.common import (
    Module,
    template_filter,
    template_global,
)
from ellar.common.templating import Environment
from ellar.core import ModuleBase, injector_context
from ellar.core.modules import ModuleTemplateRef
from ellar.threading.sync_worker import execute_async_context_manager


@Module(template_folder="some_template", name="app_template")
class AppTemplateModuleTest(ModuleBase):
    @template_filter(name="app_filter")
    def template_filter_test(self, value):
        return f"new filter {value}"

    @template_global(name="app_global")
    def template_global_test(self, value):
        return f"new global {value}"


app = AppFactory.create_from_app_module(module=AppTemplateModuleTest)


class TestAppTemplating:
    def test_app_get_module_loaders(self):
        loaders = list(app.get_module_loaders())
        assert len(loaders) == 2
        module_ref = loaders[1]
        assert isinstance(module_ref, ModuleTemplateRef)
        assert isinstance(module_ref.get_module_instance(), AppTemplateModuleTest)

    def test_app_jinja_environment(self):
        with execute_async_context_manager(injector_context(app.injector)):
            environment = app.injector.get(Environment)
            assert isinstance(environment, Environment)

            assert "app_filter" in environment.filters
            assert "app_global" in environment.globals
            template = environment.from_string(
                """<html>global: {{app_global(2)}} filter: {{3 | app_filter}}</html>"""
            )
            result = template.render()
            assert result == "<html>global: new global 2 filter: new filter 3</html>"

    # def test_app_template_filter(self):
    #     app = Test.create_test_module().create_application()
    #
    #     @app.template_filter()
    #     def square(value):
    #         return value * value
    #
    #     @app.template_filter(name="triple")
    #     def triple_function(value):
    #         return value * value * value
    #
    #     template = app.jinja_environment.from_string(
    #         """<html>filter square: {{2 | square}}, filter triple_function: {{3 | triple}}</html>"""
    #     )
    #     result = template.render()
    #     assert result == "<html>filter square: 4, filter triple_function: 27</html>"
    #
    # def test_app_template_global(self):
    #     app = Test.create_test_module().create_application()
    #
    #     @app.template_global()
    #     def square(value):
    #         return value * value
    #
    #     @app.template_global(name="triple")
    #     def triple_function(value):
    #         return value * value * value
    #
    #     template = app.jinja_environment.from_string(
    #         """<html>filter square: {{square(2)}}, filter triple_function: {{triple(3)}}</html>"""
    #     )
    #     result = template.render()
    #     assert result == "<html>filter square: 4, filter triple_function: 27</html>"
