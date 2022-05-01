from typing import List, Optional

from pydantic import BaseModel

from ellar.core import ArchitekAppFactory

app = ArchitekAppFactory.create_app()


class Item(BaseModel):
    name: str
    price: Optional[float] = None
    owner_ids: Optional[List[int]] = None


@app.Get("/items/valid", response=Item)
def get_valid():
    return {"name": "valid", "price": 1.0}


@app.Get("/items/coerce", response=Item)
def get_coerce():
    return {"name": "coerce", "price": "1.0"}


@app.Get("/items/validlist", response=List[Item])
def get_validlist():
    return [
        {"name": "foo"},
        {"name": "bar", "price": 1.0},
        {"name": "baz", "price": 2.0, "owner_ids": [1, 2, 3]},
    ]


# TODO: remaining test
# def test tuple return
# def test ellip return
# def test status return
# def multiple status return
# def default 200 return
# test resmodel not found


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
