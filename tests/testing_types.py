from dataclasses import dataclass
from typing import Union


class BlogObjectDTO:
    title: str
    author: str


@dataclass
class NoteSchemaDC:
    id: Union[int, None]
    text: str
    completed: bool
