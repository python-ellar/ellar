import pytest
from ellar.common.constants import NOT_SET
from ellar.core.versioning import VersioningSchemes as VERSIONING
from ellar.testing import Test

from .operations import (
    ControllerIndividualVersioning,
    ControllerListVersioning,
    ControllerVersioning,
    mr_with_version,
    mr_with_version_list,
)

tm = Test.create_test_module(
    controllers=[
        ControllerVersioning,
        ControllerIndividualVersioning,
        ControllerListVersioning,
    ]
)
app = tm.create_application()
app.enable_versioning(
    VERSIONING.HEADER, version_parameter="v", header_parameter="accept"
)


@pytest.mark.parametrize(
    "path, header, expected_result",
    [
        ("/individual/version", "v=1", {"version": "v1"}),
        ("/individual/version", "v=2", {"version": "v2"}),
        ("/individual/version", "v=3", {"version": "v3"}),
        ("/controller-versioning/version", "v=1", {"version": "default"}),
        ("/controller-versioning/version", "v=2", {"version": "v2"}),
        ("/controller-versioning-list/version", "v=1", {"version": "default"}),
        ("/controller-versioning-list/version", "v=2", {"version": "default"}),
        ("/controller-versioning-list/version", "v=3", {"version": "v3"}),
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
        ("/individual/version", "", "1", {"version": "default"}),
        ("/individual/version", "v=1", "1", {"version": "default"}),
        ("/individual/version", "v=2", "1", {"version": "v2"}),
        ("/individual/version", "v=3", "1", {"version": "v3"}),
        # default is 2
        ("/individual/version", "", "2", {"version": "default"}),
        ("/individual/version", "v=1", "2", {"version": "v1"}),
        ("/individual/version", "v=2", "2", {"version": "default"}),
        ("/individual/version", "v=3", "2", {"version": "v3"}),
        # default is 3
        ("/individual/version", "", "3", {"version": "default"}),
        ("/individual/version", "v=1", "3", {"version": "v1"}),
        ("/individual/version", "v=2", "3", {"version": "v2"}),
        ("/individual/version", "v=3", "3", {"version": "default"}),
        # default is None or NOT_SET
        ("/individual/version", "", NOT_SET, {"version": "default"}),
        ("/individual/version", "v=1", NOT_SET, {"version": "v1"}),
        ("/individual/version", "v=2", NOT_SET, {"version": "v2"}),
        ("/individual/version", "v=3", NOT_SET, {"version": "v3"}),
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


@pytest.mark.parametrize(
    "path, header, expected_result, status",
    [
        ("/individual/version", "v=4", {"version": "default"}, 200),
        ("/individual/version", "version=2", {"version": "v2"}, 200),
        ("/individual/version", "version=1", {"version": "v1"}, 200),
        (
            "/controller-versioning/version",
            "v=4",
            {"detail": 'Invalid version in "accept" header.'},
            406,
        ),
        ("/controller-versioning/version", "version=2", {"version": "v2"}, 200),
        ("/controller-versioning/version", "version=1", {"version": "default"}, 200),
        (
            "/controller-versioning-list/version",
            "v=4",
            {"detail": 'Invalid version in "accept" header.'},
            406,
        ),
        (
            "/controller-versioning-list/version",
            "version=2",
            {"version": "default"},
            200,
        ),
        (
            "/controller-versioning-list/version",
            "version=1",
            {"version": "default"},
            200,
        ),
    ],
)
def test_header_versioning_version_parameter(path, header, expected_result, status):
    app.enable_versioning(VERSIONING.HEADER)
    client = tm.get_test_client()

    response = client.get(
        path, headers={"accept": f"application/json; {header}"}
    )  # version_parameter for query lookup is 'version'
    assert response.status_code == status
    assert response.json() == expected_result


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
    response = client.get("/individual/version", headers=headers)
    assert response.status_code == 406
    assert response.json() == {"detail": 'Invalid version in "accept" header.'}


@pytest.mark.parametrize(
    "path, header, expected_result",
    [
        ("/individual/version", {"custom_parameter": "version=1;"}, {"version": "v1"}),
        ("/individual/version", {"custom_parameter": "version=2;"}, {"version": "v2"}),
        ("/individual/version", {"custom_parameter": "version=3;"}, {"version": "v3"}),
        (
            "/controller-versioning/version",
            {"custom_parameter": "version=1;"},
            {"version": "default"},
        ),
        (
            "/controller-versioning/version",
            {"custom_parameter": "version=2;"},
            {"version": "v2"},
        ),
        (
            "/controller-versioning-list/version",
            {"custom_parameter": "version=1;"},
            {"version": "default"},
        ),
        (
            "/controller-versioning-list/version",
            {"custom_parameter": "version=2;"},
            {"version": "default"},
        ),
        (
            "/controller-versioning-list/version",
            {"custom_parameter": "version=3;"},
            {"version": "v3"},
        ),
    ],
)
def test_header_route_versioning_with_different_header_key(
    path, header, expected_result
):
    app.enable_versioning(VERSIONING.HEADER, header_parameter="custom_parameter")
    client = tm.get_test_client()
    response = client.get(path, headers=header)
    assert response.status_code == 200
    assert response.json() == expected_result


new_tm = Test.create_test_module(routers=(mr_with_version, mr_with_version_list))
new_app = new_tm.create_application()
new_app.enable_versioning(
    VERSIONING.HEADER, version_parameter="v", header_parameter="accept"
)


@pytest.mark.parametrize(
    "path, header, expected_result",
    [
        ("/with-version/version", "v=1", {"version": "v1 only"}),
        ("/with-version/version", "v=2", {"version": "v2 and v3 only"}),
        ("/with-version/version", "v=2", {"version": "v2 and v3 only"}),
        ("/with-version-list/version", "v=1", {"version": "v1 and v2"}),
        ("/with-version-list/version", "v=2", {"version": "v1 and v2"}),
    ],
)
def test_header_route_versioning_for_module_router_versions_and_version_list(
    path, header, expected_result
):
    client = new_tm.get_test_client()
    response = client.get(path, headers={"accept": f"application/json; {header}"})
    assert response.status_code == 200
    assert response.json() == expected_result
