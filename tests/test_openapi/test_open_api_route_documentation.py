import typing as t

from ellar.auth.guards import GuardAPIKeyCookie
from ellar.common import Body, ModuleRouter, Query
from ellar.common.constants import CONTROLLER_OPERATION_HANDLER_KEY
from ellar.common.responses.models import ResponseModel, ResponseModelField
from ellar.core.connection import HTTPConnection
from ellar.core.routing import ModuleRouterFactory
from ellar.openapi import OpenAPIRouteDocumentation, openapi_info
from ellar.openapi.constants import OPENAPI_OPERATION_KEY
from ellar.reflect import reflect
from pydantic.schema import get_flat_models_from_fields, get_model_name_map

from ..schema import BlogObjectDTO, CreateCarSchema, Filter, NoteSchemaDC


class CustomCookieAPIKey(GuardAPIKeyCookie):
    parameter_name = "custom-key"

    async def authentication_handler(
        self, connection: HTTPConnection, key: t.Optional[t.Any]
    ) -> t.Optional[t.Any]:
        return True


class CustomResponseModel(ResponseModel):
    model_field_or_schema = CreateCarSchema


router = ModuleRouter()


@router.get(
    "/cars/{car_id:int}",
    response={
        200: t.List[t.Union[NoteSchemaDC, BlogObjectDTO]],
        401: t.Union[NoteSchemaDC, t.List[BlogObjectDTO]],
        404: CustomResponseModel(),
    },
)
@openapi_info(
    summary="Endpoint Summary",
    description="Endpoint Description",
    deprecated=False,
    tags=["endpoint", "endpoint-25"],
)
def get_car_by_id(car_id: int, filter: Filter = Query()):
    res = filter.dict()
    res.update(car_id=car_id)
    return res


@router.get("/create", response={201: CreateCarSchema})
def create_car(car: CreateCarSchema):
    return car


@router.http_route("/list", response={200: CreateCarSchema}, methods=["get", "post"])
def list_and_create_car(car: CreateCarSchema = Body(default=None)):
    return car


ModuleRouterFactory.build(router)


def test_open_api_route_model_input_fields():
    route_operation = reflect.get_metadata(
        CONTROLLER_OPERATION_HANDLER_KEY, get_car_by_id
    )
    openapi_route_doc = OpenAPIRouteDocumentation(route=route_operation)
    assert len(openapi_route_doc.input_fields) == 3

    for field in openapi_route_doc.input_fields:
        assert field.field_info.in_.value in ["query", "path"]


def test_open_api_route_model_output_fields():
    route_operation = reflect.get_metadata(
        CONTROLLER_OPERATION_HANDLER_KEY, get_car_by_id
    )
    openapi_route_doc = OpenAPIRouteDocumentation(route=route_operation)
    assert len(openapi_route_doc.output_fields) == 3

    for field in openapi_route_doc.output_fields:
        assert isinstance(field, ResponseModelField)


def test_open_api_route_model_get_openapi_operation_metadata():
    route_operation = reflect.get_metadata(
        CONTROLLER_OPERATION_HANDLER_KEY, get_car_by_id
    )
    openapi = reflect.get_metadata(OPENAPI_OPERATION_KEY, get_car_by_id) or {}
    openapi_route_doc = OpenAPIRouteDocumentation(route=route_operation, **openapi)
    result = openapi_route_doc.get_openapi_operation_metadata("post")
    assert result == {
        "tags": ["endpoint", "endpoint-25"],
        "summary": "Endpoint Summary",
        "description": "Endpoint Description",
        "operationId": "get_car_by_id_cars__car_id__post",
    }

    result = openapi_route_doc.get_openapi_operation_metadata("some_http_method")
    assert result == {
        "tags": ["endpoint", "endpoint-25"],
        "summary": "Endpoint Summary",
        "description": "Endpoint Description",
        "operationId": "get_car_by_id_cars__car_id__some_http_method",
    }


