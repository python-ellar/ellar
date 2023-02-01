import typing as t

from ellar.common import Module, ModuleRouter, render
from ellar.core.guard import GuardCanActivate
from ellar.core.main import App
from ellar.core.modules import ModuleBase
from ellar.openapi.openapi_v3 import OpenAPI

__all__ = ["OpenAPIDocumentModule"]


@Module(template_folder="templates")
class OpenAPIDocumentModule(ModuleBase):
    def __init__(
        self,
        app: App,
        document: t.Optional[OpenAPI] = None,
        openapi_url: t.Optional[str] = None,
        guards: t.List[t.Union[t.Type[GuardCanActivate], GuardCanActivate]] = None,
    ):
        self.app = app
        self._openapi_url = openapi_url
        self._openapi_router_prefix = ""
        self._openapi_router = self.create_open_api_router(guards=guards)

        if not openapi_url and document:
            self._openapi_url = "/openapi.json"

            @self._openapi_router.get(self._openapi_url, include_in_schema=False)
            def openapi_schema() -> t.Any:
                assert document and isinstance(document, OpenAPI), "Invalid Document"
                return document

        app.router.append(self._openapi_router)

    def create_open_api_router(
        self, guards: t.List[t.Union[t.Type[GuardCanActivate], GuardCanActivate]] = None
    ) -> ModuleRouter:
        return ModuleRouter(self._openapi_router_prefix, guards=guards)

    def _setup_docs(
        self, *, template_name: str, path: str, **template_context: t.Optional[t.Any]
    ) -> None:
        _path = path.lstrip("/").rstrip("/")

        @self._openapi_router.get(f"/{_path}", include_in_schema=False)
        @render(template_name)
        def _doc() -> t.Any:
            return template_context

    def setup_swagger_doc(
        self,
        *,
        path: str = "docs",
        title: str = "Ellar Swagger Doc",
        swagger_js_url: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui-bundle.js",
        swagger_css_url: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui.css",
        swagger_favicon_url: str = "https://eadwincode.github.io/ellar/img/Icon.svg",
    ) -> None:
        self._setup_docs(
            template_name="swagger",
            path=path,
            title=title,
            swagger_js_url=swagger_js_url,
            swagger_css_url=swagger_css_url,
            swagger_favicon_url=swagger_favicon_url,
            openapi_url=self._openapi_url,
        )

    def setup_redocs(
        self,
        *,
        path: str = "redoc",
        title: str = "Ellar Redoc",
        redoc_js_url: str = "https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
        redoc_favicon_url: str = "https://eadwincode.github.io/ellar/img/Icon.svg",
        with_google_fonts: bool = True,
    ) -> None:
        self._setup_docs(
            template_name="redocs",
            path=path,
            openapi_url=self._openapi_url,
            title=title,
            redoc_js_url=redoc_js_url,
            redoc_favicon_url=redoc_favicon_url,
            with_google_fonts=with_google_fonts,
        )
