from abc import abstractmethod
from typing import Dict, Type, TypeVar, Optional

from injector import (  # noqa
    Scope as InjectorScope,
    ScopeDecorator,
    SingletonScope as InjectorSingletonScope,
    ThreadLocalScope as InjectorThreadLocalScope,
    NoScope as InjectorNoScope, Provider,
)

__all__ = [
    'request_scope',
    'transient',
    'singleton',
    'ScopeDecorator',
    'DIScope',
    'TransientScope',
    'RequestScope',
    'SingletonScope'
]

T = TypeVar('T')


class DIScope(InjectorScope):
    @abstractmethod
    def get(self, key: Type[T], provider: Provider[T], context: Optional[Dict[type, Provider]] = None) -> Provider[T]:
        """Get a :class:`Provider` for a key.

        :param context: Dictionary of cached services resolved during request
        :param key: The key to return a provider for.
        :param provider: The default Provider associated with the key.
        :returns: A Provider instance that can provide an instance of key.
        """
        raise NotImplementedError  # pragma: no cover


class RequestScope(DIScope):
    def get(self, key: Type[T], provider: Provider[T], context: Optional[Dict[type, Provider]] = None) -> Provider[T]:
        if context is None:
            # if context is not available then return transient scope
            return provider
        try:
            return context[key]
        except KeyError:
            context[key] = provider
            return provider


class SingletonScope(InjectorSingletonScope, DIScope):
    def get(self, key: Type[T], provider: Provider[T], context: Optional[Dict[type, Provider]] = None) -> Provider[T]:
        return super().get(key, provider)


class TransientScope(InjectorNoScope, DIScope):
    def get(self, key: Type[T], provider: Provider[T], context: Optional[Dict[type, Provider]] = None) -> Provider[T]:
        return provider


transient = ScopeDecorator(TransientScope)
singleton = ScopeDecorator(SingletonScope)
request_scope = ScopeDecorator(RequestScope)
