import typing as t

from jinja2 import Environment as BaseEnvironment

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.main import App


class Environment(BaseEnvironment):
    """Works like a regular Jinja2 environment"""

    def __init__(self, app: "App", **options: t.Any) -> None:
        if "loader" not in options:
            options["loader"] = app.create_global_jinja_loader()
        BaseEnvironment.__init__(self, **options)
        self.app = app
