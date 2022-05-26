import copy
import email
import inspect
import json
import typing as t
from abc import ABC, ABCMeta, abstractmethod

import anyio
from pydantic.error_wrappers import ErrorWrapper
from pydantic.errors import MissingError
from pydantic.fields import ModelField, Undefined
from pydantic.utils import lenient_issubclass
from starlette.datastructures import FormData, Headers, QueryParams
from starlette.exceptions import HTTPException

from ellar.constants import sequence_shape_to_type, sequence_shapes, sequence_types
from ellar.core.context import IExecutionContext
from ellar.core.datastructures import UploadFile
from ellar.exceptions import RequestValidationError
from ellar.logger import logger
from ellar.types import T

if t.TYPE_CHECKING:  # pragma: no cover
    from .params import Param


class RouteParameterModelField(ModelField):
    field_info: "Param"


class BaseRouteParameterResolver(ABC, metaclass=ABCMeta):
    @abstractmethod
    @t.no_type_check
    async def resolve(self, *args: t.Any, **kwargs: t.Any) -> t.Tuple:
        """Resolve handle"""


class RouteParameterResolver(BaseRouteParameterResolver, ABC):
    def __init__(self, model_field: ModelField, *args: t.Any, **kwargs: t.Any) -> None:
        self.model_field: RouteParameterModelField = t.cast(
            RouteParameterModelField, model_field
        )

    def assert_field_info(self) -> None:
        from . import params

        assert isinstance(
            self.model_field.field_info, params.Param
        ), "Params must be subclasses of Param"

    @classmethod
    def create_error(cls, loc: t.Any) -> ErrorWrapper:
        return ErrorWrapper(MissingError(), loc=loc)

    @classmethod
    def validate_error_sequence(cls, errors: t.Any) -> t.List[ErrorWrapper]:
        if not errors:
            return []
        return list(errors) if isinstance(errors, list) else [errors]

    async def resolve(self, *args: t.Any, **kwargs: t.Any) -> t.Tuple:
        value_ = await self.resolve_handle(*args, **kwargs)
        return value_

    @abstractmethod
    @t.no_type_check
    async def resolve_handle(self, *args: t.Any, **kwargs: t.Any) -> t.Tuple:
        """resolver action"""


class HeaderParameterResolver(RouteParameterResolver):
    @classmethod
    def get_received_parameter(
        cls, ctx: IExecutionContext
    ) -> t.Union[QueryParams, Headers]:
        connection = ctx.switch_to_http_connection()
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
        connection = ctx.switch_to_http_connection()
        return connection.query_params


class PathParameterResolver(RouteParameterResolver):
    @classmethod
    def get_received_parameter(cls, ctx: IExecutionContext) -> t.Mapping[str, t.Any]:
        connection = ctx.switch_to_http_connection()
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
        connection = ctx.switch_to_http_connection()
        return connection.cookies


class WsBodyParameterResolver(RouteParameterResolver):
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
            request = ctx.switch_to_request()
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


class BulkParameterResolver(RouteParameterResolver):
    def __init__(
        self, *args: t.Any, resolvers: t.List[RouteParameterResolver], **kwargs: t.Any
    ):
        super().__init__(*args, **kwargs)
        self._resolvers = resolvers or []

    @property
    def resolvers(self) -> t.List[RouteParameterResolver]:
        return self._resolvers

    def get_model_fields(self) -> t.List[ModelField]:
        return [resolver.model_field for resolver in self._resolvers]

    async def resolve_handle(
        self, ctx: IExecutionContext, *args: t.Any, **kwargs: t.Any
    ) -> t.Tuple:
        values: t.Dict[str, t.Any] = {}
        errors: t.List[ErrorWrapper] = []

        for parameter_resolver in self._resolvers:
            value_, errors_ = await parameter_resolver.resolve(ctx=ctx)
            if value_:
                values.update(value_)
            if errors_:
                errors += self.validate_error_sequence(errors_)
        if errors:
            return values, errors

        v_, errors_ = self.model_field.validate(
            values,
            {},
            loc=(self.model_field.field_info.in_.value, self.model_field.alias),
        )
        if errors_:
            errors += self.validate_error_sequence(errors_)
            return values, errors
        return {self.model_field.name: v_}, []


class BulkFormParameterResolver(FormParameterResolver, BulkParameterResolver):
    async def resolve_handle(
        self, ctx: IExecutionContext, *args: t.Any, **kwargs: t.Any
    ) -> t.Tuple:
        _body = await self.get_request_body(ctx)
        values: t.Dict[str, t.Any] = {}
        errors: t.List[ErrorWrapper] = []
        if self._resolvers:
            for parameter_resolver in self._resolvers:
                value_, errors_ = await parameter_resolver.resolve(ctx=ctx, body=_body)
                if value_:
                    values.update(value_)
                if errors_:
                    errors += self.validate_error_sequence(errors_)
            return values, errors
        return await super(BulkFormParameterResolver, self).resolve_handle(
            ctx, *args, **kwargs
        )


class BulkBodyParameterResolver(BodyParameterResolver, BulkParameterResolver):
    async def resolve_handle(
        self, ctx: IExecutionContext, *args: t.Any, **kwargs: t.Any
    ) -> t.Tuple:
        _body = await self.get_request_body(ctx)
        values, errors = await super(BulkBodyParameterResolver, self).resolve_handle(
            ctx, *args, body=_body, **kwargs
        )
        if not errors:
            _, body_value = values.popitem()
            return body_value.dict(), []
        return values, self.validate_error_sequence(errors)


class NonFieldRouteParameterResolver(BaseRouteParameterResolver, ABC):
    in_: str = "non_field_parameter"

    def __init__(self, data: t.Optional[t.Any] = None):
        self.data = data
        self.parameter_name: t.Optional[str] = None
        self.type_annotation: t.Optional[t.Type] = None

    def __call__(self, parameter_name: str, parameter_annotation: t.Type[T]) -> t.Any:
        self.parameter_name = parameter_name
        self.type_annotation = parameter_annotation
        return self

    async def resolve(self, ctx: IExecutionContext, **kwargs: t.Any) -> t.Any:
        raise NotImplementedError


class ParameterInjectable(NonFieldRouteParameterResolver):
    def __init__(self, service: t.Optional[t.Type[T]] = None) -> None:
        if service:
            assert isinstance(service, type), "Service must be a type"
        super().__init__(data=service)

    def __call__(
        self, parameter_name: str, parameter_annotation: t.Type[T]
    ) -> "ParameterInjectable":
        self.parameter_name = parameter_name
        self.type_annotation = parameter_annotation
        if not self.data and isinstance(self.type_annotation, inspect.Parameter.empty):
            raise Exception("Injectable must have a valid type")

        if (
            self.data
            and parameter_annotation is not inspect.Parameter.empty
            and parameter_annotation is not self.data
        ):
            raise Exception(
                f"Annotation({self.type_annotation}) is not the same as service({self.data})"
            )

        if not self.data:
            self.data = self.type_annotation
        return self

    async def resolve(
        self, ctx: IExecutionContext, **kwargs: t.Any
    ) -> t.Tuple[t.Dict, t.List]:
        try:
            service_provider = ctx.get_service_provider()
            if not self.data:
                raise Exception("ParameterInjectable not properly setup")
            value = service_provider.get(self.data)
            return {self.parameter_name: value}, []
        except Exception as ex:
            logger.error(f"Unable to resolve service {self.data} \nErrorMessage: {ex}")
            return {}, [ErrorWrapper(ex, loc=self.parameter_name or "provide")]
