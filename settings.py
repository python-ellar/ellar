import inspect
from typing import Optional

from starlette.responses import JSONResponse
from typing_extensions import Type
from pathlib import Path
from starletteapi.versioning import DefaultAPIVersioning, BaseAPIVersioning


class Config:
    def __init__(self):
        self.BASE_DIR = Path(inspect.getfile(self.__class__)).resolve().parent

    DEBUG: bool = False
    DEFAULT_JSON_CLASS: Type[JSONResponse] = JSONResponse
    SECRET_KEY: str = 'your-secret-key'

    TEMPLATES_AUTO_RELOAD: Optional[bool] = None
    TEMPLATE_FOLDER: Optional[str] = 'templates'

    STATIC_FOLDER: Optional[str] = 'statics'
    VERSIONING_SCHEME: BaseAPIVersioning = DefaultAPIVersioning()
    REDIRECT_SLASHES: bool = False
