import typing as t
from enum import Enum

from ellar.common.compatible import EmailStr
from ellar.common.serializer import Serializer, SerializerFilter
from pydantic import AnyUrl, BaseModel, Field


class Contact(BaseModel):
    name: t.Optional[str] = None
    url: t.Optional[AnyUrl] = None
    email: t.Optional[EmailStr] = None

    class Config:
        extra = "allow"


class License(BaseModel):
    name: str
    url: t.Optional[AnyUrl] = None

    class Config:
        extra = "allow"


class Info(BaseModel):
    title: str
    description: t.Optional[str] = None
    termsOfService: t.Optional[str] = None
    contact: t.Optional[Contact] = None
    license: t.Optional[License] = None
    version: str

    class Config:
        extra = "allow"


class ServerVariable(BaseModel):
    enum: t.Optional[t.List[str]] = None
    default: str
    description: t.Optional[str] = None

    class Config:
        extra = "allow"


class Server(BaseModel):
    url: t.Union[AnyUrl, str]
    description: t.Optional[str] = None
    variables: t.Optional[t.Dict[str, ServerVariable]] = None

    class Config:
        extra = "allow"


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

    class Config:
        extra = "allow"


class ExternalDocumentation(BaseModel):
    description: t.Optional[str] = None
    url: AnyUrl

    class Config:
        extra = "allow"


class Schema(BaseModel):
    ref: t.Optional[str] = Field(None, alias="$ref")
    title: t.Optional[str] = None
    multipleOf: t.Optional[float] = None
    maximum: t.Optional[float] = None
    exclusiveMaximum: t.Optional[float] = None
    minimum: t.Optional[float] = None
    exclusiveMinimum: t.Optional[float] = None
    maxLength: t.Optional[int] = Field(None, gte=0)
    minLength: t.Optional[int] = Field(None, gte=0)
    pattern: t.Optional[str] = None
    maxItems: t.Optional[int] = Field(None, gte=0)
    minItems: t.Optional[int] = Field(None, gte=0)
    uniqueItems: t.Optional[bool] = None
    maxProperties: t.Optional[int] = Field(None, gte=0)
    minProperties: t.Optional[int] = Field(None, gte=0)
    required: t.Optional[t.List[str]] = None
    enum: t.Optional[t.List[t.Any]] = None
    type: t.Optional[str] = None
    allOf: t.Optional[t.List["Schema"]] = None
    oneOf: t.Optional[t.List["Schema"]] = None
    AnyOf: t.Optional[t.List["Schema"]] = None
    not_: t.Optional["Schema"] = Field(None, alias="not")
    items: t.Optional["Schema"] = None
    properties: t.Optional[t.Dict[str, "Schema"]] = None
    additionalProperties: t.Optional[t.Union["Schema", Reference, bool]] = None
    description: t.Optional[str] = None
    format: t.Optional[str] = None
    default: t.Optional[t.Any] = None
    nullable: t.Optional[bool] = None
    discriminator: t.Optional[Discriminator] = None
    readOnly: t.Optional[bool] = None
    writeOnly: t.Optional[bool] = None
    xml: t.Optional[XML] = None
    externalDocs: t.Optional[ExternalDocumentation] = None
    example: t.Optional[t.Any] = None
    deprecated: t.Optional[bool] = None

    class Config:
        extra: str = "allow"


class Example(BaseModel):
    summary: t.Optional[str] = None
    description: t.Optional[str] = None
    value: t.Optional[t.Any] = None
    externalValue: t.Optional[AnyUrl] = None

    class Config:
        extra = "allow"


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

    class Config:
        extra = "allow"


class MediaType(BaseModel):
    schema_: t.Optional[t.Union[Schema, Reference]] = Field(None, alias="schema")
    example: t.Optional[t.Any] = None
    examples: t.Optional[t.Dict[str, t.Union[Example, Reference]]] = None
    encoding: t.Optional[t.Dict[str, Encoding]] = None

    class Config:
        extra = "allow"


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

    class Config:
        extra = "allow"


class Parameter(ParameterBase):
    name: str
    in_: ParameterInType = Field(..., alias="in")


class Header(ParameterBase):
    pass


class RequestBody(BaseModel):
    description: t.Optional[str] = None
    content: t.Dict[str, MediaType]
    required: t.Optional[bool] = None

    class Config:
        extra = "allow"


class Link(BaseModel):
    operationRef: t.Optional[str] = None
    operationId: t.Optional[str] = None
    parameters: t.Optional[t.Dict[str, t.Union[t.Any, str]]] = None
    requestBody: t.Optional[t.Union[t.Any, str]] = None
    description: t.Optional[str] = None
    server: t.Optional[Server] = None

    class Config:
        extra = "allow"


class Response(BaseModel):
    description: str
    headers: t.Optional[t.Dict[str, t.Union[Header, Reference]]] = None
    content: t.Optional[t.Dict[str, MediaType]] = None
    links: t.Optional[t.Dict[str, t.Union[Link, Reference]]] = None

    class Config:
        extra = "allow"


class Operation(BaseModel):
    tags: t.Optional[t.List[str]] = None
    summary: t.Optional[str] = None
    description: t.Optional[str] = None
    externalDocs: t.Optional[ExternalDocumentation] = None
    operationId: t.Optional[str] = None
    parameters: t.Optional[t.List[t.Union[Parameter, Reference]]] = None
    requestBody: t.Optional[t.Union[RequestBody, Reference]] = None

    responses: t.Dict[str, t.Union[Response, t.Any]]
    callbacks: t.Optional[
        t.Dict[str, t.Union[t.Dict[str, "PathItem"], Reference]]
    ] = None
    deprecated: t.Optional[bool] = None
    security: t.Optional[t.List[t.Dict[str, t.List[str]]]] = None
    servers: t.Optional[t.List[Server]] = None

    class Config:
        extra = "allow"


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

    class Config:
        extra = "allow"


class SecuritySchemeType(Enum):
    apiKey = "apiKey"
    http = "http"
    oauth2 = "oauth2"
    openIdConnect = "openIdConnect"


class SecurityBase(BaseModel):
    type_: SecuritySchemeType = Field(..., alias="type")
    description: t.Optional[str] = None

    class Config:
        extra = "allow"


class APIKeyIn(Enum):
    query = "query"
    header = "header"
    cookie = "cookie"


class APIKey(SecurityBase):
    type_ = Field(SecuritySchemeType.apiKey, alias="type")
    in_: APIKeyIn = Field(..., alias="in")
    name: str


class HTTPBase(SecurityBase):
    type_ = Field(SecuritySchemeType.http, alias="type")
    scheme: str


class HTTPBearer(HTTPBase):
    scheme = "bearer"
    bearerFormat: t.Optional[str] = None


class OAuthFlow(BaseModel):
    refreshUrl: t.Optional[str] = None
    scopes: t.Dict[str, str] = {}

    class Config:
        extra = "allow"


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

    class Config:
        extra = "allow"


class OAuth2(SecurityBase):
    type_ = Field(SecuritySchemeType.oauth2, alias="type")
    flows: OAuthFlows


class OpenIdConnect(SecurityBase):
    type_ = Field(SecuritySchemeType.openIdConnect, alias="type")
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

    class Config:
        extra = "allow"


class Tag(BaseModel):
    name: str
    description: t.Optional[str] = None
    externalDocs: t.Optional[ExternalDocumentation] = None

    class Config:
        extra = "allow"


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

    class Config:
        extra = "allow"


Schema.update_forward_refs()
Operation.update_forward_refs()
Encoding.update_forward_refs()
