import os

from ellar.core.middleware import FunctionBasedMiddleware
from ellar.core.routing import ASGIFileMount
from ellar.testing import Test, TestClient
from starlette.middleware import Middleware


def test_app_create_static_app(tmpdir):
    path = os.path.join(tmpdir, "example.txt")
    with open(path, "w") as file:
        file.write("<file content>")

    app = Test.create_test_module(
        config_module={"STATIC_DIRECTORIES": [tmpdir]}
    ).create_application()
    client = TestClient(app)

    res = client.get("/static/example.txt")
    assert res.status_code == 200
    assert res.text == "<file content>"


def test_app_reload_static_app(tmpdir, test_client_factory):
    os.mkdir(tmpdir / "statics")
    path = os.path.join(tmpdir, "statics", "example.txt")

    with open(path, "w") as file:
        file.write("<file content>")

    app = Test.create_test_module(
        config_module={"STATIC_DIRECTORIES": [tmpdir]}
    ).create_application()
    client = test_client_factory(app)

    res = client.get("/static/example.txt")
    assert res.status_code == 404

    app = Test.create_test_module(
        config_module={"STATIC_DIRECTORIES": [tmpdir]}
    ).create_application()
    client = test_client_factory(app)

    app.config.STATIC_DIRECTORIES = [tmpdir, tmpdir / "statics"]
    # app.rebuild_stack()

    res = client.get("/static/example.txt")
    assert res.status_code == 200
    assert res.text == "<file content>"


def test_can_mount_file_as_media(tmpdir):
    os.mkdir(tmpdir / "media")
    path = os.path.join(tmpdir, "media", "example.txt")
    with open(path, "w") as file:
        file.write("<file content>")

    tm = Test.create_test_module(
        routers=[
            ASGIFileMount(directories=[tmpdir / "media"], path="/media", name="media")
        ]
    )
    client = tm.get_test_client()

    res = client.get("/media/example.txt")
    assert res.status_code == 200
    assert res.text == "<file content>"


def test_can_mount_folders_at_parent_director():
    file_mount = ASGIFileMount(
        directories=["private"],
        path="/media",
        name="media",
        base_directory="__main__",
    )
    assert file_mount.routes == []

    tm = Test.create_test_module(routers=[file_mount])

    client = tm.get_test_client()

    res = client.get("/media/test.css")
    assert res.status_code == 200
    assert res.text == ".div {background: red}\n"


def test_file_mount_with_middleware():
    middleware_called = False

    async def asgi_middleware(execution_context, call_next):
        nonlocal middleware_called
        middleware_called = True
        await call_next()

    tm = Test.create_test_module(
        routers=[
            ASGIFileMount(
                directories=["private"],
                path="/media",
                name="media",
                base_directory="__main__",
                middleware=[
                    Middleware(FunctionBasedMiddleware, dispatch=asgi_middleware)
                ],
            )
        ]
    )
    client = tm.get_test_client()
    res = client.get("/media/test.css")

    assert res.status_code == 200
    assert res.text == ".div {background: red}\n"

    assert middleware_called is True
