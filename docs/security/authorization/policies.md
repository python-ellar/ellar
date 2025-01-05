# **Policies in Ellar**

Policies are rules that determine whether a user can perform a specific action or access a particular resource. In Ellar, policies are implemented as classes that inherit from the `Policy` base class.

## **Basic Policy Structure**

A basic policy must inherit from `Policy` and implement the `handle` method:

```python
from ellar.auth import Policy
from ellar.common import IExecutionContext
from ellar.di import injectable

@injectable
class AdultOnlyPolicy(Policy):
    async def handle(self, context: IExecutionContext) -> bool:
        # Access user information from context
        user_age = int(context.user.get("age", 0))
        return user_age >= 18
```

## **Using Policies**

To apply policies to your routes or controllers, use the `@CheckPolicies` decorator:

```python
from ellar.auth import AuthenticationRequired, Authorize, CheckPolicies
from ellar.common import Controller, get

@Controller("/content")
@Authorize()
class ContentController:
    @get("/adult")
    @CheckPolicies(AdultOnlyPolicy)
    async def adult_content(self):
        return "Adult Only Content"
```

## **Policy Context**

The `IExecutionContext` passed to the policy's `handle` method provides access to:

- User information (`context.user`)
- Request details
- Application context
- Service provider for dependency injection

## **Best Practices**

1. Always decorate policy classes with `@injectable` for proper dependency injection
2. Keep policies focused on a single responsibility
3. Make policy names descriptive of their function
4. Use type hints for better code maintainability
5. Return boolean values from the `handle` method

## **Example: Premium User Policy**

Here's an example of a policy that checks if a user has premium access:

```python
@injectable
class PremiumUserPolicy(Policy):
    async def handle(self, context: IExecutionContext) -> bool:
        subscription_type = context.user.get("subscription", "free")
        return subscription_type == "premium"

@Controller("/premium")
@Authorize()
class PremiumController:
    @get("/content")
    @CheckPolicies(PremiumUserPolicy)
    async def premium_content(self):
        return "Premium Content"
```

For more specific types of policies, see:
- [Role-Based Authorization](./role-based.md)
- [Claims-Based Authorization](./claims-based.md)
- [Custom Policies with Requirements](./custom-policies.md) 
