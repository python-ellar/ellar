# **Session**
A web session acts as a transient interaction between a user and a web application, usually initiated upon visiting a website. 
It enables the storage of user-specific data across multiple requests, facilitating personalized experiences, authentication, 
and state management within the application.

In Ellar, session management is overseen by the `SessionMiddleware`, which delegates the serialization and 
deserialization of sessions to any registered `SessionStrategy` service within the Dependency Injection (DI) container. 
Sessions can be accessed and modified using the `request.session` dictionary interface.

## **Accessing Session**
Session objects are accessible via `request.session` or by injecting `Session` into route parameters.

For example:
=== "Request Object"
    ```python
    from ellar.common import Controller, ControllerBase, get
    
    @Controller
    class SampleController(ControllerBase):
        @get()
        def index(self):
            session = self.context.switch_to_http_connection().get_request().session
            assert isinstance(session, dict)
            return {'index': 'okay'}
    ```

=== "Route Parameter Injection"
    ```python
    from ellar.common import Controller, ControllerBase, get, Inject
    
    @Controller
    class SampleController(ControllerBase):
        @get()
        def index(self, session: Inject[str, Inject.Key('Session')]):
            assert isinstance(session, dict)
            return {'index': 'okay'}
    ```

## **SessionClientStrategy**
The `SessionClientStrategy` serves as the default implementation for `SessionStrategy`, 
leveraging the `itsdangerous` package for hashing session data. It serializes session data and saves it on the client side. 
However, large session data may cause issues for some requests.

To utilize `SessionClientStrategy`, ensure the `itsdangerous` package is installed:

```shell
pip install itsdangerous
```

Activate `SessionClientStrategy` by registering it with the DI container, as demonstrated below:

```python
from ellar.common import IHostContext, JSONResponse, Module, Response, exception_handler
from ellar.core import ModuleBase
from ellar.samples.modules import HomeModule

from ellar.auth.session.strategy import SessionClientStrategy
from ellar.auth.session import SessionStrategy
from ellar.di import ProviderConfig

from .car.module import CarModule


@Module(
    modules=[HomeModule, CarModule],
    providers=[ProviderConfig(SessionStrategy, use_class=SessionClientStrategy)]
)
class ApplicationModule(ModuleBase):
    @exception_handler(404)
    def exception_404_handler(cls, context: IHostContext, exc: Exception) -> Response:
        return JSONResponse({"detail": "Resource not found."}, status_code=404)
```
By registering `ISessionStrategy` as `SessionClientStrategy` with `ProviderConfig(ISessionStrategy, use_class=SessionClientStrategy)`, `SessionMiddleware` utilizes `SessionClientStrategy` for session management.

## **SessionStrategy Configuration Options**
- **SESSION_COOKIE_NAME**: Defaults to "session".
- **SESSION_COOKIE_PATH**: Sets the path for the session cookie. If not set, the cookie is valid for all of `APPLICATION_ROOT` or '/' if not specified.
- **SESSION_COOKIE_SECURE**: Controls whether the cookie is set with the secure flag, which restricts it to HTTPS requests. Default: `False`.
- **SESSION_COOKIE_MAX_AGE**: Sets the session expiry time in seconds, defaulting to 2 weeks. If set to `None`, the cookie lasts until the browser session ends.
- **SESSION_COOKIE_SAME_SITE**: Specifies the SameSite flag to prevent sending the session cookie along with cross-site requests. Defaults to 'lax'.
- **SESSION_COOKIE_HTTPONLY**: Indicates whether the HttpOnly flag should be set, restricting cookie access to HTTP requests only. Defaults to `False`.
- **SESSION_COOKIE_DOMAIN**: Specifies the domain of the cookie, facilitating sharing between subdomains or cross-domains. The browser defaults the domain to the same host that set the cookie, excluding subdomain references.

## **Custom SessionStrategy**

In this section, we'll walk through creating another session strategy that saves session data 
to a relational database using the `EllarSQL` package.

To begin, you'll need to install the `EllarSQL` package:

```shell
pip install ellar-sql
```

Next, create a Python file named `session.py` in your project's root directory and paste the following code:

