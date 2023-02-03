from functools import wraps

from starlette.responses import Response

from ellar.common import Context, Query, Res, extra_args, get
from ellar.core import TestClientFactory
from ellar.core.connection import Request
from ellar.core.context import IExecutionContext
from ellar.core.params import ExtraEndpointArg
from ellar.openapi import OpenAPIDocumentBuilder
from ellar.serializer import serialize_object

from .sample import Filter

tm = TestClientFactory.create_test_module()


def add_additional_signature_to_endpoint(func):
    # EXTRA ARGS SETUP
    query1 = ExtraEndpointArg(name="query1", annotation=str, default_value=Query())
    query2 = ExtraEndpointArg(
        name="query2", annotation=str
    )  # will default to Query during computation

    extra_args(query1, query2)(func)

    @wraps(func)
    def _wrapper(*args, **kwargs):
        # RESOLVING EXTRA ARGS
        # All extra args must be resolved before calling route function
        # else extra argument will be pushed to the route function
        resolved_query1 = query1.resolve(kwargs)
        resolved_query2 = query2.resolve(kwargs)

        response = func(*args, **kwargs)
        response.update(query1=resolved_query1, query2=resolved_query2)
        return response

    return _wrapper


def add_extra_non_field_extra_args(func):
    # EXTRA ARGS SETUP
    context = ExtraEndpointArg(
        name="context", annotation=IExecutionContext, default_value=Context()
    )
    response = ExtraEndpointArg(
        name="response", annotation=Response, default_value=Res()
    )

    extra_args(response)(func)
    extra_args(context)(func)

    @wraps(func)
    def _wrapper(*args, **kwargs):
        # RESOLVING EXTRA ARGS
        resolved_context = context.resolve(kwargs)
        resolved_response = response.resolve(kwargs)
        assert isinstance(resolved_response, Response)
        assert isinstance(resolved_context, IExecutionContext)

        return func(*args, **kwargs)

    return _wrapper


@get("/test")
@add_extra_non_field_extra_args
@add_additional_signature_to_endpoint
def query_params_extra(
    request: Request,
    filters: Filter = Query(),
):
    return filters.dict()


tm.app.router.append(query_params_extra)

openapi_schema = {
    "openapi": "3.0.2",
    "info": {"title": "Ellar API Docs", "version": "1.0.0"},
    "paths": {
        "/test": {
            "get": {
                "operationId": "query_params_extra_test_get",
                "parameters": [
                    {
                        "required": False,
                        "schema": {
                            "title": "To",
                            "type": "string",
                            "format": "date-time",
                        },
                        "name": "to",
                        "in": "query",
                    },
                    {
                        "required": False,
                        "schema": {
                            "title": "From",
                            "type": "string",
                            "format": "date-time",
                        },
                        "name": "from",
                        "in": "query",
                    },
                    {
                        "required": False,
                        "schema": {
                            "allOf": [{"$ref": "#/components/schemas/Range"}],
                            "default": 20,
                        },
                        "name": "range",
                        "in": "query",
                    },
                    {
                        "required": True,
                        "schema": {"title": "Query1", "type": "string"},
                        "name": "query1",
                        "in": "query",
                    },
                    {
                        "required": True,
                        "schema": {"title": "Query2", "type": "string"},
                        "name": "query2",
                        "in": "query",
                    },
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {
                                "schema": {"title": "Response Model", "type": "object"}
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
    },
    "components": {
        "schemas": {
            "HTTPValidationError": {
                "title": "HTTPValidationError",
                "required": ["detail"],
                "type": "object",
                "properties": {
                    "detail": {
                        "title": "Details",
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/ValidationError"},
                    }
                },
            },
            "Range": {
                "title": "Range",
                "enum": [20, 50, 200],
                "type": "integer",
                "description": "An enumeration.",
            },
            "ValidationError": {
                "title": "ValidationError",
                "required": ["loc", "msg", "type"],
                "type": "object",
                "properties": {
                    "loc": {
                        "title": "Location",
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "msg": {"title": "Message", "type": "string"},
                    "type": {"title": "Error Type", "type": "string"},
                },
            },
        }
    },
    "tags": [],
}


def test_openapi_schema():
    document = serialize_object(OpenAPIDocumentBuilder().build_document(tm.app))
    assert document == openapi_schema


def test_query_params_extra():
    client = tm.get_client()
    response = client.get(
        "/test?from=1&to=2&range=20&foo=1&range2=50&query1=somequery1&query2=somequery2"
    )
    assert response.json() == {
        "to_datetime": "1970-01-01T00:00:02+00:00",
        "from_datetime": "1970-01-01T00:00:01+00:00",
        "range": 20,
        "query1": "somequery1",
        "query2": "somequery2",
    }

    response = client.get("/test?from=1&to=2&range=20&foo=1&range2=50")
    assert response.status_code == 422
