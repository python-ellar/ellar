import pytest
from ellar.common import ModuleRouter
from ellar.common.exceptions import ImproperConfiguration
from ellar.reflect import reflect
from ellar.testing import Test

router1 = ModuleRouter("/cat1")


@router1.get("/create")
async def create_cat():
    return {"message": "created from ModuleRouter1"}


router2 = ModuleRouter("/cat2")


@router2.get("/create")
async def create_cat_2():
    return {"message": "created from ModuleRouter2"}


router3 = ModuleRouter("/cat3")


@router3.get("/create")
async def create_cat_3():
    return {"message": "created from ModuleRouter3"}


def test_can_reach_routers():
    with reflect.context():
        router2.add_router(router1, prefix="/sr")
        router3.add_router(router2)

        tm = Test.create_test_module(routers=[router3])

        client = tm.get_test_client()
        res = client.get("cat3/cat2/create")
        assert res.status_code == 200
        assert res.json() == {"message": "created from ModuleRouter2"}

        res = client.get("cat3/cat2/sr/cat1/create")
        assert res.status_code == 200
        assert res.json() == {"message": "created from ModuleRouter1"}

        res = client.get("cat3/create")
        assert res.status_code == 200
        assert res.json() == {"message": "created from ModuleRouter3"}


def test_circular_exception_works_router_reference():
    with reflect.context():
        router2.add_router(router1)
        router1.add_router(router2)

        with pytest.raises(ImproperConfiguration, match="Circular Nested router"):
            Test.create_test_module(routers=[router2]).create_application()
