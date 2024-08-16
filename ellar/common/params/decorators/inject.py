import typing as t

from ellar.common.interfaces import IExecutionContext
from starlette.background import BackgroundTasks
from starlette.responses import Response
from typing_extensions import Annotated

from ..resolvers import (
    SystemParameterResolver,
)
from ..resolvers.system_parameters import (
    BackgroundTasksParameter,
    ExecutionContextParameter,
    HostRequestParam,
    ProviderParameterInjector,
    ResponseRequestParam,
    SessionRequestParam,
)

_DEFAULT_RESOLVERS: t.Dict[t.Union[t.Type, str], t.Type[SystemParameterResolver]] = {
    Response: ResponseRequestParam,
    IExecutionContext: ExecutionContextParameter,
    BackgroundTasks: BackgroundTasksParameter,
    "Session": SessionRequestParam,
    "Host": HostRequestParam,
}


def add_default_resolver(
    type_identifier: t.Union[t.Type, str],
    resolver_type: t.Type[SystemParameterResolver],
) -> None:  # pragma: no cover
    _DEFAULT_RESOLVERS.update({type_identifier: resolver_type})


def get_default_resolver(
    type_identifier: t.Union[t.Type, str],
) -> t.Optional[t.Type[SystemParameterResolver]]:
    return _DEFAULT_RESOLVERS.get(type_identifier)


class InjectShortcut:
    def Key(self, key: str) -> str:
        return key

    def __getitem__(self, args: t.Union[t.Any, t.Tuple[t.Type, str]]) -> t.Any:
        if isinstance(args, tuple):
            base_type, _str_default_resolve = args
            default_resolver = _DEFAULT_RESOLVERS.get(_str_default_resolve)
        else:
            if isinstance(args, str):
                # annotation = t.ForwardRef(args)
                # annotation = t.evaluate_forwardref(annotation, globals(), globals())
                args = globals().get(args, args)
            base_type = args
            default_resolver = _DEFAULT_RESOLVERS.get(base_type)

        if not default_resolver:
            default_resolver = ProviderParameterInjector

        return Annotated[base_type, default_resolver()]
