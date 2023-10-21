import pytest
from ellar.common import Cookie, Header, Inject, ModuleRouter
from ellar.core.connection import Request
from ellar.testing import Test

mr = ModuleRouter("")


@mr.get("/headers1")
def headers1(request: Inject[Request], user_agent: Header[str]):
    return user_agent


@mr.get("/headers2")
def headers2(request: Inject[Request], ua: Header[str, Header.P(alias="User-Agent")]):
    return ua


@mr.get("/headers3")
def headers3(request: Inject[Request], content_length: int = Header(...)):
    return content_length


@mr.get("/headers4")
def headers4(
    request: Inject[Request], c_len: int = Header(..., alias="Content-length")
):
    return c_len


@mr.get("/headers5")
def headers5(request: Inject[Request], missing: int = Header(...)):
    return missing


@mr.get("/cookies1")
def cookies1(request: Inject[Request], weapon: str = Cookie(...)):
    return weapon


@mr.get("/cookies2")
def cookies2(request: Inject[Request], wpn: str = Cookie(..., alias="weapon")):
    return wpn


tm = Test.create_test_module(routers=(mr,))
client = tm.get_test_client()


@pytest.mark.parametrize(
    "path,expected_status,expected_response",
    [
        ("/headers1", 200, "Ellar"),
        ("/headers2", 200, "Ellar"),
        ("/headers3", 200, 10),
        ("/headers4", 200, 10),
        (
            "/headers5",
            422,
            {
                "detail": [
                    {
                        "loc": ["header", "missing"],
                        "msg": "field required",
                        "type": "value_error.missing",
                    }
                ]
            },
        ),
        ("/cookies1", 200, "shuriken"),
        ("/cookies2", 200, "shuriken"),
    ],
)
def test_headers(path, expected_status, expected_response):
    response = client.get(
        path,
        headers={"User-Agent": "Ellar", "Content-Length": "10"},
        cookies={"weapon": "shuriken"},
    )
    assert response.status_code == expected_status, response.content
    assert response.json() == expected_response
