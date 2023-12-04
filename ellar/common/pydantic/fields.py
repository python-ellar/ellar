import typing as t
from dataclasses import dataclass

from pydantic import TypeAdapter
from pydantic import ValidationError as ValidationError
from pydantic._internal._schema_generation_shared import (  # type: ignore[attr-defined]
    GetJsonSchemaHandler as GetJsonSchemaHandler,
)
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined
from typing_extensions import Annotated, Literal

from .types import IncEx


@dataclass
class ModelField:
    field_info: FieldInfo
    name: str
    mode: Literal["validation", "serialization"] = "validation"

    @property
    def alias(self) -> str:
        a = self._alias_by_mode or self.field_info.alias
        return a if a is not None else self.name

    @property
    def required(self) -> bool:
        return self.field_info.is_required()

    @property
    def default(self) -> t.Any:
        return self.get_default()

    @property
    def type_(self) -> t.Any:
        return self.field_info.annotation

    def __post_init__(self) -> None:
        self._alias_by_mode = getattr(self.field_info, f"{self.mode}_alias", None)
        self._type_adapter: TypeAdapter[t.Any] = TypeAdapter(
            Annotated[self.field_info.annotation, self.field_info]
        )

    def get_default(self) -> t.Any:
        if self.field_info.is_required():
            return PydanticUndefined  # pragma: no cover
        return self.field_info.get_default(call_default_factory=True)

    def validate(
        self,
        value: t.Any,
        values: t.Dict[str, t.Any] = {},
        *,
        loc: t.Tuple[t.Union[int, str], ...] = (),
    ) -> t.Tuple[t.Any, t.Union[t.List[t.Dict[str, t.Any]], None]]:
        try:
            return (
                self._type_adapter.validate_python(
                    value, from_attributes=True, context=values
                ),
                None,
            )
        except ValidationError as exc:
            updated_loc_errors: t.List[t.Any] = [
                {**err, "loc": loc + err.get("loc", ())} for err in exc.errors()
            ]
            return None, updated_loc_errors

    def serialize(
        self,
        value: t.Any,
        *,
        mode: Literal["json", "python"] = "json",
        include: t.Union[IncEx, None] = None,
        exclude: t.Union[IncEx, None] = None,
        by_alias: bool = True,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> t.Any:
        return self._type_adapter.dump_python(
            value,
            mode=mode,
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )

    def __hash__(self) -> int:
        return id(self)
