from pathlib import Path
from unittest.mock import patch

from ellar.di import ProviderConfig
from ellar.testing import Test, TestClient

from ..routers import router
from ..services import CarRepository

BASEDIR = Path(__file__).resolve().parent.parent


class TestCarRouter:
    def setup_method(self):
        test_module = Test.create_test_module(
            routers=[router],
            providers=[ProviderConfig(CarRepository, use_class=CarRepository)],
            config_module={"REDIRECT_SLASHES": True},
            template_folder="views",
            static_folder="statics",
            base_directory=BASEDIR,
        )
        self.client: TestClient = test_module.get_test_client()

    @patch.object(
        CarRepository,
        "get_all",
        return_value=[{"id": 2, "model": "CLS", "name": "Mercedes", "year": 2023}],
    )
    def test_get_cars(self, mock_get_all):
        res = self.client.get("/car-as-router/")
        assert res.status_code == 200
        assert res.json() == [
            {
                "model": "CLS",
                "name": "Mercedes",
            }
        ]

    @patch.object(
        CarRepository,
        "get_all",
        return_value=[{"id": 2, "model": "CLS", "name": "Mercedes", "year": 2023}],
    )
    def test_get_car_html_with_render(self, mock_get_all):
        res = self.client.get("/car-as-router/html/outside")
        assert res.status_code == 200
        assert (
            res.content
            == b'<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <title>Index.html</title>\n</head>\n<body>\n    \n        <p>Mercedes</p>\n    \n</body>\n</html>'
        )
        assert res.template.name == "car/list.html"
