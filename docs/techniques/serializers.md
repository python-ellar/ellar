# **Serializers**
The `Serializer` class in the Ellar, is a custom class based on `pydantic` models, which provides additional functionality specific to Ellar's requirements.

To use `Serializer` in Ellar, you simply need to create a class that inherits from `Serializer` and define your data model using pydantic fields. 
Here's an example of how you could define a serializer class for a user model:

```python
from ellar.common import Serializer

class UserSerializer(Serializer):
    name: str
    email: str
    age: int

```

With this setup, you can use the `UserSerializer` class to validate incoming data and or serialize outgoing response data, 
ensuring that it matches the expected format before saving it to the database or returning it to the client.

## **Handling Responses**

Let's see how we can use **Serializer** as a responses schema which will help us validate out data output and also provide documentation on route function response.

The response schema is defined on the HTTP method decorator.

For example:
```python
# project_name/apps/items/controllers.py

from ellar.common import Controller, get, Serializer, ControllerBase

# Define a User class with username, email, first_name, and last_name attributes
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

# Define a Serializer class to validate response data
class UserSchema(Serializer):
    username: str
    email: str = None
    first_name: str = None
    last_name: str = None

# Create a fake user object
current_user = User(username='ellar', email='ellar@example.com', first_name='ellar', last_name='asgi')    

# Define an endpoint that returns the fake user's information
@Controller
class ItemsController(ControllerBase):
    @get("/me", response=UserSchema)
    def me(self):
        return current_user

```
This code sets up a User model and a `UserSerializer` class based on the `Serializer` class. 
The User model represents a user with a `username`, `email`, `first_name`, and `last_name`. 
The `UserSerializer` class is used to define the expected format of the response data in the `/me` endpoint.

When the `/me` endpoint is called, it returns the `current_user` object as the response. 
The `UserSerializer` is then used to parse and validate the `current_user` object, converting it into a dictionary representation 
that can be easily serialized to JSON. 
The resulting dictionary is then passed to the [`JSONResponseModel`](response-model.md#jsonresponsemodel) for serialization to a 
JSON string and sending the response to the client.

## **Using Dataclass as Response Schema**
We can utilize the `dataclasses` feature as a response schema by utilizing the `DataclassSerializer` a base class. 

For instance, we can convert the `UserSchema` to a dataclass by defining `UserDataclass` as follows:

```python
from dataclasses import dataclass
from ellar.common import DataclassSerializer


@dataclass
class UserDataclass(DataclassSerializer):
    username: str
    email: str = None
    first_name: str = None
    last_name: str = None

```

By replacing the `UserSchema` with `UserDataclass`, we can expect the same outcomes in the returned response, response validation, and documentation.

### **Multiple Response Types**

The `response` parameter takes different shape. Let's see how to return a different response if the user is not authenticated.

```python
# project_name/apps/items/controllers.py

from ellar.common import Controller, get, ControllerBase, Serializer

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



## **Using Response Type/Object As Response**

You can use `Response` type to change the format of data returned from endpoint functions.

```python
# project_name/apps/items/controllers.py

from ellar.common import Controller, get, ControllerBase, PlainTextResponse


@Controller
class ItemsController(ControllerBase):
    @get("/me", response=PlainTextResponse)
    def me(self):
        return "some text response."

```

Also, we can return response object from endpoint functions, and it will override initial `response` declared before.

```python
# project_name/apps/items/controllers.py

from ellar.common import Controller, get, Serializer, ControllerBase, PlainTextResponse

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
