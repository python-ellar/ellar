import typing as t
from functools import lru_cache
from pathlib import Path

from ellar.app import App
from ellar.common import (
    GuardCanActivate,
    IExecutionContext,
    Module,
    ModuleRouter,
    render,
    render_template_string,
    set_metadata,
)
from ellar.core import ModuleSetup
from ellar.di import injectable
from ellar.openapi.builder import OpenAPIDocumentBuilder
from ellar.openapi.constants import OPENAPI_OPERATION_KEY
from ellar.openapi.docs_ui import IDocumentationUI
from ellar.openapi.openapi_v3 import OpenAPI
from ellar.utils import get_unique_type
from starlette.responses import HTMLResponse

__all__ = ["OpenAPIDocumentModule"]

__BASE_DIR__ = Path(__file__).parent


ICON_SVG_PATH = "https://python-ellar.github.io/ellar/img/Icon.svg"


@injectable
class AllowAnyGuard(GuardCanActivate):
    async def can_activate(self, context: "IExecutionContext") -> bool:
        return True


class OpenAPIDocumentModule:
    @classmethod
    def setup(
        cls,
        app: App,
        docs_ui: t.Union[t.Sequence[IDocumentationUI], IDocumentationUI],
        document: t.Optional[
            t.Union[OpenAPI, t.Callable, OpenAPIDocumentBuilder]
        ] = None,
        router_prefix: str = "",
        openapi_url: t.Optional[str] = None,
        allow_any: bool = True,
        guards: t.Optional[
            t.List[t.Union[t.Type[GuardCanActivate], GuardCanActivate]]
        ] = None,
    ) -> t.Type[t.Any]:
        """
        Sets up OpenAPIDocumentModule

        @param app: Application instance
        @param docs_ui: Type of DocumentationRenderer
        @param document: Document Pydantic Model
        @param router_prefix: OPENAPI route prefix
        @param openapi_url: OPENAPI route url
        @param allow_any: Allow AllowAnyGuard on openapi routes
        @param guards: Guards that should be applied to openapi routes
        @return:
        """
        _guards = list(guards) if guards else []
        if allow_any:
            _guards = [AllowAnyGuard] + _guards
        _document_renderer: t.List[IDocumentationUI] = []
        router = ModuleRouter(
            router_prefix,
            guards=_guards,
            name="openapi",
            include_in_schema=False,
        )

        if isinstance(docs_ui, (list, tuple, set)):
            _document_renderer = list(docs_ui)
        else:
            _document_renderer = [docs_ui]  # type: ignore[list-item]

        if not openapi_url and document:
            openapi_url = "/openapi.json"

            if isinstance(document, OpenAPIDocumentBuilder):
                document_build_document = document.build_document

                @lru_cache(1200)
                def _get_document() -> OpenAPI:
                    """Build OPENAPI Schema on `openapi.json` request"""
                    return document_build_document(app)

                document = _get_document

            @router.get(
                openapi_url,
                include_in_schema=False,
                response=OpenAPI,
                name="openapi_schema",
            )
            @set_metadata(OPENAPI_OPERATION_KEY, True)
            def openapi_schema() -> t.Any:
                _docs = document
                if not isinstance(_docs, OpenAPI):
                    _docs = document()  # type: ignore[operator]
                return _docs

        for docs_ui in _document_renderer:
            if not isinstance(docs_ui, IDocumentationUI):
                raise Exception(
                    f"{docs_ui.__class__.__name__ if not isinstance(docs_ui, type) else docs_ui.__name__} "
                    f"must be of type `IDocumentationUIContext`"
                )

            docs_ui.template_context.setdefault("favicon_url", ICON_SVG_PATH)
            docs_ui.template_context.setdefault("openapi_url", openapi_url)
            cls._setup_document_manager(router=router, docs_ui=docs_ui)

        module: t.Type = Module(
            template_folder="templates",
            providers=[],
            routers=(router,),
            base_directory=str(__BASE_DIR__),
        )(get_unique_type())

        routes = ModuleSetup(module).build_and_get_routes(
            injector=app.injector, config=app.config
        )
        app.router.extend(routes)

        return module

    @classmethod
    def _setup_document_manager(
        cls,
        *,
        router: ModuleRouter,
        docs_ui: IDocumentationUI,
    ) -> None:
        _path = docs_ui.path.lstrip("/").rstrip("/")

        if not docs_ui.template_name:
            assert docs_ui.template_string, f"`{docs_ui.__class__.__name__}` class requires the `template_string` attribute to be provided."

            @t.no_type_check
            async def _doc(ctx: IExecutionContext) -> HTMLResponse:
                ctx.switch_to_http_connection().get_request()
                html_str = render_template_string(
                    docs_ui.template_string, **docs_ui.template_context
                )
                return HTMLResponse(html_str)

        else:
            assert docs_ui.template_name, f"`{docs_ui.__class__.__name__}` class requires the `template_name` attribute to be provided."

            @render(docs_ui.template_name)
            async def _doc() -> t.Any:
                return docs_ui.template_context

        _doc = router.get(
            f"/{_path}",
            include_in_schema=False,
            name=docs_ui.name,
        )(_doc)

        set_metadata(OPENAPI_OPERATION_KEY, True)(_doc)
