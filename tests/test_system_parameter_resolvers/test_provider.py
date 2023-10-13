import inspect
from unittest.mock import Mock

import pytest
from ellar.common.exceptions import ImproperConfiguration
from ellar.common.params.resolvers.system_parameters import ProviderParameterInjector
from ellar.core import ExecutionContext


class InjectableType1:
    name: str = "Ellar"


class InjectableType2:
    name: str = "Ellar"


def test_provider_setup_fails_for_no_service_defined():
    provider_resolver = ProviderParameterInjector()

    with pytest.raises(ImproperConfiguration):
        provider_resolver("parameter_name", inspect.Parameter.empty())


def test_provider_setup_fails_for_service_mismatch():
    #
    provider_resolver = ProviderParameterInjector()
    provider_resolver.data = InjectableType2

    with pytest.raises(ImproperConfiguration):
        provider_resolver("parameter_name", InjectableType1)


async def test_provider_setup_fails_when_it_has_not_service(anyio_backend):
    provider_resolver = ProviderParameterInjector()

    with pytest.raises(RuntimeError):
        await provider_resolver.resolve(Mock(spec=ExecutionContext))
