import os

from ellar.app import AppFactory
from ellar.common.constants import ELLAR_CONFIG_MODULE
from ellar.openapi import (
    OpenAPIDocumentBuilder,
    OpenAPIDocumentModule,
    SwaggerUI,
)

from .auth.auth_scheme import JWTAuthentication
from .root_module import ApplicationModule

application = AppFactory.create_from_app_module(
    ApplicationModule,
    config_module=os.environ.get(
        ELLAR_CONFIG_MODULE, "auth_project_with_handler.config:DevelopmentConfig"
    ),
)
# Register JWTAuthentication as an authentication scheme
application.add_authentication_schemes(JWTAuthentication)

# uncomment this section if you want API documentation

document_builder = OpenAPIDocumentBuilder()
document_builder.set_title("Auth With Auth Handler").set_version("1.0.2").set_contact(
    name="Author Name", url="https://www.author-name.com", email="authorname@gmail.com"
).set_license("MIT Licence", url="https://www.google.com")

document = document_builder.build_document(application)
module = OpenAPIDocumentModule.setup(document=document, docs_ui=SwaggerUI(), guards=[])
application.install_module(module)
