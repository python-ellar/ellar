from .base import IDocumentationUIContext


class SwaggerUI(IDocumentationUIContext):
    @property
    def template_name(self) -> str:
        return "swagger.html"

    @property
    def title(self) -> str:
        return self._title

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
        swagger_js_url: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui-bundle.js",
        swagger_css_url: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui.css",
        favicon_url: str = "https://eadwincode.github.io/ellar/img/Icon.svg",
    ):
        self._path = path
        self._title = title
        self._template_context = {
            "swagger_js_url": swagger_js_url,
            "swagger_css_url": swagger_css_url,
            "favicon_url": favicon_url,
        }
