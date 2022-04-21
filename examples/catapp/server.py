import os

from app_module_test.application.module import AppModuleTest
from architek.core.factory import ArchitekAppFactory
from architek.openapi.builder import OpenAPIDocumentBuilder
from architek.openapi.module import OpenAPIDocumentModule

os.environ.setdefault('ARCHITEK_CONFIG_MODULE', 'app_module_test.settings')

app = ArchitekAppFactory.create_from_app_module(AppModuleTest)

document_builder = OpenAPIDocumentBuilder()
document_builder.set_title('Mirabel Title')\
    .set_version('1.0.2')\
    .set_contact(name='Eadwin', url='https://www.yahoo.com', email='eadwin@gmail.com')\
    .set_license('MIT Licence', url='https://www.google.com')

document = document_builder.build_document(app)
module = app.install_module(OpenAPIDocumentModule, app=app, document=document)
module.setup_redocs()
module.setup_swagger_doc()
