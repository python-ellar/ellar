from ellar.common.compatible import AttributeDict


class MyDict(AttributeDict):
    pass


def test_set_value_for_attribute_dict_type():
    instance = MyDict()
    instance.name = "Ellar"
    instance.framework = "ASGI Framework"

    assert len(instance) == 2
    assert instance["name"] == "Ellar"
    assert instance["framework"] == "ASGI Framework"
    assert instance.name == instance["name"]
    assert instance.framework == instance["framework"]


def test_set_defaults_for_attribute_dict_type():
    instance = MyDict(framework="Python Framework")
    instance.set_defaults(**{"name": "Ellar", "framework": "ASGI Framework"})
    assert len(instance) == 2

    assert instance["name"] == "Ellar"
    assert instance["framework"] == "Python Framework"

    assert instance.name == instance["name"]
    assert instance.framework == instance["framework"]
