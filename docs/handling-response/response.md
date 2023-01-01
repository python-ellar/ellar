# Handling Responses

## Define a response Schema

**Ellar** allows you to define the schema of your responses both for validation and documentation purposes.

The response schema is defined on the HTTP method decorator and its applied 
to OPENAPI documentation and validation of the data returned from route handler function.

We'll create a third operation that will return information about a Fake user.

```python
# project_name/apps/items/controllers.py

from ellar.serializer import Serializer
from ellar.common import Controller, get
from ellar.core import ControllerBase

class User:
    def __init__(self, username: str, email:str=None, first_name:str=None, last_name:str=None) -> None:
        self.username = username
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.is_authenticated = False
    
    @property
    def full_name(self) -> str:
        assert self.first_name and self.last_name
        return f'{self.first_name} {self.last_name}'


class UserSchema(Serializer):
    username: str
    email: str = None
    first_name: str = None
    last_name: str = None


current_user = User(username='ellar', email='ellar@example.com', first_name='ellar', last_name='asgi')    


@Controller
class ItemsController(ControllerBase):
    @get("/me", response=UserSchema)
    def me(self):
        return current_user
```

This will convert the `User` object into a dictionary of only the defined fields.

### Multiple Response Types

The `response` parameter takes different shape. Let's see how to return a different response if the user is not authenticated.

```python
# project_name/apps/items/controllers.py

from ellar.serializer import Serializer
from ellar.common import Controller, get
from ellar.core import ControllerBase

class User:
    def __init__(self, username: str, email:str=None, first_name:str=None, last_name:str=None) -> None:
        self.username = username
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.is_authenticated = False
    
    @property
    def full_name(self) -> str:
        assert self.first_name and self.last_name
        return f'{self.first_name} {self.last_name}'


class UserSchema(Serializer):
    username: str
    email: str = None
    first_name: str = None
    last_name: str = None

    
class MessageSchema(Serializer):
    message: str

    
current_user = User(username='ellar', email='ellar@example.com', first_name='ellar', last_name='asgi')    


@Controller
class ItemsController(ControllerBase):
    @get("/me", response={200: UserSchema, 403: MessageSchema})
    def me(self):
        if not current_user.is_authenticated:
            return 403, {"message": "Please sign in first"}
        return current_user
    
    @get("/login", response=MessageSchema)
    def login(self):
        if current_user.is_authenticated:
            return dict(message=f'{current_user.full_name} already logged in.') 
        
        current_user.is_authenticated = True
        return MessageSchema(
            message=f'{current_user.full_name} logged in successfully.'
        ) 
        # the same as returning dict(message=f'{current_user.full_name} logged in successfully.')
```

Here, the `response` parameter takes a KeyValuePair of the `status` and response `Schema`.

!!! info
    Note that we returned a tuple of status code and response data (`403, {"message": "Please sign in first"}`) to specify the response validation to use.


## Using Response Type/Object As Response

You can use `Response` type to change the format of data returned from endpoint functions.

```python
# project_name/apps/items/controllers.py

from ellar.common import Controller, get
from ellar.core import ControllerBase
from starlette.responses import PlainTextResponse


@Controller
class ItemsController(ControllerBase):
    @get("/me", response=PlainTextResponse)
    def me(self):
        return "some text response."

```

Also, we can return response object from endpoint functions, and it will override initial `response` declared before.

```python
# project_name/apps/items/controllers.py

from ellar.serializer import Serializer
from ellar.common import Controller, get
from ellar.core import ControllerBase
from starlette.responses import PlainTextResponse

class UserSchema(Serializer):
    username: str
    email: str = None
    first_name: str = None
    last_name: str = None


@Controller
class ItemsController(ControllerBase):
    @get("/me", response=UserSchema)
    def me(self):
        return PlainTextResponse("some text response.", status_code=200)
```
