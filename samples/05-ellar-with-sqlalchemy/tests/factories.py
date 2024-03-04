import factory
from db_learning.models import User
from ellar_sql.factory import SESSION_PERSISTENCE_FLUSH, EllarSQLFactory

from . import common


class UserFactory(EllarSQLFactory):
    class Meta:
        model = User
        sqlalchemy_session_persistence = SESSION_PERSISTENCE_FLUSH
        sqlalchemy_session_factory = common.Session

    username = factory.Faker("user_name")
    email = factory.Faker("email")
