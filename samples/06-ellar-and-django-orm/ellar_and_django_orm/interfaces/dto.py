import typing as t
from datetime import datetime

import ellar.common as ec


class EventCategoryDTO(ec.Serializer):
    id: int
    name: str


class EventDTO(ec.Serializer):
    id: int
    title: str
    category: t.Optional[EventCategoryDTO]
    start_date: datetime
    end_date: datetime
