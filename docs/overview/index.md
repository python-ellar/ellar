
You will learn the core fundamentals of Ellar with this set of articles. We are going to build a basic CRUD application
with features that cover a lot of ground at an introductory level.


## Library Dependencies
Ellar core depends on:

- `python >= 3.7`
- `Starlette`
- `Injector`


## Quick Step
Using the Ellar CLI, you can easily set up a new project by running the following commands in your OS terminal:
```shell
$(venv) pip install ellar[standard]
$(venv) ellar new project-name
```

The `new` command will create a `project-name` project directory with other necessary files needed for the Ellar CLI tool to properly manage your project.
Also, some boilerplate files are populated and installed in a new `project_name` to get structure to your project.

```shell
project-name/
├─ project_name/
│  ├─ apps/
│  │  ├─ __init__.py
│  ├─ core/
│  ├─ domain/
│  ├─ config.py
│  ├─ root_module.py
│  ├─ server.py
│  ├─ __init__.py
├─ tests/
│  ├─ __init__.py
├─ pyproject.toml
├─ README.md
```

A brief overview of generated core files:

|                            |                                                                                                                |
|----------------------------|----------------------------------------------------------------------------------------------------------------|
| `pyproject.toml`           | Python project metadata store.                                                                                 |
| `README.md`                | Project Description and documentation.                                                                         |
| `project_name.apps`        | Root path to all project modules.                                                                              |
| `project_name.core`        | Core/business logic folder.                                                                                    |
| `project_name.domain`      | Domain logic folder.                                                                                           |
| `project_name.config`      | Application configuration file                                                                                 |
| `project_name.root_module` | The root module of the application                                                                             |
| `project_name.server`      | The entry file of the application which uses the core function `AppFactory` to create an application instance. |

In `project_name.server`, we create the `application` instance using the `AppFactory.create_from_app_module` function.
```python
# project_name/server.py
import os

from ellar.constants import ELLAR_CONFIG_MODULE
from ellar.core.factory import AppFactory
from .root_module import ApplicationModule

application = AppFactory.create_from_app_module(
    ApplicationModule,
    config_module=os.environ.get(
        ELLAR_CONFIG_MODULE, "project_name.config:DevelopmentConfig"
    ),
)
```

There are two ways to create an Ellar application using the `AppFactory`, `create_from_app_module` and `create_app`.
Both provides all necessary parameter for creating Ellar application

## Run your project
Ellar runs [UVICORN - ASGI Server](https://www.uvicorn.org/) under the hood.

```shell
$(venv) cd project-name
$(venv) ellar runserver --reload
```
`--reload` is to watch for file changes

```shell
INFO:     Will watch for changes in these directories: ['/home/user/working-directory']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [2934815] using WatchFiles
INFO:     APP SETTINGS MODULE: project_name.config:DevelopmentConfig
INFO:     Started server process [2934818]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

Now go to [http://127.0.0.1:8000](http://127.0.0.1:8000)
![Swagger UI](../img/ellar_framework.png)

For more info on Ellar CLI, click [here](https://github.com/eadwinCode/ellar-cli)

To run the application with a different configuration,
In `project_name/config`, Add a `ProductionConfig`

```python
...

class ProductionConfig(BaseConfig):
    DEBUG: bool = False
```
Next, export `ProductionConfig` string import to the environment with `ELLAR_CONFIG_MODULE` as key.

```shell
$(venv) export ELLAR_CONFIG_MODULE='project_name.config:ProductionConfig'
$(venv) ellar runserver
```

That will start up the application using `ProductionConfig`
```shell
INFO:     APP SETTINGS MODULE: project_name.config:ProductionConfig
INFO:     Started server process [2934818]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

One last thing, before we move to the next page, we need to create an app `module`.

Lets add a `Dogs` module/app to our project:
```shell
$(venv) ellar create-module dogs
```
The result of this CLI command is stored in `project-name/project_name/apps`
```
apps/
├─ dogs/
│  ├─ tests/
│  │  ├─ test_controllers.py
│  │  ├─ test_routers.py
│  │  ├─ test_services.py
│  ├─ controllers.py
│  ├─ module.py
│  ├─ schemas.py
│  ├─ services.py
│  ├─ __init__.py
```
Brief overview of the generated files:

|                    |                                                   |
|--------------------|---------------------------------------------------|
| `dogs.controllers` | A basic controller with an `index` route.         |
| `dogs.module.py`   | dogs module/app `Module` metadata definition.     |
| `dogs.services.py` | For Dogs module service declarations.             |
| `dogs.schemas.py`  | Data-transfer-object or Serializers declarations. |
| `dogs.tests/`      | testing directory for the dogs module.            |

To finish up with the created `dogs` module, we need to register it to the 
`project_name.root_module.py`

```python
# project_name/root_module.py
...
from .apps.dogs.module import DogsModule


@Module(modules=[HomeModule, DogsModule])
class ApplicationModule(ModuleBase):
    @exception_handler(404)
    def exception_404_handler(cls, request: Request, exc: Exception) -> Response:
        return JSONResponse(dict(detail="Resource not found."))
```
That's it.

Goto your browser and visit: [http://localhost:8000/dogs/](http://localhost:8000/dogs/)
```json
{
  "detail": "Welcome Dogs Resource"
}
```

## Enabling OpenAPI Docs
To set up OPENAPI documentation, we need to go back to the project folder. In the `server.py`
then add the below.
```python
# project_name/server.py

import os
from ellar.constants import ELLAR_CONFIG_MODULE
from ellar.core.factory import AppFactory
from ellar.openapi import OpenAPIDocumentModule, OpenAPIDocumentBuilder
from .root_module import ApplicationModule

application = AppFactory.create_from_app_module(
    ApplicationModule,
    config_module=os.environ.get(
        ELLAR_CONFIG_MODULE, "project_name.config:DevelopmentConfig"
    ),
)

document_builder = OpenAPIDocumentBuilder()
document_builder.set_title('Project Name API') \
    .set_version('1.0.0') \
    .set_contact(name='Eadwin', url='https://www.yahoo.com', email='eadwin@gmail.com') \
    .set_license('MIT Licence', url='https://www.google.com')

document = document_builder.build_document(application)
module = application.install_module(OpenAPIDocumentModule, document=document)
module.setup_swagger_doc()
```

Goto your browser and visit: [http://localhost:8000/docs/](http://localhost:8000/docs)
