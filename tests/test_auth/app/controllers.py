from ellar.auth import Authorization, Policy
from ellar.common import Controller, get

from .requirement import AtLeast21


@Controller("/movies")
@Authorization("AtLeast21")
class MoviesControllers:
    @get("/")
    async def fast_x(self):
        return "fast and furious 10"


@Controller("/article")
class ArticleController:
    @get("/create")
    @Authorization("CanCreateAndPublishArticle")
    async def create_and_publish(self):
        return "fast and furious 10 Article"

    @get("/create/list")
    async def get_articles(self):
        return "List of articles"

    @get("/admin-only")
    @Authorization("Administrator")
    async def admin_only(self):
        return "List of articles"

    @get("/staff-only")
    @Authorization("Staff")
    async def staff_only(self):
        return "List of articles"

    @get("/at-least-21")
    @Authorization(Policy.add_requirements(AtLeast21))
    async def at_least_21(self):
        return "Only for Age of 21 or more"

    @get("/at-least-21-case-2")
    @Authorization("AtLeast21", Policy.add_requirements(AtLeast21, AtLeast21()))
    async def at_least_21_case_2(self):
        return "Only for Age of 21 or more"
