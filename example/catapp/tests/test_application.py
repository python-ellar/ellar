import os
import pytest

from pathlib import Path
from app_module_test.application.cats.routers import cat_router

from architek.test_client import TestClientFactory

os.environ.setdefault('STARLETTEAPI_CONFIG_MODULE',  'app_module_test.tests.settings')

BASEDIR = Path(__file__).resolve().parent.parent

test_client = TestClientFactory.create_testing_module(
    routers=[cat_router],
    template_folder='views',
    static_folder='statics',
    base_directory=os.path.join(BASEDIR, 'application', 'cats')
).create_test_client()

# test_client = TestClientFactory.create_testing_module_from_module(
#     module=ItemModule
# ).create_test_client()


@pytest.mark.asyncio
async def test_cat_router():
    with test_client as client:
        response = client.get('/cats-router/html')
        assert response.status_code == 200
