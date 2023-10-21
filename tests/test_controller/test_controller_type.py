from ellar.common import Controller, ControllerBase
from ellar.reflect import reflect


@Controller()
class CarController(ControllerBase, controller_name="CarSample"):
    pass


def test_car_controller_name_changed():
    controller_name = reflect.get_metadata("name", CarController)
    assert controller_name == "carsample"
