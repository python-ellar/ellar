# **Create New Project Command**
This command will help you kickstart your new Ellar project. 

It creates a new project for you with a directory structure and adds all required files for Ellar CLI to properly manage your project.

```shell
ellar new my-project
```

will create a folder as follows:
```angular2html
my-project/
├─ my_project/
│  ├─ apps/
│  │  ├─ __init__.py
│  ├─ core/
│  ├─ config.py
│  ├─ domain
│  ├─ root_module.py
│  ├─ server.py
│  ├─ __init__.py
├─ tests/
│  ├─ __init__.py
├─ pyproject.toml
├─ README.md

```
If you want to name your project differently than the folder, you can pass the `--project-name` option.

```shell
ellar new my-project path/to/scaffold-the-new-project
```
will create a folder as follows:
```angular2html
path/to/scaffold-the-new-project/
├─ my_project/
│  ├─ apps/
│  │  ├─ __init__.py
│  ├─ core/
│  ├─ config.py
│  ├─ domain
│  ├─ root_module.py
│  ├─ server.py
│  ├─ __init__.py
├─ tests/
│  ├─ __init__.py
├─ pyproject.toml
├─ README.md

```

## **New Command CLI Arguments**
- `project-name` Set the resulting project module name.
- `directory` Path to dump the scaffolded files. `.` can be used to select the current directory.


## **New Project without pyproject requirement**
To scaffold a new project without `pyproject.toml`, add `--plain` to the `ellar new command`. For example,

```shell
ellar new my-project --plain
```

This will create a folder as follows:
```angular2html
my-project/
├─ my_project/
│  ├─ apps/
│  │  ├─ __init__.py
│  ├─ core/
│  ├─ config.py
│  ├─ domain
│  ├─ root_module.py
│  ├─ server.py
│  ├─ __init__.py
├─ tests/
│  ├─ __init__.py
├─ manage.py
├─ README.md
```
Inside the scaffolded project, the `manage.py` python file is not the entry point for the application.
It creates a new CLI interface and uses that as the new CLI command to interact with the project.

```shell
python manage.py

### OUTPUT

Usage: manage.py [OPTIONS] COMMAND [ARGS]...

  Ellar, ASGI Python Web framework

Options:
  --project TEXT  Run Specific Command on a specific project  [default:
                  default]
  -v, --version   Show the version and exit.
  --help          Show this message and exit.

Commands:
  create-module  - Scaffolds Ellar Application Module -
  runserver      - Starts Uvicorn Server -

```
Other ellar commands and will be executed through `manage.py` python file. Eg:
```shell
python manage.py runserver
```
