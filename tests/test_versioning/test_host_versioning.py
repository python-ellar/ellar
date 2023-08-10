import pytest
from ellar.common.constants import NOT_SET
from ellar.core.versioning import VersioningSchemes as VERSIONING
from ellar.testing import Test

from .operations import mr

tm = Test.create_test_module(routers=(mr,))
app = tm.create_application()
app.enable_versioning(VERSIONING.HOST, version_parameter="v")


@pytest.mark.parametrize(
    "path, host, expected_result",
    [
        ("/version", "testserver.org", {"version": "default"}),
        ("/version", "v1.testserver.org", {"version": "v1"}),
        ("/version", "v2.testserver.org", {"version": "v2"}),
        ("/version", "v3.testserver.org", {"version": "v3"}),
    ],
)
def test_host_route_versioning(path, host, expected_result):
    client = tm.get_test_client(base_url=f"http://{host}")
    response = client.get(path)
    assert response.status_code == 200
    assert response.json() == expected_result


@pytest.mark.parametrize(
    "path, host, default, expected_result",
    [
        # default is 1
        ("/version", "testserver.org", "1", {"version": "default"}),
        ("/version", "v1.testserver.org", "1", {"version": "default"}),
        ("/version", "v2.testserver.org", "1", {"version": "v2"}),
        ("/version", "v3.testserver.org", "1", {"version": "v3"}),
        # default is 2
        ("/version", "testserver.org", "2", {"version": "default"}),
        ("/version", "v1.testserver.org", "2", {"version": "v1"}),
        ("/version", "v2.testserver.org", "2", {"version": "default"}),
        ("/version", "v3.testserver.org", "2", {"version": "v3"}),
        # default is 3
        ("/version", "testserver.org", "3", {"version": "default"}),
        ("/version", "v1.testserver.org", "3", {"version": "v1"}),
        ("/version", "v2.testserver.org", "3", {"version": "v2"}),
        ("/version", "v3.testserver.org", "3", {"version": "default"}),
        # default is None or NOT_SET
        ("/version", "testserver.org", NOT_SET, {"version": "default"}),
        ("/version", "v1.testserver.org", NOT_SET, {"version": "v1"}),
        ("/version", "v2.testserver.org", NOT_SET, {"version": "v2"}),
        ("/version", "v3.testserver.org", NOT_SET, {"version": "v3"}),
    ],
)
def test_host_route_versioning_with_default_version(
    path, host, default, expected_result
):
    app.enable_versioning(VERSIONING.HOST, default_version=default)
    client = tm.get_test_client(base_url=f"http://{host}")
    response = client.get(path)
    assert response.status_code == 200
    assert response.json() == expected_result


@pytest.mark.parametrize(
    "host, version_parameter",
    [
        ("http://b1.testserver.org", "v"),
        ("http://b2.testserver.org", "v"),
        ("http://b3.testserver.org", "v"),
        ("http://b4.testserver.org", "v"),
        ("http://b4.testserver.org", "b"),
    ],
)
def test_host_route_versioning_not_found(host, version_parameter):
    app.enable_versioning(VERSIONING.HOST, version_parameter=version_parameter)
    client = tm.get_test_client(base_url=host)

    response = client.get("/version")
    assert response.status_code == 404
    assert response.json() == {"detail": "Invalid version in hostname."}


@pytest.mark.parametrize(
    "host, version_parameter, expected_result",
    [
        ("http://b1.testserver.org", "b", {"version": "v1"}),
        ("http://b2.testserver.org", "b", {"version": "v2"}),
        ("http://b3.testserver.org", "b", {"version": "v3"}),
    ],
)
def test_host_route_versioning_different_version_parameter(
    host, version_parameter, expected_result
):
    app.enable_versioning(VERSIONING.HOST, version_parameter=version_parameter)
    client = tm.get_test_client(base_url=host)

    response = client.get("/version")
    assert response.status_code == 200
    assert response.json() == expected_result
