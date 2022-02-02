from abc import ABC, abstractmethod
from typing import Sequence, List, Union, Type
from .base import GuardCanActivate


class GuardInterface(ABC):
    @abstractmethod
    def add_guards(self, *guards:  Sequence[GuardCanActivate]):
        ...

    @abstractmethod
    def get_guards(self) -> List[Union[Type['GuardCanActivate'], 'GuardCanActivate']]:
        ...
