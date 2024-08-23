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

## **Introduction**

Ellar is a lightweight ASGI framework designed to simplify the development of efficient and scalable server-side Python 
applications. Whether you're building web services, APIs, or full-fledged web applications, 
Ellar offers a high level of abstraction and powerful features to streamline your development process.

Ellar allows developers to embrace both Object-Oriented Programming (OOP) and Functional Programming (FP) paradigms. 
It is built on top of Starlette, a renowned ASGI toolkit, ensuring robust asynchronous request-handling capabilities.

## **Key Features**

- **Easy to Use**: With an intuitive API, Ellar makes it easy for developers to get started with building fast and scalable Python web applications.
- **Dependency Injection (DI)**: Ellar includes a built-in DI system, enabling easy management of dependencies and reducing coupling between components.
- **Pydantic Integration**: Integrated with Pydantic for seamless data validation, ensuring that input data is always valid.
- **Templating with Jinja2**: Built-in support for Jinja2 templates simplifies the creation of dynamic web pages.
- **OpenAPI Documentation**: Ellar has built-in support for generating OpenAPI documentation and facilitating API documentation generation with Swagger or ReDoc.
- **Controller (MVC) Architecture**: Ellar follows the Model-View-Controller (MVC) pattern, aiding in organizing code and separating concerns.
- **Guards for Authentication and Authorization**: Offers built-in support for guards, making it easy to implement authentication and authorization in applications.
- **Modularity**: Inspired by NestJS, Ellar follows a modular architecture, allowing developers to organize code into reusable modules.
- **Asynchronous Programming**: Leveraging Python's async/await feature, Ellar enables the development of efficient and high-performance applications capable of handling concurrent requests.

## **Installation**

You can install Ellar using pip:

```bash
$(venv) pip install ellar
```

## **Getting Started**

```python
# Example code showcasing Ellar usage
# (Please ensure you have properly installed Ellar first)

import uvicorn
from ellar.common import Body, Controller, ControllerBase, delete, get, post, put, Serializer, Inject
from ellar.app import AppFactory
from ellar.di import injectable, request_scope
from ellar.openapi import OpenAPIDocumentModule, OpenAPIDocumentBuilder, SwaggerUI
from pydantic import Field
from pathlib import Path

# Define a serializer for creating a car
class CreateCarSerializer(Serializer):
    name: str
    year: int = Field(..., gt=0)
    model: str

# Define a service class for car operations
@injectable(scope=request_scope)
class CarService:
    def __init__(self):
        self.detail = 'a service'

# Define a controller for car operations
@Controller
class MotoController(ControllerBase):
    def __init__(self, service: CarService):
        self._service = service
    
    @post()
    async def create(self, payload: Body[CreateCarSerializer]):
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

# Create the Ellar application
app = AppFactory.create_app(
    controllers=[MotoController],
    providers=[CarService],
    base_directory=str(Path(__file__).parent),
    config_module=dict(REDIRECT_SLASHES=True),
    template_folder='templates'
)

# Build OpenAPI documentation
document_builder = OpenAPIDocumentBuilder()
document_builder.set_title('Ellar API') \
    .set_version('1.0.2') \
    .set_contact(name='Author', url='https://www.yahoo.com', email='author@gmail.com') \
    .set_license('MIT Licence', url='https://www.google.com')
document = document_builder.build_document(app)

# Setup OpenAPI documentation module
OpenAPIDocumentModule.setup(
    app=app,
    docs_ui=SwaggerUI(),
    document=document,
    guards=[]
)

# Run the application
if __name__ == "__main__":
    uvicorn.run("main:app", port=5000, reload=True)
```


Now we can test our API at [http://127.0.0.1:5000/docs](http://127.0.0.1:5000/docs#/)

You can also try the [quick-project](https://python-ellar.github.io/ellar/quick-project/) setup to get a good idea of the library.


## **Project Documentation Status**
- Authorization: In progress

## **Dependency Summary**

Ellar has the following dependencies:

- Python >= 3.8
- Starlette
- Pydantic
- Injector

## **Contributing**
Contributions are Welcome! You can contribute in the following ways.

- **Create an Issue** - Propose a new feature. Report a bug.
- **Pull Request** - Fix a bug and typo. Refactor the code.
- **Create third-party module** - Just like ellar-throttling, ellar-jwt, ellar-sql that can solve common problem in web application development.
- **Share** - Share your thoughts on the a Blog, Twitter, and others.
- **Build your application** - Please try to use Ellar. For more details, see [docs/CONTRIBUTING.md](https://github.com/python-ellar/ellar/blob/main/docs/contribution.md).

## **Contributors**
Thanks to all contributors!

## **Author**
Ezeudoh Tochukwu https://github.com/eadwinCode

## **License**
Ellar is [MIT License](https://github.com/python-ellar/ellar/blob/main/LICENSE).
