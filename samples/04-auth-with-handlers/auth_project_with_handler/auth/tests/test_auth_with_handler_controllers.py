from unittest.mock import Mock

from ellar.common import Identity
from ellar.di import ProviderConfig
from ellar.testing import Test
from ellar_jwt import JWTService

from ..auth_scheme import JWTAuthentication
from ..controllers import AuthController
from ..module import AuthModule
from ..services import AuthService


class AuthServiceMock(AuthService):
    def __init__(self):
        super().__init__(Mock(), Mock())

    async def sign_in(self, username: str, password: str):
        return {"access_token": username, "refresh_token": username}

    async def refresh_token(self, refresh_token: str):
        return {"access_token": "new_access_token"}


class TestAuthController:
    def setup_method(self):
        self.test_module = Test.create_test_module(
            controllers=[AuthController],
            providers=[ProviderConfig(AuthService, use_class=AuthServiceMock)],
        )
        self.controller: AuthController = self.test_module.get(AuthController)
        self.controller.context = Mock()
        self.controller.context.user = Identity(
            **{"username": "Greg", "id": 23, "auth_type": "simple"}
        )

    async def test_sign_in_works_action(self, anyio_backend):
        result = await self.controller.sign_in(username="Greg", password="password")
        assert result == {"access_token": "Greg", "refresh_token": "Greg"}

    async def test_refresh_token_works(self, anyio_backend):
        result = await self.controller.refresh_token("someAccessToken")
        assert result == {"access_token": "new_access_token"}

    async def test_get_all_action(self, anyio_backend):
        result = await self.controller.get_profile()
        assert result == {"username": "Greg", "id": 23, "auth_type": "simple"}


class TestAuthControllerE2E:
    def setup_method(self):
        self.test_module = Test.create_test_module(modules=[AuthModule])
        jwt_service: JWTService = self.test_module.get(JWTService)
        self.token = jwt_service.sign({"username": "john", "id": 23, "sub": "john"})
        self.client = self.test_module.get_test_client()
        self.client.app.add_authentication_schemes(JWTAuthentication)

    def test_get_user_profile_fails_for_anonymous_user(self):
        res = self.client.get("/auth/profile")
        assert res.status_code == 401
        assert res.json() == {"detail": "Forbidden", "status_code": 401}

    def test_get_profile_endpoint_works(self):
        res = self.client.get(
            "/auth/profile", headers={"Authorization": f"Bearer {self.token}"}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["username"] == "john"
        assert data["id"] == 23

    def test_sign_in_endpoint_works(self):
        res = self.client.post(
            "/auth/login", json={"username": "clara", "password": "guess"}
        )
        data = res.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_token_endpoint_works(self):
        res = self.client.post("/auth/refresh", json={"payload": self.token})
        data = res.json()
        assert "access_token" in data
