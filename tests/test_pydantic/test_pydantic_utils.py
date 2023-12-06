from typing import List, Union

from ellar.pydantic import utils

from ..schema import NoteSchemaDC


def test_is_bytes_sequence_annotation_union():
    # For coverage
    assert utils.is_bytes_sequence_annotation(Union[List[str], List[bytes]])


def test_field_annotation_is_scalar_sequence():
    # For coverage
    assert (
        utils.field_annotation_is_scalar_sequence(Union[List[str], List[bytes]]) is True
    )
    assert (
        utils.field_annotation_is_scalar_sequence(
            Union[List[str], List[bytes], List[NoteSchemaDC]]
        )
        is False
    )


def test_is_bytes_annotation():
    # For coverage
    assert utils.is_bytes_annotation(Union[List[str], List[bytes]]) is False
    assert utils.is_bytes_annotation(bytes) is True
    assert utils.is_bytes_annotation(Union[bytes, str]) is True
