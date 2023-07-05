from ellar.auth import BaseIdentitySchemeProvider
from ellar.di import injectable

from .auth import SimpleHeaderAuthHandler


@injectable
class IdentitySchemeProvider(BaseIdentitySchemeProvider):
    def configure(self) -> None:
        self.add_authentication(SimpleHeaderAuthHandler)
