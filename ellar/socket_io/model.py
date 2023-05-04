from .context import GatewayContext


class GatewayType(type):
    pass


class GatewayBase(metaclass=GatewayType):
    context: GatewayContext
