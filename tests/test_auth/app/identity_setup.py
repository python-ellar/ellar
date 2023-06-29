from ellar.auth import BaseIdentityProvider, Policy
from ellar.di import injectable

from .auth import SimpleHeaderAuthHandler
from .requirement import AtLeast21


@injectable
class IdentityProvider(BaseIdentityProvider):
    async def configure(self) -> None:
        self.add_authentication(SimpleHeaderAuthHandler)

        self.add_authorization("AtLeast21", policy=Policy.add_requirements(AtLeast21))
        self.add_authorization("Administrator", Policy.required_role("admin"))

        self.add_authorization("Staff", Policy.required_role("staff"))

        self.add_authorization(
            "CanCreateAndPublishArticle",
            policy=Policy.required_claim("article", "create", "publish"),
        )
