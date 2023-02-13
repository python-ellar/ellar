<p align="center">
  <a href="#" target="blank"><img src="img/EllarLogoIconOnly.png" width="200" alt="Ellar Logo" /></a>
</p>

<p align="center"> Ellar - Python ASGI web framework for building fast, efficient and scalable RESTAPIs and server-side application. </p>

![Test](https://github.com/eadwinCode/ellar/actions/workflows/test_full.yml/badge.svg)
![Coverage](https://img.shields.io/codecov/c/github/eadwinCode/ellar)
[![PyPI version](https://badge.fury.io/py/ellar.svg)](https://badge.fury.io/py/ellar)
[![PyPI version](https://img.shields.io/pypi/v/ellar.svg)](https://pypi.python.org/pypi/ellar)
[![PyPI version](https://img.shields.io/pypi/pyversions/ellar.svg)](https://pypi.python.org/pypi/ellar)

---
## Introduction
Ellar is a lightweight ASGI framework for building efficient and scalable server-side python applications.
It supports both OOP (Object-Oriented Programming) and FP (Functional Programming)

Ellar is based on [Starlette (ASGI toolkit)](https://www.starlette.io/), a lightweight ASGI framework/toolkit well-suited for developing asynchronous web services in Python. 
And while Ellar provides a high level of abstraction on top of Starlette, it still incorporates some of its features, as well as those of FastAPI. 
If you are familiar with these frameworks, you will find it easy to understand and use Ellar.

## Inspiration
Ellar was deeply influenced by [NestJS](https://docs.nestjs.com/) for its ease of use and ability to handle complex project structures and applications. 
Additionally, it took some concepts from [FastAPI](https://fastapi.tiangolo.com/) in terms of request parameter handling and data serialization with Pydantic. 

With that said, the objective of Ellar is to offer a high level of abstraction in its framework APIs, along with a well-structured project setup, an object-oriented approach to web application design, 
the ability to adapt to any desired software architecture, and ultimately, speedy request handling.

## Installation
To get started, you need to scaffold a project using [Ellar-CLI](https://eadwincode.github.io/ellar-cli/) toolkit. This is recommended for a first-time user.
The scaffolded project is more like a guide to project setup.

```shell
$(venv) pip install ellar[standard]
```
OR
```shell
$(venv) pip install ellar ellar-cli
```

After that, lets create a new project. 
Run the command below and change the `project-name` with whatever name you decide.
```shell
$(venv) ellar new project-name
```

### NB:
Some shells may treat square braces (`[` and `]`) as special characters. If that's the case here, then use a quote around the characters to prevent unexpected shell expansion.
```shell
pip install "ellar[standard]"
```

then, start the app with:
```shell
$(venv) ellar runserver --reload
```

Open your browser and navigate to [`http://localhost:8000/`](http://localhost:8000/).
![Swagger UI](img/ellar_framework.png)

## Features Summary
- `Pydantic integration`
- `Dependency Injection (DI)`
- `Templating with Jinja2`
- `OpenAPI Documentation (Swagger and ReDoc)`
- `Controller (MVC)`
- `Guards (authentications, roles and permissions)`
- `Modularization (eg: flask blueprint)`
- `Websocket support`
- `Session and Cookie support`
- `CORS, GZip, Static Files, Streaming responses`

## Dependency Summary
- `Python >= 3.7`
- `Starlette`
- `Pydantic`
- `Injector`

## Status

Project is still in development

- Documentation - in progress
- Interceptors  -  [Aspect Oriented Programming](https://en.wikipedia.org/wiki/Aspect-oriented_programming) (AOP) technique
- Database Plugin with [Encode/ORM](https://github.com/encode/orm)
