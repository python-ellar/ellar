import typing as t

from ellar.common.compatible.dict import AttributeDictAccessMixin
from ellar.common.constants import ELLAR_CONFIG_MODULE
from ellar.common.types import VT
from ellar.common.utils.importer import import_from_string
from starlette.config import environ

from .app_settings_models import ConfigValidationSchema
from .mixins import ConfigDefaultTypesMixin


class ConfigRuntimeError(RuntimeError):
    pass


class Config(AttributeDictAccessMixin, dict, ConfigDefaultTypesMixin):
    __slots__ = ("config_module",)

    def __init__(
        self,
        config_module: t.Optional[str] = None,
        config_prefix: t.Optional[str] = None,
        **mapping: t.Any,
    ):
        """
        Creates a new instance of Configuration object with the given values.
        """
        super().__init__()
        self.config_module = config_module or environ.get(ELLAR_CONFIG_MODULE, None)

        self.clear()

        self._load_config_module(config_prefix or "")

        self.update(**mapping)

        validate_config = ConfigValidationSchema.parse_obj(self)
        self.update(validate_config.serialize())

    def _load_config_module(self, prefix: str) -> None:
        _prefix = prefix.upper()
        if self.config_module:
            try:
                mod = import_from_string(self.config_module)
                for setting in dir(mod):
                    if setting.isupper() and setting.startswith(_prefix):
                        self[setting.replace(_prefix, "")] = getattr(mod, setting)
            except Exception as ex:
                raise ConfigRuntimeError(str(ex)) from ex

    def set_defaults(self, **kwargs: t.Any) -> "Config":
        for k, v in kwargs.items():
            self.setdefault(k, v)
        return self

    def __repr__(self) -> str:  # pragma: no cover
        hidden_values = {key: "..." for key in self.keys()}
        return f"<Configuration {repr(hidden_values)}, settings_module: {self.config_module}>"

    def __setattr__(self, key: t.Any, value: t.Any) -> None:
        if key in self.__slots__:
            super(Config, self).__setattr__(key, value)
            return

        self[key] = value

    @property
    def config_values(self) -> t.ValuesView[VT]:
        """
        Returns a copy of the dictionary of current settings.
        """
        return super().values()
