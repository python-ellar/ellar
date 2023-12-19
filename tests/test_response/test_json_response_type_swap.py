from ellar.common import ModuleRouter, ORJSONResponse, UJSONResponse
from ellar.testing import Test

from ..schema import NoteSchemaDC


class AssertUJSONResponseSwap(UJSONResponse):
    def render(self, content) -> bytes:
        content.update(rendered="AssertUJSONResponseSwap")
        return super().render(content)


router = ModuleRouter()


@router.get("/orjson", response=ORJSONResponse)
def json_with_orjson():
    return NoteSchemaDC(id=1, completed=False, text="JSON rendered with ORJSON")


@router.get("/ujson", response=UJSONResponse)
def json_with_ujson():
    return NoteSchemaDC(id=1, completed=False, text="JSON rendered with UJSON")


@router.get("/json", response=NoteSchemaDC)
def json_swapped_with_ujson():
    return NoteSchemaDC(id=1, completed=False, text="JSON rendered with UJSON")


tm = Test.create_test_module(
    routers=[router], config_module={"DEFAULT_JSON_CLASS": AssertUJSONResponseSwap}
)
client = tm.get_test_client()


def test_orjson_response():
    res = client.get("/orjson")
    assert res.status_code == 200
    assert res.json() == {
        "completed": False,
        "id": 1,
        "text": "JSON rendered with ORJSON",
    }


def test_ujson_response():
    res = client.get("/ujson")
    assert res.status_code == 200
    assert res.json() == {
        "completed": False,
        "id": 1,
        "text": "JSON rendered with UJSON",
    }


def test_json_swapped_response():
    res = client.get("/json")
    assert res.status_code == 200
    assert res.json() == {
        "completed": False,
        "id": 1,
        "rendered": "AssertUJSONResponseSwap",
        "text": "JSON rendered with UJSON",
    }
