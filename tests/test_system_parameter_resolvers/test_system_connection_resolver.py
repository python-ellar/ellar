import pytest
from ellar.common.exceptions import ImproperConfiguration
from ellar.common.params import BaseConnectionParameterResolver


def test_improper_resolver_setup():
    class InvalidConnectionResolver(BaseConnectionParameterResolver):
        pass

    with pytest.raises(ImproperConfiguration):
        instance = InvalidConnectionResolver()
        instance("invalid", list)
