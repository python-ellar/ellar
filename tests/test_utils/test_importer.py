import os

from ellar.common.utils.importer import get_main_directory_by_stack


def test_get_main_directory_by_stack_works_for_main_directory():
    directory = get_main_directory_by_stack("__main__", stack_level=1)
    assert "test_utils" in directory


def test_get_main_directory_by_stack_works_for_main_parent_directory():
    directory = get_main_directory_by_stack(
        "__main__/__parent__/private", stack_level=1
    )
    result = os.listdir(directory)
    assert result == ["test.css"]


def test_get_main_directory_by_stack_fails_for_wrong_path():
    directory = get_main_directory_by_stack("/private/__main__", stack_level=1)
    assert directory == "/private/__main__"
