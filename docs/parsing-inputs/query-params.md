# Query parameters

When you declare other function parameters that are not part of the path parameters, they are automatically interpreted as "query" parameters.

```python
# project_name/apps/items/controllers.py

from ellar.common import get, Controller
from ellar.core import ControllerBase

fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]


@Controller
class ItemsController(ControllerBase):
    @get('/weapons')
    def list_weapons(self, limit: int = 10, offset: int = 0):
        return fake_items_db[offset: offset + limit]
```

To query this operation, you use a URL like:

```
http://localhost:8000/api/weapons?offset=0&limit=10
```
By default, all GET parameters are strings, and when you annotate your function arguments with types, they are converted to that type and validated against it.

The same benefits that apply to path parameters also apply to query parameters:

- Editor support (obviously)
- Data "parsing"
- Data validation
- Automatic documentation


Note: if you do not annotate your arguments, they will be treated as `str` types:

```python
# project_name/apps/items/controllers.py

from ellar.common import get, Controller
from ellar.core import ControllerBase

fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]


@Controller
class ItemsController(ControllerBase):
    @get('/weapons')
    def list_weapons(self, limit, offset):
        assert type(limit) == str
        assert type(offset) == str
        return fake_items_db[offset: int(offset) + int(limit)]
```

### Defaults

As query parameters are not a fixed part of a path, they are optional and can have default values:

```python
# project_name/apps/items/controllers.py

from ellar.common import get, Controller
from ellar.core import ControllerBase

fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]


@Controller
class ItemsController(ControllerBase):
    @get('/weapons')
    def list_weapons(self, limit: int = 10, offset: int = 0):
        return fake_items_db[offset: offset + limit]
```

In the example above we set default values of `offset=0` and `limit=10`.

So, going to the URL:
```
http://localhost:8000/items/weapons
```
would be the same as going to:
```
http://localhost:8000/items/weapons?offset=0&limit=10
```
If you go to, for example:
```
http://localhost:8000/items/weapons?offset=20
```

the parameter values in your function will be:

 - `offset=20`  (because you set it in the URL)
 - `limit=10`  (because that was the default value)


### Required and optional parameters

You can declare required or optional GET parameters in the same way as declaring Python function arguments:

```python
# project_name/apps/items/controllers.py

from ellar.common import get, Controller
from ellar.core import ControllerBase

weapons = ["Ninjato", "Shuriken", "Katana", "Kama", "Kunai", "Naginata", "Yari"]


@Controller
class ItemsController(ControllerBase):
    @get("/weapons/search")
    def search_weapons(self, q: str, offset: int = 0):
        results = [w for w in weapons if q in w.lower()]
        print(q, results)
        return results[offset: offset + 10]
```

In this case, **Ellar** will always validate that you pass the `q` param in the GET, and the `offset` param is an optional integer.

### GET parameters type conversion

Let's declare multiple type arguments:
```python
# project_name/apps/items/controllers.py

from ellar.common import get, Controller
from ellar.core import ControllerBase
from datetime import date


@Controller
class ItemsController(ControllerBase):
    @get("/example")
    def example(self, s: str = None, b: bool = None, d: date = None, i: int = None):
        return [s, b, d, i]
```
The `str` type is passed as is.

For the `bool` type, all the following:
```
http://localhost:8000/items/example?b=1
http://localhost:8000/items/example?b=True
http://localhost:8000/items/example?b=true
http://localhost:8000/items/example?b=on
http://localhost:8000/items/example?b=yes
```
or any other case variation (uppercase, first letter in uppercase, etc.), your function will see
the parameter `b` with a `bool` value of `True`, otherwise as `False`.

Date can be both date string and integer (unix timestamp):
```
http://localhost:8000/items/example?d=1672286800
# same as 2022-12-29

http://localhost:8000/items/example?d=2022-12-29
```

### Using Schema

You can also use Schema to encapsulate GET parameters:

```python
# project_name/apps/items/controllers.py

from typing import List
from pydantic import Field
from ellar.serializer import Serializer
from ellar.common import get, Controller, Query
from ellar.core import ControllerBase



class Filters(Serializer):
    limit: int = 100
    offset: int = None
    query: str = None
    category__in: List[str] = Field(None, alias="categories")


@Controller
class ItemsController(ControllerBase):
    @get('/query-as-schema')
    def query_as_schema(self, filters: Filters = Query()):
        return {"filters": filters.dict()}
```

![Query Doc](../img/query_filter_swagger.png)
