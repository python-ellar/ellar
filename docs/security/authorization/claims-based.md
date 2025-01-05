# Claims-Based Authorization

Claims-based authorization provides a more flexible and granular approach to authorization compared to role-based authorization. Claims are key-value pairs that represent attributes of the user and their access rights.

## Using ClaimsPolicy

Ellar provides the `ClaimsPolicy` class for implementing claims-based authorization:

```python
from ellar.auth import AuthenticationRequired, Authorize, CheckPolicies
from ellar.auth.policy import ClaimsPolicy
from ellar.common import Controller, get

@Controller("/articles")
@Authorize()
@AuthenticationRequired()
class ArticleController:
    @get("/create")
    @CheckPolicies(ClaimsPolicy("article", "create"))
    async def create_article(self):
        return "Create Article"

    @get("/publish")
    @CheckPolicies(ClaimsPolicy("article", "create", "publish"))
    async def publish_article(self):
        return "Publish Article"
```

## How ClaimsPolicy Works

The `ClaimsPolicy` checks if the user has specific claim values for a given claim type. Claims are typically stored in the user's identity:

```python
# Example user data structure with claims
user_data = {
    "id": "123",
    "username": "john_doe",
    "article": ["create", "read", "publish"],  # Claim type: "article" with multiple values
    "subscription": "premium"  # Claim type: "subscription" with single value
}
```

## Single vs Multiple Claim Values

Claims can have single or multiple values:

```python
@Controller("/content")
@Authorize()
@AuthenticationRequired()
class ContentController:
    @get("/premium")
    @CheckPolicies(ClaimsPolicy("subscription", "premium"))  # Single claim value
    async def premium_content(self):
        return "Premium Content"

    @get("/manage")
    @CheckPolicies(ClaimsPolicy("permissions", "create", "edit", "delete"))  # Multiple claim values
    async def manage_content(self):
        return "Content Management"
```

## Combining Claims Policies

You can combine multiple claims policies using logical operators:

```python
@Controller("/advanced")
@Authorize()
@AuthenticationRequired()
class AdvancedController:
    @get("/editor")
    @CheckPolicies(
        ClaimsPolicy("article", "edit") & 
        ClaimsPolicy("status", "active")
    )
    async def editor_dashboard(self):
        return "Editor Dashboard"

    @get("/moderator")
    @CheckPolicies(
        ClaimsPolicy("content", "moderate") | 
        ClaimsPolicy("role", "admin")
    )
    async def moderator_dashboard(self):
        return "Moderator Dashboard"
```

## Best Practices

1. Use descriptive claim types and values
2. Keep claim values simple and atomic
3. Use claims for fine-grained permissions
4. Consider using claims instead of roles for more flexible authorization
5. Document your claim types and their possible values

## Example: E-commerce Authorization

Here's a comprehensive example showing claims-based authorization in an e-commerce application:

```python
@Controller("/store")
@Authorize()
@AuthenticationRequired()
class StoreController:
    @get("/products")
    @CheckPolicies(ClaimsPolicy("store", "view_products"))
    async def view_products(self):
        return "Product List"

    @get("/products/manage")
    @CheckPolicies(
        ClaimsPolicy("store", "manage_products") & 
        ClaimsPolicy("account_status", "verified")
    )
    async def manage_products(self):
        return "Product Management"

    @get("/orders")
    @CheckPolicies(
        ClaimsPolicy("store", "view_orders") | 
        ClaimsPolicy("role", "customer_service")
    )
    async def view_orders(self):
        return "Order List"

    @get("/reports")
    @CheckPolicies(
        ClaimsPolicy("store", "view_reports") & 
        (ClaimsPolicy("role", "manager") | ClaimsPolicy("permissions", "analytics"))
    )
    async def view_reports(self):
        return "Store Reports"
```

## Claims vs Roles

While roles are a form of claims, dedicated claims offer several advantages:

1. **Granularity**: Claims can represent specific permissions rather than broad role categories
2. **Flexibility**: Claims can be easily added or modified without changing role structures
3. **Clarity**: Claims directly express what a user can do rather than implying it through roles
4. **Scalability**: Claims can grow with your application's needs without role explosion

For complex authorization scenarios, consider combining claims with roles and custom policies. See [Combining Policies](./combining-policies.md) for more information. 
