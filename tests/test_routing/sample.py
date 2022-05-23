from datetime import datetime
from enum import IntEnum
from typing import Optional

from pydantic import Field

from ellar.core.schema import Schema


class Product(Schema):
    name: str
    description: str = None  # type: ignore
    price: float


class Item(Schema):
    name: Optional[str] = None


class OtherItem(Schema):
    price: int


class Range(IntEnum):
    TWENTY = 20
    FIFTY = 50
    TWO_HUNDRED = 200


class Filter(Schema):
    to_datetime: datetime = Field(alias="to")
    from_datetime: datetime = Field(alias="from")
    range: Range = Range.TWENTY


class Data(Schema):
    an_int: int = Field(alias="int", default=0)
    a_float: float = Field(alias="float", default=1.5)
