"""
@Module(
    controllers=[MyController],
    providers=[
        YourService,
        ProviderConfig(IService, use_class=AService),
        ProviderConfig(IFoo, use_value=FooService()),
    ],
    routers=(routerA, routerB)
    statics='statics',
    template='template_folder',
    # base_directory -> default is the `events` folder
)
class MyModule(ModuleBase):
    def register_providers(self, container: Container) -> None:
        # for more complicated provider registrations
        pass

"""
from ellar.common import Module
from ellar.core import ModuleBase
from ellar.di import Container

from .controllers import EventsController
from .gateways import EventsGateway


@Module(
    controllers=[EventsController, EventsGateway],
    providers=[],
    routers=[],
)
class EventsModule(ModuleBase):
    """
    Events Module
    """

    def register_providers(self, container: Container) -> None:
        """for more complicated provider registrations, use container.register_instance(...)"""
