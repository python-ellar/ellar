import ellar.common as ec
from ellar.openapi import ApiTags
from ellar_sql import paginate

from db_learning.models import User


class UserSchema(ec.Serializer):
    id: int
    username: str
    email: str


# @ec.get('/users')
# @paginate(item_schema=UserSchema, per_page=100)
# def list_users():
#     return User

list_api_router = ec.ModuleRouter("/users-api")
# openapi tag
ApiTags(
    name="API Pagination",
    external_doc_url="https://python-ellar.github.io/ellar-sql/pagination/#api-pagination",
)(list_api_router)


@list_api_router.get()
@paginate(model=User, item_schema=UserSchema)
def list_users_api():
    pass
