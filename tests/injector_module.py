from ellar.core import ModuleBase
from ellar.di import Container, singleton_scope
from injector import provider


class Configuration:
    def __init__(self, connection_string):
        self.connection_string = connection_string

    def __repr__(self) -> str:
        return f"<DBConfiguration - {self.connection_string}>"


class DummyModule(ModuleBase):
    @singleton_scope
    @provider
    def str_provider(self) -> str:
        return "Ellar"

    def register_services(self, container: Container) -> None:
        configuration = Configuration(":memory:")
        container.register_instance(configuration)
