
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
ellar new my-project --project-name john-doe
```
will create a folder as follows:
```angular2html
my-project/
├─ john_doe/
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

### New Command CLI Options
- `--project-name` Set the resulting project module name. Defaults to folder-name is not provided.
