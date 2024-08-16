import typing as t

from ellar.common.constants import ELLAR_CONFIG_MODULE
from ellar.common.types import VT
from ellar.core.conf.app_settings_models import ConfigSchema
from ellar.core.conf.mixins import ConfigDefaultTypesMixin
from ellar.utils.importer import import_from_string
from starlette.config import environ


class ConfigRuntimeError(RuntimeError):
    pass


class Config(ConfigDefaultTypesMixin):
    __slots__ = (
        "_config_module",
        "_schema",
    )

    _initialized: bool = False

    def __init__(
        self,
        config_module: t.Optional[str] = None,
        config_prefix: t.Optional[str] = None,
        **mapping: t.Any,
    ):
        """
        Creates a new instance of a Configuration object with the given values.
        """

        self._config_module = config_module or environ.get(ELLAR_CONFIG_MODULE, None)

        data = self._load_config_module(config_prefix or "")
        data.update(**mapping)

        self._schema = ConfigSchema.model_validate(data, from_attributes=True)
        self._initialized = True

    @property
    def config_module(self) -> t.Optional[str]:
        return self._config_module

    def _load_config_module(self, prefix: str) -> dict:
        data = {}
        _prefix = prefix.upper()

        if self._config_module:
            try:
                mod = import_from_string(self._config_module)
                for setting in dir(mod):
                    if setting.isupper() and setting.startswith(_prefix):
                        data[setting.replace(_prefix, "")] = getattr(mod, setting)
            except Exception as ex:
                raise ConfigRuntimeError(str(ex)) from ex

        return data

    def __repr__(self) -> str:  # pragma: no cover
        hidden_values = {key: "..." for key in self._schema.serialize().keys()}
        return f"<Configuration {repr(hidden_values)}, settings_module: {self._config_module}>"

    def __str__(self) -> str:
        return repr(self)

    @property
    def config_values(self) -> t.ValuesView[VT]:
        """
        Returns a copy of the dictionary of current settings.
        """
        return self._schema.serialize().values()

    def __setattr__(self, key: t.Any, value: t.Any) -> None:
        if key in self.__slots__ + ("_initialized",):
            # Assign to __dict__ to avoid infinite __setattr__ loops.
            if self._initialized:
                raise ConfigRuntimeError(
                    f"Invalid Operation: Can not change {key} after configuration object has been created"
                )

            super().__setattr__(key, value)
        else:
            setattr(self._schema, key, value)

    def __delattr__(self, key: t.Any) -> None:
        if key in self.__slots__ + ("_initialized",):
            # TODO: add test
            raise TypeError("can't delete config attributes.")
        delattr(self._schema, key)

    def __getattr__(self, key: t.Any) -> t.Any:
        value = getattr(self._schema, key)
        if isinstance(value, (list, set, tuple, dict)):
            # return immutable value
            return type(value)(value)
        return value

    def set_defaults(self, **kwargs: t.Any) -> "Config":
        for k, v in kwargs.items():
            orig_value = getattr(self._schema, k, None)
            if orig_value is None:
                setattr(self._schema, k, v)
        return self

    def get(self, key: t.Any, _default: t.Optional[t.Any] = None) -> t.Optional[t.Any]:
        return getattr(self, key, _default)

    def __contains__(self, item: t.Any) -> bool:
        return hasattr(self._schema, item)

    def __getitem__(self, item: t.Any) -> t.Any:
        return getattr(self, item)

    def __setitem__(self, key: t.Any, value: t.Any) -> None:
        return setattr(self, key, value)
