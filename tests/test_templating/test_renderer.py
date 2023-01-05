import re
from pathlib import Path

from ellar.common import Controller, get, render
from ellar.core import ControllerBase, TestClientFactory
from ellar.core.templating import (
    TemplateResponse,
    render_template,
    render_template_string,
)

BASEDIR = Path(__file__).resolve().parent.parent


@Controller
class EllarController(ControllerBase):
    @get("/index", response={200: TemplateResponse})
    def index_render_template(self):
        """Looks for ellar/index since use_mvc=True"""
        return render_template(
            "index", request=self.context.switch_to_http_connection().get_request()
        )

    @get("/another_index2")
    def another_index2(self, first_name: str, last_name: str):
        """Since a template name is provided, it will looks for template name"""
        return render_template_string(
            "render_string",
            request=self.context.switch_to_http_connection().get_request(),
            first_name=first_name,
            last_name=last_name,
        )


@Controller(prefix="/template-static")
class TemplateWithStaticsController(ControllerBase):
    @get("/index", response={200: TemplateResponse})
    @render("watever.html")
    def index(self):
        """Looks for ellar/index since use_mvc=True"""
        return {}


tm = TestClientFactory.create_test_module(
    controllers=(EllarController,), base_directory=BASEDIR, template_folder="templates"
)


def test_render_template_string():
    client = tm.get_client()
    response = client.get("/ellar/another_index2?first_name=Eadwin&last_name=Eadwin")
    assert response.status_code == 200
    content = re.sub("\\s+", " ", response.text).strip()
    assert content == '"Hi Eadwin Eadwin!.\\nWelcome to Ellar Framework"'


def test_render_template():
    client = tm.get_client()
    response = client.get("/ellar/index")
    assert response.status_code == 200
    content = re.sub("\\s+", " ", response.text).strip()
    assert (
        content == '<!DOCTYPE html> <html lang="en"> '
        '<head> <meta charset="UTF-8"> <title>Index Page</title> </head> <body> </body> </html>'
    )


def test_render_template_with_static_ref():
    test_module = TestClientFactory.create_test_module(
        controllers=(TemplateWithStaticsController,),
        template_folder="templates",
        base_directory=Path(__file__).resolve().parent,
    )
    client = test_module.get_client()
    response = client.get("/template-static/index")
    assert response.status_code == 200
    content = re.sub("\\s+", " ", response.text).strip()
    assert (
        content
        == '<!DOCTYPE html> <head> <title>Welcome - Ellar ASGI Python Framework</title> <link rel="stylesheet" href="http://testserver/static/watever.txt"/> </head>'
    )
