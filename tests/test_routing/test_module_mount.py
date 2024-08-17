from ellar.common import constants
from ellar.core.routing import EllarControllerMount
from ellar.reflect import reflect


class ControlType:
    pass


def test_module_mount_default_handler(test_client_factory, reflect_context):
    mount = EllarControllerMount("/")
    reflect.define_metadata(constants.CONTROLLER_CLASS_KEY, ControlType, mount)

    client = test_client_factory(mount.handle)
    res = client.get("/")
    assert res.status_code == 404
    assert res.text == "Not Found"
