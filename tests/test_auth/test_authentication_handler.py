import typing as t

import pytest
from ellar.auth import AppIdentitySchemes, BaseAuthenticationHandler
from ellar.common import Identity, IHostContext


class ExampleAuthHandler(BaseAuthenticationHandler):
    scheme = "example"

    async def authenticate(self, context: IHostContext) -> t.Optional[Identity]:
        return Identity(id=23)


def test_auth_handler_raises_exception():
    with pytest.raises(
        RuntimeError, match=r"'SampleAuthHandler' has no attribute 'scheme'"
    ):

        class SampleAuthHandler(BaseAuthenticationHandler):
            async def authenticate(self, context: IHostContext) -> t.Optional[Identity]:
                pass

    assert ExampleAuthHandler().openapi_security_scheme() is None


def test_app_authentication_schemes():
    auth_scheme = AppIdentitySchemes()
    auth_scheme.add_authentication(ExampleAuthHandler)

    assert auth_scheme.find_authentication_scheme("example") is ExampleAuthHandler

    with pytest.raises(
        RuntimeError, match=r'No Authentication Scheme found with the name:"example2"'
    ):
        auth_scheme.find_authentication_scheme("example2")


def test_app_authentication_scheme_():
    auth_scheme = AppIdentitySchemes()
    auth_scheme.add_authentication(ExampleAuthHandler)
    assert list(auth_scheme.get_authentication_schemes()) == [ExampleAuthHandler]
