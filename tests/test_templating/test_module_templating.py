import os

import pytest

from ellar.common import Module, template_filter, template_global
from ellar.core import TestClientFactory
from ellar.core.modules import ModuleBase, ModuleDecorator


@Module(template_folder="views")
class SomeModule(ModuleBase):
    @template_global("dec_global")
    def double_global_dec(cls, n):
        return n * 2

    @template_filter()
    def double_filter_dec_2(cls, n):
        return n * 2

    @template_global()
    def double_global_dec_2(cls, n):
        return n * 2


@Module(
    static_folder="module_statics",
)
class SomeModule2:
    @template_filter()
    def double_filter(cls, n):
        return n * 2

    @template_global()
    def double_global(cls, n):
        return n * 2

    @template_filter("dec_filter")
    def double_filter_dec(cls, n):
        return n * 2


tm = TestClientFactory.create_test_module_from_module(module=SomeModule)


def test_template_globals_and_template_filters_computation():
    app = tm.app
    environment = app.jinja_environment
    app.install_module(SomeModule2)

    for item in ["double_filter", "dec_filter", "double_filter_dec_2"]:
        assert item in environment.filters

    for item in ["double_global", "dec_global", "double_global_dec_2"]:
        assert item in environment.globals


@ModuleDecorator()
class ModuleTemplatingDefaults:
    pass


@pytest.mark.parametrize(
    "module, static_folder, template_folder",
    [
        (SomeModule, "static", "views"),
        (ModuleTemplatingDefaults, "static", "templates"),
        (SomeModule2, "module_statics", "templates"),
    ],
)
def test_module_templating_works(module, static_folder, template_folder):
    assert module.template_folder == template_folder

    assert module.jinja_loader.searchpath[0] == os.path.join(
        module.root_path, template_folder
    )
    assert os.path.exists(module.jinja_loader.searchpath[0])
    assert os.path.exists(module.static_directory)
    assert module.static_directory == os.path.join(module.root_path, static_folder)
    assert static_folder in module.static_directory
