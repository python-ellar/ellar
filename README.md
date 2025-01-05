# Ellar - Modern Python ASGI Framework
<p align="center">
  <img src="https://python-ellar.github.io/ellar/img/EllarLogoB.png" width="200" alt="Ellar Logo" />
</p>

![Test](https://github.com/python-ellar/ellar/actions/workflows/test_full.yml/badge.svg)
![Coverage](https://img.shields.io/codecov/c/github/python-ellar/ellar)
[![PyPI version](https://badge.fury.io/py/ellar.svg)](https://badge.fury.io/py/ellar)
[![PyPI version](https://img.shields.io/pypi/v/ellar.svg)](https://pypi.python.org/pypi/ellar)
[![PyPI version](https://img.shields.io/pypi/pyversions/ellar.svg)](https://pypi.python.org/pypi/ellar)

## Overview

Ellar is a modern, fast, and lightweight ASGI framework for building scalable web applications and APIs with Python. Built on top of Starlette and inspired by the best practices of frameworks like NestJS, Ellar combines the power of async Python with elegant architecture patterns.

## ✨ Key Features

- 🚀 **High Performance**: Built on ASGI standards for maximum performance and scalability
- 💉 **Dependency Injection**: Built-in DI system for clean and maintainable code architecture
- 🔍 **Type Safety**: First-class support for Python type hints and Pydantic validation
- 📚 **OpenAPI Integration**: Automatic Swagger/ReDoc documentation generation
- 🏗️ **Modular Architecture**: Organize code into reusable modules inspired by NestJS
- 🔐 **Built-in Security**: Comprehensive authentication and authorization system
- 🎨 **Template Support**: Integrated Jinja2 templating for server-side rendering
- 🔌 **WebSocket Support**: Real-time bidirectional communication capabilities
- 🧪 **Testing Utilities**: Comprehensive testing tools for unit and integration tests

## 🚀 Quick Start

### Installation

```bash
pip install ellar
```

### Basic Example

```python
from ellar.common import get, Controller, ControllerBase
from ellar.app import AppFactory
import uvicorn

@Controller()
class HomeController(ControllerBase):
    @get('/')
    async def index(self):
        return {'message': 'Welcome to Ellar Framework!'}

app = AppFactory.create_app(controllers=[HomeController])

if __name__ == "__main__":
    uvicorn.run("main:app", port=5000, reload=True)
```

## 📚 Complete Example

```python
from ellar.common import Body, Controller, ControllerBase, delete, get, post, put, Serializer
from ellar.di import injectable, request_scope
from ellar.app import AppFactory
from pydantic import Field

# Define Data Model
class CreateCarSerializer(Serializer):
    name: str
    year: int = Field(..., gt=0)
    model: str

# Define Service
@injectable(scope=request_scope)
class CarService:
    def __init__(self):
        self.detail = 'car service'

# Define Controller
@Controller
class CarController(ControllerBase):
    def __init__(self, service: CarService):
        self._service = service
    
    @post()
    async def create(self, payload: Body[CreateCarSerializer]):
        result = payload.dict()
        result.update(message='Car created successfully')
        return result

    @get('/{car_id:str}')
    async def get_one(self, car_id: str):
        return f"Retrieved car #{car_id}"

app = AppFactory.create_app(
    controllers=[CarController],
    providers=[CarService]
)
```

## 🔧 Requirements

- Python >= 3.8
- Starlette >= 0.27.0
- Pydantic >= 2.0
- Injector >= 0.19.0

## 📖 Documentation

- Complete documentation: [https://python-ellar.github.io/ellar/](https://python-ellar.github.io/ellar/)
- API Reference: [https://python-ellar.github.io/ellar/references/](https://python-ellar.github.io/ellar/references/)

## 🤝 Contributing

We welcome contributions! Here's how you can help:

- Create an issue for bugs or feature requests
- Submit pull requests for improvements
- Create third-party modules
- Share your experience with Ellar
- Build and showcase your applications

See [CONTRIBUTING.md](https://github.com/python-ellar/ellar/blob/main/docs/contribution.md) for detailed guidelines.

## 📝 License

Ellar is [MIT Licensed](LICENSE).

## 👤 Author

Ezeudoh Tochukwu [@eadwinCode](https://github.com/eadwinCode)
