import typing

from starletteapi.routing.route_models.route_param_model import RouteParameterModel


class OpenAPIDocumentation:
    def __init__(
            self,
            *,
            route_parameter_model: RouteParameterModel,
            operation_id: typing.Optional[str] = None,
            summary: typing.Optional[str] = None,
            description: typing.Optional[str] = None,
            tags: typing.Optional[typing.List[str]] = None,
            deprecated: typing.Optional[bool] = None,
    ):

        self.operation_id = operation_id
        self.summary = summary
        self.description = description
        self.tags = tags
        self.deprecated = deprecated
        self.route_parameter_model = route_parameter_model

        if tags and not isinstance(tags, list):
            self.tags = [self.tags]
