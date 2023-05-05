from ellar.common import Controller, ControllerBase, ModuleRouter, get, ws_route


@Controller("/prefix")
class SampleController(ControllerBase):
    @get("/sample")
    def sample_example(self):
        pass

    @ws_route("/sample")
    def sample_example_ws(self):
        pass


router = ModuleRouter("/prefix/router", name="mr")


@router.get("/example")
def example(ctx):
    pass