def test_open_api_route_get_openapi_operation_parameters_works_for_empty_model_name_map():
    route_operation = reflect.get_metadata(
        CONTROLLER_OPERATION_HANDLER_KEY, get_car_by_id
    )
    openapi = reflect.get_metadata(OPENAPI_OPERATION_KEY, get_car_by_id) or {}
    openapi_route_doc = OpenAPIRouteDocumentation(route=route_operation, **openapi)
    result = openapi_route_doc.get_openapi_operation_parameters(model_name_map={})
    assert result == [
        {
            "name": "car_id",
            "in": "path",
            "required": True,
            "schema": {"title": "Car Id", "include_in_schema": True, "type": "integer"},
        },
        {
            "name": "to",
            "in": "query",
            "required": False,
            "schema": {
                "title": "To",
                "include_in_schema": True,
                "type": "string",
                "format": "date-time",
            },
        },
        {
            "name": "from",
            "in": "query",
            "required": False,
            "schema": {
                "title": "From",
                "include_in_schema": True,
                "type": "string",
                "format": "date-time",
            },
        },
    ]


def test_open_api_route_get_openapi_operation_parameters_works():
    route_operation = reflect.get_metadata(CONTROLLER_OPERATION_HANDLER_KEY, create_car)
    openapi_route_doc = OpenAPIRouteDocumentation(route=route_operation)
    models = get_flat_models_from_fields(
        openapi_route_doc.get_route_models(), known_models=set()
    )
    model_name_map = get_model_name_map(models)
    result = openapi_route_doc.get_openapi_operation_parameters(
        model_name_map=model_name_map
    )
    assert result == []


def test_open_api_route_get_openapi_operation_request_body():
    route_operation = reflect.get_metadata(CONTROLLER_OPERATION_HANDLER_KEY, create_car)
    openapi_route_doc = OpenAPIRouteDocumentation(route=route_operation)
    models = get_flat_models_from_fields(
        openapi_route_doc.get_route_models(), known_models=set()
    )
    model_name_map = get_model_name_map(models)
    result = openapi_route_doc.get_openapi_operation_request_body(
        model_name_map=model_name_map
    )
    assert result == {
        "content": {
            "application/json": {
                "schema": {
                    "allOf": [{"$ref": "#/components/schemas/CreateCarSchema"}],
                    "include_in_schema": True,
                    "title": "Car",
                }
            }
        },
        "required": True,
    }


def test_open_api_route_get_child_openapi_path():
    route_operation = reflect.get_metadata(CONTROLLER_OPERATION_HANDLER_KEY, create_car)
    openapi_route_doc = OpenAPIRouteDocumentation(route=route_operation)

    models = get_flat_models_from_fields(
        openapi_route_doc.get_route_models(), known_models=set()
    )
    model_name_map = get_model_name_map(models)
    result = openapi_route_doc.get_child_openapi_path(
        model_name_map=model_name_map,
    )
    assert isinstance(result, tuple)
    assert result[0] == {
        "get": {
            "summary": None,
            "operationId": "create_car_create_get",
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "title": "Car",
                            "include_in_schema": True,
                            "allOf": [{"$ref": "#/components/schemas/CreateCarSchema"}],
                        }
                    }
                },
            },
            "responses": {
                201: {
                    "description": "Successful Response",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/CreateCarSchema"}
                        }
                    },
                },
                "422": {
                    "description": "Validation Error",
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/HTTPValidationError"
                            }
                        }
                    },
                },
            },
        }
    }


def test_open_api_route_get_openapi_path():
    route_operation = reflect.get_metadata(CONTROLLER_OPERATION_HANDLER_KEY, create_car)
    openapi_route_doc = OpenAPIRouteDocumentation(route=route_operation)

    models = get_flat_models_from_fields(
        openapi_route_doc.get_route_models(), known_models=set()
    )
    model_name_map = get_model_name_map(models)
    paths = {}
    security_schemes = {}

    openapi_route_doc.get_openapi_path(
        model_name_map=model_name_map,
        paths=paths,
        security_schemes=security_schemes,
        path_prefix=None,
    )

    assert paths == {
        "/create": {
            "get": {
                "summary": None,
                "operationId": "create_car_create_get",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "title": "Car",
                                "include_in_schema": True,
                                "allOf": [
                                    {"$ref": "#/components/schemas/CreateCarSchema"}
                                ],
                            }
                        }
                    },
                },
                "responses": {
                    201: {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/CreateCarSchema"
                                }
                            }
                        },
                    },
                    "422": {
                        "description": "Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPValidationError"
                                }
                            }
                        },
                    },
                },
            }
        }
    }
    assert len(security_schemes) == 0

    paths = {}
    security_schemes = {}

    openapi_route_doc.get_openapi_path(
        model_name_map=model_name_map,
        paths=paths,
        security_schemes=security_schemes,
        path_prefix="/some-prefix",
    )
    assert len(security_schemes) == 0
    assert paths == {
        "/some-prefix/create": {
            "get": {
                "summary": None,
                "operationId": "create_car_create_get",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "title": "Car",
                                "include_in_schema": True,
                                "allOf": [
                                    {"$ref": "#/components/schemas/CreateCarSchema"}
                                ],
                            }
                        }
                    },
                },
                "responses": {
                    201: {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/CreateCarSchema"
                                }
                            }
                        },
                    },
                    "422": {
                        "description": "Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPValidationError"
                                }
                            }
                        },
                    },
                },
            }
        }
    }


