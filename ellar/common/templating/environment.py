import typing as t

from jinja2 import ChoiceLoader
from jinja2 import Environment as BaseEnvironment

from .loader import JinjaLoader

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.app.main import App


class Environment(BaseEnvironment):
    """Works like a regular Jinja2 environment"""

    def __init__(self, app: "App", **options: t.Any) -> None:
        if "loader" not in options:
            options["loader"] = ChoiceLoader(
                [JinjaLoader(app), *app.config.JINJA_LOADERS]
            )
        BaseEnvironment.__init__(self, **options)
        self.app = app
