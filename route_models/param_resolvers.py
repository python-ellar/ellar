import typing as t
import email
import inspect
import json
from abc import ABC, abstractmethod

import anyio
from pydantic import MissingError
from pydantic.error_wrappers import ErrorWrapper
from pydantic.utils import deepcopy, lenient_issubclass
from starlette.datastructures import FormData, QueryParams, Headers
from starlette.exceptions import HTTPException
from starletteapi.logger import logger
from pydantic.fields import (
    ModelField, Undefined,
)
from starletteapi.requests import Request
from starletteapi.websockets import WebSocket
from starletteapi.types import T
from starletteapi.constants import sequence_shapes, sequence_types, sequence_shape_to_type
from starletteapi.context import ExecutionContext
from starletteapi.datastructures import UploadFile
from starletteapi.exceptions import RequestValidationError
from starletteapi.route_models.helpers import is_scalar_sequence_field


class BaseRouteParameterResolver(ABC):
    @abstractmethod
    async def resolve(self, *args: t.Any, **kwargs: t.Any) -> t.Tuple:
        """Resolve handle"""


class RouteParameterResolver(BaseRouteParameterResolver, ABC):
    def __init__(self, model_field: ModelField, *args: t.Any, **kwargs: t.Any):
        self.model_field = model_field

    def assert_field_info(self):
        from . import params
        assert isinstance(
            self.model_field.field_info, params.Param
        ), "Params must be subclasses of Param"

    @classmethod
    def create_error(cls, loc: t.Any) -> ErrorWrapper:
        return ErrorWrapper(MissingError(), loc=loc)

    async def resolve(self, *args: t.Any, **kwargs: t. Any) -> t.Tuple:
        value_ = await self.resolve_handle(*args, **kwargs)
        return value_

    @abstractmethod
    async def resolve_handle(self, *args: t.Any, **kwargs: t.Any) -> t.Tuple:
        ...


class HeaderParameterResolver(RouteParameterResolver):
    @classmethod
    def get_received_parameter(cls, ctx: ExecutionContext) -> t.Union[QueryParams, Headers]:
        connection = ctx.switch_to_http_connection()
        return connection.headers

    async def resolve_handle(self, ctx: ExecutionContext, *args: t.Any, **kwargs: t.Any):
        received_params = self.get_received_parameter(ctx=ctx)
        if is_scalar_sequence_field(self.model_field):
            value = received_params.getlist(self.model_field.alias) or self.model_field.default
        else:
            value = received_params.get(self.model_field.alias)
        self.assert_field_info()
        field_info = self.model_field.field_info
        values = {}
        if value is None:
            if self.model_field.required:
                errors = [self.create_error(loc=(field_info.in_.value, self.model_field.alias))]
                return {}, errors
            else:
                values[self.model_field.name] = deepcopy(self.model_field.default)

        v_, errors_ = self.model_field.validate(
            value, values, loc=(field_info.in_.value, self.model_field.alias)
        )
        return {self.model_field.name: v_}, errors_


class QueryParameterResolver(HeaderParameterResolver):
    @classmethod
    def get_received_parameter(cls, ctx: ExecutionContext) -> t.Union[QueryParams, Headers]:
        connection = ctx.switch_to_http_connection()
        return connection.query_params


class PathParameterResolver(RouteParameterResolver):
    @classmethod
    def get_received_parameter(cls, ctx: ExecutionContext) -> t.Mapping[str, t.Any]:
        connection = ctx.switch_to_http_connection()
        return connection.path_params

    async def resolve_handle(self, ctx: ExecutionContext, **kwargs: t.Any):
        received_params = self.get_received_parameter(ctx=ctx)
        value = received_params.get(str(self.model_field.alias))
        self.assert_field_info()

        v_, errors_ = self.model_field.validate(
            value, {}, loc=(self.model_field.field_info.in_.value, self.model_field.alias)
        )
        return {self.model_field.name: v_}, errors_


class CookieParameterResolver(PathParameterResolver):
    @classmethod
    def get_received_parameter(cls, ctx: ExecutionContext) -> t.Mapping[str, t.Any]:
        connection = ctx.switch_to_http_connection()
        return connection.cookies


class WsBodyParameterResolver(RouteParameterResolver):
    async def resolve_handle(self, ctx: ExecutionContext, *args: t.Any, body: t.Any, **kwargs: t.Any):
        embed = getattr(self.model_field.field_info, "embed", False)
        received_body = {self.model_field.alias: body}
        loc = ("body",)
        if embed:
            received_body = body
            loc = ("body", self.model_field.alias)
        try:
            value = received_body.get(self.model_field.alias)
            v_, errors_ = self.model_field.validate(value, {}, loc=loc)
            return {self.model_field.name: v_}, errors_
        except AttributeError:
            errors = [self.create_error(loc=loc)]
            return None, errors


