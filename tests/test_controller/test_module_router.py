import pytest

from ellar.core.routing import ModuleRouter

from .sample import router

another_router = ModuleRouter("/prefix/another", tag="another_router", name="arouter")


@another_router.get("/sample")
def some_example(self):
    pass


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
    for route in router_instance.routes:
        reversed_path = router_instance.url_path_for(f"{name}:{route.name}")
        assert reversed_path == router_instance.path_format.replace(
            "/{path}", route.path
        )


def test_tag_configuration_module_router():
    new_router = ModuleRouter("/items/{orgID:int}", name="override_name", tag="new_tag")
    assert new_router.get_meta()["tag"] == "new_tag"
    assert new_router.name == "override_name"

    new_router = ModuleRouter("/items/{orgID:int}", name="new_name")
    assert new_router.get_meta()["tag"] == "new_name"
    assert new_router.name == "new_name"

    new_controller = ModuleRouter("/items/{orgID:int}", tag="new_tag")
    assert new_controller.get_meta()["tag"] == "new_tag"
    assert new_controller.name is None

    new_router = ModuleRouter("/items/{orgID:int}")
    assert new_router.get_meta()["tag"] == "Module Router"
    assert new_router.name is None


def test_module_router_url_reverse():
    new_router = ModuleRouter("/items/{orgID:int}", name="has_name")

    @new_router.get
    def some_route():
        pass

    reversed_path = new_router.url_path_for(
        f"{new_router.name}:{new_router.routes[0].name}"
    )
    path = new_router.path_format.replace("/{path}", new_router.routes[0].path)
    assert reversed_path == path
