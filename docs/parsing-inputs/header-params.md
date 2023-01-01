# Header Parameters

You can define Header parameters the same way you define `Query`, `Path` and `Cookie` parameters.

To query this operation, you use a URL like:

## Import `Header`

First import `Header` from `ellar.common` module

## Declare `Header` parameters

Then declare the header parameters using the same structure as with `Path`, `Query` and `Cookie`.

The first value is the default value, you can pass all the extra validation or annotation parameters:

```python
# project_name/apps/items/controllers.py

from ellar.common import Controller, get, Header
from ellar.core import ControllerBase
from typing import Optional


@Controller
class ItemsController(ControllerBase):
    @get("/")
    async def read_items(self, user_agent: Optional[str] = Header(default=None)):
        return {"User-Agent": user_agent}
```

!!! info
    To declare headers, you need to use `Header`, because otherwise the parameters would be interpreted as query parameters.

## Automatic conversion

`Header` has a little extra functionality.

Most of the standard headers are separated by a "hyphen" character, also known as the "minus symbol" (`-`).

But a variable like `user-agent` is not valid in Python.

By default, `Header` will convert the parameter names characters from underscore (`_`) to hyphen (`-`) to extract and document the headers.

Also, HTTP headers are case-insensitive, so, you can declare them with standard Python style (also known as "snake_case").

So, you can use `user_agent` as you normally would in Python code, instead of needing to capitalize the first letters as `User_Agent` or something similar.

If for some reason you need to disable automatic conversion of underscores to hyphens, set the parameter `convert_underscores` of `Header` to `False`:

```python
# project_name/apps/items/controllers.py

from ellar.common import Controller, get, Header
from ellar.core import ControllerBase
from typing import Optional


@Controller
class ItemsController(ControllerBase):
    @get("/")
    async def read_items(
        self, strange_header: Optional[str] = Header(default=None, convert_underscores=False)
    ):
        return {"strange_header": strange_header}
```

!!! warning
    Before setting `convert_underscores` to `False`, bear in mind that some HTTP proxies and servers disallow the usage of headers with underscores.


## Duplicate headers

It is possible to receive duplicate headers. That means, the same header with multiple values.

You can define those cases using a list in the type declaration.

You will receive all the values from the duplicate header as a Python `list`.

For example, to declare a header of `X-Token` that can appear more than once, you can write:

```python
# project_name/apps/items/controllers.py

from ellar.common import Controller, get, Header
from ellar.core import ControllerBase
from typing import Optional, List


@Controller
class ItemsController(ControllerBase):
    @get("/")
    async def read_items(self, x_token: Optional[List[str]] = Header(default=None)):
        return {"X-Token values": x_token}
```

If you communicate with that *path operation* sending two HTTP headers like:

```
X-Token: foo
X-Token: bar
```

The response would be like:

```JSON
{
    "X-Token values": [
        "bar",
        "foo"
    ]
}
```

### Using Schema

You can also use Schema to encapsulate `Header` parameters:

```python
# project_name/apps/items/controllers.py

from typing import List
from ellar.serializer import Serializer
from ellar.common import get, Controller, Header
from ellar.core import ControllerBase



class HeaderSchema(Serializer):
    version: int = 1
    x_token: List[str] = None # similar to x_token: Optional[List[str]]


@Controller
class ItemsController(ControllerBase):
    @get('/header-as-schema')
    def header_as_schema(self, headers: HeaderSchema = Header()):
        return {"headers": headers.dict()}
```
