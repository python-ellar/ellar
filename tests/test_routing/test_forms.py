from ellar.common import Form
from ellar.core import TestClientFactory

tm = TestClientFactory.create_test_module()


@tm.app.Post("/form/python-list")
def post_form_param_list(items: list = Form(...)):
    return items


@tm.app.Post("/form/python-set")
def post_form_param_set(items: set = Form(...)):
    return items


@tm.app.Post("/form/python-tuple")
def post_form_param_tuple(items: tuple = Form(...)):
    return items


client = tm.get_client()


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