def test_open_api_route_get_openapi_path_with_security():
    route_operation = reflect.get_metadata(CONTROLLER_OPERATION_HANDLER_KEY, create_car)
    openapi_route_doc = OpenAPIRouteDocumentation(
        route=route_operation, guards=[CustomCookieAPIKey()]
    )

    models = get_flat_models_from_fields(
        openapi_route_doc.get_route_models(), known_models=set()
    )
    model_name_map = get_model_name_map(models)
    paths = {}
    security_schemes = {}

    openapi_route_doc.get_openapi_path(
        model_name_map=model_name_map,
        paths=paths,
        security_schemes=security_schemes,
        path_prefix=None,
    )

    assert len(security_schemes) == 1
    assert security_schemes == {
        "CustomCookieAPIKey": {
            "type": "apiKey",
            "description": None,
            "in": "cookie",
            "name": "custom-key",
        }
    }

    assert paths == {
        "/create": {
            "get": {
                "summary": None,
                "operationId": "create_car_create_get",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "title": "Car",
                                "include_in_schema": True,
                                "allOf": [
                                    {"$ref": "#/components/schemas/CreateCarSchema"}
                                ],
                            }
                        }
                    },
                },
                "security": [{"CustomCookieAPIKey": []}],
                "responses": {
                    201: {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/CreateCarSchema"
                                }
                            }
                        },
                    },
                    "422": {
                        "description": "Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPValidationError"
                                }
                            }
                        },
                    },
                },
            }
        }
    }


def test_open_api_route__get_openapi_path_object_works_for_routes_with_multiple_method():
    route_operation = reflect.get_metadata(
        CONTROLLER_OPERATION_HANDLER_KEY, list_and_create_car
    )
    openapi_route_doc = OpenAPIRouteDocumentation(
        route=route_operation, guards=[CustomCookieAPIKey()]
    )

    models = get_flat_models_from_fields(
        openapi_route_doc.get_route_models(), known_models=set()
    )
    model_name_map = get_model_name_map(models)
    result = openapi_route_doc._get_openapi_path_object(model_name_map=model_name_map)
    assert isinstance(result, tuple)
    assert result[0] == {
        "get": {
            "summary": None,
            "operationId": "list_and_create_car_list_get",
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": {
                            "title": "Car",
                            "include_in_schema": True,
                            "allOf": [{"$ref": "#/components/schemas/CreateCarSchema"}],
                        }
                    }
                }
            },
            "security": [{"CustomCookieAPIKey": []}],
            "responses": {
                200: {
                    "description": "Successful Response",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/CreateCarSchema"}
                        }
                    },
                },
                "422": {
                    "description": "Validation Error",
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/HTTPValidationError"
                            }
                        }
                    },
                },
            },
        },
        "post": {
            "summary": None,
            "operationId": "list_and_create_car_list_post",
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": {
                            "title": "Car",
                            "include_in_schema": True,
                            "allOf": [{"$ref": "#/components/schemas/CreateCarSchema"}],
                        }
                    }
                }
            },
            "security": [{"CustomCookieAPIKey": []}],
            "responses": {
                200: {
                    "description": "Successful Response",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/CreateCarSchema"}
                        }
                    },
                },
                "422": {
                    "description": "Validation Error",
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/HTTPValidationError"
                            }
                        }
                    },
                },
            },
        },
    }
    assert result[1] == {
        "CustomCookieAPIKey": {
            "type": "apiKey",
            "description": None,
            "in": "cookie",
            "name": "custom-key",
        }
    }
