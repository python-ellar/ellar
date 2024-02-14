import json
import typing as t

from .base import IDocumentationUI


class StopLightUI(IDocumentationUI):
    @property
    def name(self) -> str:
        return "stoplight"

    @property
    def template_name(self) -> t.Optional[str]:
        return None

    @property
    def path(self) -> str:
        return self._path

    @property
    def template_context(self) -> dict:
        return self._template_context

    @property
    def template_string(self) -> t.Optional[str]:
        return """
            <!doctype html>
            <html lang="en">
              <head>
                <title>{{title}}</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
                <link rel="shortcut icon" href="{{favicon_url}}">
                <!-- Embed elements Elements via Web Component -->
                <script src="{{stoplight_js_url}}" crossorigin></script>
                <link rel="stylesheet" href="{{stoplight_css_url}}">
                <script>
                    window.__element_config = {{ config | safe }}
                </script>
              </head>
              <body>

                <elements-api
                  apiDescriptionUrl="{{openapi_url}}"
                  ...window.__element_config
                />

              </body>
            </html>
        """

    def __init__(
        self,
        path: str = "elements",
        title: str = "Ellar Stoplight",
        stoplight_js_url: str = "https://unpkg.com/@stoplight/elements/web-components.min.js",
        stoplight_css_url: str = "https://unpkg.com/@stoplight/elements/styles.min.css",
        favicon_url: str = "https://eadwincode.github.io/ellar/img/Icon.svg",
        config: t.Optional[dict] = None,
    ):
        _config = config or {}
        _config.setdefault("router", "hash")
        _config.setdefault("layout", "sidebar")

        self._path = path
        self._template_context = {
            "title": title,
            "stoplight_js_url": stoplight_js_url,
            "stoplight_css_url": stoplight_css_url,
            "favicon_url": favicon_url,
            "config": json.dumps(_config),
        }
