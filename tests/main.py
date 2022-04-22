from typing import Optional
from uuid import UUID

from pydantic import Field

from architek.common import Path, Query
from architek.core.factory import ArchitekAppFactory
from architek.core.schema import PydanticSchema

app = ArchitekAppFactory.create_app()


@app.Get("/root")
def non_operation():
    return {"message": "Hello World"}


@app.Get("/text")
def get_text():
    return "Hello World"


@app.Get("/path/{item_id}")
def get_id(item_id):
    return item_id


@app.Get("/path/str/{item_id}")
def get_str_id(item_id: str):
    return item_id


@app.Get("/path/int/{item_id}")
def get_int_id(item_id: int):
    return item_id


@app.Get("/path/float/{item_id}")
def get_float_id(item_id: float):
    return item_id


@app.Get("/path/bool/{item_id}")
def get_bool_id(item_id: bool):
    return item_id


@app.Get("/path/param/{item_id}")
def get_path_param_id(item_id: Optional[str] = Path(None)):
    return item_id


@app.Get("/path/param-required/{item_id}")
def get_path_param_required_id(item_id: str = Path(...)):
    return item_id


@app.Get("/path/param-minlength/{item_id}")
def get_path_param_min_length(item_id: str = Path(..., min_length=3)):
    return item_id


@app.Get("/path/param-maxlength/{item_id}")
def get_path_param_max_length(item_id: str = Path(..., max_length=3)):
    return item_id


@app.Get("/path/param-min_maxlength/{item_id}")
def get_path_param_min_max_length(item_id: str = Path(..., max_length=3, min_length=2)):
    return item_id


@app.Get("/path/param-gt/{item_id}")
def get_path_param_gt(item_id: float = Path(..., gt=3)):
    return item_id


@app.Get("/path/param-gt0/{item_id}")
def get_path_param_gt0(item_id: float = Path(..., gt=0)):
    return item_id


@app.Get("/path/param-ge/{item_id}")
def get_path_param_ge(item_id: float = Path(..., ge=3)):
    return item_id


@app.Get("/path/param-lt/{item_id}")
def get_path_param_lt(item_id: float = Path(..., lt=3)):
    return item_id


@app.Get("/path/param-lt0/{item_id}")
def get_path_param_lt0(item_id: float = Path(..., lt=0)):
    return item_id


@app.Get("/path/param-le/{item_id}")
def get_path_param_le(item_id: float = Path(..., le=3)):
    return item_id


@app.Get("/path/param-lt-gt/{item_id}")
def get_path_param_lt_gt(item_id: float = Path(..., lt=3, gt=1)):
    return item_id


@app.Get("/path/param-le-ge/{item_id}")
def get_path_param_le_ge(item_id: float = Path(..., le=3, ge=1)):
    return item_id


@app.Get("/path/param-lt-int/{item_id}")
def get_path_param_lt_int(item_id: int = Path(..., lt=3)):
    return item_id


@app.Get("/path/param-gt-int/{item_id}")
def get_path_param_gt_int(item_id: int = Path(..., gt=3)):
    return item_id


@app.Get("/path/param-le-int/{item_id}")
def get_path_param_le_int(item_id: int = Path(..., le=3)):
    return item_id


@app.Get("/path/param-ge-int/{item_id}")
def get_path_param_ge_int(item_id: int = Path(..., ge=3)):
    return item_id


@app.Get("/path/param-lt-gt-int/{item_id}")
def get_path_param_lt_gt_int(item_id: int = Path(..., lt=3, gt=1)):
    return item_id


@app.Get("/path/param-le-ge-int/{item_id}")
def get_path_param_le_ge_int(item_id: int = Path(..., le=3, ge=1)):
    return item_id


@app.Get("/path/param-starlette-str/{item_id:str}")
def get_path_param_starlette_str(item_id):
    return item_id


@app.Get("/path/param-starlette-int/{item_id:int}")
def get_path_param_starlette_int(item_id: int):
    assert isinstance(item_id, int)
    return item_id


@app.Get("/path/param-starlette-int-str/{item_id:int}")
def get_path_param_starlette_int_str(item_id: str):
    assert isinstance(item_id, str)
    return item_id


@app.Get("/path/param-starlette-uuid/{item_id:uuid}")
def get_path_param_starlette_uuid(item_id: UUID):
    assert isinstance(item_id, UUID)
    return item_id


@app.Get("/query")
def get_query(query):
    return f"foo bar {query}"


@app.Get("/query/optional")
def get_query_optional(query=None):
    if query is None:
        return "foo bar"
    return f"foo bar {query}"


@app.Get("/query/int")
def get_query_type(query: int):
    return f"foo bar {query}"


@app.Get("/query/int/optional")
def get_query_type_optional(query: int = None):
    if query is None:
        return "foo bar"
    return f"foo bar {query}"


@app.Get("/query/int/default")
def get_query_type_optional_10(query: int = 10):
    return f"foo bar {query}"


@app.Get("/query/param-required")
def get_query_param_required(query=Query(...)):
    return f"foo bar {query}"


@app.Get("/query/param-required/int")
def get_query_param_required_type(query: int = Query(...)):
    return f"foo bar {query}"


class AliasedSchema(PydanticSchema):
    query: str = Field(..., alias="aliased.-_~name")


@app.Get("/query/aliased-name")
def get_query_aliased_name(query: AliasedSchema = Query(..., alias="aliased.-_~name")):
    return f"foo bar {query.query}"


@app.Get("/query/param-required")
def get_query_param_required(query=Query(...)):
    return f"foo bar {query}"


@app.Get("/query/param-required/int")
def get_query_param_required_type(query: int = Query(...)):
    return f"foo bar {query}"


# @router.get("/query")
# def get_query(request, query):
#     return f"foo bar {query}"
#
#
# @router.get("/query/optional")
# def get_query_optional(request, query=None):
#     if query is None:
#         return "foo bar"
#     return f"foo bar {query}"
#
#
# @router.get("/query/int")
# def get_query_type(request, query: int):
#     return f"foo bar {query}"
#
#
# @router.get("/query/int/optional")
# def get_query_type_optional(request, query: int = None):
#     if query is None:
#         return "foo bar"
#     return f"foo bar {query}"
#
#
@app.Get("/query/param")
def get_query_param(request, query=Query(None)):
    if query is None:
        return "foo bar"
    return f"foo bar {query}"
