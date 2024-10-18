import copy
import email.message
import json
import typing as t

import anyio
from ellar.common.constants import (
    sequence_types,
)
from ellar.common.exceptions import RequestValidationError
from ellar.common.interfaces import IExecutionContext
from ellar.common.logging import request_logger
from ellar.pydantic import (
    is_sequence_field,
    lenient_issubclass,
)
from ellar.pydantic import (
    types as pydantic_types,
)
from ellar.pydantic.utils import (
    is_bytes_sequence_annotation,
    serialize_sequence_value,
)
from starlette.datastructures import (
    FormData,
    Headers,
    QueryParams,
)
from starlette.datastructures import (
    UploadFile as StarletteUploadFile,
)
from starlette.exceptions import HTTPException

from .base import BaseRouteParameterResolver, ResolverResult


class HeaderParameterResolver(BaseRouteParameterResolver):
    @classmethod
    def get_received_parameter(
        cls, ctx: IExecutionContext
    ) -> t.Union[QueryParams, Headers]:
        connection = ctx.switch_to_http_connection().get_client()
        return connection.headers

    async def resolve_handle(
        self,
        ctx: IExecutionContext,
        *args: t.Any,
        alias: t.Optional[str] = None,
        name: t.Optional[str] = None,
        **kwargs: t.Any,
    ) -> ResolverResult:
        alias = alias or self.model_field.alias
        name = name or self.model_field.name
        request_logger.debug(
            f"Resolving Header Parameters - '{self.__class__.__name__}'"
        )
        received_params = self.get_received_parameter(ctx=ctx)
        if is_sequence_field(self.model_field):
            value = received_params.getlist(alias) or self.model_field.default
        else:
            value = received_params.get(alias)
        self.assert_field_info()
        field_info = self.model_field.field_info
        values = {}
        if value is None:
            if self.model_field.required:
                errors = [self.create_error(loc=(field_info.in_.value, alias))]
                return ResolverResult(
                    {}, errors, raw_data=self.create_raw_data(value, field_name=name)
                )
            else:
                value = copy.deepcopy(self.model_field.default)
                values[name] = value
                return ResolverResult(
                    values, [], raw_data=self.create_raw_data(value, field_name=name)
                )

        v_, errors_ = self.model_field.validate(
            value, values, loc=(field_info.in_.value, alias)
        )

        return ResolverResult(
            data={name: v_},
            errors=self.validate_error_sequence(errors_),
            raw_data=self.create_raw_data(value, field_name=name),
        )


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

    async def resolve_handle(
        self,
        ctx: IExecutionContext,
        alias: t.Optional[str] = None,
        name: t.Optional[str] = None,
        **kwargs: t.Any,
    ) -> ResolverResult:
        alias = alias or self.model_field.alias
        name = name or self.model_field.name
        request_logger.debug(f"Resolving Path Parameters - '{self.__class__.__name__}'")
        received_params = self.get_received_parameter(ctx=ctx)
        value = received_params.get(str(alias))
        self.assert_field_info()

        v_, errors_ = self.model_field.validate(
            value,
            {},
            loc=(self.model_field.field_info.in_.value, alias),
        )
        return ResolverResult(
            data={name: v_},
            errors=self.validate_error_sequence(errors_),
            raw_data=self.create_raw_data(value, field_name=name),
        )


class CookieParameterResolver(PathParameterResolver):
    @classmethod
    def get_received_parameter(cls, ctx: IExecutionContext) -> t.Mapping[str, t.Any]:
        connection = ctx.switch_to_http_connection().get_client()
        return connection.cookies


class WsBodyParameterResolver(BaseRouteParameterResolver):
    async def resolve_handle(
        self,
        ctx: IExecutionContext,
        *args: t.Any,
        body: t.Any,
        alias: t.Optional[str] = None,
        name: t.Optional[str] = None,
        **kwargs: t.Any,
    ) -> t.Tuple:
        alias = alias or self.model_field.alias
        name = name or self.model_field.name
        request_logger.debug(
            f"Resolving Websocket Body Parameters - '{self.__class__.__name__}'"
        )
        embed = getattr(self.model_field.field_info, "embed", False)
        received_body = {alias: body}
        loc = ("body",)
        if embed:
            received_body = body
            loc = ("body", alias)  # type:ignore
        try:
            value = received_body.get(alias)

            if value is None:
                if self.model_field.required:
                    return ResolverResult(
                        None,
                        [self.create_error(loc=loc)],
                        raw_data=self.create_raw_data(value, field_name=name),
                    )
                else:
                    value = copy.deepcopy(self.model_field.default)
                    return ResolverResult(
                        {name: value},
                        [],
                        raw_data=self.create_raw_data(value, field_name=name),
                    )

            v_, errors_ = self.model_field.validate(value, {}, loc=loc)
            return ResolverResult(
                data={name: v_},
                errors=self.validate_error_sequence(errors_),
                raw_data=self.create_raw_data(value, field_name=name),
            )
        except AttributeError:
            errors = [self.create_error(loc=loc)]
            return ResolverResult(
                None, errors, raw_data=self.create_raw_data(None, field_name=name)
            )


