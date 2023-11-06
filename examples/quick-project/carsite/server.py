import os

from ellar.app import AppFactory
from ellar.common.constants import ELLAR_CONFIG_MODULE
from ellar.openapi import (
    OpenAPIDocumentBuilder,
    OpenAPIDocumentModule,
    SwaggerUI,
)

from .root_module import ApplicationModule

application = AppFactory.create_from_app_module(
    ApplicationModule,
    config_module=os.environ.get(
        ELLAR_CONFIG_MODULE, "carsite.config:DevelopmentConfig"
    ),
)

document_builder = OpenAPIDocumentBuilder()
document_builder.set_title("CarSite API").set_version("1.0.0").set_contact(
    name="Author", url="https://www.yahoo.com", email="author@gmail.com"
).set_license("MIT Licence", url="https://www.google.com")

document = document_builder.build_document(application)
module = OpenAPIDocumentModule.setup(document=document, docs_ui=SwaggerUI(), guards=[])
application.install_module(module)
