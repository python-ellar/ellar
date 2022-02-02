from typing import Sequence, Union, cast, List, Type, Any
from .base import GuardCanActivate
from .interface import GuardInterface


class _OperationGuard:
    def __init__(self, *guards: Sequence[GuardCanActivate]):
        self.guards = guards

    @classmethod
    def is_guard_type(cls, type_: Any) -> bool:
        if not isinstance(type_, type) and issubclass(type(type_), GuardInterface):
            return True
        if issubclass(type_, GuardInterface):
            return True
        return False

    def __call__(
            self, func_or_controller: Union[Type[GuardInterface], GuardInterface, Any]
    ) -> Union[Type[GuardInterface], GuardInterface, Any]:
        if self.is_guard_type(func_or_controller):
            func_or_controller = cast(GuardInterface, func_or_controller)
            func_or_controller.add_guards(*self.guards)
        else:
            _guards = cast(List, getattr(func_or_controller, '_guards', []))
            _guards.extend(self.guards)
            setattr(func_or_controller, '_guards', _guards)
        return func_or_controller


Guards = _OperationGuard
