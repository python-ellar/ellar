from ellar.common.params.args import add_default_resolver
from ellar.common.params.resolvers.non_parameter import ExecutionContextParameter

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
