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
- `directory` Path to dump the scaffolded files. `.` can be used to select current directory.
