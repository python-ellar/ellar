from unittest.mock import patch

from ellar.app import AppFactory
from ellar.common import Form, ModuleRouter
from ellar.core import Request
from ellar.testing import TestClient

mr = ModuleRouter("")


@mr.post("/form/python-list")
def post_form_param_list(items: list = Form(...)):
    return items


@mr.post("/form/python-set")
def post_form_param_set(items: set = Form(...)):
    return items


@mr.post("/form/python-tuple")
def post_form_param_tuple(items: tuple = Form(...)):
    return items


@mr.post("/form/python-tuple-failed")
def cause_form_to_fail(items: tuple = Form(...)):
    return items


app = AppFactory.create_app(routers=(mr,))
client = TestClient(app)


def test_python_list_param_as_form():
    response = client.post(
        "/form/python-list", data={"items": ["first", "second", "third"]}
    )
    assert response.status_code == 200, response.text
    assert response.json() == ["first", "second", "third"]


def test_python_set_param_as_form():
    response = client.post(
        "/form/python-set", data={"items": ["first", "second", "third"]}
    )
    assert response.status_code == 200, response.text
    assert set(response.json()) == {"first", "second", "third"}


def test_python_tuple_param_as_form():
    response = client.post(
        "/form/python-tuple", data={"items": ["first", "second", "third"]}
    )
    assert response.status_code == 200, response.text
    assert response.json() == ["first", "second", "third"]


@patch.object(Request, "form")
def test_form_resolution_fails(mock_form):
    async def raise_exception():
        raise Exception()

    mock_form.return_value = raise_exception
    response = client.post(
        "/form/python-tuple-failed", data={"items": ["first", "second", "third"]}
    )
    assert response.status_code == 400
    assert response.json() == {
        "detail": "There was an error parsing the body",
        "status_code": 400,
    }
