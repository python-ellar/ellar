import ellar
from ellar.common import Controller, ControllerBase, UseGuards, get, render
from ellar.reflect import fail_silently

from .guard import HomeGuard


@Controller(prefix="", include_in_schema=False)
@UseGuards(HomeGuard)
class HomeController(ControllerBase):
    @get("/")
    @render()
    def index(self):
        github_url = "https://github.com/python-ellar/ellar"
        doc_url = "https://python-ellar.github.io/ellar/"

        openapi_schema = (
            (
                name,
                fail_silently(
                    self.context.switch_to_http_connection().get_request().url_for,
                    f"openapi:{name}",
                ),
            )
            for name in ["swagger", "redoc", "stoplight"]
        )
        return {
            "message": "",
            "docs_url": doc_url,
            "git_hub": github_url,
            "version": ellar.__version__,
            "release_url": f"{github_url}/releases/{ellar.__version__}",
            "example_project_url": f"{github_url}/tree/main/samples",
            "openapi_schema": openapi_schema,
        }
