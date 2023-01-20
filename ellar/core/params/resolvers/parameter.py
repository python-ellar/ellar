import copy
import email
import json
import typing as t

import anyio
from pydantic.error_wrappers import ErrorWrapper
from pydantic.fields import Undefined
from pydantic.utils import lenient_issubclass
from starlette.datastructures import FormData, Headers, QueryParams
from starlette.exceptions import HTTPException

from ellar.constants import sequence_shape_to_type, sequence_shapes, sequence_types
from ellar.core.context import IExecutionContext
from ellar.core.datastructures import UploadFile
from ellar.core.exceptions import RequestValidationError

from .base import BaseRouteParameterResolver


class HeaderParameterResolver(BaseRouteParameterResolver):
    @classmethod
    def get_received_parameter(
        cls, ctx: IExecutionContext
    ) -> t.Union[QueryParams, Headers]:
        connection = ctx.switch_to_http_connection().get_client()
        return connection.headers

    async def resolve_handle(
        self, ctx: IExecutionContext, *args: t.Any, **kwargs: t.Any
    ) -> t.Tuple:
        received_params = self.get_received_parameter(ctx=ctx)
        if (
            self.model_field.shape in sequence_shapes
            or self.model_field.type_ in sequence_types
        ):
            value = (
                received_params.getlist(self.model_field.alias)
                or self.model_field.default
            )
        else:
            value = received_params.get(self.model_field.alias)
        self.assert_field_info()
        field_info = self.model_field.field_info
        values = {}
        if value is None:
            if self.model_field.required:
                errors = [
                    self.create_error(
                        loc=(field_info.in_.value, self.model_field.alias)
                    )
                ]
                return {}, errors
            else:
                values[self.model_field.name] = copy.deepcopy(self.model_field.default)
                return values, []

        v_, errors_ = self.model_field.validate(
            value, values, loc=(field_info.in_.value, self.model_field.alias)
        )
        return {self.model_field.name: v_}, self.validate_error_sequence(errors_)


class QueryParameterResolver(HeaderParameterResolver):
    @classmethod
    def get_received_parameter(
        cls, ctx: IExecutionContext
    ) -> t.Union[QueryParams, Headers]:
        connection = ctx.switch_to_http_connection().get_client()
        return connection.query_params


class PathParameterResolver(BaseRouteParameterResolver):
    @classmethod
    def get_received_parameter(cls, ctx: IExecutionContext) -> t.Mapping[str, t.Any]:
        connection = ctx.switch_to_http_connection().get_client()
        return connection.path_params

    async def resolve_handle(self, ctx: IExecutionContext, **kwargs: t.Any) -> t.Tuple:
        received_params = self.get_received_parameter(ctx=ctx)
        value = received_params.get(str(self.model_field.alias))
        self.assert_field_info()

        v_, errors_ = self.model_field.validate(
            value,
            {},
            loc=(self.model_field.field_info.in_.value, self.model_field.alias),
        )
        return {self.model_field.name: v_}, self.validate_error_sequence(errors_)


class CookieParameterResolver(PathParameterResolver):
    @classmethod
    def get_received_parameter(cls, ctx: IExecutionContext) -> t.Mapping[str, t.Any]:
        connection = ctx.switch_to_http_connection().get_client()
        return connection.cookies


class WsBodyParameterResolver(BaseRouteParameterResolver):
    async def resolve_handle(
        self, ctx: IExecutionContext, *args: t.Any, body: t.Any, **kwargs: t.Any
    ) -> t.Tuple:
        embed = getattr(self.model_field.field_info, "embed", False)
        received_body = {self.model_field.alias: body}
        loc = ("body",)
        if embed:
            received_body = body
            loc = ("body", self.model_field.alias)  # type:ignore
        try:
            value = received_body.get(self.model_field.alias)
            v_, errors_ = self.model_field.validate(value, {}, loc=loc)
            return {self.model_field.name: v_}, self.validate_error_sequence(errors_)
        except AttributeError:
            errors = [self.create_error(loc=loc)]
            return None, errors


class BodyParameterResolver(WsBodyParameterResolver):
    def __init__(self, *args: t.Any, **kwargs: t.Any):
        super().__init__(*args, **kwargs)

    async def get_request_body(self, ctx: IExecutionContext) -> t.Any:
        try:
            request = ctx.switch_to_http_connection().get_request()
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
        self,
        ctx: IExecutionContext,
        *args: t.Any,
        body: t.Optional[t.Any] = None,
        **kwargs: t.Any,
    ) -> t.Tuple:
        body = body or await self.get_request_body(ctx)
        return await super(BodyParameterResolver, self).resolve_handle(
            ctx, *args, body=body, **kwargs
        )


class FormParameterResolver(BodyParameterResolver):
    async def process_and_validate(
        self, *, values: t.Dict, value: t.Any, loc: t.Tuple
    ) -> t.Tuple:
        v_, errors_ = self.model_field.validate(value, values, loc=loc)
        values[self.model_field.name] = v_
        return values, errors_

    async def get_request_body(self, ctx: IExecutionContext) -> t.Any:
        try:
            request = ctx.switch_to_http_connection().get_request()
            body_bytes = await request.form()
            return body_bytes
        except Exception as e:
            raise HTTPException(
                status_code=400, detail="There was an error parsing the body"
            ) from e

    async def resolve_handle(
        self,
        ctx: IExecutionContext,
        *args: t.Any,
        body: t.Optional[t.Any] = None,
        **kwargs: t.Any,
    ) -> t.Tuple:
        _body = body or await self.get_request_body(ctx)
        embed = getattr(self.model_field.field_info, "embed", False)
        values = {}  # type: ignore
        received_body = {self.model_field.alias: _body}
        loc = ("body",)

        if embed:
            received_body = _body
            loc = ("body", self.model_field.alias)  # type:ignore

        if (
            self.model_field.shape in sequence_shapes
            or self.model_field.type_ in sequence_types
        ) and isinstance(_body, FormData):
            loc = ("body", self.model_field.alias)  # type: ignore
            value = _body.getlist(self.model_field.alias)
        else:
            try:
                value = received_body.get(self.model_field.alias)  # type: ignore
            except AttributeError:
                errors = [self.create_error(loc=loc)]
                return values, errors

        if not value or self.model_field.shape in sequence_shapes and len(value) == 0:
            if self.model_field.required:
                return await self.process_and_validate(
                    values=values, value=_body, loc=loc
                )
            else:
                values[self.model_field.name] = copy.deepcopy(self.model_field.default)
            return values, []

        return await self.process_and_validate(values=values, value=value, loc=loc)


class FileParameterResolver(FormParameterResolver):
    async def process_and_validate(
        self, *, values: t.Dict, value: t.Any, loc: t.Tuple
    ) -> t.Tuple:
        if lenient_issubclass(self.model_field.type_, bytes) and isinstance(
            value, UploadFile
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
        return values, self.validate_error_sequence(errors_)
