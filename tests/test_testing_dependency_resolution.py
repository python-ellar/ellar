"""
Tests for TestModule automatic dependency resolution feature.
"""

import pytest
from ellar.common import Controller, Module, get
from ellar.core import ForwardRefModule, ModuleBase
from ellar.di import InjectByTag, ProviderConfig, injectable
from ellar.di.exceptions import UnsatisfiedRequirement
from ellar.testing import Test
from ellar.testing.dependency_analyzer import (
    ApplicationModuleDependencyAnalyzer,
    ControllerDependencyAnalyzer,
    DependencyResolutionError,
)

# ============================================================================
# Test Services and Modules
# ============================================================================


class IAuthService:
    """Auth service interface"""

    def authenticate(self, token: str) -> dict:
        pass


class IDatabaseService:
    """Database service interface"""

    def query(self, sql: str) -> list:
        pass


class ILoggingService:
    """Logging service interface"""

    def log(self, message: str) -> None:
        pass


@injectable
class AuthService(IAuthService):
    """Concrete auth service"""

    def authenticate(self, token: str) -> dict:
        return {"user": "test_user", "token": token}


@injectable
class DatabaseService(IDatabaseService):
    """Concrete database service"""

    def query(self, sql: str) -> list:
        return [{"id": 1, "name": "test"}]


@injectable
class LoggingService(ILoggingService):
    """Concrete logging service"""

    def log(self, message: str) -> None:
        pass


@Module(
    name="LoggingModule",
    providers=[ProviderConfig(ILoggingService, use_class=LoggingService)],
    exports=[ILoggingService],
)
class LoggingModule(ModuleBase):
    """Module providing logging service"""


@Module(
    name="DatabaseModule",
    modules=[LoggingModule],  # Nested dependency
    providers=[ProviderConfig(IDatabaseService, use_class=DatabaseService)],
    exports=[IDatabaseService],
)
class DatabaseModule(ModuleBase):
    """Module providing database service with logging dependency"""


@Module(
    name="AuthModule",
    providers=[ProviderConfig(IAuthService, use_class=AuthService)],
    exports=[IAuthService],
)
class AuthModule(ModuleBase):
    """Module providing auth service"""


@Module(
    name="ApplicationModule",
    modules=[DatabaseModule, AuthModule],
)
class ApplicationModule(ModuleBase):
    """Application root module"""


# ============================================================================
# Test Controllers
# ============================================================================


@Controller()
class UserController:
    """Controller with single dependency"""

    def __init__(self, auth_service: IAuthService):
        self.auth_service = auth_service

    @get("/users")
    def get_users(self):
        return {"users": []}


@Controller()
class AdminController:
    """Controller with multiple dependencies"""

    def __init__(self, auth_service: IAuthService, db_service: IDatabaseService):
        self.auth_service = auth_service
        self.db_service = db_service

    @get("/admin")
    def get_admin(self):
        return {"admin": True}


@Controller()
class PublicController:
    """Controller with no dependencies"""

    @get("/public")
    def get_public(self):
        return {"public": True}


# ============================================================================
# Unit Tests: ControllerDependencyAnalyzer
# ============================================================================


def test_controller_dependency_analyzer_single_dependency():
    """Test extracting single dependency from controller"""
    analyzer = ControllerDependencyAnalyzer()
    dependencies = analyzer.get_dependencies(UserController)

    assert len(dependencies) == 1
    assert IAuthService in dependencies


def test_controller_dependency_analyzer_multiple_dependencies():
    """Test extracting multiple dependencies from controller"""
    analyzer = ControllerDependencyAnalyzer()
    dependencies = analyzer.get_dependencies(AdminController)

    assert len(dependencies) == 2
    assert IAuthService in dependencies
    assert IDatabaseService in dependencies


def test_controller_dependency_analyzer_no_dependencies():
    """Test controller with no dependencies"""
    analyzer = ControllerDependencyAnalyzer()
    dependencies = analyzer.get_dependencies(PublicController)

    assert len(dependencies) == 0


