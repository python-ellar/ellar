FORM_OPENAPI_DOC = {
    "openapi": "3.1.0",
    "info": {"title": "Ellar API Docs", "version": "1.0.0"},
    "paths": {
        "/": {
            "post": {
                "tags": ["default"],
                "operationId": "form_upload_single_case_1__post",
                "requestBody": {
                    "content": {
                        "multipart/form-data": {
                            "schema": {
                                "$ref": "#/components/schemas/body_form_upload_single_case_1__post"
                            }
                        }
                    },
                    "required": True,
                },
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {
                                "schema": {"type": "object", "title": "Response Model"}
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
        },
        "/form-with-schema-spreading": {
            "post": {
                "tags": ["default"],
                "operationId": "form_params_schema_spreading_form_with_schema_spreading_post",
                "requestBody": {
                    "content": {
                        "multipart/form-data": {
                            "schema": {
                                "$ref": "#/components/schemas/body_form_params_schema_spreading_form_with_schema_spreading_post"
                            }
                        }
                    },
                    "required": True,
                },
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {
                                "schema": {"type": "object", "title": "Response Model"}
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
        },
        "/mixed": {
            "post": {
                "tags": ["default"],
                "operationId": "form_upload_single_case_2_mixed_post",
                "requestBody": {
                    "content": {
                        "multipart/form-data": {
                            "schema": {
                                "$ref": "#/components/schemas/body_form_upload_single_case_2_mixed_post"
                            }
                        }
                    },
                    "required": True,
                },
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {
                                "schema": {"type": "object", "title": "Response Model"}
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
        },
        "/mixed-optional": {
            "post": {
                "tags": ["default"],
                "operationId": "form_upload_multiple_case_2_mixed_optional_post",
                "requestBody": {
                    "content": {
                        "multipart/form-data": {
                            "schema": {
                                "allOf": [
                                    {
                                        "$ref": "#/components/schemas/body_form_upload_multiple_case_2_mixed_optional_post"
                                    }
                                ],
                                "title": "Body",
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {
                                "schema": {"type": "object", "title": "Response Model"}
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
        },
        "/multiple": {
            "post": {
                "tags": ["default"],
                "operationId": "form_upload_multiple_case_1_multiple_post",
                "requestBody": {
                    "content": {
                        "multipart/form-data": {
                            "schema": {
                                "$ref": "#/components/schemas/body_form_upload_multiple_case_1_multiple_post"
                            }
                        }
                    },
                    "required": True,
                },
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {
                                "schema": {"type": "object", "title": "Response Model"}
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
        },
    },
    "components": {
        "schemas": {
            "HTTPValidationError": {
                "properties": {
                    "detail": {
                        "items": {"$ref": "#/components/schemas/ValidationError"},
                        "type": "array",
                        "title": "Details",
                    }
                },
                "type": "object",
                "required": ["detail"],
                "title": "HTTPValidationError",
            },
            "Range": {"type": "integer", "enum": [20, 50, 200], "title": "Range"},
            "ValidationError": {
                "properties": {
                    "loc": {
                        "items": {"type": "string"},
                        "type": "array",
                        "title": "Location",
                    },
                    "msg": {"type": "string", "title": "Message"},
                    "type": {"type": "string", "title": "Error Type"},
                },
                "type": "object",
                "required": ["loc", "msg", "type"],
                "title": "ValidationError",
            },
            "body_form_params_schema_spreading_form_with_schema_spreading_post": {
                "properties": {
                    "momentOfTruth": {
                        "type": "string",
                        "format": "binary",
                        "title": "Momentoftruth",
                    },
                    "to": {
                        "type": "string",
                        "format": "date-time",
                        "title": "To",
                        "repr": True,
                    },
                    "from": {
                        "type": "string",
                        "format": "date-time",
                        "title": "From",
                        "repr": True,
                    },
                    "range": {
                        "allOf": [{"$ref": "#/components/schemas/Range"}],
                        "default": 20,
                        "repr": True,
                    },
                },
                "type": "object",
                "required": ["momentOfTruth", "to", "from"],
                "title": "body_form_params_schema_spreading_form_with_schema_spreading_post",
            },
            "body_form_upload_multiple_case_1_multiple_post": {
                "properties": {
                    "test1": {
                        "items": {
                            "anyOf": [
                                {"type": "string", "format": "binary"},
                                {"type": "string"},
                            ]
                        },
                        "type": "array",
                        "title": "Test1",
                    }
                },
                "type": "object",
                "required": ["test1"],
                "title": "body_form_upload_multiple_case_1_multiple_post",
            },
            "body_form_upload_multiple_case_2_mixed_optional_post": {
                "properties": {
                    "file": {"type": "string", "format": "binary", "title": "File"},
                    "field0": {"type": "string", "title": "Field0", "default": ""},
                    "field1": {"type": "string", "title": "Field1"},
                },
                "type": "object",
                "title": "body_form_upload_multiple_case_2_mixed_optional_post",
            },
            "body_form_upload_single_case_1__post": {
                "properties": {
                    "test": {"type": "string", "format": "binary", "title": "Test"}
                },
                "type": "object",
                "required": ["test"],
                "title": "body_form_upload_single_case_1__post",
            },
            "body_form_upload_single_case_2_mixed_post": {
                "properties": {
                    "test_alias": {
                        "type": "string",
                        "format": "binary",
                        "title": "Test Alias",
                    },
                    "test2": {"type": "string", "format": "binary", "title": "Test2"},
                },
                "type": "object",
                "required": ["test_alias", "test2"],
                "title": "body_form_upload_single_case_2_mixed_post",
            },
        }
    },
    "tags": [],
}
