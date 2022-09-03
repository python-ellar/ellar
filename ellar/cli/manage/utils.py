import importlib
import os
import typing as t


def import_project_module(project: str) -> t.Optional[t.Any]:
    try:
        mod = importlib.import_module(project)
        return mod
    except Exception as ex:
        raise ex


def get_project_module(cwd: str) -> t.Optional[str]:
    dir_basename = os.path.basename(cwd)
    project_path = os.path.join(cwd, dir_basename.lower())
    if os.path.exists(project_path):
        return dir_basename.lower()
