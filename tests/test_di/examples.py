from abc import ABC, abstractmethod

from ellar.di import injectable
from ellar.di.scopes import RequestORTransientScope, RequestScope, TransientScope


class Foo:
    def __init__(self):
        pass


class Foo1:
    def __init__(self):
        pass


@injectable
class Foo2:
    def __init__(self, one: Foo1):
        self.one = one


@injectable
class CircularDependencyType:
    def __init__(self, circle: "CircularDependencyType"):
        self.circular = circle


@injectable
class InjectType:
    pass


@injectable(TransientScope)
class InjectType2:
    def __init__(self, one: Foo2):
        self.one = one


# abstract interface
class IRepository(ABC):
    @abstractmethod
    def get_by_id(self, _id):
        pass


class IDBContext(ABC):
    @abstractmethod
    def context(self):
        pass


@injectable
class AnyDBContext(IDBContext):
    def context(self):
        pass


@injectable
class FooDBCatsRepository(IRepository):
    def __init__(self, context: IDBContext):
        self.context = context

    def get_by_id(self, _id):
        pass


class IContext(ABC):
    @property
    @abstractmethod
    def id(self):
        pass

    @property
    @abstractmethod
    def user(self):
        pass


@injectable(RequestScope)
class AnyContext(IContext):
    def __init__(self):
        pass

    @property
    def id(self):
        return "Example"

    @property
    def user(self):
        return "Example"


@injectable(RequestORTransientScope)
class TransientRequestContext(IContext):
    def __init__(self):
        pass

    @property
    def id(self):
        return "Example"

    @property
    def user(self):
        return "Example"
