import importlib
import typing as t

from starlette.config import environ

from . import default_settings
from .app_settings_models import StarletteAPIConfig
from starletteapi.types import VT
from ..compatible.dict import DataMutableMapper, AttributeDictAccess, DataMapper
from ..constants import STARLETTEAPI_CONFIG_MODULE


class _ConfigState(DataMutableMapper):
    pass


_config_state = _ConfigState()


class Config(DataMapper, AttributeDictAccess):
    __slots__ = ('validate_config', 'config_module')

    def __init__(self, config_state: _ConfigState = _config_state, **mapping: t.Any, ):
        """
        Creates a new instance of Configuration object with the given values.
        """
        super().__init__()
        self.config_module = environ.get(STARLETTEAPI_CONFIG_MODULE, None)
        if 'app_configured' not in config_state:
            config_state.clear()
            for setting in dir(default_settings):
                if setting.isupper():
                    config_state[setting] = getattr(default_settings, setting)

            if self.config_module:
                mod = importlib.import_module(self.config_module)
                for setting in dir(mod):
                    if setting.isupper():
                        config_state[setting] = getattr(mod, setting)

        config_state.update(**mapping)

        self._data: _ConfigState = config_state
        self.validate_config: StarletteAPIConfig = StarletteAPIConfig.from_orm(self._data)

    def __contains__(self, item: str) -> bool:
        return item in self._data

    def set_defaults(self, **kwargs: t.Any):
        for k, v in kwargs.items():
            self._data.setdefault(k, v)

    def __repr__(self) -> str:
        hidden_values = {key: "..." for key in self._data.keys()}
        return f"<Configuration {repr(hidden_values)}, settings_module: {self.config_module}>"

    @property
    def values(self) -> t.ValuesView[VT]:
        """
        Returns a copy of the dictionary of current settings.
        """
        return self._data.values()
