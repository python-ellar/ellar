import pytest

from ellar.constants import NOT_SET
from ellar.core import TestClientFactory
from ellar.core.versioning import VERSIONING

from .operations import mr

tm = TestClientFactory.create_test_module(routers=(mr,))

tm.app.enable_versioning(VERSIONING.HOST, version_parameter="v")


@pytest.mark.parametrize(
    "path, host, expected_result",
    [
        ("/version", "testserver.org", dict(version="default")),
        ("/version", "v1.testserver.org", dict(version="v1")),
        ("/version", "v2.testserver.org", dict(version="v2")),
        ("/version", "v3.testserver.org", dict(version="v3")),
    ],
)
def test_host_route_versioning(path, host, expected_result):
    client = tm.get_client(base_url=f"http://{host}")
    response = client.get(path)
    assert response.status_code == 200
    assert response.json() == expected_result


@pytest.mark.parametrize(
    "path, host, default, expected_result",
    [
        # default is 1
        ("/version", "testserver.org", "1", dict(version="default")),
        ("/version", "v1.testserver.org", "1", dict(version="default")),
        ("/version", "v2.testserver.org", "1", dict(version="v2")),
        ("/version", "v3.testserver.org", "1", dict(version="v3")),
        # default is 2
        ("/version", "testserver.org", "2", dict(version="default")),
        ("/version", "v1.testserver.org", "2", dict(version="v1")),
        ("/version", "v2.testserver.org", "2", dict(version="default")),
        ("/version", "v3.testserver.org", "2", dict(version="v3")),
        # default is 3
        ("/version", "testserver.org", "3", dict(version="default")),
        ("/version", "v1.testserver.org", "3", dict(version="v1")),
        ("/version", "v2.testserver.org", "3", dict(version="v2")),
        ("/version", "v3.testserver.org", "3", dict(version="default")),
        # default is None or NOT_SET
        ("/version", "testserver.org", NOT_SET, dict(version="default")),
        ("/version", "v1.testserver.org", NOT_SET, dict(version="v1")),
        ("/version", "v2.testserver.org", NOT_SET, dict(version="v2")),
        ("/version", "v3.testserver.org", NOT_SET, dict(version="v3")),
    ],
)
def test_host_route_versioning_with_default_version(
    path, host, default, expected_result
):
    tm.app.enable_versioning(VERSIONING.HOST, default_version=default)
    client = tm.get_client(base_url=f"http://{host}")
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
    tm.app.enable_versioning(VERSIONING.HOST, version_parameter=version_parameter)
    client = tm.get_client(base_url=host)

    response = client.get("/version")
    assert response.status_code == 404
    assert response.json() == {"detail": "Invalid version in hostname."}


@pytest.mark.parametrize(
    "host, version_parameter, expected_result",
    [
        ("http://b1.testserver.org", "b", dict(version="v1")),
        ("http://b2.testserver.org", "b", dict(version="v2")),
        ("http://b3.testserver.org", "b", dict(version="v3")),
    ],
)
def test_host_route_versioning_different_version_parameter(
    host, version_parameter, expected_result
):
    tm.app.enable_versioning(VERSIONING.HOST, version_parameter=version_parameter)
    client = tm.get_client(base_url=host)

    response = client.get("/version")
    assert response.status_code == 200
    assert response.json() == expected_result
