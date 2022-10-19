import os

from ellar.constants import ELLAR_CONFIG_MODULE
from ellar.core.factory import AppFactory

# from ellar.openapi import OpenAPIDocumentModule, OpenAPIDocumentBuilder
from .root_module import ApplicationModule

application = AppFactory.create_from_app_module(
    ApplicationModule,
    config_module=os.environ.get(
        ELLAR_CONFIG_MODULE, "example_project_2.config:DevelopmentConfig"
    ),
)

# uncomment this section if you want API documentation

# document_builder = OpenAPIDocumentBuilder()
# document_builder.set_title('Example_project_2 Title') \
#     .set_version('1.0.2') \
#     .set_contact(name='Author Name', url='https://www.author-name.com', email='authorname@gmail.com') \
#     .set_license('MIT Licence', url='https://www.google.com')
#
# document = document_builder.build_document(app)
# module = application.install_module(OpenAPIDocumentModule, document=document)
# module.setup_swagger_doc()