class BodyParameterResolver(WsBodyParameterResolver):
    def __init__(self, *args: t.Any, **kwargs: t.Any):
        super().__init__(*args, **kwargs)

    async def get_request_body(self, ctx: ExecutionContext) -> t.Any:
        try:
            request = ctx.switch_to_request()
            body_bytes = await request.body()
            if body_bytes:
                json_body: t.Any = Undefined
                content_type_value = request.headers.get("content-type")
                if not content_type_value:
                    json_body = await request.json()
                else:
                    message = email.message.Message()
                    message["content-type"] = content_type_value
                    if message.get_content_maintype() == "application":
                        subtype = message.get_content_subtype()
                        if subtype == "json" or subtype.endswith("+json"):
                            json_body = await request.json()
                if json_body != Undefined:
                    body_bytes = json_body
            return body_bytes
        except json.JSONDecodeError as e:
            raise RequestValidationError([ErrorWrapper(e, ("body", e.pos))])
        except Exception as e:
            raise HTTPException(
                status_code=400, detail="There was an error parsing the body"
            ) from e

    async def resolve_handle(
            self, ctx: ExecutionContext,
            *args: t.Any, body: t.Optional[t.Any] = None,
            **kwargs: t.Any
    ):
        body = body or await self.get_request_body(ctx)
        return await super(BodyParameterResolver, self).resolve_handle(ctx, *args, body=body, **kwargs)


class FormParameterResolver(BodyParameterResolver):
    async def process_and_validate(self, *, values: t.Dict, value: t.Any, loc: t.Tuple):
        v_, errors_ = self.model_field.validate(value, values, loc=loc)
        values[self.model_field.name] = v_
        return values, errors_

    async def get_request_body(self, ctx: ExecutionContext) -> t.Any:
        try:
            request = ctx.switch_to_request()
            body_bytes = await request.form()
            return body_bytes
        except Exception as e:
            raise HTTPException(
                status_code=400, detail="There was an error parsing the body"
            ) from e

    async def resolve_handle(
            self,
            ctx: ExecutionContext,
            *args: t.Any,
            body: t.Optional[t.Any] = None,
            **kwargs: t.Any
    ):
        _body = body or await self.get_request_body(ctx)
        values = {}
        received_body = {self.model_field.alias: _body}
        loc = ("body",)

        if (
                self.model_field.shape in sequence_shapes or self.model_field.type_ in sequence_types
        ) and isinstance(_body, FormData):
            loc = ("body", self.model_field.alias)
            value = _body.getlist(self.model_field.alias)
        else:
            try:
                value = received_body.get(self.model_field.alias)
            except AttributeError:
                errors = [self.create_error(loc=loc)]
                return values, errors

        if not value or self.model_field.shape in sequence_shapes and len(value) == 0:
            if self.model_field.required:
                return await self.process_and_validate(values=values, value=_body, loc=loc)
            else:
                values[self.model_field.name] = deepcopy(self.model_field.default)
            return values, []

        return await self.process_and_validate(values=values, value=value, loc=loc)


class BulkFormParameterResolver(FormParameterResolver):
    def __init__(self, *args: t.Any, form_resolvers: t.List[RouteParameterResolver], **kwargs: t.Any):
        super().__init__(*args, **kwargs)
        self._form_resolvers = form_resolvers

    async def resolve_handle(self, ctx: ExecutionContext, *args: t.Any, **kwargs: t.Any):
        _body = await self.get_request_body(ctx)
        values: t.Dict[str, t.Any] = {}
        errors: t.List[ErrorWrapper] = []
        if self._form_resolvers:
            for parameter_resolver in self._form_resolvers:
                value_, errors_ = await parameter_resolver.resolve(ctx=ctx, body=_body)
                if value_:
                    values.update(value_)
                if errors_:
                    errors += errors_
            return values, errors
        return super(BulkFormParameterResolver, self).resolve_handle(ctx, *args, **kwargs)