def test_controller_dependency_analyzer_inherited_constructor():
    """Test controller with inherited constructor"""

    class BaseController:
        def __init__(self, auth: IAuthService):
            self.auth = auth

    @Controller()
    class DerivedController(BaseController):
        pass

    analyzer = ControllerDependencyAnalyzer()
    dependencies = analyzer.get_dependencies(DerivedController)

    # Should find dependency from parent class
    assert IAuthService in dependencies


# ============================================================================
# Unit Tests: ApplicationModuleDependencyAnalyzer
# ============================================================================


def test_application_module_analyzer_builds_tree():
    """Test that ApplicationModuleDependencyAnalyzer builds module tree"""
    analyzer = ApplicationModuleDependencyAnalyzer(ApplicationModule)

    assert analyzer.application_module == ApplicationModule
    assert analyzer._module_tree is not None


def test_application_module_analyzer_find_service_in_exports():
    """Test finding module that exports a service"""
    analyzer = ApplicationModuleDependencyAnalyzer(ApplicationModule)

    providing_module = analyzer.find_module_providing_service(IAuthService)

    assert providing_module == AuthModule


def test_application_module_analyzer_find_service_in_providers():
    """Test finding module that provides a service (checks providers.keys())"""

    @Module(
        name="InternalModule",
        providers=[ProviderConfig(IAuthService, use_class=AuthService)],
        exports=[IAuthService],  # Must be exported to be found
    )
    class InternalModule(ModuleBase):
        pass

    @Module(name="TestAppModule", modules=[InternalModule])
    class TestAppModule(ModuleBase):
        pass

    analyzer = ApplicationModuleDependencyAnalyzer(TestAppModule)
    providing_module = analyzer.find_module_providing_service(IAuthService)

    assert providing_module == InternalModule


def test_application_module_analyzer_service_not_found():
    """Test finding service that doesn't exist"""

    class IUnknownService:
        pass

    analyzer = ApplicationModuleDependencyAnalyzer(ApplicationModule)
    providing_module = analyzer.find_module_providing_service(IUnknownService)

    assert providing_module is None


def test_application_module_analyzer_get_all_modules():
    """Test getting all modules in the tree"""
    analyzer = ApplicationModuleDependencyAnalyzer(ApplicationModule)

    all_modules = analyzer.get_all_modules()

    # Should include ApplicationModule, DatabaseModule, AuthModule, LoggingModule
    assert len(all_modules) >= 3
    assert AuthModule in all_modules
    assert DatabaseModule in all_modules


def test_application_module_analyzer_get_module_dependencies_recursive():
    """Test getting module dependencies recursively"""
    analyzer = ApplicationModuleDependencyAnalyzer(ApplicationModule)

    # DatabaseModule depends on LoggingModule
    dependencies = analyzer.get_module_dependencies(DatabaseModule)

    assert LoggingModule in dependencies


def test_application_module_analyzer_get_module_dependencies_none():
    """Test getting dependencies for module with no dependencies"""
    analyzer = ApplicationModuleDependencyAnalyzer(ApplicationModule)

    # AuthModule has no dependencies
    dependencies = analyzer.get_module_dependencies(AuthModule)

    assert len(dependencies) == 0


# ============================================================================
# Unit Tests: ForwardRefModule Resolution
# ============================================================================


def test_forward_ref_resolution_by_type():
    """Test resolving ForwardRefModule by type"""

    # Need to have DatabaseModule actually registered in the application tree
    @Module(
        name="ForwardRefTestModule",
        modules=[AuthModule, DatabaseModule],  # Register DatabaseModule first
    )
    class ForwardRefTestModule(ModuleBase):
        pass

    analyzer = ApplicationModuleDependencyAnalyzer(ForwardRefTestModule)

    # Now test resolving a ForwardRef to DatabaseModule
    forward_ref = ForwardRefModule(module=DatabaseModule)
    resolved = analyzer.resolve_forward_ref(forward_ref)

    assert resolved == DatabaseModule


