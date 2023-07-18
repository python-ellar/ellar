import base64
import pickle
import typing as t

from ellar.auth.handlers import HeaderAPIKeyAuthenticationHandler
from ellar.auth.identity import UserIdentity
from ellar.common import AnonymousIdentity, Identity, IHostContext
from ellar.di import injectable


@injectable
class SimpleHeaderAuthHandler(HeaderAPIKeyAuthenticationHandler):
    async def authentication_handler(
        self, context: IHostContext, key: str
    ) -> t.Optional[Identity]:
        data = pickle.loads(base64.b64decode(key))
        if isinstance(data, dict):
            return UserIdentity(auth_type="token", **data)
        return AnonymousIdentity()
