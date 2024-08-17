import logging
import typing as t

from ellar.di import RequestScopeContext, request_context_var
from injector import (
    NoScope as TransientScope,
)
from injector import (
    Scope as InjectorScope,
)
from injector import (
    ScopeDecorator as ScopeDecorator,
)
from injector import (
    SingletonScope as SingletonScope,
)
from injector import (
    UnsatisfiedRequirement,
)

from .providers import InstanceProvider, Provider
from .types import T


class RequestScope(InjectorScope):
    def get_context(self) -> t.Optional[RequestScopeContext]:
        try:
            return request_context_var.get()
        except Exception as ex:
            logging.exception(ex)
            return None

    def get(self, key: t.Type[T], provider: Provider[T]) -> Provider[T]:
        scoped_context = self.get_context()

        if scoped_context is None:
            raise UnsatisfiedRequirement(None, key)
        try:
            return scoped_context.context[key]
        except KeyError:
            # if context is available and provider is not in context,
            # we switch to instance provider which will keep the instance alive throughout request lifetime
            provider = InstanceProvider(provider.get(self.injector))
            scoped_context.context[key] = provider
            return provider


class RequestORTransientScope(RequestScope):
    def get(self, key: t.Type[T], provider: Provider[T]) -> Provider[T]:
        scoped_context = self.get_context()

        if scoped_context is None:
            return provider
        try:
            return scoped_context.context[key]
        except KeyError:
            # if context is available and provider is not in context,
            # we switch to instance provider which will keep the instance alive throughout request lifetime
            provider = InstanceProvider(provider.get(self.injector))
            scoped_context.context[key] = provider
            return provider


transient_scope = ScopeDecorator(TransientScope)
singleton_scope = ScopeDecorator(SingletonScope)
request_scope = ScopeDecorator(RequestScope)
request_or_transient_scope = ScopeDecorator(RequestORTransientScope)
