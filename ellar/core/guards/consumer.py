import typing as t

from ellar.common import IExecutionContext, IGuardsConsumer
from ellar.common.constants import GUARDS_KEY
from ellar.di import EllarInjector, injectable

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.common import GuardCanActivate
    from ellar.common.routing import RouteOperationBase


@injectable
class GuardConsumer(IGuardsConsumer):
    def __init__(self, injector: EllarInjector) -> None:
        self.injector = injector

    async def execute(
        self, context: IExecutionContext, route_operation: "RouteOperationBase"
    ) -> None:
        await self.run_route_guards(context)

    @t.no_type_check
    async def run_route_guards(self, context: IExecutionContext) -> None:

        for guard in self._get_guards(context):
            await self.run_guard(context, guard)

    async def run_guard(
        self, context: IExecutionContext, guard_instance: "GuardCanActivate"
    ) -> None:
        result = await guard_instance.can_activate(context)
        if not result:
            guard_instance.raise_exception()

    def _get_guards(self, context: IExecutionContext) -> t.Iterable["GuardCanActivate"]:
        app = context.get_app()
        reflector = app.reflector

        targets = [context.get_handler(), context.get_class()]

        return map(
            self.get_guard_instance,
            reflector.get_all_and_override(GUARDS_KEY, *targets)
            or context.get_app().get_guards(),
        )

    def get_guard_instance(
        self, guard: t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]
    ) -> "GuardCanActivate":
        if isinstance(guard, type):
            return self.injector.get(guard)  # type: ignore[no-any-return]
        return guard
