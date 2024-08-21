import typing as t

from ellar.auth.handlers import AuthenticationHandlerType
from ellar.common import (
    EllarInterceptor,
    GuardCanActivate,
    IExceptionHandler,
    IIdentitySchemes,
)
from ellar.core import VersioningSchemes, current_config, current_injector
from ellar.di import is_decorated_with_injectable
from ellar.di.injector.tree_manager import TreeData
from ellar.events import ensure_build_context


@ensure_build_context(app_ready=True)
def ensure_available_in_providers(*items: t.Any) -> None:
    """
    Ensures that Providers at least belows to a particular module
    :param items:
    :return:
    """
    app_module = current_injector.tree_manager.get_app_module()

    def _predicate(item_: t.Type) -> t.Callable:
        def _(data: TreeData) -> bool:
            return item_ in data.exports or item_ in data.providers

        return _

    for item in items:
        if isinstance(item, type) and is_decorated_with_injectable(item):
            module = next(
                app_module.tree_manager.find_module(predicate=_predicate(item))
            )
            if not module:
                # if no module was found, we add item to ApplicationModule and export it also
                app_module.tree_manager.get_app_module().add_provider(
                    provider=item, export=True
                )


@ensure_build_context(app_ready=True)
def use_authentication_schemes(*authentication: AuthenticationHandlerType) -> None:
    """
    Registered Authentication Handlers to the application
    :param authentication:
    :return:
    """
    __identity_scheme = current_injector.get(IIdentitySchemes)
    for auth in authentication:
        __identity_scheme.add_authentication(auth)
        ensure_available_in_providers(auth)


@ensure_build_context()
def use_exception_handler(
    *exception_handlers: IExceptionHandler,
) -> None:
    """
    Adds Application Exception Handlers
    :param exception_handlers: IExceptionHandler
    :return:
    """
    for exception_handler in exception_handlers:
        if exception_handler not in current_config.EXCEPTION_HANDLERS:
            current_config.EXCEPTION_HANDLERS = current_config.EXCEPTION_HANDLERS + [
                exception_handler
            ]
            ensure_available_in_providers(exception_handler)


@ensure_build_context()
def enable_versioning(
    schema: VersioningSchemes,
    version_parameter: str = "version",
    default_version: t.Optional[str] = None,
    **init_kwargs: t.Any,
) -> None:
    """
    Enables an Application Versioning scheme
    :param schema: VersioningSchemes
    :param version_parameter: versioning parameter lookup key. Default: 'version'
    :param default_version: versioning default value. Default: None
    :param init_kwargs: Other schema initialization keyword args.
    :return:
    """
    current_config.VERSIONING_SCHEME = schema.value(
        version_parameter=version_parameter,
        default_version=default_version,
        **init_kwargs,
    )


@ensure_build_context(app_ready=True)
def use_global_guards(
    *guards: t.Union[GuardCanActivate, t.Type[GuardCanActivate]],
) -> None:
    """
    Registers Application Global Guards that affects all routes registered in ApplicationRouter
    :param guards:
    :return: None
    """
    current_config.GLOBAL_GUARDS = list(current_config.GLOBAL_GUARDS) + list(guards)
    ensure_available_in_providers(*guards)


@ensure_build_context(app_ready=True)
def use_global_interceptors(
    *interceptors: t.Union[EllarInterceptor, t.Type[EllarInterceptor]],
) -> None:
    """
    Registers Application Global Interceptor that affects all routes registered in ApplicationRouter
    :param interceptors:
    :return: None
    """
    current_config.GLOBAL_INTERCEPTORS = list(
        current_config.GLOBAL_INTERCEPTORS
    ) + list(interceptors)
    ensure_available_in_providers(*interceptors)
