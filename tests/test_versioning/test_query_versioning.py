import pytest
from ellar.common.constants import NOT_SET
from ellar.core.versioning import VersioningSchemes as VERSIONING
from ellar.testing import Test

from .operations import mr

tm = Test.create_test_module(routers=(mr,))
app = tm.create_application()
app.enable_versioning(VERSIONING.QUERY, version_parameter="v")


@pytest.mark.parametrize(
    "path, expected_result",
    [
        ("/version", {"version": "default"}),
        ("/version?v=1", {"version": "v1"}),
        ("/version?v=2", {"version": "v2"}),
        ("/version?v=3", {"version": "v3"}),
    ],
)
def test_query_route_versioning(path, expected_result):
    client = tm.get_test_client()
    response = client.get(path)
    assert response.status_code == 200
    assert response.json() == expected_result


@pytest.mark.parametrize(
    "path, default, expected_result",
    [
        # default is 1
        ("/version", "1", {"version": "default"}),
        ("/version?v=1", "1", {"version": "default"}),
        ("/version?v=2", "1", {"version": "v2"}),
        ("/version?v=3", "1", {"version": "v3"}),
        # default is 2
        ("/version", "2", {"version": "default"}),
        ("/version?v=1", "2", {"version": "v1"}),
        ("/version?v=2", "2", {"version": "default"}),
        ("/version?v=3", "2", {"version": "v3"}),
        # default is 3
        ("/version", "3", {"version": "default"}),
        ("/version?v=1", "3", {"version": "v1"}),
        ("/version?v=2", "3", {"version": "v2"}),
        ("/version?v=3", "3", {"version": "default"}),
        # default is None or NOT_SET
        ("/version", NOT_SET, {"version": "default"}),
        ("/version?v=1", NOT_SET, {"version": "v1"}),
        ("/version?v=2", NOT_SET, {"version": "v2"}),
        ("/version?v=3", NOT_SET, {"version": "v3"}),
    ],
)
def test_query_route_versioning_with_default_version(path, default, expected_result):
    app.enable_versioning(
        VERSIONING.QUERY, version_parameter="v", default_version=default
    )
    client = tm.get_test_client()
    response = client.get(path)
    assert response.status_code == 200
    assert response.json() == expected_result


def test_query_versioning_version_parameter():
    app.enable_versioning(VERSIONING.QUERY)
    client = tm.get_test_client()

    response = client.get(
        "/version?v=4"
    )  # version_parameter for query lookup is 'version'
    assert response.status_code == 200
    assert response.json() == {"version": "default"}

    response = client.get("/version?version=2")
    assert response.status_code == 200
    assert response.json() == {"version": "v2"}

    response = client.get("/version?version=1")
    assert response.status_code == 200
    assert response.json() == {"version": "v1"}


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
    app.enable_versioning(VERSIONING.QUERY, version_parameter="v")
    client = tm.get_test_client()

    response = client.get(path)
    assert response.status_code == 404
    assert response.json() == {"detail": "Invalid version in query parameter."}
