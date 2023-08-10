import os

from ellar.common.constants import ELLAR_CONFIG_MODULE
from ellar.core.factory import AppFactory
from ellar.openapi import (
    OpenAPIDocumentBuilder,
    OpenAPIDocumentModule,
    ReDocDocumentGenerator,
    SwaggerDocumentGenerator,
)

from .root_module import ApplicationModule

application = AppFactory.create_from_app_module(
    ApplicationModule,
    config_module=os.environ.get(
        ELLAR_CONFIG_MODULE, "carapp.config:DevelopmentConfig"
    ),
)

document_builder = OpenAPIDocumentBuilder()
document_builder.set_title("Ellar API").set_version("1.0.2").set_contact(
    name="John Doe", url="https://www.yahoo.com", email="johnDoe@gmail.com"
).set_license("MIT Licence", url="https://www.google.com")

document = document_builder.build_document(application)
module = OpenAPIDocumentModule.setup(
    document_generator=[SwaggerDocumentGenerator(), ReDocDocumentGenerator()],
    document=document,
    guards=[],
)
application.install_module(module)
