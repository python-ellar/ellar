import os

from ellar.app import App, AppFactory
from ellar.common import datastructures
from ellar.common.constants import ELLAR_CONFIG_MODULE
from ellar.core import LazyModuleImport as lazyLoad
from ellar.openapi import OpenAPIDocumentBuilder, OpenAPIDocumentModule, SwaggerUI

from ellar_storage import StorageService


def seed_files(application):
    # Seed some files into the containers configured.

    storage_service: StorageService = application.injector.get(StorageService)

    # save a file in files folder
    storage_service.save(
        file=datastructures.ContentFile(b"We can now save files in files folder", name="file.txt"),
        upload_storage='files')
    # save a file in images folder
    storage_service.save(
        file=datastructures.ContentFile(b"We can now save files in images folder", name="image.txt"),
        upload_storage='images')
    # save a file in document folder
    storage_service.save(
        file=datastructures.ContentFile(b"We can now save files in documents folder", name="docs.txt"),
        upload_storage='documents')


def bootstrap() -> App:
    application = AppFactory.create_from_app_module(
        lazyLoad("ellar_storage_tut.root_module:ApplicationModule"),
        config_module=os.environ.get(
            ELLAR_CONFIG_MODULE, "ellar_storage_tut.config:DevelopmentConfig"
        ),
        global_guards=[]
    )

    # uncomment this section if you want API documentation

    document_builder = OpenAPIDocumentBuilder()
    document_builder.set_title('Ellar_storage_tut Title') \
        .set_version('1.0.2') \
        .set_contact(name='Author Name', url='https://www.author-name.com', email='authorname@gmail.com') \
        .set_license('MIT Licence', url='https://www.google.com') \
        .add_server('/', description='Development Server')

    document = document_builder.build_document(application)
    OpenAPIDocumentModule.setup(
       app=application,
       document=document,
       docs_ui=SwaggerUI(),
       guards=[]
    )

    seed_files(application)

    return application
