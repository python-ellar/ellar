# Role-Based Authorization

Role-based authorization is a common approach where access to resources is determined by the roles assigned to a user. Ellar provides built-in support for role-based authorization through the `RolePolicy` class.

## Using RolePolicy

The `RolePolicy` class allows you to check if a user has specific roles:

```python
from ellar.auth import AuthenticationRequired, Authorize, CheckPolicies
from ellar.auth.policy import RolePolicy
from ellar.common import Controller, get

@Controller("/admin")
@Authorize()
@AuthenticationRequired()
class AdminController:
    @get("/dashboard")
    @CheckPolicies(RolePolicy("admin"))
    async def admin_dashboard(self):
        return "Admin Dashboard"

    @get("/reports")
    @CheckPolicies(RolePolicy("admin", "analyst"))  # Requires both roles
    async def view_reports(self):
        return "Admin Reports"
```

## How RolePolicy Works

The `RolePolicy` checks the user's roles against the required roles. The roles are typically stored in the user's claims under the "roles" key:

```python
# Example user data structure
user_data = {
    "id": "123",
    "username": "john_doe",
    "roles": ["admin", "user"]
}
```

## Multiple Role Requirements

You can require multiple roles in different ways:

```python
@Controller("/organization")
@Authorize()
@AuthenticationRequired()
class OrganizationController:
    @get("/finance")
    @CheckPolicies(RolePolicy("admin") | RolePolicy("finance"))  # Requires either role
    async def finance_dashboard(self):
        return "Finance Dashboard"

    @get("/hr-admin")
    @CheckPolicies(RolePolicy("hr") & RolePolicy("admin"))  # Requires both roles
    async def hr_admin_dashboard(self):
        return "HR Admin Dashboard"

    @get("/super-admin")
    @CheckPolicies(RolePolicy("admin", "super"))  # Requires both roles (alternative syntax)
    async def super_admin_dashboard(self):
        return "Super Admin Dashboard"
```

## Best Practices

1. Use role names that are descriptive and follow a consistent naming convention
2. Keep the number of roles manageable
3. Consider using claims for more fine-grained permissions
4. Use role combinations when more complex access rules are needed

## Example: Multi-Department Access

Here's an example showing how to handle access for users with different department roles:

```python
@Controller("/departments")
@Authorize()
@AuthenticationRequired()
class DepartmentController:
    @get("/it")
    @CheckPolicies(RolePolicy("it_staff") | RolePolicy("it_manager"))
    async def it_department(self):
        return "IT Department"

    @get("/it/admin")
    @CheckPolicies(RolePolicy("it_manager"))
    async def it_admin(self):
        return "IT Administration"

    @get("/cross-department")
    @CheckPolicies(
        RolePolicy("it_manager") | 
        RolePolicy("hr_manager") | 
        RolePolicy("finance_manager")
    )
    async def department_managers(self):
        return "Department Managers Only"
```

## Combining with Other Policies

Role-based authorization can be combined with other policy types for more complex authorization scenarios. See [Combining Policies](./combining-policies.md) for more information. 
