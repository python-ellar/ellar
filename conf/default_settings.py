import typing as t

from starlette.middleware import Middleware
from starlette.responses import JSONResponse

from starletteapi.exceptions import RequestValidationError, APIException
from starletteapi.versioning import DefaultAPIVersioning, BaseAPIVersioning
from starletteapi.exception_handlers import api_exception_handler, request_validation_exception_handler


DEBUG: bool = False

DEFAULT_JSON_CLASS: t.Type[JSONResponse] = JSONResponse
SECRET_KEY: str = 'your-secret-key'

TEMPLATES_AUTO_RELOAD: t.Optional[bool] = None

VERSIONING_SCHEME: BaseAPIVersioning = DefaultAPIVersioning()
REDIRECT_SLASHES: bool = False

STATIC_FOLDER_PACKAGES: t.Optional[t.List[t.Union[str, t.Tuple[str]]]] = []
STATIC_MOUNT_PATH: str = '/static'

MIDDLEWARE: t.Sequence[Middleware] = []

APP_EXCEPTION_HANDLERS: t.Dict[t.Union[int, t.Type[Exception]], t.Callable] = {
    RequestValidationError: request_validation_exception_handler,
    APIException: api_exception_handler
}

# A dictionary mapping either integer status codes,
# or exception class types onto callables which handle the exceptions.
# Exception handler callables should be of the form
# `handler(request, exc) -> response` and may be be either standard functions, or async functions.
USER_CUSTOM_EXCEPTION_HANDLERS: t.Dict[t.Union[int, t.Type[Exception]], t.Callable] = {}
