import typing as t

from starlette.exceptions import WebSocketException

from .commands import EllarTyper, command
from .datastructures import UploadFile
from .decorators import (
    Controller,
    Module,
    UseGuards,
    UseInterceptors,
    Version,
    exception_handler,
    extra_args,
    file,
    middleware,
    openapi_info,
    render,
    serializer_filter,
    set_metadata,
    template_filter,
    template_global,
)
from .exceptions import (
    APIException,
    AuthenticationFailed,
    HTTPException,
    MethodNotAllowed,
    NotAcceptable,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    UnsupportedMediaType,
)
from .interfaces import (
    IApplicationShutdown,
    IApplicationStartup,
    IExceptionHandler,
    IExceptionMiddlewareService,
    IExecutionContext,
    IExecutionContextFactory,
    IGuardsConsumer,
    IHostContext,
    IHostContextFactory,
    IHTTPConnectionContextFactory,
    IHTTPHostContext,
    IInterceptorsConsumer,
    IModuleSetup,
    IModuleTemplateLoader,
    IResponseModel,
    IWebSocketContextFactory,
    IWebSocketHostContext,
)
from .models import (
    BaseAPIKey,
    BaseAuthGuard,
    BaseHttpAuth,
    ControllerBase,
    ControllerType,
    EllarInterceptor,
    GuardCanActivate,
)
from .params.decorators import (
    Body,
    Context,
    Cookie,
    File,
    Form,
    Header,
    Host,
    Http,
    Path,
    Provide,
    Query,
    Req,
    Res,
    Session,
    Ws,
    WsBody,
)
from .params.params import ParamFieldInfo as Param, ParamTypes
from .responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    ORJSONResponse,
    PlainTextResponse,
    RedirectResponse,
    Response,
    StreamingResponse,
    UJSONResponse,
)
from .routing import (
    ModuleRouter,
    delete,
    get,
    head,
    http_route,
    options,
    patch,
    post,
    put,
    trace,
    ws_route,
)
from .serializer import DataclassSerializer, Serializer, serialize_object
from .templating import TemplateResponse, render_template, render_template_string

__all__ = [
    "ControllerBase",
    "serialize_object",
    "ControllerType",
    "BaseAuthGuard",
    "BaseAPIKey",
    "BaseHttpAuth",
    "GuardCanActivate",
    "EllarTyper",
    "Serializer",
    "DataclassSerializer",
    "WebSocketException",
    "APIException",
    "AuthenticationFailed",
    "NotAuthenticated",
    "NotFound",
    "NotAcceptable",
    "PermissionDenied",
    "HTTPException",
    "UnsupportedMediaType",
    "MethodNotAllowed",
    "render_template",
    "render_template_string",
    "command",
    "ModuleRouter",
    "render",
    "Module",
    "UseGuards",
    "Param",
    "ParamTypes",
    "set_metadata",
    "Controller",
    "openapi_info",
    "Version",
    "delete",
    "get",
    "head",
    "http_route",
    "options",
    "patch",
    "post",
    "put",
    "trace",
    "ws_route",
    "Body",
    "Cookie",
    "File",
    "Form",
    "Header",
    "Path",
    "Query",
    "WsBody",
    "Context",
    "Provide",
    "Req",
    "Ws",
    "middleware",
    "exception_handler",
    "serializer_filter",
    "template_filter",
    "template_global",
    "Res",
    "Session",
    "Host",
    "Http",
    "UploadFile",
    "file",
    "extra_args",
    "JSONResponse",
    "UJSONResponse",
    "ORJSONResponse",
    "StreamingResponse",
    "HTMLResponse",
    "FileResponse",
    "PlainTextResponse",
    "RedirectResponse",
    "TemplateResponse",
    "Response",
    "IHostContext",
    "IExecutionContextFactory",
    "IExecutionContext",
    "IHostContextFactory",
    "IHTTPHostContext",
    "IWebSocketContextFactory",
    "IWebSocketHostContext",
    "IHTTPConnectionContextFactory",
    "IExceptionMiddlewareService",
    "IExceptionHandler",
    "IModuleSetup",
    "IResponseModel",
    "IModuleTemplateLoader",
    "IInterceptorsConsumer",
    "IGuardsConsumer",
    "EllarInterceptor",
    "UseInterceptors",
    "IApplicationStartup",
    "IApplicationShutdown",
]


def __dir__() -> t.List[str]:
    return sorted(__all__)  # pragma: no cover
