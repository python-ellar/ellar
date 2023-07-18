import ellar
from ellar.common import Controller, ControllerBase, UseGuards, get, render

from .guard import HomeGuard


@Controller(prefix="", include_in_schema=False)
@UseGuards(HomeGuard)
class HomeController(ControllerBase):
    @get("/")
    @render()
    def index(self):
        github_url = "https://github.com/eadwincode/ellar"
        doc_url = "https://eadwincode.github.io/ellar/"
        return {
            "message": "",
            "docs_url": doc_url,
            "git_hub": github_url,
            "version": ellar.__version__,
            "release_url": f"{github_url}/releases/{ellar.__version__}",
            "example_project_url": f"{github_url}/tree/main/examples",
        }
