import typing as t

if t.TYPE_CHECKING:
    from starletteapi.routing.operations import ExtraOperationArgs
    from starletteapi.guard import GuardCanActivate


class OperationMeta(dict):
    extra_route_args: t.List['ExtraOperationArgs']
    response_override: t.Union[t.Dict[int, t.Union[t.Type, t.Any]], t.Type, None]
    route_versioning: t.Set[t.Union[int, float, str]]
    route_guards: t.List[t.Union[t.Type['GuardCanActivate'], 'GuardCanActivate']]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('extra_route_args', [])
        kwargs.setdefault('response_override', None)
        kwargs.setdefault('route_versioning', set())
        kwargs.setdefault('route_guards', [])
        super(OperationMeta, self).__init__(*args, **kwargs)

    def __getitem__(self, name) -> t.Any:
        try:
            return self.__getattr__(name)
        except AttributeError:
            raise KeyError(name)

    def __getattr__(self, name) -> t.Any:
        if name in self:
            value = self.get(name)
            return value
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )
