from ellar.common import (
    Controller,
    ControllerBase,
    File,
    Form,
    Inject,
    Query,
    UploadFile,
    delete,
    file,
    get,
    post,
)

from ellar_storage import StorageService


@Controller('/upload')
class FileManagerController(ControllerBase):
    def __init__(self, storage_service: StorageService):
        self._storage_service = storage_service

    @post("/", response=str)
    def upload_file(
            self,
            upload: File[UploadFile],
            storage_service: Inject[StorageService],
            upload_storage: Form[str]
    ):
        assert self._storage_service == storage_service
        res = storage_service.save(file=upload, upload_storage=upload_storage)
        return res.filename

    @get("/")
    @file(media_type="application/octet-stream", streaming=True)
    def download_file(self, path: Query[str]):
        res = self._storage_service.get(path)
        return {"media_type": res.content_type, "content": res.as_stream()}

    @get("/download_as_attachment")
    @file(media_type="application/octet-stream")
    def download_as_attachment(self, path: Query[str]):
        res = self._storage_service.get(path)
        return {
            "path": res.get_cdn_url(),  # since we are using a local storage, this will return a path to the file
            "filename": res.filename,
            'media_type': res.content_type
        }

    @delete("/", response=dict)
    def delete_file(self, path: Query[str]):
        self._storage_service.delete(path)
        return ""
