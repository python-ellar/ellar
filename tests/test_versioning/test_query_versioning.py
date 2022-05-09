import pytest

from ellar.constants import NOT_SET
from ellar.core import TestClientFactory
from ellar.core.versioning import VERSIONING

from .operations import mr

tm = TestClientFactory.create_test_module(routers=(mr,))

tm.app.enable_versioning(VERSIONING.QUERY, version_parameter="v")


@pytest.mark.parametrize(
    "path, expected_result",
    [
        ("/version", dict(version="default")),
        ("/version?v=1", dict(version="v1")),
        ("/version?v=2", dict(version="v2")),
        ("/version?v=3", dict(version="v3")),
    ],
)
def test_query_route_versioning(path, expected_result):
    client = tm.get_client()
    response = client.get(path)
    assert response.status_code == 200
    assert response.json() == expected_result


@pytest.mark.parametrize(
    "path, default, expected_result",
    [
        # default is 1
        ("/version", "1", dict(version="default")),
        ("/version?v=1", "1", dict(version="default")),
        ("/version?v=2", "1", dict(version="v2")),
        ("/version?v=3", "1", dict(version="v3")),
        # default is 2
        ("/version", "2", dict(version="default")),
        ("/version?v=1", "2", dict(version="v1")),
        ("/version?v=2", "2", dict(version="default")),
        ("/version?v=3", "2", dict(version="v3")),
        # default is 3
        ("/version", "3", dict(version="default")),
        ("/version?v=1", "3", dict(version="v1")),
        ("/version?v=2", "3", dict(version="v2")),
        ("/version?v=3", "3", dict(version="default")),
        # default is None or NOT_SET
        ("/version", NOT_SET, dict(version="default")),
        ("/version?v=1", NOT_SET, dict(version="v1")),
        ("/version?v=2", NOT_SET, dict(version="v2")),
        ("/version?v=3", NOT_SET, dict(version="v3")),
    ],
)
def test_query_route_versioning_with_default_version(path, default, expected_result):
    tm.app.enable_versioning(
        VERSIONING.QUERY, version_parameter="v", default_version=default
    )
    client = tm.get_client()
    response = client.get(path)
    assert response.status_code == 200
    assert response.json() == expected_result


def test_query_versioning_version_parameter():
    tm.app.enable_versioning(VERSIONING.QUERY)
    client = tm.get_client()

    response = client.get(
        "/version?v=4"
    )  # version_parameter for query lookup is 'version'
    assert response.status_code == 200
    assert response.json() == dict(version="default")

    response = client.get("/version?version=2")
    assert response.status_code == 200
    assert response.json() == dict(version="v2")

    response = client.get("/version?version=1")
    assert response.status_code == 200
    assert response.json() == dict(version="v1")


@pytest.mark.parametrize(
    "path",
    [
        "/version?v=4",
        "/version?v=1.0",
        "/version?v=2.0",
        "/version?v=3.0",
    ],
)
def test_query_route_versioning_not_found(path):
    tm.app.enable_versioning(VERSIONING.QUERY, version_parameter="v")
    client = tm.get_client()

    response = client.get(path)
    assert response.status_code == 404
    assert response.json() == {"detail": "Invalid version in query parameter."}