def test_forward_ref_resolution_by_name():
    """Test resolving ForwardRefModule by module name"""

    # Need to have DatabaseModule actually registered in the application tree
    @Module(
        name="ForwardRefTestModule2",
        modules=[AuthModule, DatabaseModule],  # Register DatabaseModule first
    )
    class ForwardRefTestModule2(ModuleBase):
        pass

    analyzer = ApplicationModuleDependencyAnalyzer(ForwardRefTestModule2)

    # Now test resolving a ForwardRef by name
    forward_ref = ForwardRefModule(module_name="DatabaseModule")
    resolved = analyzer.resolve_forward_ref(forward_ref)

    assert resolved == DatabaseModule


def test_forward_ref_resolution_not_found():
    """Test resolving ForwardRefModule that doesn't exist"""

    @Module(name="ForwardRefTestModule3", modules=[AuthModule])
    class ForwardRefTestModule3(ModuleBase):
        pass

    analyzer = ApplicationModuleDependencyAnalyzer(ForwardRefTestModule3)

    forward_ref = ForwardRefModule(module_name="NonExistentModule")
    resolved = analyzer.resolve_forward_ref(forward_ref)

    assert resolved is None


# ============================================================================
# Integration Tests: Test.create_test_module()
# ============================================================================


def test_create_test_module_auto_resolves_controller_dependencies(reflect_context):
    """Test that controller dependencies are automatically resolved"""
    tm = Test.create_test_module(
        controllers=[UserController], application_module=ApplicationModule
    )

    tm.create_application()

    # Should be able to get the controller without UnsatisfiedRequirement
    controller = tm.get(UserController)

    assert controller is not None
    assert isinstance(controller.auth_service, IAuthService)


def test_create_test_module_auto_resolves_multiple_dependencies(reflect_context):
    """Test that multiple controller dependencies are resolved"""
    tm = Test.create_test_module(
        controllers=[AdminController], application_module=ApplicationModule
    )

    tm.create_application()
    controller = tm.get(AdminController)

    assert controller is not None
    assert isinstance(controller.auth_service, IAuthService)
    assert isinstance(controller.db_service, IDatabaseService)


def test_create_test_module_auto_resolves_nested_dependencies(reflect_context):
    """Test that nested module dependencies are recursively resolved"""
    tm = Test.create_test_module(
        controllers=[AdminController],  # Needs DatabaseModule which needs LoggingModule
        application_module=ApplicationModule,
    )

    app = tm.create_application()

    # Should be able to get services from nested dependencies
    module_ref = app.injector.tree_manager.get_module(tm.module).value

    controller = module_ref.get(AdminController)
    assert controller is not None

    # Verify nested module (LoggingModule) is available
    db_module_data = app.injector.tree_manager.get_module(DatabaseModule)
    assert db_module_data is not None

    logging_service = db_module_data.value.get(ILoggingService)
    assert logging_service is not None


def test_create_test_module_manual_override_takes_precedence(reflect_context):
    """Test that manually provided modules override auto-resolution"""

    class MockAuthService(IAuthService):
        def authenticate(self, token: str) -> dict:
            return {"user": "mock_user", "token": "mock"}

    @Module(
        name="MockAuthModule",
        providers=[ProviderConfig(IAuthService, use_class=MockAuthService)],
        exports=[IAuthService],
    )
    class MockAuthModule(ModuleBase):
        pass

    tm = Test.create_test_module(
        controllers=[UserController],
        modules=[MockAuthModule],  # Explicitly override
        application_module=ApplicationModule,
    )

    tm.create_application()
    controller = tm.get(UserController)

    # Should use MockAuthService
    result = controller.auth_service.authenticate("test")
    assert result["user"] == "mock_user"


