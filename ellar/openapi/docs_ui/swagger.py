from .base import IDocumentationUI


class SwaggerUI(IDocumentationUI):
    @property
    def name(self) -> str:
        return "swagger"

    @property
    def template_name(self) -> str:
        return "swagger.html"

    @property
    def path(self) -> str:
        return self._path

    @property
    def template_context(self) -> dict:
        return self._template_context

    def __init__(
        self,
        path: str = "docs",
        title: str = "Ellar Swagger Doc",
        swagger_js_url: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
        favicon_url: str = "https://eadwincode.github.io/ellar/img/Icon.svg",
        dark_theme: bool = False,
    ):
        self._path = path
        self._template_context = {
            "title": title,
            "swagger_js_url": swagger_js_url,
            "swagger_css_url": swagger_css_url,
            "favicon_url": favicon_url,
            "dark_theme": dark_theme,
        }
