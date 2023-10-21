import pytest
from ellar.common import Controller, ControllerBase, UseGuards, Version, set_metadata
from ellar.common.constants import CONTROLLER_METADATA, GUARDS_KEY, VERSIONING_KEY
from ellar.common.exceptions import ImproperConfiguration
from ellar.reflect import reflect


@set_metadata("OtherAttributes", "Something")
@Controller(
    prefix="/decorator",
    name="test",
)
@Version("v1")
@UseGuards()
class ControllerDecorationTest:
    pass


@Controller
class ControllerDefaultTest:
    pass


@Controller
@set_metadata("OtherAttributes", "Something")
class ControllerWithSetMetadata:
    pass


@Controller
@set_metadata("OtherAttributes", "Something")
class ControllerWithSetMetadataAndControllerBase(ControllerBase):
    pass


def test_controller_decoration_default():
    assert (
        reflect.get_metadata(CONTROLLER_METADATA.NAME, ControllerDefaultTest)
        == "defaulttest"
    )

    assert reflect.get_metadata(GUARDS_KEY, ControllerDefaultTest) is None
    assert reflect.get_metadata(VERSIONING_KEY, ControllerDefaultTest) is None
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
    assert reflect.get_metadata(GUARDS_KEY, ControllerDecorationTest) == []
    assert reflect.get_metadata(VERSIONING_KEY, ControllerDecorationTest) == {
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

    assert (
        reflect.get_metadata("OtherAttributes", ControllerDecorationTest) == "Something"
    )


def test_controller_set_metadata_decorator_works():
    assert (
        reflect.get_metadata("OtherAttributes", ControllerWithSetMetadata)
        == "Something"
    )

    assert (
        reflect.get_metadata(
            "OtherAttributes", ControllerWithSetMetadataAndControllerBase
        )
        == "Something"
    )


def test_controller_decorator_fails_as_a_function_decorator():
    def controller_function():
        pass  # pragma: no cover

    with pytest.raises(
        ImproperConfiguration,
        match=f"Controller is a class decorator - {controller_function}",
    ):
        Controller("/some-prefix")(controller_function)
