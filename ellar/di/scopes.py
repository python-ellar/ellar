import typing as t
from abc import abstractmethod

from injector import (
    NoScope as InjectorNoScope,
    Scope as InjectorScope,
    ScopeDecorator as ScopeDecorator,
    SingletonScope as InjectorSingletonScope,
)

from ellar.types import T

from .providers import InstanceProvider, Provider


class DIScope(InjectorScope):
    @abstractmethod
    def get(
        self,
        key: t.Type[T],
        provider: Provider[T],
        context: t.Optional[t.Dict[type, Provider]] = None,
    ) -> Provider[T]:
        """Get a :class:`Provider` for a key.

        :param context: Dictionary of cached services resolved during request
        :param key: The key to return a provider for.
        :param provider: The default Provider associated with the key.
        :returns: A Provider instance that can provide an instance of key.
        """
        raise NotImplementedError  # pragma: no cover


class RequestScope(DIScope):
    def get(
        self,
        key: t.Type[T],
        provider: Provider[T],
        context: t.Optional[t.Dict[type, Provider]] = None,
    ) -> Provider[T]:
        if context is None:
            # if context is not available then return transient scope
            return provider
        try:
            return context[key]
        except KeyError:
            # if context is available and provider is not in context,
            # we switch to instance provider which will keep the instance alive throughout request lifetime
            provider = InstanceProvider(provider.get(self.injector))
            context[key] = provider
            return provider


class SingletonScope(InjectorSingletonScope, DIScope):
    def get(
        self,
        key: t.Type[T],
        provider: Provider[T],
        context: t.Optional[t.Dict[type, Provider]] = None,
    ) -> Provider[T]:
        return super().get(key, provider)


class TransientScope(InjectorNoScope, DIScope):
    def get(
        self,
        key: t.Type[T],
        provider: Provider[T],
        context: t.Optional[t.Dict[type, Provider]] = None,
    ) -> Provider[T]:
        return provider


transient_scope = ScopeDecorator(TransientScope)
singleton_scope = ScopeDecorator(SingletonScope)
request_scope = ScopeDecorator(RequestScope)
