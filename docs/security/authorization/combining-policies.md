# **Combining Policies**

Ellar provides powerful operators to combine different types of policies for complex authorization scenarios. This guide shows you how to use these combinations effectively.

## **Basic Policy Operators**

Ellar supports three logical operators for combining policies:

- `&` (AND): Both policies must return `True`
- `|` (OR): At least one policy must return `True`
- `~` (NOT): Inverts the policy result

## **Simple Combinations**

Here are basic examples of combining policies:

```python
from ellar.auth import AuthenticationRequired, Authorize, CheckPolicies
from ellar.auth.policy import RolePolicy, ClaimsPolicy
from ellar.common import Controller, get

@Controller("/examples")
@Authorize()
@AuthenticationRequired()
class ExampleController:
    @get("/and-example")
    @CheckPolicies(RolePolicy("admin") & RolePolicy("editor"))
    async def requires_both_roles(self):
        return "Must be both admin and editor"

    @get("/or-example")
    @CheckPolicies(RolePolicy("admin") | RolePolicy("moderator"))
    async def requires_either_role(self):
        return "Must be either admin or moderator"

    @get("/not-example")
    @CheckPolicies(~RolePolicy("banned"))
    async def not_banned(self):
        return "Access allowed if not banned"
```

## **Complex Combinations**

You can create more complex authorization rules by combining multiple policies:

```python
@Controller("/advanced")
@Authorize()
@AuthenticationRequired()
class AdvancedController:
    @get("/complex")
    @CheckPolicies(
        (RolePolicy("editor") & ClaimsPolicy("department", "content")) |
        RolePolicy("admin")
    )
    async def complex_access(self):
        return "Complex access rules"

    @get("/nested")
    @CheckPolicies(
        RolePolicy("user") &
        (ClaimsPolicy("subscription", "premium") | RolePolicy("staff")) &
        ~RolePolicy("restricted")
    )
    async def nested_rules(self):
        return "Nested policy rules"
```

## **Combining Different Policy Types**

You can mix and match different types of policies:

```python
from ellar.auth import RolePolicy, ClaimsPolicy
from ellar.common import Controller, get
from .custom_policies import AgeRequirementPolicy, TeamMemberPolicy

@Controller("/mixed")
@Authorize()
class MixedPolicyController:
    @get("/content")
    @CheckPolicies(
        (AgeRequirementPolicy[18] & ClaimsPolicy("region", "US", "CA")) |
        RolePolicy("global_admin")
    )
    async def age_and_region(self):
        return "Age and region restricted content"

    @get("/team-access")
    @CheckPolicies(
        TeamMemberPolicy["engineering"] &
        (RolePolicy("developer") | RolePolicy("team_lead")) &
        ClaimsPolicy("security_clearance", "level2")
    )
    async def team_access(self):
        return "Team-specific access"
```

## **Real-World Examples**

Here are some practical examples of policy combinations:

### **Content Management System**   

```python
@Controller("/cms")
@Authorize()
class CMSController:
    @get("/articles/{id}/edit")
    @CheckPolicies(
        (RolePolicy("editor") & ClaimsPolicy("article", "edit")) |
        RolePolicy("admin") |
        (TeamMemberPolicy["content"] & ClaimsPolicy("article", "edit"))
    )
    async def edit_article(self):
        return "Edit Article"

    @get("/articles/{id}/publish")
    @CheckPolicies(
        (RolePolicy("editor") & ClaimsPolicy("article", "publish") & ~RolePolicy("junior")) |
        RolePolicy("senior_editor") |
        RolePolicy("admin")
    )
    async def publish_article(self):
        return "Publish Article"
```

### **E-commerce Platform**

```python
@Controller("/store")
@Authorize()
class StoreController:
    @get("/products/{id}/manage")
    @CheckPolicies(
        (RolePolicy("vendor") & ClaimsPolicy("store", "manage_products")) |
        RolePolicy("store_admin")
    )
    async def manage_product(self):
        return "Manage Product"

    @get("/orders/{id}/refund")
    @CheckPolicies(
        (RolePolicy("support") & ClaimsPolicy("order", "refund") & AgeRequirementPolicy[21]) |
        RolePolicy("finance_admin")
    )
    async def process_refund(self):
        return "Process Refund"
```

## **Best Practices**

1. **Readability**
    - Use parentheses to make complex combinations clear
    - Break long policy combinations into multiple lines
    - Consider creating custom policies for very complex rules

2. **Performance**
    - Order OR conditions with the most likely to succeed first
    - Order AND conditions with the least expensive to evaluate first
    - Consider caching policy results for expensive evaluations

3. **Maintenance**
    - Document complex policy combinations
    - Create reusable policy combinations for common patterns
    - Keep policy logic modular and testable

4. **Security**
    - Always start with the principle of least privilege
    - Use OR combinations carefully as they broaden access
    - Regularly audit policy combinations for security implications

## **Common Patterns**

Here are some common patterns for combining policies:

```python
# Role hierarchy
base_access = RolePolicy("user")
elevated_access = base_access & RolePolicy("premium")
admin_access = elevated_access & RolePolicy("admin")

# Feature access with fallback
feature_access = (
    ClaimsPolicy("feature", "beta") & RolePolicy("beta_tester")
) | RolePolicy("admin")

# Geographic restrictions with age verification
regional_access = (
    AgeRequirementPolicy[21] & 
    ClaimsPolicy("region", "US", "CA")
) | RolePolicy("global_access")

# Team-based access with role requirements
team_access = (
    TeamMemberPolicy["project-x"] & 
    (RolePolicy("developer") | RolePolicy("designer"))
) & ~RolePolicy("restricted")
```

For more specific examples of each policy type, refer to:
- [Role-Based Authorization](./role-based.md)
- [Claims-Based Authorization](./claims-based.md)
- [Custom Policies with Requirements](./custom-policies.md) 
