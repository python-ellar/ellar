import typing as t

from pydantic import BaseModel, Field


class ValidationError(BaseModel):
    loc: t.List[str] = Field(..., title="Location")
    msg: str = Field(..., title="Message")
    type: str = Field(..., title="Error Type")


class HTTPValidationError(BaseModel):
    detail: t.List[ValidationError] = Field(..., title="Details")
