import typing as t
from enum import Enum

from ellar.common.serializer import Serializer, SerializerFilter
from ellar.pydantic import AnyUrl, BaseModel, EmailStr, Field, model_rebuild


class Contact(BaseModel):
    name: t.Optional[str] = None
    url: t.Optional[AnyUrl] = None
    email: t.Optional[EmailStr] = None

    model_config = {"extra": "allow"}


class License(BaseModel):
    name: str
    url: t.Optional[AnyUrl] = None

    model_config = {"extra": "allow"}


class Info(BaseModel):
    title: str
    description: t.Optional[str] = None
    termsOfService: t.Optional[str] = None
    contact: t.Optional[Contact] = None
    license: t.Optional[License] = None
    version: str

    model_config = {"extra": "allow"}


class ServerVariable(BaseModel):
    enum: t.Optional[t.List[str]] = None
    default: str
    description: t.Optional[str] = None

    model_config = {"extra": "allow"}


class Server(BaseModel):
    url: t.Union[AnyUrl, str]
    description: t.Optional[str] = None
    variables: t.Optional[t.Dict[str, ServerVariable]] = None

    model_config = {"extra": "allow"}


class Reference(BaseModel):
    ref: str = Field(..., alias="$ref")


class Discriminator(BaseModel):
    propertyName: str
    mapping: t.Optional[t.Dict[str, str]] = None


class XML(BaseModel):
    name: t.Optional[str] = None
    namespace: t.Optional[str] = None
    prefix: t.Optional[str] = None
    attribute: t.Optional[bool] = None
    wrapped: t.Optional[bool] = None

    model_config = {"extra": "allow"}


class ExternalDocumentation(BaseModel):
    description: t.Optional[str] = None
    url: AnyUrl

    model_config = {"extra": "allow"}


