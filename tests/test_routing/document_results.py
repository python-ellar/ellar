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
                                "title": "Test",
                                "type": "string",
                                "format": "binary",
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
