import re
from pathlib import Path

import pytest
from jinja2 import TemplateNotFound

from ellar.common import Controller, Get, Render
from ellar.core import TestClientFactory
from ellar.core.response.model import EmptyAPIResponseModel, HTMLResponseModel
from ellar.core.response.model.html import HTMLResponseModelRuntimeError

BASEDIR = Path(__file__).resolve().parent.parent


@Controller
class EllarController:
    @Get(
        "/index",
        response={200: HTMLResponseModel(template_name="index.html", use_mvc=True)},
    )
    def index2(self):
        """Looks for ellar/index since use_mvc=True"""
        return {"index": True, "use_mvc": True}

    @Get("/index2")
    @Render()
    def index(self):
        """detest its mvc and Looks for ellar/index"""
        return {"index": True, "use_mvc": True}

    @Get(
        "/another_index",
        response={200: HTMLResponseModel(template_name="ellar/index", use_mvc=False)},
    )
    def another_index(self):
        """Looks for ellar/index, since use_mvc=False"""
        return {"index": True, "use_mvc": False}

    @Get("/another_index2")
    @Render(template_name="ellar/index.html")
    def another_index2(self):
        """Since a template name is provided, it will looks for template name"""
        return {"index": True, "use_mvc": False}


test_module = TestClientFactory.create_test_module(
    template_folder="templates", base_directory=BASEDIR, controllers=(EllarController,)
)


@test_module.app.Get(
    "/render_template", response=HTMLResponseModel(template_name="index", use_mvc=False)
)
def render_template():
    return {}


@test_module.app.Get("/render_template2")
@Render(template_name="index")
def render_template():
    return {}


@pytest.mark.parametrize(
    "path, template",
    [
        ("/ellar/index", "ellar/index.html"),
        ("/ellar/index2", "ellar/index.html"),
        ("/ellar/another_index", "ellar/index.html"),
        ("/ellar/another_index2", "ellar/index.html"),
    ],
)
def test_ellar_index_should_use_controller_name_with_function_name(path, template):
    client = test_module.get_client()
    response = client.get(path)
    response.raise_for_status()
    content = re.sub("\\s+", " ", response.text).strip()
    assert (
        content == '<html lang="en"> <head> <meta charset="UTF-8"> '
        '<title>Ellar Index Page</title> </head> <a href="http://testserver/ellar/another_index">world</a> '
        "</html>"
    )
    assert response.template.name == template
    assert set(response.context.keys()) == {"index", "request", "use_mvc"}


@pytest.mark.parametrize(
    "path, template",
    [
        ("/render_template", "index.html"),
        ("/render_template2", "index.html"),
    ],
)
def test_function_template_rendering(path, template):
    client = test_module.get_client()
    response = client.get(path)
    response.raise_for_status()
    content = re.sub("\\s+", " ", response.text).strip()
    assert (
        content == '<!DOCTYPE html> <html lang="en"> '
        '<head> <meta charset="UTF-8"> <title>Index Page</title> </head> <body> </body> </html>'
    )
    assert response.template.name == template


def test_render_exception_works():
    with pytest.raises(
        Exception, match="template_name is required for function endpoints"
    ):

        @test_module.app.Get("/render_template3")
        @Render()
        def render_template3():
            pass

    @Render()
    @test_module.app.Get("/render_template4")
    def render_template4():
        pass

    assert isinstance(
        render_template4.response_model.models[200], EmptyAPIResponseModel
    )


def test_runtime_exception_works():
    @test_module.app.Get(
        "/runtime_error_1", response=HTMLResponseModel(template_name="index2")
    )
    def runtime_error_1():
        pass

    @test_module.app.Get("/runtime_error_2")
    @Render(template_name="index2")
    def runtime_error_2():
        pass

    @test_module.app.Get(
        "/runtime_controller_error_1",
        response=HTMLResponseModel(template_name="index2", use_mvc=True),
    )
    def runtime_controller_error_1():
        pass

    assert isinstance(runtime_error_1.response_model.models[200], HTMLResponseModel)
    assert isinstance(runtime_error_2.response_model.models[200], HTMLResponseModel)
    client = test_module.get_client()

    with pytest.raises(TemplateNotFound):
        client.get("/runtime_error_1")

    with pytest.raises(TemplateNotFound):
        client.get("/runtime_error_2")

    with pytest.raises(HTMLResponseModelRuntimeError):
        client.get("/runtime_controller_error_1")
