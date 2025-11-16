"""
Dependency analysis utilities for TestModule to automatically resolve module dependencies.
"""

import inspect
import typing as t
from typing import get_type_hints

import injector
from ellar.di.constants import Tag
from ellar.utils.importer import import_from_string

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.common import ControllerBase
    from ellar.core import ForwardRefModule, ModuleBase
    from ellar.di import ModuleTreeManager


class DependencyResolutionError(Exception):
    """Raised when a dependency cannot be resolved"""

    def __init__(
        self,
        dependency_type: t.Type,
        controller: t.Type["ControllerBase"],
        application_module: t.Optional[t.Type["ModuleBase"]] = None,
    ):
        if application_module:
            message = (
                f"Controller '{controller.__name__}' requires '{dependency_type.__name__}', "
                f"but it's not found in ApplicationModule '{application_module.__name__}'. "
                f"Please either:\n"
                f"  1. Register the module providing '{dependency_type.__name__}' in ApplicationModule\n"
                f"  2. Register it explicitly in Test.create_test_module(modules=[...])\n"
                f"  3. Provide it as a mock in providers=[...]"
            )
        else:
            message = (
                f"Controller '{controller.__name__}' requires '{dependency_type.__name__}', "
                f"but no application_module was provided to resolve it from. "
                f"Please provide application_module parameter or register dependencies manually."
            )

        super().__init__(message)


class ApplicationModuleDependencyAnalyzer:
    """Analyzes ApplicationModule to find and resolve dependencies"""

    def __init__(self, application_module: t.Union[t.Type["ModuleBase"], str]):
        # Support both module type and import string
        if isinstance(application_module, str):
            from ellar.utils.importer import import_from_string

            self.application_module = t.cast(
                t.Type["ModuleBase"], import_from_string(application_module)
            )
        else:
            self.application_module = application_module

        self._module_tree = self._build_module_tree()

    def _build_module_tree(self) -> "ModuleTreeManager":
        """Build complete module tree for ApplicationModule"""
        from ellar.app import AppFactory
        from ellar.core.modules import ModuleSetup

        module_setup = ModuleSetup(self.application_module)
        return AppFactory.read_all_module(module_setup)

    def get_type_from_tag(self, tag: t.Any) -> t.Optional[t.Type[t.Any]]:
        """
        Get the type/interface associated with a given tag from ApplicationModule tree

        When a controller uses InjectByTag('tag_name'), this method finds the provider
        registered with that tag and returns its actual type/interface.

        :param tag: NewType created by InjectByTag function
        :return: The type/interface of the provider with matching tag, or None if not found
        """

        # Extract the tag string from NewType
        # InjectByTag returns t.NewType(Tag(tag_string), Tag)
        # where Tag(tag_string) becomes the __name__ and Tag class is __supertype__
        # Since Tag is a subclass of str, the Tag instance itself is the tag string
        if not hasattr(tag, "__name__"):
            return None

        tag_instance = getattr(tag, "__name__", None)
        if not isinstance(tag_instance, Tag):
            return None

        # Tag is a str subclass, so tag_instance itself is the tag string
        tag_string = str(tag_instance)

        for module_data in self._module_tree.modules.values():
            module_setup = module_data.value

            for _k, v in module_setup.providers.items():
                if v.tag == tag_string:
                    return v.get_type()

        return None

    def find_module_providing_service(
        self, service_type: t.Type
    ) -> t.Optional[t.Type["ModuleBase"]]:
        """
        Search ApplicationModule tree for module that provides/exports a service

        Returns the module that exports the service, or None if not found
        """
        result = self._module_tree.search_module_tree(
            filter_item=lambda data: True,
            find_predicate=lambda data: (
                service_type in data.exports or service_type in data.providers.keys()
            ),
        )
        return t.cast(t.Type["ModuleBase"], result.value.module) if result else None

    def get_all_modules(self) -> t.List[t.Type["ModuleBase"]]:
        """Get all modules in the ApplicationModule tree"""
        return [
            t.cast(t.Type["ModuleBase"], data.value.module)
            for data in self._module_tree.modules.values()
        ]

    def get_module_dependencies(
        self, module: t.Type["ModuleBase"]
    ) -> t.List[t.Type["ModuleBase"]]:
        """
        Get all module dependencies for a given module recursively

        This returns all modules that the given module depends on,
        including nested dependencies.
        """
        module_data = self._module_tree.get_module(module)
        if not module_data:
            return []

        dependencies = []
        visited = set()

        def collect_dependencies(mod: t.Type["ModuleBase"]) -> None:
            if mod in visited:
                return
            visited.add(mod)

            mod_data = self._module_tree.get_module(mod)
            if not mod_data:
                return

            # Get direct dependencies
            dep_modules = self._module_tree.get_module_dependencies(mod)
            for dep in dep_modules:
                dep_module = t.cast(t.Type["ModuleBase"], dep.value.module)
                if dep_module not in dependencies:
                    dependencies.append(dep_module)
                # Recursively collect nested dependencies
                collect_dependencies(dep_module)

        collect_dependencies(module)
        return dependencies

    def resolve_forward_ref(
        self, forward_ref: "ForwardRefModule"
    ) -> t.Optional[t.Type["ModuleBase"]]:
        """
        Resolve a ForwardRefModule to its actual module from ApplicationModule tree

        ForwardRefModule can reference by:
        - module_name: e.g., ForwardRefModule(module_name="UserModule")
        - module (type): e.g., ForwardRefModule(module=UserModule)
        - module (string): e.g., ForwardRefModule(module="app.users:UserModule")
        """

        # ForwardRefModule has either 'module' or 'module_name', not both
        if hasattr(forward_ref, "module_name") and forward_ref.module_name:
            # Search by module name (uses @Module(name="..."))
            result = self._module_tree.search_module_tree(
                filter_item=lambda data: True,
                find_predicate=lambda data: data.name == forward_ref.module_name,
            )
            return t.cast(t.Type["ModuleBase"], result.value.module) if result else None

        elif hasattr(forward_ref, "module") and forward_ref.module:
            # Module can be a Type or a string import path
            if isinstance(forward_ref.module, str):
                # Import string path, e.g., "app.users:UserModule"
                try:
                    module_cls = import_from_string(forward_ref.module)
                except Exception:
                    return None
            else:
                # Direct type reference
                module_cls = forward_ref.module

            # Search for this module type in the tree
            module_data = self._module_tree.get_module(module_cls)
            return (
                t.cast(t.Type["ModuleBase"], module_data.value.module)
                if module_data
                else None
            )

        return None


