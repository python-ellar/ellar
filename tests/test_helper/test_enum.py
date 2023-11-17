from ellar.common.utils.enums import create_enums_from_dict, create_enums_from_list


def test_create_enums_from_list():
    new_enum = create_enums_from_list("new_enum", "key1", "key2")
    assert new_enum.__name__ == "new_enum"
    assert new_enum.key1.value == "key1"
    assert new_enum.key2.value == "key2"


def test_create_enums_from_dict():
    new_enum_2 = create_enums_from_dict("new_enum_2", key1="value1", key2="value2")
    assert new_enum_2.__name__ == "new_enum_2"
    assert new_enum_2.key1.value == "value1"
    assert new_enum_2.key2.value == "value2"
