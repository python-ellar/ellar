# **Create Project Command**
This command helps you create just an Ellar project provided the `"pyproject.toml"` file exists in the working directory(`CWD`)

```shell
ellar create-project my_new_project directory
```

for example:
```shell
ellar create-project my_new_project 
```

will create a folder as follows:
```angular2html
my_new_project/
├─ apps/
│  ├─ __init__.py
├─ core/
├─ config.py
├─ domain
├─ root_module.py
├─ server.py
├─ __init__.py
```


## **Create Project Command Arguments**
- `project-name` Set the resulting project module name.
- `directory` Path to dump the scaffolded files. `.` can be used to select current directory.
