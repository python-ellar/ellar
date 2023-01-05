from ellar.common import Controller
from ellar.constants import CONTROLLER_METADATA, NOT_SET
from ellar.reflect import reflect


@Controller(
    prefix="/decorator",
    description="Some description",
    external_doc_description="external",
    guards=[],
    version=("v1",),
    tag="dec",
    external_doc_url="https://example.com",
    name="test",
)
class ControllerDecorationTest:
    pass


@Controller
class ControllerDefaultTest:
    pass


def test_controller_decoration_default():
    assert (
        reflect.get_metadata(CONTROLLER_METADATA.NAME, ControllerDefaultTest)
        == "defaulttest"
    )

    assert reflect.get_metadata(CONTROLLER_METADATA.OPENAPI, ControllerDefaultTest) == {
        "tag": NOT_SET,
        "description": None,
        "external_doc_description": None,
        "external_doc_url": None,
    }
    assert reflect.get_metadata(CONTROLLER_METADATA.GUARDS, ControllerDefaultTest) == []
    assert (
        reflect.get_metadata(CONTROLLER_METADATA.VERSION, ControllerDefaultTest)
        == set()
    )
    assert (
        reflect.get_metadata(CONTROLLER_METADATA.PATH, ControllerDefaultTest)
        == "/defaulttest"
    )
    assert (
        reflect.get_metadata(
            CONTROLLER_METADATA.INCLUDE_IN_SCHEMA, ControllerDefaultTest
        )
        is True
    )


def test_controller_decoration_test():
    assert (
        reflect.get_metadata(CONTROLLER_METADATA.NAME, ControllerDecorationTest)
        == "test"
    )

    assert reflect.get_metadata(
        CONTROLLER_METADATA.OPENAPI, ControllerDecorationTest
    ) == {
        "tag": "dec",
        "description": "Some description",
        "external_doc_description": "external",
        "external_doc_url": "https://example.com",
    }
    assert (
        reflect.get_metadata(CONTROLLER_METADATA.GUARDS, ControllerDecorationTest) == []
    )
    assert reflect.get_metadata(
        CONTROLLER_METADATA.VERSION, ControllerDecorationTest
    ) == {
        "v1",
    }
    assert (
        reflect.get_metadata(CONTROLLER_METADATA.PATH, ControllerDecorationTest)
        == "/decorator"
    )
    assert (
        reflect.get_metadata(
            CONTROLLER_METADATA.INCLUDE_IN_SCHEMA, ControllerDecorationTest
        )
        is True
    )