class BodyParameterResolver(WsBodyParameterResolver):
    def __init__(self, *args: t.Any, **kwargs: t.Any):
        super().__init__(*args, **kwargs)

    async def get_request_body(self, ctx: IExecutionContext) -> t.Any:
        request_logger.debug(
            f"Resolving Request Body Parameters - '{self.__class__.__name__}'"
        )
        try:
            request = ctx.switch_to_http_connection().get_request()
            body_bytes = await request.body()
            if body_bytes:
                json_body: t.Any = pydantic_types.Undefined
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
                if json_body != pydantic_types.Undefined:
                    body_bytes = json_body
            return body_bytes
        except json.JSONDecodeError as e:
            request_logger.error("JSONDecodeError: ", exc_info=True)
            raise RequestValidationError(
                [
                    {
                        "type": "json_invalid",
                        "loc": ("body", e.pos),
                        "msg": "JSON decode error",
                        "input": {},
                        "ctx": {"error": e.msg},
                    }
                ],
                body=e.doc,
            ) from e
        except Exception as e:
            request_logger.error("Unable to parse the body: ", exc_info=e)
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
        self, *, values: t.Dict, value: t.Any, loc: t.Tuple, field_name: str
    ) -> t.Tuple:
        v_, errors_ = self.model_field.validate(value, values, loc=loc)
        values[field_name] = v_
        return ResolverResult(
            data=values,
            errors=self.validate_error_sequence(errors_),
            raw_data=self.create_raw_data(value),
        )

    async def get_request_body(self, ctx: IExecutionContext) -> t.Any:
        request_logger.debug(
            f"Resolving Request Form Parameters - '{self.__class__.__name__}'"
        )
        try:
            request = ctx.switch_to_http_connection().get_request()
            body_bytes = await request.form()
            return body_bytes
        except Exception as e:
            request_logger.error("Unable to parse the body: ", exc_info=True)
            raise HTTPException(
                status_code=400, detail="There was an error parsing the body"
            ) from e

    async def resolve_handle(
        self,
        ctx: IExecutionContext,
        *args: t.Any,
        body: t.Optional[t.Any] = None,
        alias: t.Optional[str] = None,
        name: t.Optional[str] = None,
        **kwargs: t.Any,
    ) -> t.Tuple:
        alias = alias or self.model_field.alias
        name = name or self.model_field.name
        _body = body or await self.get_request_body(ctx)
        embed = getattr(self.model_field.field_info, "embed", False)
        received_body = {alias: _body}
        loc = ("body",)

        if embed:
            received_body = _body
            loc = ("body", alias)  # type:ignore

        if is_sequence_field(self.model_field) and isinstance(_body, FormData):
            loc = ("body", alias)  # type: ignore
            value = _body.getlist(alias)
        else:
            value = received_body.get(alias)  # type: ignore

        if (
            value is None
            or value == ""
            or (is_sequence_field(self.model_field) and len(value) == 0)
        ):
            if self.model_field.required:
                return ResolverResult(
                    None,
                    [self.create_error(loc=loc)],
                    self.create_raw_data(value, field_name=name),
                )
            else:
                value = copy.deepcopy(self.model_field.default)
                return ResolverResult(
                    {name: value},
                    [],
                    raw_data=self.create_raw_data(value, field_name=name),
                )

        return await self.process_and_validate(
            values={}, value=value, loc=loc, field_name=name
        )


class FileParameterResolver(FormParameterResolver):
    def __init__(self, *args: t.Any, **kwargs: t.Any):
        super().__init__(*args, **kwargs)
        self._is_byte = lenient_issubclass(self.model_field.type_, bytes)
        self._is_list = is_sequence_field(self.model_field)
        self._is_byte_list = is_bytes_sequence_annotation(self.model_field.type_)

    async def process_and_validate(
        self, *, values: t.Dict, value: t.Any, loc: t.Tuple, field_name: str
    ) -> t.Tuple:
        if self._is_byte and isinstance(value, StarletteUploadFile):
            value = await value.read()
        elif self._is_list and self._is_byte_list and isinstance(value, sequence_types):
            results: t.List[t.Union[bytes, str]] = []

            async def process_fn(
                fn: t.Callable[[], t.Coroutine[t.Any, t.Any, t.Any]],
            ) -> None:
                result = await fn()
                results.append(result)

            async with anyio.create_task_group() as tg:
                for sub_value in value:
                    tg.start_soon(process_fn, sub_value.read)
            value = serialize_sequence_value(field=self.model_field, value=results)

        v_, errors_ = self.model_field.validate(value, values, loc=loc)
        values[field_name] = v_

        return ResolverResult(
            data=values,
            errors=self.validate_error_sequence(errors_),
            raw_data=self.create_raw_data(value, field_name=field_name),
        )
