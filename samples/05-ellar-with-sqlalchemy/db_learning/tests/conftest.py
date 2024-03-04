import os

import pytest
import sqlalchemy as sa
from ellar.common.constants import ELLAR_CONFIG_MODULE
from ellar.testing import Test
from ellar_sql import EllarSQLService

from ..root_module import ApplicationModule
from . import common

os.environ.setdefault(ELLAR_CONFIG_MODULE, "db_learning.config:TestConfig")


@pytest.fixture(scope="session")
def tm():
    test_module = Test.create_test_module(modules=[ApplicationModule])
    yield test_module


@pytest.fixture(scope="session")
def db(tm):
    db_service = tm.get(EllarSQLService)
    db_service.create_all()

    yield

    db_service.drop_all()


@pytest.fixture(scope="session")
def db_session(db, tm):
    db_service = tm.get(EllarSQLService)

    yield db_service.session_factory()

    db_service.session_factory.remove()


@pytest.fixture
def factory_session(db, tm):
    engine = tm.get(sa.Engine)
    common.Session.configure(bind=engine)

    yield

    common.Session.remove()
