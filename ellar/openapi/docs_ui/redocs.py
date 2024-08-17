from .base import IDocumentationUI


class ReDocUI(IDocumentationUI):
    @property
    def name(self) -> str:
        return "redoc"

    @property
    def template_name(self) -> str:
        return "redocs.html"

    @property
    def path(self) -> str:
        return self._path

    @property
    def template_context(self) -> dict:
        return self._template_context

    def __init__(
        self,
        path: str = "redoc",
        title: str = "Ellar Redoc",
        redoc_js_url: str = "https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
        favicon_url: str = "https://eadwincode.github.io/ellar/img/Icon.svg",
        with_google_fonts: bool = True,
    ):
        self._path = path
        self._template_context = {
            "title": title,
            "redoc_js_url": redoc_js_url,
            "favicon_url": favicon_url,
            "with_google_fonts": with_google_fonts,
        }
