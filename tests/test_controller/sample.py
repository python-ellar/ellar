from ellar.common import Controller, Get, WsRoute
from ellar.core import ControllerBase
from ellar.core.routing import ModuleRouter


@Controller("/prefix")
class SampleController(ControllerBase):
    @Get("/sample")
    def sample_example(self):
        pass

    @WsRoute("/sample")
    def sample_example_ws(self):
        pass


router = ModuleRouter("/prefix/router", name="mr")


@router.Get("/example")
def example(ctx):
    pass
