from typing import List, Optional

import pytest
from pydantic import BaseModel

from ellar.core import AppFactory
from ellar.core.response.model import RouteResponseExecution
from ellar.core.routing import ModuleRouter

mr = ModuleRouter("")


class Item(BaseModel):
    name: str
    price: Optional[float] = None
    owner_ids: Optional[List[int]] = None


@mr.get("/items/valid", response=Item)
def get_valid():
    return {"name": "valid", "price": 1.0}


@mr.get("/items/coerce", response=Item)
def get_coerce():
    return {"name": "coerce", "price": "1.0"}


@mr.get("/items/validlist", response=List[Item])
def get_validlist():
    return [
        {"name": "foo"},
        {"name": "bar", "price": 1.0},
        {"name": "baz", "price": 2.0, "owner_ids": [1, 2, 3]},
    ]


@mr.get("/items/valid_tuple_return", response={200: List[Item], 201: Item})
def get_valid_tuple_return():
    return 201, {"name": "baz", "price": 2.0, "owner_ids": [1, 2, 3]}


@mr.get("/items/not_found_res_model", response={200: List[Item], 201: Item})
def get_not_found_res_model():
    return 301, {"name": "baz", "price": 2.0, "owner_ids": [1, 2, 3]}


app = AppFactory.create_app(routers=(mr,))


def test_valid_tuple_return(test_client_factory):
    client = test_client_factory(app)
    response = client.get("/items/valid_tuple_return")
    response.raise_for_status()
    assert response.json() == {"name": "baz", "price": 2.0, "owner_ids": [1, 2, 3]}


def test_get_not_found_res_model(test_client_factory):
    client = test_client_factory(app)
    with pytest.raises(RouteResponseExecution):
        client.get("/items/not_found_res_model")


def test_valid(test_client_factory):
    client = test_client_factory(app)
    response = client.get("/items/valid")
    response.raise_for_status()
    assert response.json() == {"name": "valid", "price": 1.0, "owner_ids": None}


def test_coerce(test_client_factory):
    client = test_client_factory(app)
    response = client.get("/items/coerce")
    response.raise_for_status()
    assert response.json() == {"name": "coerce", "price": 1.0, "owner_ids": None}


def test_validlist(test_client_factory):
    client = test_client_factory(app)
    response = client.get("/items/validlist")
    response.raise_for_status()
    assert response.json() == [
        {"name": "foo", "price": None, "owner_ids": None},
        {"name": "bar", "price": 1.0, "owner_ids": None},
        {"name": "baz", "price": 2.0, "owner_ids": [1, 2, 3]},
    ]
