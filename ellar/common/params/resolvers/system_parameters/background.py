import typing as t

from ellar.common.interfaces import IExecutionContext
from starlette.background import BackgroundTask, BackgroundTasks

from .base import SystemParameterResolver


class BackgroundTasksParameter(SystemParameterResolver):
    async def resolve(
        self, ctx: IExecutionContext, **kwargs: t.Any
    ) -> t.Tuple[t.Dict, t.List]:
        res = ctx.switch_to_http_connection().get_response()

        if res.background and isinstance(
            res.background, BackgroundTasks
        ):  # pragma: no cover
            return {self.parameter_name: res.background}, []

        background_tasks = BackgroundTasks()

        if res.background and isinstance(res.background, BackgroundTask):
            background_tasks.add_task(res.background.func)

        res.background = background_tasks

        return {self.parameter_name: res.background}, []
