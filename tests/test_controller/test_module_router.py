import pytest
from ellar.common import ModuleRouter
from ellar.core.router_builders import ModuleRouterBuilder

from .sample import router

another_router = ModuleRouter("/prefix/another", name="arouter")


@another_router.get("/sample")
def some_example():
    return {"message": "okay"}


@another_router.get("/sample")
def some_example_3():
    # some_example_3 overrides `sample_example` OPERATION since its the same 'path' and 'method'
    pass


@another_router.http_route("/sample", methods=["get"])
def some_example_4():
    # some_example_4 overrides `sample_example_3` OPERATION since its the same 'path' and 'method'
    pass


@another_router.http_route("/sample", methods=["get", "post"])
def some_example_5():
    # `sample_example_4 - get` overrides `sample_example_5 - get` RUNTIME CALL in that order
    # And '/sample' POST call will be handled here
    pass


@another_router.ws_route("/sample")
def some_example_ws():
    pass


@another_router.ws_route("/sample")
def some_example_ws_2():
    # `some_example_ws_2` overrides `some_example_ws` OPERATION
    pass


@pytest.mark.parametrize(
    "router_instance, prefix, tag, name",
    [
        (router, "/prefix", "mr", "mr"),
        (another_router, "/prefix/another", "another_router", "arouter"),
    ],
)
def test_build_routes(router_instance, prefix, tag, name):
    mount = ModuleRouterBuilder.build(router_instance)
    for route in mount.routes:
        reversed_path = mount.url_path_for(f"{name}:{route.name}")
        assert reversed_path == mount.path_format.replace("/{path}", route.path)


def test_module_router_url_reverse():
    new_router = ModuleRouter("/items/{orgID:int}", name="has_name")

    @new_router.get
    def some_route():
        pass

    mount = ModuleRouterBuilder.build(new_router)

    reversed_path = mount.url_path_for(f"{mount.name}:{mount.routes[0].name}")
    path = mount.path_format.replace("/{path}", mount.routes[0].path)
    assert reversed_path == path
