from typing import Optional
from uuid import UUID

from ellar.app import AppFactory
from ellar.common import Inject, ModuleRouter, Path, Query, Serializer
from ellar.core.connection import Request
from pydantic import Field

router = ModuleRouter("")


@router.get("/root")
def non_operation():
    return {"message": "Hello World"}


@router.get("/text")
def get_text():
    return "Hello World"


@router.get("/path/{item_id}")
def get_id(item_id):
    return item_id


@router.get("/path/str/{item_id}")
def get_str_id(item_id: str):
    return item_id


@router.get("/path/int/{item_id}")
def get_int_id(item_id: int):
    return item_id


@router.get("/path/float/{item_id}")
def get_float_id(item_id: float):
    return item_id


@router.get("/path/bool/{item_id}")
def get_bool_id(item_id: bool):
    return item_id


@router.get("/path/param/{item_id}")
def get_path_param_id(item_id: Optional[str] = Path(None)):
    return item_id


@router.get("/path/param-required/{item_id}")
def get_path_param_required_id(item_id: str = Path(...)):
    return item_id


@router.get("/path/param-minlength/{item_id}")
def get_path_param_min_length(item_id: str = Path(..., min_length=3)):
    return item_id


@router.get("/path/param-maxlength/{item_id}")
def get_path_param_max_length(item_id: str = Path(..., max_length=3)):
    return item_id


@router.get("/path/param-min_maxlength/{item_id}")
def get_path_param_min_max_length(item_id: str = Path(..., max_length=3, min_length=2)):
    return item_id


@router.get("/path/param-gt/{item_id}")
def get_path_param_gt(item_id: float = Path(..., gt=3)):
    return item_id


@router.get("/path/param-gt0/{item_id}")
def get_path_param_gt0(item_id: float = Path(..., gt=0)):
    return item_id


@router.get("/path/param-ge/{item_id}")
def get_path_param_ge(item_id: float = Path(..., ge=3)):
    return item_id


@router.get("/path/param-lt/{item_id}")
def get_path_param_lt(item_id: float = Path(..., lt=3)):
    return item_id


@router.get("/path/param-lt0/{item_id}")
def get_path_param_lt0(item_id: float = Path(..., lt=0)):
    return item_id


@router.get("/path/param-le/{item_id}")
def get_path_param_le(item_id: float = Path(..., le=3)):
    return item_id


@router.get("/path/param-lt-gt/{item_id}")
def get_path_param_lt_gt(item_id: float = Path(..., lt=3, gt=1)):
    return item_id


@router.get("/path/param-le-ge/{item_id}")
def get_path_param_le_ge(item_id: float = Path(..., le=3, ge=1)):
    return item_id


@router.get("/path/param-lt-int/{item_id}")
def get_path_param_lt_int(item_id: int = Path(..., lt=3)):
    return item_id


@router.get("/path/param-gt-int/{item_id}")
def get_path_param_gt_int(item_id: int = Path(..., gt=3)):
    return item_id


@router.get("/path/param-le-int/{item_id}")
def get_path_param_le_int(item_id: int = Path(..., le=3)):
    return item_id


@router.get("/path/param-ge-int/{item_id}")
def get_path_param_ge_int(item_id: int = Path(..., ge=3)):
    return item_id


@router.get("/path/param-lt-gt-int/{item_id}")
def get_path_param_lt_gt_int(item_id: int = Path(..., lt=3, gt=1)):
    return item_id


@router.get("/path/param-le-ge-int/{item_id}")
def get_path_param_le_ge_int(item_id: int = Path(..., le=3, ge=1)):
    return item_id


@router.get("/path/param-starlette-str/{item_id:str}")
def get_path_param_starlette_str(item_id):
    return item_id


@router.get("/path/param-starlette-int/{item_id:int}")
def get_path_param_starlette_int(item_id: int):
    assert isinstance(item_id, int)
    return item_id


@router.get("/path/param-starlette-int-str/{item_id:int}")
def get_path_param_starlette_int_str(item_id: str):
    assert isinstance(item_id, str)
    return item_id


@router.get("/path/param-starlette-uuid/{item_id:uuid}")
def get_path_param_starlette_uuid(item_id: UUID):
    assert isinstance(item_id, UUID)
    return item_id


@router.get("/query")
def get_query(query):
    return f"foo bar {query}"


@router.get("/query/optional")
def get_query_optional(query=None):
    if query is None:
        return "foo bar"
    return f"foo bar {query}"


@router.get("/query/int")
def get_query_type(query: int):
    return f"foo bar {query}"


@router.get("/query/int/optional")
def get_query_type_optional(query: int = None):
    if query is None:
        return "foo bar"
    return f"foo bar {query}"


@router.get("/query/int/default")
def get_query_type_optional_10(query: int = 10):
    return f"foo bar {query}"


@router.get("/query/param-required")
def get_query_param_required(query=Query(...)):
    assert isinstance(query, str)
    return f"foo bar {query}"


@router.get("/query/param-required/int")
def get_query_param_required_type(query: int = Query(...)):
    assert isinstance(query, int)
    return f"foo bar {query}"


class AliasedSchema(Serializer):
    query: str = Field(..., alias="aliased.-_~name")


@router.get("/query/aliased-name")
def get_query_aliased_name(query: AliasedSchema = Query(..., alias="aliased.-_~name")):
    return f"foo bar {query.query}"


@router.get("/query/param")
def get_query_param(request: Inject[Request], query=Query(None)):
    if query is None:
        return "foo bar"
    return f"foo bar {query}"


app = AppFactory.create_app(
    routers=[
        router,
    ]
)