class Schema(BaseModel):
    # Ref: JSON Schema 2020-12: https://json-schema.org/draft/2020-12/json-schema-core.html#name-the-json-schema-core-vocabu
    # Core Vocabulary
    schema_: t.Optional[str] = Field(default=None, alias="$schema")
    vocabulary: t.Optional[str] = Field(default=None, alias="$vocabulary")
    id: t.Optional[str] = Field(default=None, alias="$id")
    anchor: t.Optional[str] = Field(default=None, alias="$anchor")
    dynamicAnchor: t.Optional[str] = Field(default=None, alias="$dynamicAnchor")
    ref: t.Optional[str] = Field(default=None, alias="$ref")
    dynamicRef: t.Optional[str] = Field(default=None, alias="$dynamicRef")
    defs: t.Optional[t.Dict[str, "SchemaOrBool"]] = Field(default=None, alias="$defs")
    comment: t.Optional[str] = Field(default=None, alias="$comment")
    # Ref: JSON Schema 2020-12: https://json-schema.org/draft/2020-12/json-schema-core.html#name-a-vocabulary-for-applying-s
    # A Vocabulary for Applying Subschemas
    allOf: t.Optional[t.List["SchemaOrBool"]] = None
    anyOf: t.Optional[t.List["SchemaOrBool"]] = None
    oneOf: t.Optional[t.List["SchemaOrBool"]] = None
    not_: t.Optional["SchemaOrBool"] = Field(default=None, alias="not")
    if_: t.Optional["SchemaOrBool"] = Field(default=None, alias="if")
    then: t.Optional["SchemaOrBool"] = None
    else_: t.Optional["SchemaOrBool"] = Field(default=None, alias="else")
    dependentSchemas: t.Optional[t.Dict[str, "SchemaOrBool"]] = None
    prefixItems: t.Optional[t.List["SchemaOrBool"]] = None
    # TODO: uncomment and remove below when deprecating Pydantic v1
    # It generales a list of schemas for tuples, before prefixItems was available
    # items: Optional["SchemaOrBool"] = None
    items: t.Optional[t.Union["SchemaOrBool", t.List["SchemaOrBool"]]] = None
    contains: t.Optional["SchemaOrBool"] = None
    properties: t.Optional[t.Dict[str, "SchemaOrBool"]] = None
    patternProperties: t.Optional[t.Dict[str, "SchemaOrBool"]] = None
    additionalProperties: t.Optional["SchemaOrBool"] = None
    propertyNames: t.Optional["SchemaOrBool"] = None
    unevaluatedItems: t.Optional["SchemaOrBool"] = None
    unevaluatedProperties: t.Optional["SchemaOrBool"] = None
    # Ref: JSON Schema Validation 2020-12: https://json-schema.org/draft/2020-12/json-schema-validation.html#name-a-vocabulary-for-structural
    # A Vocabulary for Structural Validation
    type: t.Optional[str] = None
    enum: t.Optional[t.List[t.Any]] = None
    const: t.Optional[t.Any] = None
    multipleOf: t.Optional[float] = Field(default=None, gt=0)
    maximum: t.Optional[float] = None
    exclusiveMaximum: t.Optional[float] = None
    minimum: t.Optional[float] = None
    exclusiveMinimum: t.Optional[float] = None
    maxLength: t.Optional[int] = Field(default=None, ge=0)
    minLength: t.Optional[int] = Field(default=None, ge=0)
    pattern: t.Optional[str] = None
    maxItems: t.Optional[int] = Field(default=None, ge=0)
    minItems: t.Optional[int] = Field(default=None, ge=0)
    uniqueItems: t.Optional[bool] = None
    maxContains: t.Optional[int] = Field(default=None, ge=0)
    minContains: t.Optional[int] = Field(default=None, ge=0)
    maxProperties: t.Optional[int] = Field(default=None, ge=0)
    minProperties: t.Optional[int] = Field(default=None, ge=0)
    required: t.Optional[t.List[str]] = None
    dependentRequired: t.Optional[t.Dict[str, t.Set[str]]] = None
    # Ref: JSON Schema Validation 2020-12: https://json-schema.org/draft/2020-12/json-schema-validation.html#name-vocabularies-for-semantic-c
    # Vocabularies for Semantic Content With "format"
    format: t.Optional[str] = None
    # Ref: JSON Schema Validation 2020-12: https://json-schema.org/draft/2020-12/json-schema-validation.html#name-a-vocabulary-for-the-conten
    # A Vocabulary for the Contents of String-Encoded Data
    contentEncoding: t.Optional[str] = None
    contentMediaType: t.Optional[str] = None
    contentSchema: t.Optional["SchemaOrBool"] = None
    # Ref: JSON Schema Validation 2020-12: https://json-schema.org/draft/2020-12/json-schema-validation.html#name-a-vocabulary-for-basic-meta
    # A Vocabulary for Basic Meta-Data Annotations
    title: t.Optional[str] = None
    description: t.Optional[str] = None
    default: t.Optional[t.Any] = None
    deprecated: t.Optional[bool] = None
    readOnly: t.Optional[bool] = None
    writeOnly: t.Optional[bool] = None
    examples: t.Optional[t.List[t.Any]] = None
    # Ref: OpenAPI 3.1.0: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.0.md#schema-object
    # Schema Object
    discriminator: t.Optional[Discriminator] = None
    xml: t.Optional[XML] = None
    externalDocs: t.Optional[ExternalDocumentation] = None

    model_config = {"extra": "allow"}


# Ref: https://json-schema.org/draft/2020-12/json-schema-core.html#name-json-schema-documents
# A JSON Schema MUST be an object or a boolean.
SchemaOrBool = t.Union[Schema, bool]


class Example(BaseModel):
    summary: t.Optional[str] = None
    description: t.Optional[str] = None
    value: t.Optional[t.Any] = None
    externalValue: t.Optional[AnyUrl] = None

    model_config = {"extra": "allow"}


class ParameterInType(Enum):
    query = "query"
    header = "header"
    path = "path"
    cookie = "cookie"


