import typing as t

from ellar.common import (
    GuardCanActivate,
    IExecutionContext,
    IModuleSetup,
    Module,
    ModuleRouter,
    render,
    set_metadata,
)
from ellar.core import DynamicModule, ModuleBase
from ellar.di import injectable
from ellar.openapi.constants import OPENAPI_OPERATION_KEY
from ellar.openapi.docs_ui import IDocumentationUIContext
from ellar.openapi.openapi_v3 import OpenAPI

__all__ = ["OpenAPIDocumentModule"]


@injectable
class AllowAnyGuard(GuardCanActivate):
    async def can_activate(self, context: "IExecutionContext") -> bool:
        return True


@Module(template_folder="templates")
class OpenAPIDocumentModule(ModuleBase, IModuleSetup):
    @classmethod
    def setup(
        cls,
        docs_ui: t.Union[t.Sequence[IDocumentationUIContext], IDocumentationUIContext],
        document: t.Optional[OpenAPI] = None,
        router_prefix: str = "",
        openapi_url: t.Optional[str] = None,
        allow_any: bool = True,
        guards: t.Optional[
            t.List[t.Union[t.Type[GuardCanActivate], GuardCanActivate]]
        ] = None,
    ) -> DynamicModule:
        """
        Sets up OpenAPIDocumentModule

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
            name="ellar-open-api",
            include_in_schema=False,
        )

        if isinstance(docs_ui, (list, tuple, set)):
            _document_renderer = list(docs_ui)
        else:
            _document_renderer = [docs_ui]  # type: ignore[list-item]

        if not openapi_url and document:
            openapi_url = "/openapi.json"

            @router.get(openapi_url, include_in_schema=False)
            @set_metadata(OPENAPI_OPERATION_KEY, True)
            def openapi_schema() -> t.Any:
                assert document and isinstance(document, OpenAPI), "Invalid Document"
                return document

        for doc_gen in _document_renderer:
            if not isinstance(doc_gen, IDocumentationUIContext):
                raise Exception(
                    f"{doc_gen.__class__.__name__ if not isinstance(doc_gen, type) else doc_gen.__name__} "
                    f"must be of type `IDocumentationUIContext`"
                )

            template_context = dict(doc_gen.template_context)
            template_context.setdefault(
                "favicon_url", "https://eadwincode.github.io/ellar/img/Icon.svg"
            )
            cls._setup_document_manager(
                router=router,
                template_name=doc_gen.template_name,
                path=doc_gen.path,
                openapi_url=openapi_url,
                title=doc_gen.title,
                **template_context,
            )
        return DynamicModule(module=cls, providers=[], routers=(router,))

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
        def _doc() -> t.Any:
            return template_context
