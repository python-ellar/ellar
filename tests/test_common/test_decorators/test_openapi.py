from ellar.common import openapi_info
from ellar.compatible import AttributeDict
from ellar.constants import OPENAPI_KEY
from ellar.core.connection import Request
from ellar.reflect import reflect


@openapi_info(
    summary="Endpoint Summary",
    description="Endpoint Description",
    deprecated=False,
    operation_id="4524d-z23zd-453ed-2342e",
    tags=["endpoint", "endpoint-25"],
)
def endpoint(request: Request):
    pass  # pragma: no cover


def test_openapi_sets_endpoint_meta():
    open_api_data = reflect.get_metadata(OPENAPI_KEY, endpoint)
    assert isinstance(open_api_data, AttributeDict)
    assert open_api_data.summary == "Endpoint Summary"
    assert open_api_data.description == "Endpoint Description"
    assert open_api_data.deprecated is False
    assert open_api_data.operation_id == "4524d-z23zd-453ed-2342e"
    assert open_api_data.tags == ["endpoint", "endpoint-25"]