class Encoding(BaseModel):
    contentType: t.Optional[str] = None
    headers: t.Optional[t.Dict[str, t.Union["Header", Reference]]] = None
    style: t.Optional[str] = None
    explode: t.Optional[bool] = None
    allowReserved: t.Optional[bool] = None

    model_config = {"extra": "allow"}


class MediaType(BaseModel):
    schema_: t.Optional[t.Union[Schema, Reference]] = Field(None, alias="schema")
    example: t.Optional[t.Any] = None
    examples: t.Optional[t.Dict[str, t.Union[Example, Reference]]] = None
    encoding: t.Optional[t.Dict[str, Encoding]] = None

    model_config = {"extra": "allow"}


class ParameterBase(BaseModel):
    description: t.Optional[str] = None
    required: t.Optional[bool] = None
    deprecated: t.Optional[bool] = None

    style: t.Optional[str] = None
    explode: t.Optional[bool] = None
    allowReserved: t.Optional[bool] = None
    schema_: t.Optional[t.Union[Schema, Reference]] = Field(None, alias="schema")
    example: t.Optional[t.Any] = None
    examples: t.Optional[t.Dict[str, t.Union[Example, Reference]]] = None

    content: t.Optional[t.Dict[str, MediaType]] = None

    model_config = {"extra": "allow"}


class Parameter(ParameterBase):
    name: str
    in_: ParameterInType = Field(..., alias="in")


class Header(ParameterBase):
    pass


class RequestBody(BaseModel):
    description: t.Optional[str] = None
    content: t.Dict[str, MediaType]
    required: t.Optional[bool] = None

    model_config = {"extra": "allow"}


class Link(BaseModel):
    operationRef: t.Optional[str] = None
    operationId: t.Optional[str] = None
    parameters: t.Optional[t.Dict[str, t.Union[t.Any, str]]] = None
    requestBody: t.Optional[t.Union[t.Any, str]] = None
    description: t.Optional[str] = None
    server: t.Optional[Server] = None

    model_config = {"extra": "allow"}


class Response(BaseModel):
    description: str
    headers: t.Optional[t.Dict[str, t.Union[Header, Reference]]] = None
    content: t.Optional[t.Dict[str, MediaType]] = None
    links: t.Optional[t.Dict[str, t.Union[Link, Reference]]] = None

    model_config = {"extra": "allow"}


class Operation(BaseModel):
    tags: t.Optional[t.List[str]] = None
    summary: t.Optional[str] = None
    description: t.Optional[str] = None
    externalDocs: t.Optional[ExternalDocumentation] = None
    operationId: t.Optional[str] = None
    parameters: t.Optional[t.List[t.Union[Parameter, Reference]]] = None
    requestBody: t.Optional[t.Union[RequestBody, Reference]] = None

    responses: t.Dict[str, t.Union[Response, t.Any]]
    callbacks: t.Optional[t.Dict[str, t.Union[t.Dict[str, "PathItem"], Reference]]] = (
        None
    )
    deprecated: t.Optional[bool] = None
    security: t.Optional[t.List[t.Dict[str, t.List[str]]]] = None
    servers: t.Optional[t.List[Server]] = None

    model_config = {"extra": "allow"}


class PathItem(BaseModel):
    ref: t.Optional[str] = Field(None, alias="$ref")
    summary: t.Optional[str] = None
    description: t.Optional[str] = None
    get: t.Optional[Operation] = None
    put: t.Optional[Operation] = None
    post: t.Optional[Operation] = None
    delete: t.Optional[Operation] = None
    options: t.Optional[Operation] = None
    head: t.Optional[Operation] = None
    patch: t.Optional[Operation] = None
    trace: t.Optional[Operation] = None
    servers: t.Optional[t.List[Server]] = None
    parameters: t.Optional[t.List[t.Union[Parameter, Reference]]] = None

    model_config = {"extra": "allow"}


class SecuritySchemeType(Enum):
    apiKey = "apiKey"
    http = "http"
    oauth2 = "oauth2"
    openIdConnect = "openIdConnect"


