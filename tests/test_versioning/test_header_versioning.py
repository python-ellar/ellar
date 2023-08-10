import pytest
from ellar.common.constants import NOT_SET
from ellar.core.versioning import VersioningSchemes as VERSIONING
from ellar.testing import Test

from .operations import mr

tm = Test.create_test_module(routers=(mr,))
app = tm.create_application()
app.enable_versioning(
    VERSIONING.HEADER, version_parameter="v", header_parameter="accept"
)


@pytest.mark.parametrize(
    "path, header, expected_result",
    [
        ("/version", "", {"version": "default"}),
        ("/version", "v=1", {"version": "v1"}),
        ("/version", "v=2", {"version": "v2"}),
        ("/version", "v=3", {"version": "v3"}),
    ],
)
def test_header_route_versioning(path, header, expected_result):
    client = tm.get_test_client()
    response = client.get(path, headers={"accept": f"application/json; {header}"})
    assert response.status_code == 200
    assert response.json() == expected_result


@pytest.mark.parametrize(
    "path, header, default, expected_result",
    [
        # default is 1
        ("/version", "", "1", {"version": "default"}),
        ("/version", "v=1", "1", {"version": "default"}),
        ("/version", "v=2", "1", {"version": "v2"}),
        ("/version", "v=3", "1", {"version": "v3"}),
        # default is 2
        ("/version", "", "2", {"version": "default"}),
        ("/version", "v=1", "2", {"version": "v1"}),
        ("/version", "v=2", "2", {"version": "default"}),
        ("/version", "v=3", "2", {"version": "v3"}),
        # default is 3
        ("/version", "", "3", {"version": "default"}),
        ("/version", "v=1", "3", {"version": "v1"}),
        ("/version", "v=2", "3", {"version": "v2"}),
        ("/version", "v=3", "3", {"version": "default"}),
        # default is None or NOT_SET
        ("/version", "", NOT_SET, {"version": "default"}),
        ("/version", "v=1", NOT_SET, {"version": "v1"}),
        ("/version", "v=2", NOT_SET, {"version": "v2"}),
        ("/version", "v=3", NOT_SET, {"version": "v3"}),
    ],
)
def test_header_route_versioning_with_default_version(
    path, header, default, expected_result
):
    app.enable_versioning(
        VERSIONING.HEADER,
        version_parameter="v",
        header_parameter="accept",
        default_version=default,
    )
    client = tm.get_test_client()
    response = client.get(path, headers={"accept": f"application/json; {header}"})
    assert response.status_code == 200
    assert response.json() == expected_result


def test_header_versioning_version_parameter():
    app.enable_versioning(VERSIONING.HEADER)
    client = tm.get_test_client()

    response = client.get(
        "/version", headers={"accept": "application/json; v=4"}
    )  # version_parameter for query lookup is 'version'
    assert response.status_code == 200
    assert response.json() == {"version": "default"}

    response = client.get("/version", headers={"accept": "application/json; version=2"})
    assert response.status_code == 200
    assert response.json() == {"version": "v2"}

    response = client.get("/version", headers={"accept": "application/json; version=1"})
    assert response.status_code == 200
    assert response.json() == {"version": "v1"}


@pytest.mark.parametrize(
    "headers",
    [
        ({"accept": "application/json; v=4"}),
        ({"accept": "application/json; v=1.0"}),
        ({"accept": "application/json; v=2.0"}),
        ({"accept": "application/json; v=3.0"}),
    ],
)
def test_header_route_versioning_fails_for_float_versions(headers):
    app.enable_versioning(VERSIONING.HEADER, version_parameter="v")
    client = tm.get_test_client()
    response = client.get("/version", headers=headers)
    assert response.status_code == 406
    assert response.json() == {"detail": 'Invalid version in "accept" header.'}


def test_header_route_versioning_with_different_header_key():
    app.enable_versioning(VERSIONING.HEADER, header_parameter="custom_parameter")
    client = tm.get_test_client()
    response = client.get("/version", headers={"custom_parameter": "version=1;"})
    assert response.status_code == 200
    assert response.json() == {"version": "v1"}

    response = client.get("/version", headers={"custom_parameter": "version=2;"})
    assert response.status_code == 200
    assert response.json() == {"version": "v2"}

    response = client.get("/version", headers={"custom_parameter": "version=3;"})
    assert response.status_code == 200
    assert response.json() == {"version": "v3"}
