# Custom Policies with Requirements

Custom policies with requirements provide the most flexible way to implement authorization logic in Ellar. They allow you to pass additional parameters to your policies and implement complex authorization rules.

## Creating a Policy with Requirements

To create a policy with requirements, inherit from `PolicyWithRequirement`:

```python
from ellar.auth import PolicyWithRequirement
from ellar.common import IExecutionContext
from ellar.di import injectable
import typing as t

@injectable
class AgeRequirementPolicy(PolicyWithRequirement):
    async def handle(self, context: IExecutionContext, requirement: t.Any) -> bool:
        min_age = requirement.values()[0]  # Access the first requirement argument
        user_age = int(context.user.get("age", 0))
        return user_age >= min_age

@injectable
class TeamMemberPolicy(PolicyWithRequirement):
    async def handle(self, context: IExecutionContext, requirement: t.Any) -> bool:
        team_name = requirement.values()[0]
        user_teams = context.user.get("teams", [])
        return team_name in user_teams
```

## Using Policies with Requirements

Apply policies with requirements using square bracket notation:

```python
from ellar.auth import AuthenticationRequired, Authorize, CheckPolicies
from ellar.common import Controller, get

@Controller("/content")
@Authorize()
@AuthenticationRequired()
class ContentController:
    @get("/adult")
    @CheckPolicies(AgeRequirementPolicy[21])  # Requires age >= 21
    async def adult_content(self):
        return "Adult Content"

    @get("/team")
    @CheckPolicies(TeamMemberPolicy["engineering"])  # Requires membership in engineering team
    async def team_content(self):
        return "Team Content"
```

## Multiple Requirements

You can pass multiple requirements to a policy:

```python
@injectable
class ProjectAccessPolicy(PolicyWithRequirement):
    async def handle(self, context: IExecutionContext, requirement: t.Any) -> bool:
        project_id = requirement.arg_1
        access_level = requirement.arg_2
        
        user_projects = context.user.get("projects", {})
        user_access = user_projects.get(project_id)
        
        return user_access and user_access >= access_level

@Controller("/projects")
@Authorize()
@AuthenticationRequired()
class ProjectController:
    @get("/{project_id}/edit")
    @CheckPolicies(ProjectAccessPolicy["project-123", "write"])
    async def edit_project(self):
        return "Edit Project"

    @get("/{project_id}/admin")
    @CheckPolicies(ProjectAccessPolicy["project-123", "admin"])
    async def admin_project(self):
        return "Project Administration"
```

## Custom Requirement Types

You can define custom requirement types for more structured requirements:

```python
from ellar.common.compatible import AttributeDict

class ProjectRequirement(AttributeDict):
    def __init__(self, project_id: str, min_access_level: str) -> None:
        super().__init__({
            "project_id": project_id,
            "min_access_level": min_access_level
        })

@injectable
class EnhancedProjectPolicy(PolicyWithRequirement):
    requirement_type = ProjectRequirement  # Specify custom requirement type

    async def handle(self, context: IExecutionContext, requirement: ProjectRequirement) -> bool:
        user_projects = context.user.get("projects", {})
        user_access = user_projects.get(requirement.project_id)
        
        return user_access and user_access >= requirement.min_access_level

@Controller("/enhanced-projects")
@Authorize()
@AuthenticationRequired()
class EnhancedProjectController:
    @get("/{project_id}/manage")
    @CheckPolicies(EnhancedProjectPolicy[ProjectRequirement("project-123", "manage")])
    async def manage_project(self):
        return "Manage Project"
```

## Complex Example: Multi-Factor Authorization

Here's an example of a policy that requires both age verification and location-based access:

```python
class RegionRequirement(AttributeDict):
    def __init__(self, min_age: int, allowed_regions: list[str]) -> None:
        super().__init__({
            "min_age": min_age,
            "allowed_regions": allowed_regions
        })

@injectable
class RegionalAgePolicy(PolicyWithRequirement):
    requirement_type = RegionRequirement

    async def handle(self, context: IExecutionContext, requirement: RegionRequirement) -> bool:
        user_age = int(context.user.get("age", 0))
        user_region = context.user.get("region", "")
        
        age_requirement_met = user_age >= requirement.min_age
        region_requirement_met = user_region in requirement.allowed_regions
        
        return age_requirement_met and region_requirement_met

@Controller("/regional")
@Authorize()
@AuthenticationRequired()
class RegionalController:
    @get("/content")
    @CheckPolicies(
        RegionalAgePolicy[RegionRequirement(21, ["US", "CA", "UK"])]
    )
    async def regional_content(self):
        return "Region-Restricted Content"

    @get("/special")
    @CheckPolicies(
        RegionalAgePolicy[RegionRequirement(18, ["US"])] |
        RegionalAgePolicy[RegionRequirement(21, ["CA", "UK"])]
    )
    async def special_content(self):
        return "Special Content with Different Regional Requirements"
```

## Best Practices

1. Use descriptive names for policy and requirement classes
2. Keep requirement parameters simple and type-safe
3. Document the expected format and values of requirements
4. Use custom requirement types for complex parameter sets
5. Consider combining policies for complex authorization scenarios
6. Handle edge cases and invalid requirement values gracefully

## Combining with Other Policy Types

Policies with requirements can be combined with other policy types using logical operators:

```python
@Controller("/mixed")
@Authorize()
@AuthenticationRequired()
class MixedController:
    @get("/special")
    @CheckPolicies(
        AgeRequirementPolicy[21] &
        RolePolicy("premium_user")
    )
    async def special_access(self):
        return "Special Access Content"

    @get("/alternative")
    @CheckPolicies(
        (AgeRequirementPolicy[18] & TeamMemberPolicy["beta-testers"]) |
        RolePolicy("admin")
    )
    async def alternative_access(self):
        return "Alternative Access Content"
```

For more information about combining different types of policies, see [Combining Policies](./combining-policies.md). 
