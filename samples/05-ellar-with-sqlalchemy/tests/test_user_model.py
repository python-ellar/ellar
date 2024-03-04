import pytest
import sqlalchemy.exc as sa_exc

from .factories import UserFactory

# from db_learning.models import User
#
# def test_username_must_be_unique(db_session):
#     # Creating and adding the first user
#     user1 = User(username='ellarSQL', email='ellarsql@gmail.com')
#     db_session.add(user1)
#     db_session.commit()
#
#     # Attempting to add a second user with the same username
#     user2 = User(username='ellarSQL', email='ellarsql2@gmail.com')
#     db_session.add(user2)
#
#     # Expecting an IntegrityError due to unique constraint violation
#     with pytest.raises(sa_exc.IntegrityError):
#         db_session.commit()


def test_username_must_be_unique(factory_session):
    user1 = UserFactory()
    with pytest.raises(sa_exc.IntegrityError):
        UserFactory(username=user1.username)