def test_create_test_module_without_application_module_works_as_before(reflect_context):
    """Test backward compatibility: without application_module, manual registration required"""
    # This should work with manual registration
    tm = Test.create_test_module(
        controllers=[UserController],
        modules=[AuthModule],  # Manual registration
        # No application_module
    )

    tm.create_application()
    controller = tm.get(UserController)

    assert controller is not None


def test_create_test_module_without_application_module_fails_on_missing_deps(
    reflect_context,
):
    """Test that missing dependencies still fail without application_module"""
    tm = Test.create_test_module(
        controllers=[UserController]
        # No modules, no application_module
    )

    tm.create_application()

    # Should fail because IAuthService is not registered
    with pytest.raises(UnsatisfiedRequirement):
        tm.get(UserController)


def test_create_test_module_forward_ref_resolution(reflect_context):
    """Test that ForwardRefModule is automatically resolved"""

    @Module(
        name="ModuleWithForwardRef",
        modules=[ForwardRefModule(module=AuthModule)],
    )
    class ModuleWithForwardRef(ModuleBase):
        pass

    @Module(name="TestAppWithForwardRef", modules=[AuthModule, ModuleWithForwardRef])
    class TestAppWithForwardRef(ModuleBase):
        pass

    tm = Test.create_test_module(
        controllers=[UserController],
        modules=[ModuleWithForwardRef],  # Contains ForwardRef to AuthModule
        application_module=TestAppWithForwardRef,
    )

    tm.create_application()
    controller = tm.get(UserController)

    assert controller is not None
    assert isinstance(controller.auth_service, IAuthService)


def test_create_test_module_no_controllers_still_works(reflect_context):
    """Test that create_test_module works without controllers"""
    tm = Test.create_test_module(
        modules=[AuthModule], application_module=ApplicationModule
    )

    tm.create_application()

    # Should be able to get services directly
    auth_service = tm.get(IAuthService)
    assert auth_service is not None


def test_create_test_module_complex_hierarchy(reflect_context):
    """Test complex module hierarchy with multiple levels"""

    class IUserRepo:
        pass

    @injectable
    class UserRepo(IUserRepo):
        def __init__(self, db: IDatabaseService):
            self.db = db

    @Module(
        name="UserModule",
        modules=[DatabaseModule],
        providers=[ProviderConfig(IUserRepo, use_class=UserRepo, tag="user_repo")],
        exports=[IUserRepo],
    )
    class UserModule(ModuleBase):
        pass

    @Module(name="ComplexAppModule", modules=[UserModule, AuthModule])
    class ComplexAppModule(ModuleBase):
        pass

    @Controller()
    class ComplexController:
        def __init__(self, user_repo: InjectByTag("user_repo"), auth: IAuthService):
            self.user_repo = user_repo
            self.auth = auth

    tm = Test.create_test_module(
        controllers=[ComplexController], application_module=ComplexAppModule
    )

    tm.create_application()
    controller = tm.get(ComplexController)

    assert controller is not None
    assert isinstance(controller.user_repo, IUserRepo)
    assert isinstance(controller.auth, IAuthService)


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


def test_dependency_resolution_error_with_application_module():
    """Test DependencyResolutionError message with application_module"""

    class IMissingService:
        pass

    @Controller()
    class ControllerWithMissing:
        def __init__(self, missing: IMissingService):
            self.missing = missing

    error = DependencyResolutionError(
        IMissingService, ControllerWithMissing, ApplicationModule
    )

    assert "ControllerWithMissing" in str(error)
    assert "IMissingService" in str(error)
    assert "ApplicationModule" in str(error)
    assert "Please either:" in str(error)


