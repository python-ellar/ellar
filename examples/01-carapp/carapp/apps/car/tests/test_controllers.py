from unittest.mock import patch

from ellar.di import ProviderConfig
from ellar.testing import Test, TestClient

from ..controllers import CarController
from ..schemas import CarListFilter, CreateCarSerializer
from ..services import CarRepository


class TestCarController:
    def setup_method(self):
        self.test_module = Test.create_test_module(
            controllers=[CarController],
            providers=[ProviderConfig(CarRepository, use_class=CarRepository)],
        )
        self.controller: CarController = self.test_module.get(CarController)

    async def test_create_action(self, anyio_backend):
        result = await self.controller.create(
            CreateCarSerializer(name="Mercedes", year=2022, model="CLS")
        )

        assert result == {
            "id": "1",
            "message": "This action adds a new car",
            "model": "CLS",
            "name": "Mercedes",
            "year": 2022,
        }

    @patch.object(
        CarRepository,
        "get_all",
        return_value=[{"id": 2, "model": "CLS", "name": "Mercedes", "year": 2023}],
    )
    async def test_get_all_action(self, mock_get_all, anyio_backend):
        result = await self.controller.get_all(query=CarListFilter(offset=0, limit=10))

        assert result == {
            "cars": [{"id": 2, "model": "CLS", "name": "Mercedes", "year": 2023}],
            "message": "This action returns all cars at limit=10, offset=0",
        }


class TestCarControllerE2E:
    def setup_method(self):
        test_module = Test.create_test_module(
            controllers=[
                CarController,
            ],
            providers=[ProviderConfig(CarRepository, use_class=CarRepository)],
            config_module={"REDIRECT_SLASHES": True},
        )
        self.client: TestClient = test_module.get_test_client()

    def test_create_action(self):
        res = self.client.post(
            "/car", json={"name": "Mercedes", "year": 2022, "model": "CLS"}
        )
        assert res.status_code == 200
        assert res.json() == {
            "id": "1",
            "message": "This action adds a new car",
            "model": "CLS",
            "name": "Mercedes",
            "year": 2022,
        }

    @patch.object(
        CarRepository,
        "get_all",
        return_value=[{"id": 2, "model": "CLS", "name": "Mercedes", "year": 2023}],
    )
    def test_get_all_action(self, mock_get_all):
        res = self.client.get("/car?offset=0&limit=10")
        assert res.status_code == 200
        assert res.json() == {
            "cars": [{"id": 2, "model": "CLS", "name": "Mercedes", "year": 2023}],
            "message": "This action returns all cars at limit=10, offset=0",
        }
