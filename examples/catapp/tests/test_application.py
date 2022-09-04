import os
from pathlib import Path

import pytest
from ellar.core.testclient import TestClientFactory

from catapp.application.cats.routers import cat_router

os.environ.setdefault('ELLAR_CONFIG_MODULE',  'catapp.config:TestingConfig')

BASEDIR = Path(__file__).resolve().parent.parent

test_client = TestClientFactory.create_test_module(
    routers=[cat_router],
    template_folder='views',
    static_folder='statics',
    base_directory=os.path.join(BASEDIR, 'application', 'cats')
).get_client()

# test_client = TestClientFactory.create_testing_module_from_module(
#     module=ItemModule
# ).create_test_client()


@pytest.mark.asyncio
async def test_cat_router():
    with test_client as client:
        response = client.get('/cats-router/html')
        assert response.status_code == 200
