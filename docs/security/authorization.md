# Authorization

Authorization is a crucial security feature in Ellar that determines what resources authenticated users can access. Ellar provides a flexible and powerful authorization system through policies, roles, and claims.

## Table of Contents

1. [Basic Authorization](#basic-authorization)
2. [Policies](./authorization/policies.md)
3. [Role-Based Authorization](./authorization/role-based.md) 
4. [Claims-Based Authorization](./authorization/claims-based.md)
5. [Custom Policies with Requirements](./authorization/custom-policies.md)
6. [Combining Policies](./authorization/combining-policies.md)

## Basic Authorization

To use authorization in your Ellar application, you need to:

1. Decorate your controllers or routes with `@Authorize()`
2. Apply specific policies using `@CheckPolicies()`
3. Ensure users are authenticated using `@AuthenticationRequired()`

Here's a basic example:

```python
from ellar.auth import AuthenticationRequired, Authorize, CheckPolicies
from ellar.common import Controller, get

@Controller("/articles")
@Authorize()  # Enable authorization for all routes
@AuthenticationRequired()  # Require authentication
class ArticleController:
    @get("/admin")
    @CheckPolicies(RolePolicy("admin"))  # Only allow admins
    async def admin_dashboard(self):
        return "Admin Dashboard"

    @get("/public")
    async def public_articles(self):  # Accessible to any authenticated user
        return "Public Articles"
```

For detailed information about specific authorization features, please refer to the respective sections in the documentation.
