import os

import pytest
from ellar.common import Module, template_filter, template_global
from ellar.core import Config
from ellar.core.modules import ModuleBase, ModuleTemplateRef
from ellar.di import EllarInjector
from ellar.testing import Test


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
class SomeModule2(ModuleBase):
    @template_filter()
    def double_filter(cls, n):
        return n * 2

    @template_global()
    def double_global(cls, n):
        return n * 2

    @template_filter("dec_filter")
    def double_filter_dec(cls, n):
        return n * 2


tm = Test.create_test_module(modules=[SomeModule])
app = tm.create_application()


def test_template_globals_and_template_filters_computation():
    app.install_module(SomeModule2)
    environment = app.jinja_environment

    for item in ["double_filter", "dec_filter", "double_filter_dec_2"]:
        assert item in environment.filters

    for item in ["double_global", "dec_global", "double_global_dec_2"]:
        assert item in environment.globals


@Module()
class ModuleTemplatingDefaults:
    """default to template_folder='templates' and static_folder='static', which already exist at the parent directory"""


@Module(template_folder="invalid-path/templates", static_folder="invalid-path/static")
class NoneJinjaLoaderTemplating:
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
    config = Config()
    container = EllarInjector().container
    module_ref = ModuleTemplateRef(
        module_type=module, container=container, config=config
    )
    assert module_ref.template_folder == template_folder

    assert module_ref.jinja_loader.searchpath[0] == os.path.join(
        module_ref.root_path, template_folder
    )
    assert os.path.exists(module_ref.jinja_loader.searchpath[0])
    assert os.path.exists(module_ref.static_directory)
    assert module_ref.static_directory == os.path.join(
        module_ref.root_path, static_folder
    )
    assert static_folder in module_ref.static_directory


def test_none_jinja_loader_module():
    config = Config()
    container = EllarInjector().container
    module_ref = ModuleTemplateRef(
        module_type=NoneJinjaLoaderTemplating, container=container, config=config
    )
    assert module_ref.jinja_loader is None
    assert module_ref.static_directory is None
