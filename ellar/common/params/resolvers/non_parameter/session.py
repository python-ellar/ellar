import typing as t

from ellar.common.interfaces import IExecutionContext

from .base import BaseConnectionParameterResolver


class HostRequestParam(BaseConnectionParameterResolver):
    lookup_connection_field = None

    async def get_value(self, ctx: IExecutionContext) -> t.Any:
        connection = ctx.switch_to_http_connection().get_client()
        if connection.client:
            return connection.client.host


class SessionRequestParam(BaseConnectionParameterResolver):
    lookup_connection_field = "session"
