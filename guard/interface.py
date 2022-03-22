from abc import ABC, abstractmethod, ABCMeta
from typing import Sequence, List, Union, Type
from .base import GuardCanActivate


class GuardInterface(ABC, metaclass=ABCMeta):
    @abstractmethod
    def add_guards(self, *guards:  Sequence[GuardCanActivate]):
        ...

    @abstractmethod
    def get_guards(self) -> List[Union[Type['GuardCanActivate'], 'GuardCanActivate']]:
        ...