class SecurityBase(BaseModel):
    type_: SecuritySchemeType = Field(..., alias="type")
    description: t.Optional[str] = None

    model_config = {"extra": "allow"}


class APIKeyIn(Enum):
    query = "query"
    header = "header"
    cookie = "cookie"


class APIKey(SecurityBase):
    type_: SecuritySchemeType = Field(default=SecuritySchemeType.apiKey, alias="type")
    in_: APIKeyIn = Field(alias="in")
    name: str


class HTTPBase(SecurityBase):
    type_: SecuritySchemeType = Field(default=SecuritySchemeType.http, alias="type")
    scheme: str


class HTTPBearer(HTTPBase):
    scheme: t.Literal["bearer"] = "bearer"
    bearerFormat: t.Optional[str] = None


class OAuthFlow(BaseModel):
    refreshUrl: t.Optional[str] = None
    scopes: t.Dict[str, str] = {}

    model_config = {"extra": "allow"}


class OAuthFlowImplicit(OAuthFlow):
    authorizationUrl: str


class OAuthFlowPassword(OAuthFlow):
    tokenUrl: str


class OAuthFlowClientCredentials(OAuthFlow):
    tokenUrl: str


class OAuthFlowAuthorizationCode(OAuthFlow):
    authorizationUrl: str
    tokenUrl: str


class OAuthFlows(BaseModel):
    implicit: t.Optional[OAuthFlowImplicit] = None
    password: t.Optional[OAuthFlowPassword] = None
    clientCredentials: t.Optional[OAuthFlowClientCredentials] = None
    authorizationCode: t.Optional[OAuthFlowAuthorizationCode] = None

    model_config = {"extra": "allow"}


class OAuth2(SecurityBase):
    type_: SecuritySchemeType = Field(default=SecuritySchemeType.oauth2, alias="type")
    flows: OAuthFlows


class OpenIdConnect(SecurityBase):
    type_: SecuritySchemeType = Field(
        default=SecuritySchemeType.openIdConnect, alias="type"
    )
    openIdConnectUrl: str


SecurityScheme = t.Union[APIKey, HTTPBase, OAuth2, OpenIdConnect, HTTPBearer]


class Components(BaseModel):
    schemas: t.Optional[t.Dict[str, t.Union[Schema, Reference]]] = None
    responses: t.Optional[t.Dict[str, t.Union[Response, Reference]]] = None
    parameters: t.Optional[t.Dict[str, t.Union[Parameter, Reference]]] = None
    examples: t.Optional[t.Dict[str, t.Union[Example, Reference]]] = None
    requestBodies: t.Optional[t.Dict[str, t.Union[RequestBody, Reference]]] = None
    headers: t.Optional[t.Dict[str, t.Union[Header, Reference]]] = None
    securitySchemes: t.Optional[t.Dict[str, t.Union[SecurityScheme, Reference]]] = None
    links: t.Optional[t.Dict[str, t.Union[Link, Reference]]] = None

    callbacks: t.Optional[
        t.Dict[str, t.Union[t.Dict[str, PathItem], Reference, t.Any]]
    ] = None

    model_config = {"extra": "allow"}


class Tag(BaseModel):
    name: str
    description: t.Optional[str] = None
    externalDocs: t.Optional[ExternalDocumentation] = None

    model_config = {"extra": "allow"}


class OpenAPI(Serializer):
    _filter = SerializerFilter(exclude_none=True, by_alias=True)

    openapi: str
    info: Info
    servers: t.Optional[t.List[Server]] = None

    paths: t.Dict[str, PathItem]
    components: t.Optional[Components] = None
    security: t.Optional[t.List[t.Dict[str, t.List[str]]]] = None
    tags: t.Optional[t.List[Tag]] = None
    externalDocs: t.Optional[ExternalDocumentation] = None

    model_config = {"extra": "allow"}


model_rebuild(Schema)
model_rebuild(Operation)
model_rebuild(Encoding)
