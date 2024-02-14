# **Documentation UserInterface**
The `IDocumentationUI` interface serves as a fundamental abstraction within Ellar, 
enabling seamless integration with various openapi documentation rendering libraries such as `Swagger`, `ReDocs`, and others.

```python
import typing as t
from abc import ABC, abstractmethod

class IDocumentationUI(ABC):
    """
    Defines the contract for integrating openapi documentation rendering libraries within Ellar.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the documentation UI, e.g., Swagger, ReDocs, Stoplight."""

    @property
    @abstractmethod
    def path(self) -> str:
        """The preferred URL path for accessing the documentation."""

    @property
    @abstractmethod
    def template_name(self) -> t.Optional[str]:
        """
        The name of the HTML template used for rendering the documentation UI.
        If None, the `template_string` attribute will be used for inline template rendering.
        """

    @property
    def template_string(self) -> t.Optional[str]:
        """
        The templated HTML string for rendering the documentation UI.
        If a template file is used (`template_name` is not None), this attribute should be None.
        """
        return None

    @property
    @abstractmethod
    def template_context(self) -> dict:
        """
        Additional settings and context data to be passed to the documentation template.
        """

```

By implementing the `IDocumentationUI` interface, developers can extend 
Ellar's capabilities to support additional documentation rendering libraries 
beyond the default support for `Swagger` and `ReDocs`.

## **SwaggerUI Integration**
Ellar provides built-in support for rendering [Swagger UI](https://swagger.io/tools/swagger-ui/), enabling interaction with API resources. It offers flexibility through various initialization parameters.

```python
from ellar.openapi import SwaggerUI

swagger_ui = SwaggerUI(
    path= "docs",
    title="EllarSwagger Doc",
    swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
    swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
    favicon_url="https://eadwincode.github.io/ellar/img/Icon.svg",
    dark_theme=False,
)
```

### Properties
- **path**: The URL path used to access the Swagger UI page.
- **title**: The title displayed in the HTML header.
- **swagger_js_url**: The CDN URL for Swagger JS.
- **swagger_css_url**: The CDN URL for Swagger CSS.
- **favicon_url**: The URL for the HTML favicon.
- **dark_theme**: Indicates whether to apply a dark theme to Swagger CSS.

## **ReDocUI Integration**
Ellar also supports rendering [ReDoc UI](https://redocly.github.io/redoc/), providing another option for interacting with API resources.

```python
from ellar.openapi import ReDocUI

redoc_ui = ReDocUI(
    path= "redoc",
    title= "Ellar Redoc",
    redoc_js_url= "https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
    favicon_url= "https://eadwincode.github.io/ellar/img/Icon.svg",
    with_google_fonts= True,
)
```

### Properties
- **path**: The URL path for accessing the ReDoc UI page.
- **title**: The title displayed in the HTML header.
- **redoc_js_url**: The CDN URL for ReDoc JS.
- **favicon_url**: The URL for the HTML favicon.
- **with_google_fonts**: Indicates whether to include Google Fonts.

## **StopLightUI Integration**
For rendering [StopLight UI](https://github.com/stoplightio/elements/blob/main/docs/getting-started/elements/html.md), Ellar offers built-in integration, enhancing interaction with API resources.

```python
from ellar.openapi import StopLightUI

stoplight_ui = StopLightUI(
    path= "elements",
    title= "Ellar Stoplight",
    stoplight_js_url= "https://unpkg.com/@stoplight/elements/web-components.min.js",
    stoplight_css_url= "https://unpkg.com/@stoplight/elements/styles.min.css",
    favicon_url= "https://eadwincode.github.io/ellar/img/Icon.svg",
    config=dict(router="hash", layout="sidebar", hideExport=True)
)
```

### Properties
- **path**: The URL path for accessing the Stoplight UI page.
- **title**: The title displayed in the HTML header.
- **stoplight_js_url**: The CDN URL for StopLight JS.
- **stoplight_css_url**: The CDN URL for StopLight CSS.
- **config**: Configuration options for Stoplight elements as documented [here]().
- **favicon_url**: The URL for the HTML favicon.

## **Custom Documentation UI**
You can easily create custom documentation UIs tailored to their specific needs within Ellar. 
This involves defining a custom class that implements the `IDocumentationUI` interface.

```python
import typing as t
from ellar.openapi import IDocumentationUI

class MyDocUI(IDocumentationUI):
    @property
    def name(self) -> str:
        """The name of the custom documentation UI."""
        return "my_custom_doc"

    @property
    def path(self) -> str:
        """The URL path for accessing the custom documentation UI."""
        return "my_doc"

    @property
    def template_name(self) -> t.Optional[str]:
        """The name of the HTML template file used for rendering."""
        return "my_custom.html"

    @property
    def template_string(self) -> t.Optional[str]:
        """The templated HTML string for rendering the documentation UI."""
        return None

    @property
    def template_context(self) -> dict:
        """Additional context data to be passed to the documentation template."""
        return {
            # Add any necessary context data here
        }
```

After defining the custom `MyDocUI` class, it can be integrated into 
Ellar's OpenAPI module setup by specifying it in the `doc_ui` parameter.

It's important to note that `openapi_url` will be passed alongside with `template_context` provided in `MyDocUI`.

```python
import os

from ellar.app import AppFactory
from ellar.common.constants import ELLAR_CONFIG_MODULE
from ellar.core import LazyModuleImport as lazyLoad
from ellar.openapi import (
    OpenAPIDocumentBuilder,
    OpenAPIDocumentModule,
)
from .my_doc_ui import MyDocUI

application = AppFactory.create_from_app_module(
    lazyLoad("carapp.root_module:ApplicationModule"),
    config_module=os.environ.get(
        ELLAR_CONFIG_MODULE, "carapp.config:DevelopmentConfig"
    ),
)

document_builder = OpenAPIDocumentBuilder()
document_builder.set_title("Ellar API") \
    .set_version("1.0.2") \
    .set_contact(name="John Doe", url="https://www.yahoo.com", email="johnDoe@gmail.com") \
    .set_license("MIT Licence", url="https://www.google.com") \
    .add_server('/', description='Development Server')

document = document_builder.build_document(application)

OpenAPIDocumentModule.setup(
    app=application,
    docs_ui=MyDocUI(),
    document=document,
    guards=[],
)
```
