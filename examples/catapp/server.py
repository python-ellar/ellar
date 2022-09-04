import os

from ellar.core.factory import AppFactory
from ellar.openapi.builder import OpenAPIDocumentBuilder
from ellar.openapi.module import OpenAPIDocumentModule

from .application.module import AppModuleTest

os.environ.setdefault('ELLAR_CONFIG_MODULE', 'catapp.config:DevelopmentConfig')

app = AppFactory.create_from_app_module(AppModuleTest)

document_builder = OpenAPIDocumentBuilder()
document_builder.set_title('Cat Application')\
    .set_version('1.0.2')\
    .set_contact(name='Eadwin', url='https://www.yahoo.com', email='eadwin@gmail.com')\
    .set_license('MIT Licence', url='https://www.google.com')

document = document_builder.build_document(app)
module = app.install_module(OpenAPIDocumentModule, document=document)
module.setup_redocs()
module.setup_swagger_doc()
