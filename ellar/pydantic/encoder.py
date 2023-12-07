import datetime
import typing as t
from collections import defaultdict, deque
from decimal import Decimal
from enum import Enum
from ipaddress import (
    IPv4Address,
    IPv4Interface,
    IPv4Network,
    IPv6Address,
    IPv6Interface,
    IPv6Network,
)
from pathlib import Path
from re import Pattern
from types import GeneratorType
from uuid import UUID

from pydantic.color import Color
from pydantic.networks import AnyUrl, NameEmail
from pydantic.types import SecretBytes, SecretStr

ENCODERS_BY_TYPE: t.Dict[t.Type[t.Any], t.Callable[[t.Any], t.Any]] = {
    bytes: lambda o: o.decode(),
    Color: str,
    datetime.date: lambda o: o.isoformat(),
    datetime.datetime: lambda o: o.isoformat(),
    datetime.time: lambda o: o.isoformat(),
    datetime.timedelta: lambda td: td.total_seconds(),
    Decimal: lambda o: int(o) if o.as_tuple().exponent >= 0 else float(o),
    Enum: lambda o: o.value,
    frozenset: list,
    deque: list,
    GeneratorType: list,
    IPv4Address: str,
    IPv4Interface: str,
    IPv4Network: str,
    IPv6Address: str,
    IPv6Interface: str,
    IPv6Network: str,
    NameEmail: str,
    Path: str,
    Pattern: lambda o: o.pattern,
    SecretBytes: str,
    SecretStr: str,
    set: list,
    UUID: str,
    # Url: str,
    AnyUrl: str,
}


def generate_encoders_by_class_tuples(
    type_encoder_map: t.Dict[t.Any, t.Callable[[t.Any], t.Any]],
) -> t.Dict[t.Callable[[t.Any], t.Any], t.Tuple[t.Any, ...]]:
    encoders_by_class_tuples: t.Dict[
        t.Callable[[t.Any], t.Any], t.Tuple[t.Any, ...]
    ] = defaultdict(tuple)
    for type_, encoder in type_encoder_map.items():
        encoders_by_class_tuples[encoder] += (type_,)
    return encoders_by_class_tuples


encoders_by_class_tuples = generate_encoders_by_class_tuples(ENCODERS_BY_TYPE)
