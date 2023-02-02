import pytest

from ellar.common import Controller, set_metadata
from ellar.constants import CONTROLLER_METADATA, GUARDS_KEY, NOT_SET, VERSIONING_KEY
from ellar.core import ControllerBase
from ellar.core.exceptions import ImproperConfiguration
from ellar.reflect import reflect


@set_metadata("OtherAttributes", "Something")
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

    assert reflect.get_metadata(CONTROLLER_METADATA.OPENAPI, ControllerDefaultTest) == {
        "tag": NOT_SET,
        "description": None,
        "external_doc_description": None,
        "external_doc_url": None,
    }
    assert reflect.get_metadata(GUARDS_KEY, ControllerDefaultTest) == []
    assert reflect.get_metadata(VERSIONING_KEY, ControllerDefaultTest) == set()
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
