import re
from pathlib import Path

from ellar.common import (
    Controller,
    ControllerBase,
    TemplateResponse,
    get,
    render,
    render_template,
    render_template_string,
)
from ellar.testing import Test

BASEDIR = Path(__file__).resolve().parent.parent


@Controller
class EllarController(ControllerBase):
    @get("/index-2", response={200: TemplateResponse})
    def index_render_template(self):
        """Looks for index.html in all template folder"""
        return render_template(
            "index", self.context.switch_to_http_connection().get_request()
        )

    @get("/index")
    @render()
    def index(self):
        """Looks for `ellar/index.html` in template folder because no template name was provided so use_mvc=True"""
        return {}

    @get("/another_index")
    def another_index(self, first_name: str, last_name: str):
        """Since a template name is provided, it will looks for template name"""
        return render_template_string(
            request=self.context.switch_to_http_connection().get_request(),
            template_string="""Hi {{ first_name }} {{ last_name }}!.\nWelcome to Ellar Framework""",
            first_name=first_name,
            last_name=last_name,
        )

    @get("/render-as-string")
    def render_template_as_string(self):
        """Render template as string with template name"""
        return render_template_string(
            request=self.context.switch_to_http_connection().get_request(),
            template_string="index.html",
        )


@Controller(prefix="/template-static")
class TemplateWithStaticsController(ControllerBase):
    @get("/index", response={200: TemplateResponse})
    @render("watever.html")
    def index(self):
        """Looks for watever.html in all template folder"""
        return {}


tm = Test.create_test_module(
    controllers=(EllarController,), base_directory=BASEDIR, template_folder="templates"
)


def test_render_template_string():
    client = tm.get_test_client()
    response = client.get("/ellar/another_index?first_name=Eadwin&last_name=Eadwin")
    assert response.status_code == 200
    content = re.sub("\\s+", " ", response.text).strip()
    assert content == '"Hi Eadwin Eadwin!.\\nWelcome to Ellar Framework"'


def test_render_template():
    client = tm.get_test_client()
    response = client.get("/ellar/index-2")
    assert response.status_code == 200
    content = re.sub("\\s+", " ", response.text).strip()
    assert (
        content == '<!DOCTYPE html> <html lang="en"> '
        '<head> <meta charset="UTF-8"> <title>Index Page</title> </head> <body> </body> </html>'
    )


def test_render_template_as_string_from_template_name():
    client = tm.get_test_client()

    response = client.get("/ellar/render-as-string")
    assert response.status_code == 200

    content = re.sub("\\s+", " ", response.text).strip()
    assert (
        "<title>Index Page</title>\\n</head>\\n<body>\\n\\n</body>\\n</html>" in content
    )


def test_ellar_controller_index():
    client = tm.get_test_client()
    response = client.get("/ellar/index")
    assert response.status_code == 200
    content = re.sub("\\s+", " ", response.text).strip()
    assert (
        content
        == '<html lang="en"> <head> <meta charset="UTF-8"> <title>Ellar Index Page</title> </head> '
        '<a href="http://testserver/ellar/another_index">world</a> </html>'
    )


def test_render_template_with_static_ref():
    test_module = Test.create_test_module(
        controllers=(TemplateWithStaticsController,),
        template_folder="templates",
        base_directory=Path(__file__).resolve().parent,
    )
    client = test_module.get_test_client()
    response = client.get("/template-static/index")
    assert response.status_code == 200
    content = re.sub("\\s+", " ", response.text).strip()
    assert (
        content
        == '<!DOCTYPE html> <head> <title>Welcome - Ellar ASGI Python Framework</title> <link rel="stylesheet" href="http://testserver/static/watever.txt"/> </head>'
    )
