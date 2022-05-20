from dataclasses import dataclass
from typing import Optional, Union

from pydantic import BaseModel


class BlogObjectDTO:
    title: str
    author: str


@dataclass
class NoteSchemaDC:
    id: Union[int, None]
    text: str
    completed: bool


class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None


class User(BaseModel):
    username: str
    full_name: Optional[str] = None
