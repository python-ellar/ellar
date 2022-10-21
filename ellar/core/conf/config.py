import typing as t

from starlette.config import environ

from ellar.compatible.dict import AttributeDictAccessMixin, DataMutableMapper
from ellar.constants import ELLAR_CONFIG_MODULE
from ellar.helper.importer import import_from_string
from ellar.types import VT

from .app_settings_models import ConfigValidationSchema
from .mixins import ConfigDefaultTypesMixin


class ConfigRuntimeError(RuntimeError):
    pass


class Config(DataMutableMapper, AttributeDictAccessMixin, ConfigDefaultTypesMixin):
    __slots__ = ("config_module", "_data")

    def __init__(
        self,
        config_module: str = None,
        **mapping: t.Any,
    ):
        """
        Creates a new instance of Configuration object with the given values.
        """
        super().__init__()
        self.config_module = config_module or environ.get(ELLAR_CONFIG_MODULE, None)

        self._data.clear()

        if self.config_module:
            try:
                mod = import_from_string(self.config_module)
                for setting in dir(mod):
                    if setting.isupper():
                        self._data[setting] = getattr(mod, setting)
            except Exception as ex:
                raise ConfigRuntimeError(str(ex))

        self._data.update(**mapping)

        validate_config = ConfigValidationSchema.parse_obj(self._data)
        self._data.update(validate_config.serialize())

    def set_defaults(self, **kwargs: t.Any) -> "Config":
        for k, v in kwargs.items():
            self._data.setdefault(k, v)
        return self

    def __repr__(self) -> str:
        hidden_values = {key: "..." for key in self._data.keys()}
        return f"<Configuration {repr(hidden_values)}, settings_module: {self.config_module}>"

    def __setattr__(self, key: t.Any, value: t.Any) -> None:
        if key in self.__slots__:
            super(Config, self).__setattr__(key, value)
            return

        self._data[key] = value

    @property
    def values(self) -> t.ValuesView[VT]:
        """
        Returns a copy of the dictionary of current settings.
        """
        return self._data.values()
