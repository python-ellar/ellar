import typing as t

from ellar.core.routing.controller import ControllerDecorator

if t.TYPE_CHECKING:
    from ellar.core.guard import GuardCanActivate


@t.overload
def Controller(
    prefix: t.Optional[str] = None,
) -> ControllerDecorator:  # pragma: no cover
    ...


@t.overload
def Controller(
    prefix: t.Optional[str] = None,
    *,
    tag: t.Optional[str] = None,
    description: t.Optional[str] = None,
    external_doc_description: t.Optional[str] = None,
    external_doc_url: t.Optional[str] = None,
    name: t.Optional[str] = None,
    version: t.Union[t.Tuple, str] = (),
    guards: t.Optional[
        t.List[t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]]
    ] = None,
) -> ControllerDecorator:  # pragma: no cover
    ...


def Controller(
    prefix: t.Optional[str] = None,
    *,
    tag: t.Optional[str] = None,
    description: t.Optional[str] = None,
    external_doc_description: t.Optional[str] = None,
    external_doc_url: t.Optional[str] = None,
    name: t.Optional[str] = None,
    version: t.Union[t.Tuple, str] = (),
    guards: t.Optional[
        t.List[t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]]
    ] = None,
) -> t.Union[ControllerDecorator, t.Callable]:
    if isinstance(prefix, type):
        return ControllerDecorator("")(prefix)

    def _decorator(cls: t.Type) -> ControllerDecorator:
        _controller = ControllerDecorator(
            prefix=prefix,
            tag=tag,
            description=description,
            external_doc_description=external_doc_description,
            external_doc_url=external_doc_url,
            name=name,
            version=version,
            guards=guards,
        )
        return _controller(cls)

    return _decorator
