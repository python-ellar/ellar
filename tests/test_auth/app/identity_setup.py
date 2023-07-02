from ellar.auth import BaseIdentityProvider
from ellar.di import injectable

from .auth import SimpleHeaderAuthHandler


@injectable
class IdentityProvider(BaseIdentityProvider):
    def configure(self) -> None:
        self.add_authentication(SimpleHeaderAuthHandler)
