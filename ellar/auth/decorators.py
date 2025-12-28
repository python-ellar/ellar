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

    This decorator enforces one or more policies that must be satisfied for the user to access the decorated endpoint.
    Policies can be specified as string identifiers (resolved via provider) or `PolicyType` objects.

    Example:
    ```python
    @Controller()
    class UserController:
        @CheckPolicies('admin', RequireRole('manager'))
        def get_sensitive_data(self):
            return {'data': 'sensitive information'}
    ```

    :param policies: Variable number of policy requirements.
        - String policies are resolved using the service provider.
        - `PolicyType` objects are evaluated directly.
    :return: A decorator function that applies the policy requirements.
    """

    def _decorator(target: t.Callable) -> t.Union[t.Callable, t.Any]:
        set_meta(POLICY_KEYS, list(policies))(target)
        return target

    return _decorator


def Authorize() -> t.Callable:
    """
    Enables authorization checks for a controller or route function.

    This decorator registers the `AuthorizationInterceptor`, which performs two primary checks:
    1. Verifies that the user is authenticated.
    2. Validates any policy requirements specified using `@CheckPolicies`.

    Example:
    ```python
    @Controller()
    @Authorize()  # Enable authorization for all routes in the controller
    class SecureController:
        @get('/')
        @CheckPolicies('admin')  # Require admin policy for this specific route
        def secure_endpoint(self):
            return {'message': 'secure data'}
    ```

    :return: A decorator function that enables authorization checks.
    """

    return set_meta(constants.ROUTE_INTERCEPTORS, [AuthorizationInterceptor])


def AuthenticationRequired(
    authentication_scheme: t.Optional[str] = None,
    openapi_scope: t.Optional[t.List] = None,
) -> t.Callable:
    """
    Requires authentication for accessing a controller or route function.

    This decorator adds the `AuthenticatedRequiredGuard` to ensure that requests are authenticated
    before accessing the protected resource.

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

    :param authentication_scheme: Optional name of the authentication scheme to use.
        This must match a scheme defined in the application's authentication setup.
    :param openapi_scope: Optional list of OpenAPI security scopes required for the endpoint.
        These scopes are reflected in the OpenAPI documentation.
    :return: A decorator function that enforces authentication requirements.
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

    This decorator is useful for excluding specific routes from authentication requirements
    applied at the controller level (e.g., via `@AuthenticationRequired`).

    Example:
    ```python
    @Controller()
    @AuthenticationRequired()  # Require auth for all routes by default
    class UserController:
        @get('/private')
        def private_data(self):  # Inherits auth requirement
            return {'private': 'data'}

        @get('/public')
        @SkipAuth()  # Overrides controller-level auth requirement
        def public_data(self):
            return {'public': 'data'}
    ```

    :return: A decorator function that marks the endpoint to skip authentication.
    """

    return set_meta(
        constants.SKIP_AUTH,
        True,
    )
