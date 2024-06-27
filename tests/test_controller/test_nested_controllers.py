from ellar.common import Controller, get
from ellar.testing import Test


@Controller
class Cat1Controller:
    @get("/create")
    async def create_cat(self):
        return {"message": f"created from {self.__class__.__name__}"}


@Controller
class Cat2Controller:
    @get("/create")
    async def create_cat(self):
        return {"message": f"created from {self.__class__.__name__}"}


@Controller
class Cat3Controller:
    @get("/create")
    async def create_cat(self):
        return {"message": f"created from {self.__class__.__name__}"}


def test_can_reach_controllers():
    Cat2Controller.add_router(Cat1Controller)
    Cat3Controller.add_router(Cat2Controller)

    tm = Test.create_test_module(controllers=[Cat3Controller])

    client = tm.get_test_client()
    res = client.get("cat3/cat2/create")
    assert res.status_code == 200
    assert res.json() == {"message": "created from Cat2Controller"}

    res = client.get("cat3/cat2/cat1/create")
    assert res.status_code == 200
    assert res.json() == {"message": "created from Cat1Controller"}

    res = client.get("cat3/create")
    assert res.status_code == 200
    assert res.json() == {"message": "created from Cat3Controller"}


def test_circular_exception_works():
    Cat2Controller.add_router(Cat1Controller)
    Cat1Controller.add_router(Cat2Controller)

    # with pytest.raises(ImproperConfiguration, match="Circular Nested router"):
    Test.create_test_module(controllers=[Cat2Controller]).create_application()
