# Cookie Parameters

You can define Cookie parameters the same way you define `Path` parameters.

## Import `Cookie`

First import `Cookie` from `ellar.common` module

## Declare `Cookie` parameters

Then declare the cookie parameters using the same structure as with `Path` and `Query`.

The first value is the default value, you can pass all the extra validation or annotation parameters:

```python
# project_name/apps/items/controllers.py

from typing import Optional
from ellar.common import get, Controller, Cookie
from ellar.core import ControllerBase


@Controller
class ItemsController(ControllerBase):
    @get("/")
    async def read_items(self, ads_id: Optional[str] = Cookie(default=None)):
        return {"ads_id": ads_id}
```

!!! info
    To declare cookies, you need to use `Cookie`, because otherwise the parameters would be interpreted as `query` parameters.

### Using Schema

You can also use Schema to encapsulate `Cookies` parameters:

```python
# project_name/apps/items/controllers.py

from ellar.serializer import Serializer
from ellar.common import get, Controller, Cookie
from ellar.core import ControllerBase



class CookieSchema(Serializer):
    cookieItem1: int = 100
    cookieItem2: str = None


@Controller
class ItemsController(ControllerBase):
    @get('/cookie-as-schema')
    def cookie_as_schema(self, cookie_values: CookieSchema = Cookie()):
        return {"cookie_values": cookie_values.dict()}
```
