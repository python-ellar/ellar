from ellar.common import Controller, get, render
from ellar.core import ControllerBase


@Controller(prefix="", include_in_schema=False)
class HomeController(ControllerBase):
    @get("/")
    @render()
    def index(self):
        return {
            "message": "",
            "docs_url": "https://eadwincode.github.io/ellar/",
            "git_hub": "https://github.com/eadwincode/ellar",
        }
