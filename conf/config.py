import importlib
import typing as t

from starlette.config import environ

from . import default_settings
from .app_settings_models import StarletteAPIConfig

from ..constants import STARLETTEAPI_CONFIG_MODULE

KT = t.TypeVar('KT')
VT = t.TypeVar('VT')


class _ConfigState(t.MutableMapping[KT, VT]):
    __slots__ = ('_config', )

    def __init__(self):
        self._config = dict()

    def __getitem__(self, k: KT) -> VT:
        return self._config.__getitem__(k)

    def __len__(self) -> int:
        return len(self._config)

    def __iter__(self) -> t.Iterator[t.Any]:
        return iter(self._config)

    def __setitem__(self, k: KT, v: VT) -> None:
        self._config.__setitem__(k, v)

    def __delitem__(self, v: KT) -> None:
        self._config.__delitem__(v)


_config_state = _ConfigState()


class Config:
    __slots__ = ('validate_config', '_config', 'config_module')

    _config: _ConfigState

    def __init__(self, config_state: _ConfigState = _config_state, **mapping: t.Any, ):
        """
        Creates a new instance of Configuration object with the given values.
        """

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

        self._config: _ConfigState = config_state
        self.validate_config: StarletteAPIConfig = StarletteAPIConfig.from_orm(self._config)

    def __contains__(self, item: str) -> bool:
        return item in self._config

    def __getitem__(self, name):
        try:
            return self.__getattr__(name)
        except AttributeError:
            raise KeyError(name)

    def __getattr__(self, name) -> t.Any:
        if name in self:
            value = self._config.get(name)
            return value
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )

    def set_defaults(self, **kwargs: t.Any):
        for k, v in kwargs.items():
            self._config.setdefault(k, v)

    def __repr__(self) -> str:
        hidden_values = {key: "..." for key in self._config.keys()}
        return f"<Configuration {repr(hidden_values)}, settings_module: {self.config_module}>"

    @property
    def values(self) -> t.ValuesView[VT]:
        """
        Returns a copy of the dictionary of current settings.
        """
        return self._config.values()
