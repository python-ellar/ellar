import ellar.common as ec
from ellar.openapi import ApiTags
from ellar_sql import model, paginate

from db_learning.models import User

list_template_router = ec.ModuleRouter("/users-template")
# openapi tag
ApiTags(
    name="Template Pagination",
    external_doc_url="https://python-ellar.github.io/ellar-sql/pagination/#template-pagination",
)(list_template_router)

## CASE 1
# @list_template_router.get('/users')
# @ec.render('list.html')
# @paginate(as_template_context=True)
# def list_users():
#     return model.select(User), {'name': 'Template Pagination'} # pagination model, template context


## CASE 2
@list_template_router.get()
@ec.render("list.html")
@paginate(model=model.select(User), as_template_context=True)
def list_users_template():
    return {"name": "Template Pagination"}
