import pytest
from ellar.common.compatible import AttributeDict
from ellar.common.responses.models import EmptyAPIResponseModel
from ellar.common.routing.schema import RouteParameters, WsRouteParameters
from ellar.common.routing.websocket import WebSocketExtraHandler
from pydantic import BaseModel


class Item(BaseModel):
    name: str


class SampleResponseModel(EmptyAPIResponseModel):
    pass


class SampleWebSocketExtraHandler(WebSocketExtraHandler):
    pass


def test_route_parameter_schema():
    route_parameter = RouteParameters(
        methods=["get"], path="/path", endpoint=lambda: "testing"
    )
    data = AttributeDict(route_parameter.dict())

    assert data.methods == ["GET"]
    assert isinstance(data.response[200], EmptyAPIResponseModel)
    assert data.include_in_schema
    assert data.name is None

    with pytest.raises(ValueError):
        RouteParameters(methods=["get"], path="/path", endpoint="testing")

    with pytest.raises(ValueError, match="Method SOMETHING_ELSE not allowed"):
        RouteParameters(
            methods=["something_else"], path="/path", endpoint=lambda: "testing"
        )

    route_parameter = RouteParameters(
        methods=["get"],
        path="/path",
        endpoint=lambda: "testing",
        response=SampleResponseModel(),
    )
    data = AttributeDict(route_parameter.dict())
    assert isinstance(data.response[200], SampleResponseModel)

    route_parameter = RouteParameters(
        methods=["get"],
        path="/path",
        endpoint=lambda: "testing",
        response={404: SampleResponseModel(), 200: Item},
    )
    data = AttributeDict(route_parameter.dict())
    assert isinstance(data.response[404], SampleResponseModel)
    assert data.response[200] == Item


def test_ws_route_parameter_schema():
    ws_route_parameter = WsRouteParameters(path="/path", endpoint=lambda: "testing")
    data = AttributeDict(ws_route_parameter.dict())

    assert data.encoding == "json"
    assert data.use_extra_handler is False
    assert data.extra_handler_type is None

    with pytest.raises(ValueError):
        WsRouteParameters(path="/path", endpoint="testing")

    with pytest.raises(ValueError):
        WsRouteParameters(
            path="/path", encoding="something_else", endpoint=lambda: "testing"
        )

    ws_route_parameter = WsRouteParameters(
        path="/path",
        extra_handler_type=SampleWebSocketExtraHandler,
        encoding="text",
        use_extra_handler=True,
        endpoint=lambda: "testing",
    )
    data = AttributeDict(ws_route_parameter.dict())
    assert data.encoding == "text"
    assert data.use_extra_handler
    assert data.extra_handler_type is SampleWebSocketExtraHandler
