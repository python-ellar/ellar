from functools import wraps

from ellar.common import IExecutionContext, Inject, Query, extra_args, get
from ellar.common.params import ExtraEndpointArg
from ellar.common.serializer import serialize_object
from ellar.core.connection import Request
from ellar.openapi import OpenAPIDocumentBuilder
from ellar.testing import Test
from starlette.responses import Response

from .sample import Filter

tm = Test.create_test_module()
app = tm.create_application()


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
        name="context", annotation=Inject[IExecutionContext], default_value=None
    )
    response = ExtraEndpointArg(
        name="response", annotation=Inject[Response], default_value=None
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
    request: Inject[Request],
    filters: Filter = Query(),
):
    return filters.dict()


app.router.append(query_params_extra)

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
                            "include_in_schema": True,
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
                            "include_in_schema": True,
                        },
                        "name": "from",
                        "in": "query",
                    },
                    {
                        "required": False,
                        "schema": {
                            "allOf": [{"$ref": "#/components/schemas/Range"}],
                            "default": 20,
                            "include_in_schema": True,
                        },
                        "name": "range",
                        "in": "query",
                    },
                    {
                        "required": True,
                        "schema": {
                            "title": "Query1",
                            "type": "string",
                            "include_in_schema": True,
                        },
                        "name": "query1",
                        "in": "query",
                    },
                    {
                        "required": True,
                        "schema": {
                            "title": "Query2",
                            "type": "string",
                            "include_in_schema": True,
                        },
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
    document = serialize_object(OpenAPIDocumentBuilder().build_document(app))
    assert document == openapi_schema


def test_query_params_extra():
    client = tm.get_test_client()
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
