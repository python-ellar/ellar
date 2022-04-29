from ellar.compatible import AttributeDict
from ellar.core.operation_meta import OperationMeta


def test_operation_meta_defaults():
    operation_meta = OperationMeta()

    assert isinstance(operation_meta.extra_route_args, list)
    assert isinstance(operation_meta.response_override, AttributeDict)
    assert isinstance(operation_meta.extra_route_args, list)

    assert isinstance(operation_meta.route_versioning, set)
    assert isinstance(operation_meta.route_guards, list)
    assert isinstance(operation_meta.openapi, AttributeDict)

    # check can access dict value like an attribute
    operation_meta.update(me="Eadwin")
    operation_meta["response_override"].set_defaults(me="Eadwin")
    operation_meta["openapi"].set_defaults(me="Eadwin")
    assert operation_meta.me == "Eadwin"
    assert operation_meta.response_override.me == "Eadwin"
    assert operation_meta.openapi.me == "Eadwin"
