import typing as t
from starletteapi.module.base import StarletteAPIModuleBase
from starletteapi.guard import GuardCanActivate
from starletteapi.main import StarletteApp
from starletteapi.openapi.openapi_v3 import OpenAPI
from starletteapi.templating import Render
from starletteapi.module import Module
from starletteapi.routing import Guards


@Module(
    template_folder='templates'
)
class OpenAPIDocumentModule(StarletteAPIModuleBase):
    def __init__(
            self,
            app: StarletteApp,
            document: t.Optional[OpenAPI] = None,
            openapi_url: t.Optional[str] = None,
            guards: t.Optional[t.List[t.Union[t.Type['GuardCanActivate'], 'GuardCanActivate']]] = None,
    ):
        self._guards = guards or []
        self.app: StarletteApp = app
        self._openapi_url = openapi_url
        if not openapi_url and document:
            self._openapi_url = f"/openapi.json"

            @Guards(*self._guards)
            @self.app.Get(self._openapi_url, include_in_schema=False)
            def openapi_schema():
                return document.dict(by_alias=True, exclude_none=True)

    def _setup_docs(
            self,
            *,
            template_name: str,
            path: str,
            **template_context: t.Optional[t.Any]
    ):
        _path = path.lstrip('/').rstrip('/')

        @Guards(*self._guards)
        @self.app.Get(f"/{_path}", include_in_schema=False)
        @Render(template_name)
        def _doc():
            return template_context

    def setup_swagger_doc(
            self,
            *,
            path: str = "docs",
            title: str = 'StarletterAPI Swagger Doc',
            swagger_js_url: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui-bundle.js",
            swagger_css_url: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui.css",
            swagger_favicon_url: str = "https://fastapi.tiangolo.com/img/favicon.png",
    ):
        self._setup_docs(
            template_name='swagger', path=path,
            title=title, swagger_js_url=swagger_js_url, swagger_css_url=swagger_css_url,
            swagger_favicon_url=swagger_favicon_url, openapi_url=self._openapi_url
        )

    def setup_redocs(
            self,
            *,
            path: str = "redoc",
            title: str = 'StarletterAPI Redoc',
            redoc_js_url: str = "https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
            redoc_favicon_url: str = "https://fastapi.tiangolo.com/img/favicon.png",
            with_google_fonts: bool = True,
    ):
        self._setup_docs(
            template_name='redocs', path=path,
            openapi_url=self._openapi_url, title=title,
            redoc_js_url=redoc_js_url, redoc_favicon_url=redoc_favicon_url,
            with_google_fonts=with_google_fonts
        )
