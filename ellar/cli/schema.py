import typing as t

from pydantic.fields import Field

from ellar.core import schema


class EllarPyProjectSerializer(schema.Serializer):
    project_name: str = Field(alias="project-name")
    application: str = Field(alias="application")
    config: str = Field(alias="config")
    root_module: str = Field(alias="root-module")
    apps_module: str = Field(alias="apps-module")


class EllarScaffoldList(schema.Serializer):
    name: str
    is_directory: bool
    name_in_context: t.Optional[bool] = Field(default=None, alias="name-context")
    files: t.Optional[t.List["EllarScaffoldList"]]


EllarScaffoldList.update_forward_refs()


class EllarScaffoldSchema(schema.Serializer):
    context: t.List[str]
    files: t.List[EllarScaffoldList]
