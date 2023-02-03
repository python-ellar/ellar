import pytest

from ellar.core import TestClientFactory
from ellar.core.versioning import VERSIONING

from .operations import (
    ControllerIndividualVersioning,
    ControllerListVersioning,
    ControllerVersioning,
    mr,
)

tm = TestClientFactory.create_test_module(
    routers=(mr,),
    controllers=[
        ControllerVersioning,
        ControllerIndividualVersioning,
        ControllerListVersioning,
    ],
)
tm.app.enable_versioning(VERSIONING.NONE)


@pytest.mark.parametrize(
    "path, expected_result",
    [
        ("/version", dict(version="default")),
        ("/version?v=1", dict(version="default")),
        ("/version?v=2", dict(version="default")),
        ("/version?v=3", dict(version="default")),
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
        ("/version", "", dict(version="default")),
        ("/version", "v=1", dict(version="default")),
        ("/version", "v=2", dict(version="default")),
        ("/version", "v=3", dict(version="default")),
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
        ("/version", "testserver.org", dict(version="default")),
        ("/version", "v1.testserver.org", dict(version="default")),
        ("/version", "v2.testserver.org", dict(version="default")),
        ("/version", "v3.testserver.org", dict(version="default")),
    ],
)
def test_default_route_versioning_host(path, host, expected_result):
    client = tm.get_client(base_url=f"http://{host}")
    response = client.get(path)
    assert response.status_code == 200
    assert response.json() == expected_result
