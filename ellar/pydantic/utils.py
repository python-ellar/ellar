import typing as t
from collections import deque
from dataclasses import is_dataclass

from pydantic import (
    BaseModel,
    PydanticSchemaGenerationError,
    PydanticUndefinedAnnotation,
    create_model,
)
from pydantic import ValidationError as ValidationError
from pydantic._internal._typing_extra import eval_type_lenient
from pydantic._internal._utils import lenient_issubclass
from pydantic.fields import FieldInfo
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaValue
from starlette.datastructures import UploadFile
from typing_extensions import Annotated, Literal, get_args, get_origin

from .exceptions import InvalidModelFieldSetupException
from .fields import ModelField
from .types import NoneType, Undefined, UnionType

sequence_annotation_to_type = {
    t.Sequence: list,
    t.List: list,
    list: list,
    t.Tuple: tuple,
    tuple: tuple,
    t.Set: set,
    set: set,
    t.FrozenSet: frozenset,
    frozenset: frozenset,
    t.Deque: deque,
    deque: deque,
}

sequence_types = tuple(sequence_annotation_to_type.keys())


evaluate_forwardref = eval_type_lenient


def model_rebuild(model: t.Type[BaseModel]) -> None:
    model.model_rebuild()


def model_dump(
    model: BaseModel, mode: t.Literal["json", "python"] = "json", **kwargs: t.Any
) -> t.Any:
    return model.model_dump(mode=mode, **kwargs)


def get_schema_from_model_field(
    *,
    field: ModelField,
    field_mapping: t.Dict[
        t.Tuple[ModelField, t.Literal["validation", "serialization"]], JsonSchemaValue
    ],
    separate_input_output_schemas: bool = True,
) -> t.Dict[str, t.Any]:
    override_mode: t.Union[t.Literal["validation"], None] = (
        None if separate_input_output_schemas else "validation"
    )
    # This expects that GenerateJsonSchema was already used to generate the definitions
    json_schema = field_mapping[(field, override_mode or field.mode)]
    if "$ref" not in json_schema:
        # TODO remove when deprecating Pydantic v1
        # Ref: https://github.com/pydantic/pydantic/blob/d61792cc42c80b13b23e3ffa74bc37ec7c77f7d1/pydantic/schema.py#L207
        json_schema["title"] = field.field_info.title or field.alias.title().replace(
            "_", " "
        )
    return json_schema


def get_definitions(
    *,
    fields: t.List[ModelField],
    schema_generator: GenerateJsonSchema,
    separate_input_output_schemas: bool = True,
) -> t.Tuple[
    t.Dict[
        t.Tuple[ModelField, t.Literal["validation", "serialization"]], JsonSchemaValue
    ],
    t.Dict[str, t.Dict[str, t.Any]],
]:
    override_mode: t.Union[Literal["validation"], None] = (
        None if separate_input_output_schemas else "validation"
    )
    inputs = [
        (field, override_mode or field.mode, field._type_adapter.core_schema)
        for field in fields
    ]
    field_mapping, definitions = schema_generator.generate_definitions(inputs=inputs)
    return field_mapping, definitions  # type: ignore[return-value]


def is_scalar_field(field: ModelField) -> bool:
    from ellar.common.params.params import BodyFieldInfo, WsBodyFieldInfo

    return (
        field_annotation_is_scalar(field.field_info.annotation)
        and not isinstance(field.field_info, BodyFieldInfo)
        and not isinstance(field.field_info, WsBodyFieldInfo)
    )


def is_sequence_field(field: ModelField) -> bool:
    return annotation_is_sequence(field.field_info.annotation)


def is_scalar_sequence_field(field: ModelField) -> bool:
    return field_annotation_is_scalar_sequence(field.field_info.annotation)


def serialize_sequence_value(*, field: ModelField, value: t.Any) -> t.Sequence[t.Any]:
    origin_type = (
        t.get_origin(field.field_info.annotation) or field.field_info.annotation
    )
    assert issubclass(origin_type, sequence_types)  # type: ignore[arg-type]
    return sequence_annotation_to_type[origin_type](value)  # type: ignore[no-any-return]


def get_missing_field_error(loc: t.Tuple[str, ...]) -> t.Dict[str, t.Any]:
    error = ValidationError.from_exception_data(
        "Field required", [{"type": "missing", "loc": loc, "input": {}}]
    ).errors()[0]
    error["input"] = None
    return error  # type: ignore[return-value]


def create_body_model(
    *, fields: t.Sequence[ModelField], model_name: str
) -> t.Type[BaseModel]:
    field_params = {f.name: (f.field_info.annotation, f.field_info) for f in fields}
    body_model: t.Type[BaseModel] = create_model(  # type: ignore[call-overload]
        model_name, **field_params
    )
    return body_model


def regenerate_error_with_loc(
    *, errors: t.Sequence[t.Any], loc_prefix: t.Tuple[t.Union[str, int], ...]
) -> t.List[t.Dict[str, t.Any]]:
    updated_loc_errors: t.List[t.Any] = [
        {**err, "loc": loc_prefix + err.get("loc", ())} for err in errors
    ]

    return updated_loc_errors


