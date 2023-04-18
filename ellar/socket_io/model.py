import typing as t

from engineio import AsyncServer

if t.TYPE_CHECKING:
    from ellar.core import IExecutionContext


class GatewayType(type):
    pass


class GatewayContext(t.NamedTuple):
    server: AsyncServer
    sid: str
    message: t.Any
    context: "IExecutionContext"
    environment: t.Dict


class GatewayBase(metaclass=GatewayType):
    context: GatewayContext