class BulkBodyParameterResolver(BodyParameterResolver):
    def __init__(self, *args: t.Any, resolvers: t.List[RouteParameterResolver], **kwargs: t.Any):
        super().__init__(*args, **kwargs)
        self.resolvers = resolvers

    async def resolve_handle(self, ctx: ExecutionContext, *args: t.Any, **kwargs: t.Any):
        _body = await self.get_request_body(ctx)
        values, errors = await super(BulkBodyParameterResolver, self).resolve_handle(ctx, *args, body=_body, **kwargs)
        if not errors:
            _, body_value = values.popitem()
            return body_value.dict(), errors
        return values, errors


class FileParameterResolver(FormParameterResolver):
    async def process_and_validate(self, *, values: t.Dict, value: t.Any, loc: t.Tuple):
        if (
                lenient_issubclass(self.model_field.type_, bytes)
                and isinstance(value, UploadFile)
        ):
            value = await value.read()
        elif (
                self.model_field.shape in sequence_shapes
                and lenient_issubclass(self.model_field.type_, bytes)
                and isinstance(value, sequence_types)
        ):
            results: t.List[t.Union[bytes, str]] = []

            async def process_fn(
                    fn: t.Callable[[], t.Coroutine[t.Any, t.Any, t.Any]]
            ) -> None:
                result = await fn()
                results.append(result)

            async with anyio.create_task_group() as tg:
                for sub_value in value:
                    tg.start_soon(process_fn, sub_value.read)
            value = sequence_shape_to_type[self.model_field.shape](results)

        v_, errors_ = self.model_field.validate(value, values, loc=loc)
        values[self.model_field.name] = v_
        return values, errors_


class NonFieldRouteParameterResolver(BaseRouteParameterResolver, ABC):
    def __init__(self, data: t.Optional[t.Any] = None):
        self.data = data
        self.parameter_name = None
        self.type_annotation = None

    def __call__(self, parameter_name: str, parameter_annotation: t.Type[T]) -> t.Any:
        self.parameter_name = parameter_name
        self.type_annotation = parameter_annotation
        return self

    async def resolve(self, ctx: ExecutionContext, **kwargs: t.Any) -> t.Any:
        raise NotImplementedError


class ParameterInjectable(NonFieldRouteParameterResolver):
    def __init__(self, service: t.Optional[t.Type[T]] = None) -> None:
        if service:
            assert isinstance(service, type), 'Service must be a type'
        super().__init__(data=service)

    def __call__(self, parameter_name: str, parameter_annotation: t.Type[T]) -> T:
        self.parameter_name = parameter_name
        self.type_annotation = parameter_annotation
        if not self.data and isinstance(self.type_annotation, inspect.Parameter.empty):
            raise Exception('Injectable must have a valid type')

        if self.data and parameter_annotation is not inspect.Parameter.empty and parameter_annotation is not self.data:
            raise Exception(f'Annotation({self.type_annotation}) is not the same as service({self.data})')

        if not self.data:
            self.data = self.type_annotation
        return self

    async def resolve(self, ctx: ExecutionContext, **kwargs: t.Any) -> t.Tuple[t.Dict[str, T], t.List]:
        try:
            service_provider = ctx.get_service_provider()
            value = service_provider.get(self.data)
            return {self.parameter_name: value}, []
        except Exception as ex:
            logger.error(f"Unable to resolve service {self.data} \nErrorMessage: {ex}")
            return {}, [ErrorWrapper(ex)]


class RequestParameter(NonFieldRouteParameterResolver):
    async def resolve(self, ctx: ExecutionContext, **kwargs: t.Any) -> t.Tuple[t.Dict, t.List]:
        try:
            request = ctx.switch_to_request()
            return {self.parameter_name: request}, []
        except Exception as ex:
            return {}, [ErrorWrapper(ex)]


class WebSocketParameter(NonFieldRouteParameterResolver):
    async def resolve(self, ctx: ExecutionContext, **kwargs: t.Any) -> t.Tuple[t.Dict, t.List]:
        try:
            websocket = ctx.switch_to_websocket()
            return {self.parameter_name: websocket}, []
        except Exception as ex:
            return {}, [ErrorWrapper(ex)]


class ExecutionContextParameter(NonFieldRouteParameterResolver):
    async def resolve(self, ctx: ExecutionContext, **kwargs: t.Any) -> t.Tuple[t.Dict, t.List]:
        return {self.parameter_name: ctx}, []


def req() -> Request:
    return t.cast(Request, RequestParameter())


def ws() -> WebSocket:
    return t.cast(WebSocket, WebSocketParameter())


def cxt() -> ExecutionContext:
    return t.cast(ExecutionContext, ExecutionContextParameter())


def provide(service: t.Optional[t.Type[T]] = None) -> T:
    return t.cast(T, ParameterInjectable(service))




