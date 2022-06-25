import re
from pathlib import Path

from ellar.common import Controller, get
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
        return render_template("index", request=self.context.switch_to_request())

    @get("/another_index2")
    def another_index2(self, first_name: str, last_name: str):
        """Since a template name is provided, it will looks for template name"""
        return render_template_string(
            "render_string",
            request=self.context.switch_to_request(),
            first_name=first_name,
            last_name=last_name,
        )


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
