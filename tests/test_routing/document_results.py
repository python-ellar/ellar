FORM_OPENAPI_DOC = {
    "openapi": "3.0.2",
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
                                "title": "Body",
                                "allOf": [
                                    {
                                        "$ref": "#/components/schemas/body_form_upload_single_case_1__post"
                                    }
                                ],
                                "include_in_schema": True,
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
        },
        "/form-with-schema-spreading": {
            "post": {
                "tags": ["default"],
                "operationId": "form_params_schema_spreading_form_with_schema_spreading_post",
                "requestBody": {
                    "content": {
                        "multipart/form-data": {
                            "schema": {
                                "title": "Body",
                                "allOf": [
                                    {
                                        "$ref": "#/components/schemas/body_form_params_schema_spreading_form_with_schema_spreading_post"
                                    }
                                ],
                                "include_in_schema": True,
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
        },
        "/mixed": {
            "post": {
                "tags": ["default"],
                "operationId": "form_upload_single_case_2_mixed_post",
                "requestBody": {
                    "content": {
                        "multipart/form-data": {
                            "schema": {
                                "title": "Body",
                                "allOf": [
                                    {
                                        "$ref": "#/components/schemas/body_form_upload_single_case_2_mixed_post"
                                    }
                                ],
                                "include_in_schema": True,
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
        },
        "/mixed-optional": {
            "post": {
                "tags": ["default"],
                "operationId": "form_upload_multiple_case_2_mixed_optional_post",
                "requestBody": {
                    "content": {
                        "multipart/form-data": {
                            "schema": {
                                "title": "Body",
                                "allOf": [
                                    {
                                        "$ref": "#/components/schemas/body_form_upload_multiple_case_2_mixed_optional_post"
                                    }
                                ],
                                "include_in_schema": True,
                            }
                        }
                    }
                },
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
        },
        "/multiple": {
            "post": {
                "tags": ["default"],
                "operationId": "form_upload_multiple_case_1_multiple_post",
                "requestBody": {
                    "content": {
                        "multipart/form-data": {
                            "schema": {
                                "title": "Body",
                                "allOf": [
                                    {
                                        "$ref": "#/components/schemas/body_form_upload_multiple_case_1_multiple_post"
                                    }
                                ],
                                "include_in_schema": True,
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
        },
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
            "body_form_params_schema_spreading_form_with_schema_spreading_post": {
                # form inputs are combined into one just like json body fields
                "title": "body_form_params_schema_spreading_form_with_schema_spreading_post",
                "required": ["momentOfTruth"],
                "type": "object",
                "properties": {
                    "momentOfTruth": {
                        "title": "Momentoftruth",
                        "type": "string",
                        "format": "binary",
                        "include_in_schema": True,
                    },
                    "to": {
                        "title": "To",
                        "type": "string",
                        "format": "date-time",
                        "include_in_schema": True,
                    },
                    "from": {
                        "title": "From",
                        "type": "string",
                        "format": "date-time",
                        "include_in_schema": True,
                    },
                    "range": {
                        "allOf": [{"$ref": "#/components/schemas/Range"}],
                        "default": 20,
                        "include_in_schema": True,
                    },
                },
            },
            "body_form_upload_multiple_case_1_multiple_post": {
                "title": "body_form_upload_multiple_case_1_multiple_post",
                "required": ["test1"],
                "type": "object",
                "properties": {
                    "test1": {
                        "title": "Test1",
                        "type": "array",
                        "items": {
                            "anyOf": [
                                {"type": "string", "format": "binary"},
                                {"type": "string"},
                            ]
                        },
                        "include_in_schema": True,
                    }
                },
            },
            "body_form_upload_multiple_case_2_mixed_optional_post": {
                "title": "body_form_upload_multiple_case_2_mixed_optional_post",
                "type": "object",
                "properties": {
                    "file": {
                        "title": "File",
                        "type": "string",
                        "format": "binary",
                        "include_in_schema": True,
                    },
                    "field0": {
                        "title": "Field0",
                        "type": "string",
                        "default": "",
                        "include_in_schema": True,
                    },
                    "field1": {
                        "title": "Field1",
                        "type": "string",
                        "include_in_schema": True,
                    },
                },
            },
            "body_form_upload_single_case_1__post": {
                "title": "body_form_upload_single_case_1__post",
                "required": ["test"],
                "type": "object",
                "properties": {
                    "test": {
                        "title": "Test",
                        "type": "string",
                        "format": "binary",
                        "include_in_schema": True,
                    }
                },
            },
            "body_form_upload_single_case_2_mixed_post": {
                "title": "body_form_upload_single_case_2_mixed_post",
                "required": ["test_alias", "test2"],
                "type": "object",
                "properties": {
                    "test_alias": {
                        "title": "Test Alias",
                        "type": "string",
                        "format": "binary",
                        "include_in_schema": True,
                    },
                    "test2": {
                        "title": "Test2",
                        "type": "string",
                        "format": "binary",
                        "include_in_schema": True,
                    },
                },
            },
        }
    },
    "tags": [],
}
