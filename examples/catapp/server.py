import os

from catapp.application.module import AppModuleTest
from ellar.core.factory import AppFactory
from ellar.openapi.builder import OpenAPIDocumentBuilder
from ellar.openapi.module import OpenAPIDocumentModule

os.environ.setdefault('ELLAR_CONFIG_MODULE', 'app_module_test.settings')

app = AppFactory.create_from_app_module(AppModuleTest)

document_builder = OpenAPIDocumentBuilder()
document_builder.set_title('Mirabel Title')\
    .set_version('1.0.2')\
    .set_contact(name='Eadwin', url='https://www.yahoo.com', email='eadwin@gmail.com')\
    .set_license('MIT Licence', url='https://www.google.com')

document = document_builder.build_document(app)
module = app.install_module(OpenAPIDocumentModule, app=app, document=document)
module.setup_redocs()
module.setup_swagger_doc()