```python title="project_name/session.py"
import pickle
import secrets
import typing as t
from ellar_sql import model, first_or_none
from datetime import datetime, timedelta

from ellar.auth.session import SessionStrategy, SessionCookieObject, SessionCookieOption
from ellar.threading import run_as_sync

from itsdangerous import want_bytes


class SessionTable(model.Model):
    id = model.Column(model.Integer, primary_key=True)
    session_id = model.Column(model.String(255), unique=True)
    data = model.Column(model.LargeBinary)
    expiry = model.Column(model.DateTime)

    def __init__(self, session_id, data, expiry):
        super().__init__()

        self.session_id = session_id
        self.data = data
        self.expiry = expiry

    def __repr__(self):
        return "<Session data %s>" % self.data


class EllarSQLSessionStrategy(SessionStrategy):
    """Uses the EllarSQL for a session backend."""

    serializer = pickle

    def __init__(
            self,
            key_prefix: str,
            name: str = "ellar-sql"
    ):
        self.key_prefix = key_prefix
        self._session_option = SessionCookieOption(NAME=name)

    @property
    def session_cookie_options(self) -> SessionCookieOption:
        return self._session_option

    def serialize_session(
            self,
            session: t.Union[str, SessionCookieObject],
    ) -> str:
        return self._save_session_data(session)

    def deserialize_session(self, session_data: t.Optional[str]) -> SessionCookieObject:
        return self._fetch_record(session_data)

    async def _try_coroutine(self, func: t.Optional[t.Coroutine]) -> None:
        if isinstance(func, t.Coroutine):
            await func

    @run_as_sync
    async def _fetch_record(self, key: str) -> SessionCookieObject:
        """Get the saved session (record) from the database"""
        key  = key or secrets.token_urlsafe(5)
        store_id = self.key_prefix + key
        record: t.Optional[SessionTable] = await first_or_none(
            model.select(SessionTable).filter_by(session_id=store_id))

        # If the expiration time is less than or equal to the current time (expired), delete the document
        if record is not None:
            expiration_datetime = record.expiry
            if expiration_datetime is None or expiration_datetime <= datetime.utcnow():
                session = SessionTable.get_db_session()
                await self._try_coroutine(session.delete(record))
                await self._try_coroutine(session.commit())

                record = None

        # If the saved session still exists after checking for expiration, load the session data from the document
        if record:
            try:
                session_data = self.serializer.loads(want_bytes(record.data))
                return SessionCookieObject(session_data, sid=key)
            except pickle.UnpicklingError:
                return SessionCookieObject(sid=key)

        return SessionCookieObject(sid=key)

    @run_as_sync
    async def _save_session_data(self, session: t.Union[str, SessionCookieObject], ) -> str:
        """Generate a prefixed session id"""
        prefixed_session_id = self.key_prefix + session.sid

        # If the session is empty, do not save it to the database or set a cookie
        if not session:
            # If the session was deleted (empty and modified), delete the saved session  from the database and tell the client to delete the cookie
            if session.modified:
                record = await first_or_none(model.select(SessionTable).filter_by(session_id=prefixed_session_id))
                session = SessionTable.get_db_session()

                await self._try_coroutine(session.delete(record))
                await self._try_coroutine(session.commit())

            return self.get_cookie_header_value(session, delete=True)

        # Serialize session data
        serialized_session_data = self.serializer.dumps(dict(session))

        # Get the new expiration time for the session
        expiration_datetime = datetime.utcnow() + timedelta(days=14)

        # Update existing or create new session in the database
        record = await first_or_none(model.select(SessionTable).filter_by(session_id=prefixed_session_id))
        db_session = SessionTable.get_db_session()

        if record:
            record.data = serialized_session_data
            record.expiry = expiration_datetime
        else:
            db_session = SessionTable.get_db_session()
            record = SessionTable(
                session_id=prefixed_session_id,
                data=serialized_session_data,
                expiry=expiration_datetime,
            )
            db_session.add(record)
        await self._try_coroutine(db_session.commit())

        return self.get_cookie_header_value(session.sid)
```

In the code above, session data is serialized to bytes using the Python `pickle` package, and other processes are standard SQLAlchemy actions.

Next, register the `EllarSQLSessionStrategy` as the `SessionStrategy`:

```python
from ellar.common import IHostContext, JSONResponse, Module, Response, exception_handler, IApplicationStartup
from ellar.core import ModuleBase
from ellar.samples.modules import HomeModule
from ellar.auth.session import SessionStrategy
from ellar.di import ProviderConfig
from ellar_sql import EllarSQLService

from .car.module import CarModule
from .session import EllarSQLSessionStrategy


@Module(
    modules=[HomeModule, CarModule],
    providers=[ProviderConfig(SessionStrategy, use_class=EllarSQLSessionStrategy)]
)
class ApplicationModule(ModuleBase, IApplicationStartup):
    async def on_startup(self, app: "App") -> None:
        ellar_sql_service = app.injector.get(EllarSQLService)
        ellar_sql_service.create_all()
    
    @exception_handler(404)
    def exception_404_handler(cls, context: IHostContext, exc: Exception) -> Response:
        return JSONResponse({"detail": "Resource not found."}, status_code=404)
```

In the above code, the `on_startup` method from `IApplicationStartup` ensures that the `SessionTable` is created.

Once this setup is complete, restart the local server to observe session table data in your relational database.

## **Disable Session**
To disable sessions in your Ellar application, set `SESSION_DISABLED=True` in your application configuration. 
This configuration change will effectively turn off session functionality throughout your Ellar application.
