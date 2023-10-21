# **Input Validation Tutorial**

In this section, we are going to learn how inputs are parsed in the Ellar route handle functions.

To get started, we need to create another module for this tutorial.

Open the terminal, navigate to the root level of the project and run the command that scaffolds a new module to your project.

```shell
$(venv) ellar create-module items
```

Next, goto `project_name/root_module.py` and add `ItemsModule` to list of modules.

```python
from ellar.common import Module, exception_handler, IExecutionContext, JSONResponse, Response
from ellar.core import ModuleBase
from ellar.samples.modules import HomeModule
from .apps.car.module import CarModule
from .apps.items.module import ItemsModule


@Module(modules=[HomeModule, CarModule, ItemsModule])
class ApplicationModule(ModuleBase):
    @exception_handler(404)
    def exception_404_handler(cls, ctx: IExecutionContext, exc: Exception) -> Response:
        return JSONResponse(dict(detail="Resource not found."))

```

With the server running:
```shell
$(venv) ellar runserver --reload
```

visit [http://localhost:8000/items/](http://localhost:8000/items/),

```json
{
  "detail": "Welcome Items Resource"
}
```

All code example will be done on the `ItemController` in `project_name/apps/items/controllers.py`. 
Please keep it open.

## **Tutorial**
You are going to learn how to use the following route handler parameter:

- [Path](path-params.md)
- [Query](query-params.md)
- [Header](header-params.md)
- [Cookie](cookie-params.md)
- [Body](body.md)
- [Form](form-params.md)
- [File](file-params.md)
