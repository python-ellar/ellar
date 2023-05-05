import typing as t


class TemplateFunctionData(t.NamedTuple):
    func: t.Callable
    name: t.Optional[str]
