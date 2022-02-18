import typing as t
import inspect
from pathlib import Path
from starletteapi.module import StarletteAPIModuleBase, ApplicationModuleBase
from starletteapi.module.base import BaseModule, StarletteAPIModuleBase
from starletteapi.guard import GuardCanActivate, Guards
from starletteapi.main import StarletteApp
from starletteapi.openapi.openapi_v3 import OpenAPI
from starletteapi.templating import Render


class OpenAPIDocumentModule(BaseModule, StarletteAPIModuleBase):
    def __init__(self):
        self._module_base_directory = None
        self._template_folder = 'templates'
        self._static_folder = None
        self._resolve_module_base_directory()

    def _resolve_module_base_directory(self):
        if not self._module_base_directory:
            self._module_base_directory = Path(inspect.getfile(self.module)).resolve().parent

    @property
    def module(self) -> t.Union[t.Type[StarletteAPIModuleBase], t.Type[ApplicationModuleBase]]:
        return self.__class__

    def _setup_docs(
            self,
            *,
            template_name: str,
            app: 'StarletteApp',
            path: str, document: OpenAPI,
            guards: t.Optional[t.List[t.Union[t.Type['GuardCanActivate'], 'GuardCanActivate']]] = None,
            **template_context: t.Optional[t.Any]
    ):
        _path = path.lstrip('/').rstrip('/')
        _guards = guards or []
        openapi_schema_path = template_context.get("openapi_url")
        app.add_module(self)

        if not openapi_schema_path:
            openapi_schema_path = f"/openapi.json"

            @Guards(*_guards)
            @app.Get(openapi_schema_path, include_in_schema=False)
            def openapi_schema():
                return document.dict(by_alias=True, exclude_none=True)

        @Guards(*_guards)
        @app.Get(f"/{_path}", include_in_schema=False)
        @Render(template_name)
        def _doc():
            template_context.update(openapi_url=openapi_schema_path)
            return template_context

    @classmethod
    def setup_swagger_doc(
            cls,
            *,
            path: str = "docs",
            app: 'StarletteApp',
            document: OpenAPI,
            guards: t.Optional[t.List[t.Union[t.Type['GuardCanActivate'], 'GuardCanActivate']]] = None,
            title: str = 'StarletterAPI Swagger Doc',
            swagger_js_url: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui-bundle.js",
            swagger_css_url: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui.css",
            swagger_favicon_url: str = "https://fastapi.tiangolo.com/img/favicon.png",
            oauth2_redirect_url: t.Optional[str] = None,
            init_oauth: t.Optional[t.Dict[str, t.Any]] = None,
            openapi_url: t.Optional[str] = None,
    ):
        module = cls()
        module._setup_docs(
            template_name='swagger', path=path, app=app, document=document, guards=guards,
            title=title, swagger_js_url=swagger_js_url, swagger_css_url=swagger_css_url,
            swagger_favicon_url=swagger_favicon_url, openapi_url=openapi_url
        )

    @classmethod
    def setup_redocs(
            cls,
            *,
            path: str = "redoc",
            app: 'StarletteApp',
            document: OpenAPI,
            guards: t.Optional[t.List[t.Union[t.Type['GuardCanActivate'], 'GuardCanActivate']]] = None,
            title: str = 'StarletterAPI Redoc',
            redoc_js_url: str = "https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
            redoc_favicon_url: str = "https://fastapi.tiangolo.com/img/favicon.png",
            with_google_fonts: bool = True,
            openapi_url: t.Optional[str] = None,
    ):
        module = cls()
        module._setup_docs(
            template_name='redocs', path=path, app=app, document=document, guards=guards,
            openapi_url=openapi_url, title=title, redoc_js_url=redoc_js_url, redoc_favicon_url=redoc_favicon_url,
            with_google_fonts=with_google_fonts
        )
