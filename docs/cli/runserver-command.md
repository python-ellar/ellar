# **Runserver Command**
This is command is a wrapper around the `UVICORN` ASGI server. It helps to create a link necessary for `UVICORN` to run your Ellar application properly.

```shell
ellar runserver --reload
```
will product the following output:
```shell
INFO:     Will watch for changes in these directories: ['/home/user/working-directory']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [2934815] using WatchFiles
INFO:     APP SETTINGS MODULE: john_doe.config:DevelopmentConfig
INFO:     Started server process [2934818]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## **Runserver CLI Options**
```shell
ellar runserver --help
```
OR

Please check `Uvicorn` CLI [Options](https://uvicorn.org/#command-line-options)