class ControllerDependencyAnalyzer:
    """Analyzes controllers to extract their dependencies"""

    @staticmethod
    def get_dependencies(controller: t.Type["ControllerBase"]) -> t.List[t.Type]:
        """
        Extract dependency types from controller __init__ signature

        Uses injector.get_bindings() if available, falls back to type hint inspection.
        Returns list of types that need to be injected.
        """
        dependencies = []

        # Try to use injector's get_bindings first (more robust for @injectable classes)
        try:
            bindings = injector.get_bindings(controller)
            if bindings:  # Only use if it found bindings
                dependencies = [
                    binding.interface
                    for binding in bindings
                    if hasattr(binding, "interface")
                    and not isinstance(binding.interface, str)
                ]
                return dependencies
        except Exception:
            pass  # Fall through to manual inspection

        # Fallback to type hint inspection (for controllers without @injectable)
        if not hasattr(controller, "__init__"):
            return dependencies

        try:
            type_hints = get_type_hints(controller.__init__)
        except Exception:
            # Fallback to inspect if get_type_hints fails
            sig = inspect.signature(controller.__init__)
            type_hints = {
                name: param.annotation
                for name, param in sig.parameters.items()
                if param.annotation != inspect.Parameter.empty
            }

        # Extract non-primitive dependencies (skip 'self', 'return', primitives)
        for param_name, param_type in type_hints.items():
            if param_name in ("self", "return"):
                continue

            # Skip primitive types
            if param_type in (str, int, float, bool, dict, list, type(None)):
                continue

            dependencies.append(param_type)

        return dependencies
