import pytest

from ellar.core import TestClientFactory
from ellar.core.versioning import VERSIONING

from .operations import (
    ControllerIndividualVersioning,
    ControllerListVersioning,
    ControllerVersioning,
)

tm = TestClientFactory.create_test_module(
    controllers=[
        ControllerVersioning,
        ControllerIndividualVersioning,
        ControllerListVersioning,
    ]
)

tm.app.enable_versioning(VERSIONING.NONE)


@pytest.mark.parametrize(
    "path, expected_result",
    [
        ("/individual/version", dict(version="default")),
        ("/individual/version?v=1", dict(version="default")),
        ("/individual/version?v=2", dict(version="default")),
        ("/individual/version?v=3", dict(version="default")),
        ("/controller-versioning/version", dict(version="default")),
        ("/controller-versioning/version?v=1", dict(version="default")),
        ("/controller-versioning/version?v=2", dict(version="default")),
        ("/controller-versioning/version?v=3", dict(version="default")),
        ("/controller-versioning-list/version?v=1", dict(version="default")),
        ("/controller-versioning-list/version?v=2", dict(version="default")),
        ("/controller-versioning-list/version?v=3", dict(version="default")),
    ],
)
def test_default_route_versioning_query(path, expected_result):
    client = tm.get_client()
    response = client.get(path)
    assert response.status_code == 200
    assert response.json() == expected_result


@pytest.mark.parametrize(
    "path, header, expected_result",
    [
        ("/individual/version", "", dict(version="default")),
        ("/individual/version", "v=1", dict(version="default")),
        ("/individual/version", "v=2", dict(version="default")),
        ("/individual/version", "v=3", dict(version="default")),
        ("/controller-versioning/version", "", dict(version="default")),
        ("/controller-versioning/version", "v=1", dict(version="default")),
        ("/controller-versioning/version", "v=2", dict(version="default")),
        ("/controller-versioning/version", "v=3", dict(version="default")),
        ("/controller-versioning-list/version", "", dict(version="default")),
        ("/controller-versioning-list/version", "v=1", dict(version="default")),
        ("/controller-versioning-list/version", "v=2", dict(version="default")),
        ("/controller-versioning-list/version", "v=3", dict(version="default")),
    ],
)
def test_default_route_versioning_header(path, header, expected_result):
    client = tm.get_client()
    response = client.get(path, headers={"accept": f"application/json; {header}"})
    assert response.status_code == 200
    assert response.json() == expected_result


@pytest.mark.parametrize(
    "path, host, expected_result",
    [
        ("/individual/version", "testserver.org", dict(version="default")),
        ("/individual/version", "v1.testserver.org", dict(version="default")),
        ("/individual/version", "v2.testserver.org", dict(version="default")),
        ("/individual/version", "v3.testserver.org", dict(version="default")),
        ("/controller-versioning/version", "testserver.org", dict(version="default")),
        (
            "/controller-versioning/version",
            "v1.testserver.org",
            dict(version="default"),
        ),
        (
            "/controller-versioning/version",
            "v2.testserver.org",
            dict(version="default"),
        ),
        (
            "/controller-versioning/version",
            "v3.testserver.org",
            dict(version="default"),
        ),
        (
            "/controller-versioning-list/version",
            "testserver.org",
            dict(version="default"),
        ),
        (
            "/controller-versioning-list/version",
            "v1.testserver.org",
            dict(version="default"),
        ),
        (
            "/controller-versioning-list/version",
            "v2.testserver.org",
            dict(version="default"),
        ),
        (
            "/controller-versioning-list/version",
            "v3.testserver.org",
            dict(version="default"),
        ),
    ],
)
def test_default_route_versioning_host(path, host, expected_result):
    client = tm.get_client(base_url=f"http://{host}")
    response = client.get(path)
    assert response.status_code == 200
    assert response.json() == expected_result
