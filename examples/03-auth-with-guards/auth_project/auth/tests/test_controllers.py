from unittest.mock import Mock

from ellar.di import ProviderConfig
from ellar.testing import Test
from ellar_jwt import JWTModule, JWTService

from ...users.module import UsersModule
from ..controllers import AuthController
from ..guards import AuthGuard
from ..schemas import UserCredentials
from ..services import AuthService


class AuthServiceMock(AuthService):
    def __init__(self):
        super().__init__(Mock(), Mock())

    async def sign_in(self, credentials):
        return {"access_token": credentials.username}


class TestAuthController:
    def setup_method(self):
        self.test_module = Test.create_test_module(
            controllers=[AuthController],
            providers=[ProviderConfig(AuthService, use_class=AuthServiceMock)],
        )
        self.controller: AuthController = self.test_module.get(AuthController)
        self.controller.context = Mock()
        self.controller.context.user = {"username": "Greg"}

    async def test_sign_in_works_action(self, anyio_backend):
        result = await self.controller.sign_in(
            UserCredentials(username="Greg", password="password")
        )
        assert result == {"access_token": "Greg"}

    def test_get_all_action(self):
        result = self.controller.get_profile()
        assert result == {"username": "Greg"}


class TestAuthControllerE2E:
    def setup_method(self):
        self.test_module = Test.create_test_module(
            modules=[JWTModule.setup(signing_secret_key="no_secret"), UsersModule],
            controllers=[AuthController],
            providers=[ProviderConfig(AuthService, use_class=AuthServiceMock)],
            global_guards=[AuthGuard],
        )
        self.controller: AuthController = self.test_module.get(AuthController)
        jwt_service: JWTService = self.test_module.get(JWTService)
        self.token = jwt_service.sign({"username": "Greg", "id": 23})

    def test_get_profile_endpoint_works(self):
        client = self.test_module.get_test_client()
        res = client.get(
            "/auth/profile", headers={"Authorization": f"Bearer {self.token}"}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["username"] == "Greg"
        assert data["id"] == 23

    def test_sign_in_endpoint_works(self):
        client = self.test_module.get_test_client()
        res = client.post(
            "/auth/sign-in", json={"username": "chigozie", "password": "changeme"}
        )
        data = res.json()
        assert "access_token" in data
