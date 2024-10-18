import pytest
from ellar.core.templating.service import get_template_name


@pytest.mark.parametrize(
    "input_name, expected_output",
    [
        ("template", "template.html"),
        ("page.html", "page.html"),
        ("document.txt", "document.txt"),
        ("sds.rd.xml", "sds.rd.xml"),
        ("nested/path/file", "nested/path/file.html"),
        ("nested/path/file.jpg", "nested/path/file.jpg"),
        ("", ".html"),  # Edge case: empty string
        (".gitignore", ".gitignore"),  # Edge case: hidden file
    ],
)
def test_get_template_name(input_name, expected_output):
    assert get_template_name(input_name) == expected_output


def test_get_template_name_caching():
    # Test that the function is actually cached
    assert get_template_name.cache_info().hits == 0
    get_template_name("test")
    get_template_name("test")
    assert get_template_name.cache_info().hits == 1
