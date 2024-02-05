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
    set_metadata,
)
from ellar.core import ModuleSetup
from ellar.di import injectable
from ellar.openapi.builder import OpenAPIDocumentBuilder
from ellar.openapi.constants import OPENAPI_OPERATION_KEY
from ellar.openapi.docs_ui import IDocumentationUIContext
from ellar.openapi.openapi_v3 import OpenAPI
from ellar.utils import get_unique_type

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
        docs_ui: t.Union[t.Sequence[IDocumentationUIContext], IDocumentationUIContext],
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
        _document_renderer: t.List[IDocumentationUIContext] = []
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

            @router.get(openapi_url, include_in_schema=False, response=OpenAPI)
            @set_metadata(OPENAPI_OPERATION_KEY, True)
            def openapi_schema() -> t.Any:
                _docs = document
                if not isinstance(_docs, OpenAPI):
                    _docs = document()  # type: ignore[operator]
                return _docs

        for doc_gen in _document_renderer:
            if not isinstance(doc_gen, IDocumentationUIContext):
                raise Exception(
                    f"{doc_gen.__class__.__name__ if not isinstance(doc_gen, type) else doc_gen.__name__} "
                    f"must be of type `IDocumentationUIContext`"
                )

            template_context = dict(doc_gen.template_context)
            template_context.setdefault("favicon_url", ICON_SVG_PATH)
            cls._setup_document_manager(
                router=router,
                template_name=doc_gen.template_name,
                path=doc_gen.path,
                openapi_url=openapi_url,
                title=doc_gen.title,
                **template_context,
            )

        module = Module(
            template_folder="templates",
            providers=[],
            routers=(router,),
            base_directory=str(__BASE_DIR__),
        )(get_unique_type())

        module_ref = ModuleSetup(module).get_module_ref(
            app.config, app.injector.container
        )
        app.router.extend(module_ref.routes)  # type: ignore[union-attr]
        app.injector.add_module(module_ref)

        return module  # type: ignore[no-any-return]

    @classmethod
    def _setup_document_manager(
        cls,
        *,
        router: ModuleRouter,
        template_name: str,
        path: str,
        **template_context: t.Optional[t.Any],
    ) -> None:
        _path = path.lstrip("/").rstrip("/")

        @router.get(
            f"/{_path}",
            include_in_schema=False,
            name=template_name.replace(".html", ""),
        )
        @render(template_name)
        @set_metadata(OPENAPI_OPERATION_KEY, True)
        async def _doc() -> t.Any:
            return template_context
