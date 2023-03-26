import typing as t

from ellar.common import Module, ModuleRouter, render
from ellar.core import DynamicModule, IModuleSetup, ModuleBase
from ellar.core.guard import GuardCanActivate
from ellar.openapi.docs_generators import IDocumentationGenerator
from ellar.openapi.openapi_v3 import OpenAPI

__all__ = ["OpenAPIDocumentModule"]


@Module(template_folder="templates")
class OpenAPIDocumentModule(ModuleBase, IModuleSetup):
    @classmethod
    def setup(
        cls,
        document_generator: t.Union[
            t.Sequence[IDocumentationGenerator], IDocumentationGenerator
        ],
        document: OpenAPI = None,
        router_prefix: str = "",
        openapi_url: t.Optional[str] = None,
        guards: t.List[t.Union[t.Type[GuardCanActivate], GuardCanActivate]] = None,
    ) -> DynamicModule:
        _guards = list(guards) if guards else []
        _document_generator: t.List[IDocumentationGenerator] = []
        router = ModuleRouter(router_prefix, guards=_guards, name="ellar-open-api")

        if isinstance(document_generator, (list, tuple, set)):
            _document_generator = list(document_generator)
        else:
            _document_generator = [document_generator]  # type: ignore[list-item]

        if not openapi_url and document:
            openapi_url = "/openapi.json"

            @router.get(openapi_url, include_in_schema=False)
            def openapi_schema() -> t.Any:
                assert document and isinstance(document, OpenAPI), "Invalid Document"
                return document

        for doc_gen in _document_generator:
            if not isinstance(doc_gen, IDocumentationGenerator):
                raise Exception(
                    f"{doc_gen.__class__.__name__ if not isinstance(doc_gen, type) else doc_gen.__name__} "
                    f"must be of type `IDocumentationGenerator`"
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
        def _doc() -> t.Any:
            return template_context