def annotation_is_sequence(annotation: t.Union[t.Type[t.Any], None]) -> bool:
    if lenient_issubclass(annotation, (str, bytes)):
        return False

    origin = get_origin(annotation) or annotation

    if origin is UnionType or origin is t.Union or origin is Annotated:
        return search_in_annotation(
            get_args(annotation),
            sequence_types,
            skip=lambda n: lenient_issubclass(n, (str, bytes)),
        )

    return lenient_issubclass(annotation, sequence_types) or lenient_issubclass(
        origin, sequence_types
    )


def annotation_is_complex(annotation: t.Union[t.Type[t.Any], None]) -> bool:
    return (
        lenient_issubclass(annotation, (BaseModel, t.Mapping, UploadFile))
        or annotation_is_sequence(annotation)
        or is_dataclass(annotation)
    )


def field_annotation_is_complex(annotation: t.Union[t.Type[t.Any], None]) -> bool:
    origin = get_origin(annotation)
    if origin is t.Union or origin is UnionType:
        return any(field_annotation_is_complex(arg) for arg in t.get_args(annotation))

    return (
        annotation_is_complex(annotation)
        or annotation_is_complex(origin)
        or hasattr(origin, "__pydantic_core_schema__")
        or hasattr(origin, "__get_pydantic_core_schema__")
    )


def field_annotation_is_scalar(annotation: t.Any) -> bool:
    # handle Ellipsis here to make tuple[int, ...] work nicely
    return annotation is Ellipsis or not field_annotation_is_complex(annotation)


def field_annotation_is_scalar_sequence(
    annotation: t.Union[t.Type[t.Any], None],
) -> bool:
    origin = get_origin(annotation)
    if origin is t.Union or origin is UnionType:
        at_least_one_scalar_sequence = False
        for arg in get_args(annotation):
            if field_annotation_is_scalar_sequence(arg):
                at_least_one_scalar_sequence = True
                continue
            elif not field_annotation_is_scalar(arg):
                return False
        return at_least_one_scalar_sequence
    return annotation_is_sequence(annotation) and all(
        field_annotation_is_scalar(sub_annotation)
        for sub_annotation in get_args(annotation)
    )


def is_bytes_sequence_annotation(annotation: t.Any) -> bool:
    origin = get_origin(annotation)
    if origin is t.Union or origin is UnionType:
        at_least_one = False
        for arg in get_args(annotation):
            if is_bytes_sequence_annotation(arg):
                at_least_one = True
                break
        return at_least_one
    return annotation_is_sequence(annotation) and all(
        is_bytes_annotation(sub_annotation) for sub_annotation in get_args(annotation)
    )


def is_bytes_annotation(annotation: t.Any) -> bool:
    if lenient_issubclass(annotation, bytes):
        return True
    origin = get_origin(annotation)
    if origin is t.Union or origin is UnionType:
        for arg in get_args(annotation):
            if lenient_issubclass(arg, bytes):
                return True
    return False


def __default_skip__(type_: t.Any) -> bool:
    return False


def search_in_annotation(
    annotations: t.Sequence[t.Any],
    lookup: t.Tuple,
    skip: t.Callable[..., bool] = __default_skip__,
) -> t.Union[bool, t.Any]:
    for item in annotations:
        item_origin = get_origin(item) or item

        if skip(item_origin):
            continue

        if (
            item_origin is UnionType
            or item_origin is t.Union
            or item_origin is Annotated
        ):
            return search_in_annotation(get_args(item), lookup)

        if lenient_issubclass(item_origin, lookup) or lenient_issubclass(item, lookup):
            return True
    return False


def is_field_annotation_nullable(annotation: t.Any) -> bool:
    origin = get_origin(annotation)

    if origin is Annotated or origin is t.Union or origin is UnionType:
        return search_in_annotation(get_args(annotation), (NoneType,))
    return False


def get_sequence_type(annotation: t.Any) -> t.Optional[t.Type]:
    origin = get_origin(annotation) or annotation

    if lenient_issubclass(origin, sequence_types):
        return get_args(annotation)[0]

    if origin is Annotated or origin is t.Union or origin is UnionType:
        for i in get_args(annotation):
            res = get_sequence_type(i)
            if res:
                return res
    return None


def create_model_field(
    name: str,
    type_: t.Type[t.Any],
    default: t.Optional[t.Any] = Undefined,
    field_info: t.Optional[FieldInfo] = None,
    alias: t.Optional[str] = None,
    mode: t.Literal["validation", "serialization"] = "validation",
    model_field_class: t.Type[ModelField] = ModelField,
) -> ModelField:
    """
    Create a new response field. Raises if type_ is invalid.
    """
    field_info = field_info or FieldInfo(annotation=type_, default=default, alias=alias)

    kwargs = {"name": name, "field_info": field_info, "mode": mode}

    try:
        return model_field_class(**kwargs)  # type: ignore[arg-type]
    except (PydanticUndefinedAnnotation, PydanticSchemaGenerationError) as e:
        raise InvalidModelFieldSetupException(
            f"Invalid args for response field! Hint: check that {type_} is a valid pydantic field type"
        ) from e
