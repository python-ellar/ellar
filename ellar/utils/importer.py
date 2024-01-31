import inspect
import os
import re
import typing as t
from pathlib import Path

_module_import_regex = re.compile("(((\\w+)?(\\.<\\w+>)?(\\.\\w+))+)", re.IGNORECASE)


class ImportFromStringError(Exception):
    pass


def import_from_string(import_str: t.Any) -> t.Any:  # pragma: no cover
    """
    Uvicorn Util
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import failed.
    eg: ExamplePackage.ExampleModule:Attributes
    """

    if not isinstance(import_str, str):
        return import_str

    module_str, _, attrs_str = import_str.partition(":")
    if not module_str or not attrs_str:
        message = (
            'Import string "{import_str}" must be in format "<module>:<attribute>".'
        )
        raise ImportFromStringError(message.format(import_str=import_str))

    module = module_import(module_str)

    instance = module
    try:
        for attr_str in attrs_str.split("."):
            instance = getattr(instance, attr_str)
    except AttributeError as attr_ex:
        message = 'Attribute "{attrs_str}" not found in module "{module_str}".'
        raise ImportFromStringError(
            message.format(attrs_str=attrs_str, module_str=module_str)
        ) from attr_ex

    return instance


def module_import(module_str: str) -> t.Any:  # pragma: no cover
    from importlib import import_module

    try:
        module = import_module(module_str)
        return module
    except ImportError as exc:
        if exc.name != module_str:
            raise exc from None
        message = 'Could not import module "{module_str}".'
        raise ImportFromStringError(message.format(module_str=module_str)) from exc


@t.no_type_check
def get_class_import(klass: t.Union[t.Type, t.Any]) -> str:  # pragma: no cover
    """
    Generates String to import a class object
    :param klass:
    :return: string
    """
    if hasattr(klass, "__class__") and not isinstance(klass, type):
        klass = klass.__class__

    regex_path = _module_import_regex.search(str(klass))
    result = regex_path.group()
    split_result = result.rsplit(".", maxsplit=1)
    if len(split_result) == 2:
        return f"{split_result[0]}:{split_result[1]}"
    return result


def get_main_directory_by_stack(
    path: str, stack_level: int, from_dir: t.Optional[str] = None
) -> str:
    """
    Gets Directory Based on execution stack level or from a base directory

    example:
        from pathlib import Path

        directory = get_main_directory_by_stack("__main__", stack_level=1)
        file_directory = Path(__file__).resolve()

        assert directory == str(file_directory)

        directory = get_main_directory_by_stack("__main__", stack_level=2)
        assert directory == str(file_directory.parent)
    """
    forced_path_to_string = str(path)
    if forced_path_to_string.startswith("__main__") or forced_path_to_string.startswith(
        "/__main__"
    ):
        __main__, *others = forced_path_to_string.replace("/", " ").split("__main__")
        __parent__ = False

        if "__parent__" in others[0]:
            __parent__ = True

        if not from_dir:
            stack = inspect.stack()[stack_level]
            __main__parent = Path(stack.filename).resolve().parent
        else:
            # let's work with a given base directory
            __main__parent = Path(from_dir).resolve()

        if __parent__:
            others = others[0].split("__parent__")
            for item in list(others):
                if item == " ":
                    __main__parent = __main__parent.parent
                    others.remove(item)

        return os.path.join(
            str(__main__parent), *[i.strip() for i in others[0].split(" ")]
        )
    return path
