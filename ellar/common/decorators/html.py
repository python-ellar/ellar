import asyncio
import inspect
import typing as t
import warnings

from ellar.common.constants import (
    MODULE_DECORATOR_ITEM,
    NOT_SET,
    RESPONSE_OVERRIDE_KEY,
    TEMPLATE_CONTEXT_PROCESSOR_KEY,
    TEMPLATE_FILTER_KEY,
    TEMPLATE_GLOBAL_KEY,
)
from ellar.common.exceptions import ImproperConfiguration
from ellar.common.responses.models import HTMLResponseModel
from ellar.common.templating import TemplateFunctionData
from ellar.common.types import TemplateFilterCallable, TemplateGlobalCallable
from ellar.reflect import fail_silently
from ellar.utils import class_base_function_regex, get_name

from .base import set_metadata as set_meta


class RenderDecoratorException(Exception):
    pass


def render(template_name: t.Optional[str] = NOT_SET) -> t.Callable:
    """
    ========= ROUTE FUNCTION DECORATOR ==============

    Renders route function response to HTML Response

    Decorated Function is expected to return an object of dict as a context variable for the template to be rendered.

    When @render is used in a Controller Class, the function becomes the template_name and the path to the html file
    becomes `templateFolder/ControllerName/functionName`. This can be overridden by providing `template_name`.

    :param template_name: template name.

    :return:
    """
    if template_name is not NOT_SET:
        assert isinstance(
            template_name, str
        ), "Render Operation must invoked eg. @render()"
    template_name = None if template_name is NOT_SET else template_name

    def _decorator(func: t.Union[t.Callable, t.Any]) -> t.Union[t.Callable, t.Any]:
        if not inspect.isfunction(func):
            line_nos = fail_silently(
                inspect.getsourcelines, getattr(func, "endpoint", func)
            )
            warnings.warn_explicit(
                UserWarning(
                    "\n@render should be used only as a function decorator. "
                    "\nUse @render before @HTTPMethod decorator."
                ),
                category=None,
                filename=inspect.getfile(getattr(func, "endpoint", func)),
                lineno=line_nos[1] if line_nos and len(line_nos) > 0 else None,
                source=None,
            )
            return func

        endpoint_name = get_name(func)
        is_class_base_function = use_mvc = False

        if class_base_function_regex.match(repr(func)):
            is_class_base_function = True

        if not template_name and is_class_base_function:
            use_mvc = True

        if not template_name and not is_class_base_function:
            raise RenderDecoratorException(
                f"template_name is required for function endpoints. {func}"
            )

        response = HTMLResponseModel(
            template_name=template_name or endpoint_name, use_mvc=use_mvc
        )
        target_decorator = set_meta(RESPONSE_OVERRIDE_KEY, {200: response})
        return target_decorator(func)

    return _decorator


def _validate_template_function(f: t.Any) -> None:
    if asyncio.iscoroutinefunction(f):
        raise ImproperConfiguration(
            "TemplateGlobalCallable must be a non coroutine function"
        )


def template_filter(
    name: t.Optional[str] = None,
) -> t.Callable[[TemplateFilterCallable], TemplateFilterCallable]:
    """A decorator that is used to register custom template filter.
    You can specify a name for the filter, otherwise the function
    name will be used. Example::

      @template_filter()
      def reverse(cls, s):
          return s[::-1]

    :param name: the optional name of the filter, otherwise the
                 function name will be used.
    """

    def decorator(f: TemplateFilterCallable) -> TemplateFilterCallable:
        _validate_template_function(f)
        setattr(
            f,
            TEMPLATE_FILTER_KEY,
            TemplateFunctionData(func=f, name=name or get_name(f)),
        )
        setattr(f, MODULE_DECORATOR_ITEM, TEMPLATE_FILTER_KEY)
        return f

    return decorator


def template_global(
    name: t.Optional[str] = None,
) -> t.Callable[[TemplateGlobalCallable], TemplateGlobalCallable]:
    """A decorator that is used to register a custom template global function.
    You can specify a name for the global function, otherwise the function
    name will be used. Example::

        @template_global()
        def double(cls, n):
            return 2 * n

    :param name: the optional name of the global function, otherwise the
                 function name will be used.
    """

    def decorator(f: TemplateGlobalCallable) -> TemplateGlobalCallable:
        _validate_template_function(f)
        setattr(
            f,
            TEMPLATE_GLOBAL_KEY,
            TemplateFunctionData(func=f, name=name or get_name(f)),
        )
        setattr(f, MODULE_DECORATOR_ITEM, TEMPLATE_GLOBAL_KEY)
        return f

    return decorator


def template_context() -> t.Callable[[TemplateGlobalCallable], TemplateGlobalCallable]:
    """
    Registers a template context processor function. These functions run before
    rendering a template. The keys of the returned dict are added as variables
    available in the template.

    Example::

    @template_context()
    def add_my_context(cls) -> dict:
        return dict(extra_item="extra_item", ...)
    """

    def decorator(f: TemplateGlobalCallable) -> TemplateGlobalCallable:
        setattr(f, TEMPLATE_CONTEXT_PROCESSOR_KEY, f)
        setattr(f, MODULE_DECORATOR_ITEM, TEMPLATE_CONTEXT_PROCESSOR_KEY)
        return f

    return decorator
