<p align="center">
  <a href="#" target="blank"><img src="https://python-ellar.github.io/ellar/img/EllarLogoB.png" width="200" alt="Ellar Logo" /></a>
</p>
<p align="end">logo by: <a target="_blank" href="https://www.behance.net/azadvertised">Azad</a></p>

<p align="center"> Ellar - Python ASGI web framework for building fast, efficient, and scalable RESTful APIs and server-side applications. </p>

![Test](https://github.com/python-ellar/ellar/actions/workflows/test_full.yml/badge.svg)
![Coverage](https://img.shields.io/codecov/c/github/python-ellar/ellar)
[![PyPI version](https://badge.fury.io/py/ellar.svg)](https://badge.fury.io/py/ellar)
[![PyPI version](https://img.shields.io/pypi/v/ellar.svg)](https://pypi.python.org/pypi/ellar)
[![PyPI version](https://img.shields.io/pypi/pyversions/ellar.svg)](https://pypi.python.org/pypi/ellar)

## Project Status
Beta version
- Documentation - 97% complete
- Authorization Documentation - (in progress)


## **Introduction**

Ellar is a lightweight ASGI framework for building efficient and scalable server-side python applications.
It supports both OOP (Object-Oriented Programming) and FP (Functional Programming)

Ellar is based on [Starlette (ASGI toolkit)](https://www.starlette.io/), a lightweight ASGI framework/toolkit well-suited for developing asynchronous web services with Python. 

## **Features Summary**

- **Easy to Use**: Ellar has a simple and intuitive API that makes it easy to get started with building a fast and scalable web applications or web APIs in Python.
- **Dependency Injection (DI)**: It comes with DI system makes it easy to manage dependencies and reduce coupling between components.
- **Pydantic Integration**: It is properly integrated with Pydantic, a popular Python library for data validation, to ensure that input data is valid.
- **Templating with Jinja2**: Ellar provides built-in support for Jinja2 templates, making it easy to create dynamic web pages.
- **OpenAPI Documentation**: It comes with built-in support for OpenAPI documentation, making it easy to generate `Swagger` or `ReDoc` documentation for your API. And more can be added with ease if necessary.
- **Controller (MVC) Architecture**: Ellar's controller architecture follows the Model-View-Controller (MVC) pattern, making it easy to organize your code.
- **Guards for Authentication and Authorization**: It provides built-in support for guards, allowing you to easily implement authentication and authorization in your application.
- **Modularity**: Ellar follows a modular architecture inspired by NestJS, making it easy to organize your code into reusable modules.
- **Asynchronous programming**: It allows you to takes advantage of Python's `async/await` feature to write efficient and fast code that can handle large numbers of concurrent requests

## **Dependencies**
- Python >= 3.7
- Starlette
- Injector
- Pydantic

## **Installation**
```shell
$(venv) pip install ellar
```

## **Try This**
```python
import uvicorn
from ellar.common import Body, Controller, ControllerBase, delete, get, post, put, Serializer, Inject
from ellar.app import AppFactory
from ellar.di import injectable, request_scope
from ellar.openapi import OpenAPIDocumentModule, OpenAPIDocumentBuilder, SwaggerUI
from pydantic import Field
from pathlib import Path


class CreateCarSerializer(Serializer):
    name: str
    year: int = Field(..., gt=0)
    model: str


@injectable(scope=request_scope)
class CarService:
    def __init__(self):
        self.detail = 'a service'


@Controller
class MotoController(ControllerBase):
    def __init__(self, service: CarService):
        self._service = service
    
    @post()
    async def create(self, payload:  Body[CreateCarSerializer]):
        assert self._service.detail == 'a service'
        result = payload.dict()
        result.update(message='This action adds a new car')
        return result

    @put('/{car_id:str}')
    async def update(self, car_id: str, payload: Body[CreateCarSerializer]):
        result = payload.dict()
        result.update(message=f'This action updated #{car_id} car resource')
        return result

    @get('/{car_id:str}')
    async def get_one(self, car_id: str, service: Inject[CarService]):
        assert self._service == service
        return f"This action returns a #{car_id} car"

    @delete('/{car_id:str}')
    async def delete(self, car_id: str):
        return f"This action removes a #{car_id} car"


app = AppFactory.create_app(
    controllers=[MotoController],
    providers=[CarService],
    base_directory=str(Path(__file__).parent),
    config_module=dict(REDIRECT_SLASHES=True),
    template_folder='templates'
)
document_builder = OpenAPIDocumentBuilder()
document_builder.set_title('Ellar API') \
    .set_version('1.0.2') \
    .set_contact(name='Author', url='https://www.yahoo.com', email='author@gmail.com') \
    .set_license('MIT Licence', url='https://www.google.com')

document = document_builder.build_document(app)
module = OpenAPIDocumentModule.setup(
    docs_ui=SwaggerUI(),
    document=document,
    guards=[]
)
app.install_module(module)


if __name__ == "__main__":
    uvicorn.run("main:app", port=5000, reload=True)
```

Now we can test our API at [http://127.0.0.1:5000/docs](http://127.0.0.1:5000/docs#/)

You can also try the [quick-project](https://python-ellar.github.io/ellar/quick-project/) setup to get a good idea of the library.

## **HTML Templating**
Ellar has built-in support for Jinja2, which is a popular template engine for HTML. This feature allows for easy and efficient HTML templating similar to that of Flask. Jinja2 can be used to create reusable templates, and to insert dynamic data into HTML pages. It also has support for template inheritance, control structures, and other useful features that can help to simplify and streamline the process of creating HTML templates.

```html
<html>
  <body>
    <ul>
      {% for item in items %}
      <li>{{ item }}</li>
      {% endfor %}
    </ul>
  </body>
</html>
```

See the [Doc](https://python-ellar.github.io/ellar/templating/templating/) for more examples.
