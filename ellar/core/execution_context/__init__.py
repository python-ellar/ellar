from ellar.common.params import add_default_resolver
from ellar.common.params.resolvers.system_parameters import ExecutionContextParameter

from .execution import ExecutionContext
from .factory import ExecutionContextFactory, HostContextFactory
from .host import HostContext

__all__ = [
    "ExecutionContext",
    "HostContext",
    "ExecutionContextFactory",
    "HostContextFactory",
]

add_default_resolver(ExecutionContext, ExecutionContextParameter)
