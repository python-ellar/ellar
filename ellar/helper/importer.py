import re
import typing as t

_module_import_regex = re.compile("(((\\w+)?(\\.<\\w+>)?(\\.\\w+))+)", re.IGNORECASE)


class ImportFromStringError(Exception):
    pass


def import_from_string(import_str: t.Any) -> t.Any:
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
    except AttributeError:
        message = 'Attribute "{attrs_str}" not found in module "{module_str}".'
        raise ImportFromStringError(
            message.format(attrs_str=attrs_str, module_str=module_str)
        )

    return instance


def module_import(module_str: str) -> t.Any:
    from importlib import import_module

    try:
        module = import_module(module_str)
        return module
    except ImportError as exc:
        if exc.name != module_str:
            raise exc from None
        message = 'Could not import module "{module_str}".'
        raise ImportFromStringError(message.format(module_str=module_str))


@t.no_type_check
def get_class_import(klass: t.Union[t.Type, t.Any]) -> str:
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
