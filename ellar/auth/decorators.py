import typing as t

from ellar.common import constants
from ellar.common import set_metadata as set_meta

from .constants import POLICY_KEYS
from .guards import AuthenticatedRequiredGuard
from .interceptor import AuthorizationInterceptor
from .policy import PolicyType


def CheckPolicies(*policies: t.Union[str, PolicyType]) -> t.Callable:
    """
    Applies policy requirements to a controller or route function.

    This decorator allows you to specify one or more policies that must be satisfied
    for the user to access the decorated endpoint. Policies can be either string
    identifiers or PolicyType objects.

    Example:
        ```python
        @Controller()
        class UserController:
            @CheckPolicies('admin', RequireRole('manager'))
            def get_sensitive_data(self):
                return {'data': 'sensitive information'}
        ```

    Args:
        *policies: Variable number of policy requirements. Can be strings or PolicyType objects.
            - String policies are resolved using the policy provider
            - PolicyType objects are evaluated directly

    Returns:
        A decorator function that applies the policy requirements.
    """

    def _decorator(target: t.Callable) -> t.Union[t.Callable, t.Any]:
        set_meta(POLICY_KEYS, list(policies))(target)
        return target

    return _decorator


def Authorize() -> t.Callable:
    """
    Enables authorization checks for a controller or route function.

    This decorator adds the AuthorizationInterceptor which performs two main checks:
    1. Verifies that the user is authenticated
    2. Validates any policy requirements specified using @CheckPolicies

    Example:
        ```python
        @Controller()
        @Authorize()  # Enable authorization for all routes in controller
        class SecureController:
            @get('/')
            @CheckPolicies('admin')  # Require admin policy
            def secure_endpoint(self):
                return {'message': 'secure data'}
        ```

    Returns:
        A decorator function that enables authorization checks.
    """

    return set_meta(constants.ROUTE_INTERCEPTORS, [AuthorizationInterceptor])


def AuthenticationRequired(
    authentication_scheme: t.Optional[str] = None,
    openapi_scope: t.Optional[t.List] = None,
) -> t.Callable:
    """
    Requires authentication for accessing a controller or route function.

    This decorator adds the AuthenticatedRequiredGuard which ensures that requests
    are authenticated before they can access the protected resource.

    Example:
        ```python
        @Controller()
        class UserController:
            @get('/profile')
            @AuthenticationRequired('jwt')  # Require JWT authentication
            def get_profile(self):
                return {'user': 'data'}

            @get('/public')
            @AuthenticationRequired(openapi_scope=['read:public'])
            def public_data(self):
                return {'public': 'data'}
        ```

    Args:
        authentication_scheme: Optional name of the authentication scheme to use.
            This should match the scheme name defined in your authentication setup.
        openapi_scope: Optional list of OpenAPI security scopes required for the endpoint.
            These scopes will be reflected in the OpenAPI documentation.

    Returns:
        A decorator function that enforces authentication requirements.
    """
    if callable(authentication_scheme):
        return set_meta(constants.GUARDS_KEY, [AuthenticatedRequiredGuard(None, [])])(
            authentication_scheme
        )

    return set_meta(
        constants.GUARDS_KEY,
        [AuthenticatedRequiredGuard(authentication_scheme, openapi_scope or [])],
    )


def SkipAuth() -> t.Callable:
    """
    Marks a controller or route function to skip authentication checks.

    This decorator is useful when you have a controller with @AuthenticationRequired
    but want to exclude specific routes from the authentication requirement.

    Example:
        ```python
        @Controller()
        @AuthenticationRequired()  # Require auth for all routes
        class UserController:
            @get('/private')
            def private_data(self):  # This requires auth
                return {'private': 'data'}

            @get('/public')
            @SkipAuth()  # This endpoint skips auth
            def public_data(self):
                return {'public': 'data'}
        ```

    Returns:
        A decorator function that marks the endpoint to skip authentication.
    """

    return set_meta(
        constants.SKIP_AUTH,
        True,
    )