def test_dependency_resolution_error_without_application_module():
    """Test DependencyResolutionError message without application_module"""

    class IMissingService:
        pass

    @Controller()
    class ControllerWithMissing:
        def __init__(self, missing: IMissingService):
            self.missing = missing

    error = DependencyResolutionError(IMissingService, ControllerWithMissing, None)

    assert "ControllerWithMissing" in str(error)
    assert "IMissingService" in str(error)
    assert "no application_module was provided" in str(error)


def test_create_test_module_with_providers_still_works(reflect_context):
    """Test that providing services via providers still works"""

    class CustomService:
        pass

    @Controller()
    class ControllerWithCustomService:
        def __init__(self, custom: CustomService):
            self.custom = custom

    tm = Test.create_test_module(
        controllers=[ControllerWithCustomService],
        providers=[CustomService],  # Provide service directly
        application_module=ApplicationModule,
    )

    app = tm.create_application()
    controller = app.injector.tree_manager.get_module(tm.module).value.get(
        ControllerWithCustomService
    )

    assert controller is not None
    assert isinstance(controller.custom, CustomService)


def test_create_test_module_with_import_string_application_module(reflect_context):
    """Test that application_module accepts import strings"""
    # Use the module's fully qualified name as import string
    import_string = "tests.test_testing_dependency_resolution:ApplicationModule"

    tm = Test.create_test_module(
        controllers=[UserController],
        application_module=import_string,  # Pass as string!
    )

    tm.create_application()
    controller = tm.get(UserController)

    assert controller is not None
    assert isinstance(controller.auth_service, IAuthService)


def test_application_module_analyzer_with_import_string():
    """Test that ApplicationModuleDependencyAnalyzer accepts import strings"""
    import_string = "tests.test_testing_dependency_resolution:ApplicationModule"

    analyzer = ApplicationModuleDependencyAnalyzer(import_string)

    assert analyzer.application_module == ApplicationModule
    providing_module = analyzer.find_module_providing_service(IAuthService)
    assert providing_module == AuthModule


def test_get_type_from_tag():
    """Test that get_type_from_tag resolves tagged providers correctly"""

    class ITaggedService:
        pass

    @Module(
        providers=[
            ProviderConfig(ITaggedService, use_class=ITaggedService, tag="my_tag")
        ],
        exports=[ITaggedService],
    )
    class TaggedModule(ModuleBase):
        pass

    @Module(modules=[TaggedModule])
    class TestAppModule(ModuleBase):
        pass

    analyzer = ApplicationModuleDependencyAnalyzer(TestAppModule)

    # Create a tag like InjectByTag does
    tag = InjectByTag("my_tag")

    # Resolve the type from the tag
    resolved_type = analyzer.get_type_from_tag(tag)

    assert resolved_type == ITaggedService


def test_override_provider_with_automatic_resolution(reflect_context):
    """Test that override_provider works with automatic dependency resolution"""

    class MockAuthService(IAuthService):
        def authenticate(self, token: str):
            return {"user": "mock_user", "roles": ["admin"]}

    tm = Test.create_test_module(
        controllers=[UserController],
        application_module=ApplicationModule,
    )

    # Override the auth service using override_provider
    tm.override_provider(IAuthService, use_class=MockAuthService)

    tm.create_application()
    controller = tm.get(UserController)

    assert controller is not None
    assert isinstance(controller.auth_service, MockAuthService)
    # Verify it's the mocked version
    result = controller.auth_service.authenticate("test_token")
    assert result["user"] == "mock_user"
    assert result["roles"] == ["admin"]


def test_override_provider_with_use_value(reflect_context):
    """Test override_provider with use_value parameter"""

    class FixedAuthService:
        def authenticate(self, token: str):
            return {"user": "fixed_user"}

    fixed_instance = FixedAuthService()

    tm = Test.create_test_module(
        controllers=[UserController],
        application_module=ApplicationModule,
    )

    # Override with a specific instance
    tm.override_provider(IAuthService, use_value=fixed_instance)

    tm.create_application()
    controller = tm.get(UserController)

    assert controller is not None
    assert controller.auth_service is fixed_instance
