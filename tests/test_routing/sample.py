from datetime import datetime
from enum import IntEnum
from typing import List, Optional

from ellar.common.serializer import Serializer
from pydantic import Field


class Product(Serializer):
    name: str
    description: str = None  # type: ignore
    price: float


class Item(Serializer):
    name: Optional[str] = None


class OtherItem(Serializer):
    price: int


class Range(IntEnum):
    TWENTY = 20
    FIFTY = 50
    TWO_HUNDRED = 200


class Filter(Serializer):
    to_datetime: datetime = Field(alias="to")
    from_datetime: datetime = Field(alias="from")
    range: Range = Range.TWENTY


class Data(Serializer):
    an_int: int = Field(alias="int", default=0)
    a_float: float = Field(alias="float", default=1.5)


class NonPrimitiveSchema(Serializer):
    # The schema can only work for Body
    # And will fail for Path, Cookie, Query, Header, Form
    filter: Filter


class ListOfPrimitiveSchema(Serializer):
    # The schema can only work for Body, Query, Header and Form
    # And will fail for Path, Cookie
    an_int: List[int] = Field(alias="int")
    a_float: List[float] = Field(alias="float")
