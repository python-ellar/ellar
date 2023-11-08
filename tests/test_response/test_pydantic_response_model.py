from typing import Dict, List, Optional

from ellar.app import AppFactory
from ellar.common import ModuleRouter, serializer_filter
from pydantic import BaseModel, Field

mr = ModuleRouter("")


class Item(BaseModel):
    name: str = Field(..., alias="aliased_name")
    price: Optional[float] = None
    owner_ids: Optional[List[int]] = None


@mr.get("/items/valid")
def get_valid():
    return Item(aliased_name="valid", price=1.0)


@mr.get("/items/coerce")
def get_coerce():
    return Item(aliased_name="coerce", price="1.0")


@mr.get("/items/validlist")
def get_validlist():
    return [
        Item(aliased_name="foo"),
        Item(aliased_name="bar", price=1.0),
        Item(aliased_name="baz", price=2.0, owner_ids=[1, 2, 3]),
    ]


@mr.get("/items/validdict", response=Dict[str, Item])
def get_validdict():
    return {
        "k1": Item(aliased_name="foo"),
        "k2": Item(aliased_name="bar", price=1.0),
        "k3": Item(aliased_name="baz", price=2.0, owner_ids=[1, 2, 3]),
    }


@mr.get("/items/valid-exclude-unset")
@serializer_filter(exclude_unset=True)
def get_valid_exclude_unset():
    return Item(aliased_name="valid", price=1.0)


@mr.get("/items/coerce-exclude-unset")
@serializer_filter(exclude_unset=True)
def get_coerce_exclude_unset():
    return Item(aliased_name="coerce", price="1.0")


@mr.get("/items/validlist-exclude-unset")
@serializer_filter(exclude_unset=True)
def get_validlist_exclude_unset():
    return [
        Item(aliased_name="foo"),
        Item(aliased_name="bar", price=1.0),
        Item(aliased_name="baz", price=2.0, owner_ids=[1, 2, 3]),
    ]


@mr.get("/items/validdict-exclude-unset")
@serializer_filter(exclude_unset=True)
def get_validdict_exclude_unset():
    return {
        "k1": Item(aliased_name="foo"),
        "k2": Item(aliased_name="bar", price=1.0),
        "k3": Item(aliased_name="baz", price=2.0, owner_ids=[1, 2, 3]),
    }


app = AppFactory.create_app(routers=(mr,))


def test_valid(test_client_factory):
    client = test_client_factory(app)
    response = client.get("/items/valid")
    response.raise_for_status()
    assert response.json() == {"aliased_name": "valid", "price": 1.0, "owner_ids": None}


def test_coerce(test_client_factory):
    client = test_client_factory(app)
    response = client.get("/items/coerce")
    response.raise_for_status()
    assert response.json() == {
        "aliased_name": "coerce",
        "price": 1.0,
        "owner_ids": None,
    }


def test_validlist(test_client_factory):
    client = test_client_factory(app)
    response = client.get("/items/validlist")
    response.raise_for_status()
    assert response.json() == [
        {"aliased_name": "foo", "price": None, "owner_ids": None},
        {"aliased_name": "bar", "price": 1.0, "owner_ids": None},
        {"aliased_name": "baz", "price": 2.0, "owner_ids": [1, 2, 3]},
    ]


def test_validdict(test_client_factory):
    client = test_client_factory(app)
    response = client.get("/items/validdict")
    response.raise_for_status()
    assert response.json() == {
        "k1": {"aliased_name": "foo", "price": None, "owner_ids": None},
        "k2": {"aliased_name": "bar", "price": 1.0, "owner_ids": None},
        "k3": {"aliased_name": "baz", "price": 2.0, "owner_ids": [1, 2, 3]},
    }


def test_valid_exclude_unset(test_client_factory):
    client = test_client_factory(app)
    response = client.get("/items/valid-exclude-unset")
    response.raise_for_status()
    assert response.json() == {"aliased_name": "valid", "price": 1.0}


def test_coerce_exclude_unset(test_client_factory):
    client = test_client_factory(app)
    response = client.get("/items/coerce-exclude-unset")
    response.raise_for_status()
    assert response.json() == {"aliased_name": "coerce", "price": 1.0}


def test_validlist_exclude_unset(test_client_factory):
    client = test_client_factory(app)
    response = client.get("/items/validlist-exclude-unset")
    response.raise_for_status()
    assert response.json() == [
        {"aliased_name": "foo"},
        {"aliased_name": "bar", "price": 1.0},
        {"aliased_name": "baz", "price": 2.0, "owner_ids": [1, 2, 3]},
    ]


def test_validdict_exclude_unset(test_client_factory):
    client = test_client_factory(app)
    response = client.get("/items/validdict-exclude-unset")
    response.raise_for_status()
    assert response.json() == {
        "k1": {"aliased_name": "foo"},
        "k2": {"aliased_name": "bar", "price": 1.0},
        "k3": {"aliased_name": "baz", "price": 2.0, "owner_ids": [1, 2, 3]},
    }
