import os

from ellar.app import AppFactory
from ellar.common.constants import ELLAR_CONFIG_MODULE
from ellar.core import LazyModuleImport as lazyLoad
from ellar.openapi import (
    OpenAPIDocumentBuilder,
    OpenAPIDocumentModule,
    SwaggerUI,
)


def bootstrapper():
    application = AppFactory.create_from_app_module(
        lazyLoad("ellar_and_django_orm.root_module:ApplicationModule"),
        config_module=os.environ.get(
            ELLAR_CONFIG_MODULE, "ellar_and_django_orm.config:DevelopmentConfig"
        ),
    )

    document_builder = OpenAPIDocumentBuilder()
    document_builder.set_title("Ellar with DjangoORM ").set_version(
        "1.0.2"
    ).set_contact(
        name="John Doe", url="https://www.yahoo.com", email="johnDoe@gmail.com"
    ).set_license("MIT Licence", url="https://www.google.com")

    document = document_builder.build_document(application)
    OpenAPIDocumentModule.setup(
        app=application,
        docs_ui=[SwaggerUI()],
        document=document,
        guards=[],
    )

    return application
