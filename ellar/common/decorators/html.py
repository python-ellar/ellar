import asyncio
import inspect
import typing as t
import warnings

from ellar.constants import (
    NOT_SET,
    RESPONSE_OVERRIDE_KEY,
    TEMPLATE_FILTER_KEY,
    TEMPLATE_GLOBAL_KEY,
)
from ellar.core.response.model import HTMLResponseModel
from ellar.core.routing import RouteOperationBase
from ellar.core.templating import TemplateFunctionData
from ellar.exceptions import ImproperConfiguration
from ellar.helper import class_base_function_regex, get_name
from ellar.types import TemplateFilterCallable, TemplateGlobalCallable

from .base import set_meta


class RenderDecoratorException(Exception):
    pass


def render(template_name: t.Optional[str] = NOT_SET) -> t.Callable:
    if template_name is not NOT_SET:
        assert isinstance(
            template_name, str
        ), "Render Operation must invoked eg. @render()"
    template_name = None if template_name is NOT_SET else template_name

    def _decorator(func: t.Union[t.Callable, t.Any]) -> t.Union[t.Callable, t.Any]:
        if not callable(func) or isinstance(func, RouteOperationBase):
            warnings.warn_explicit(
                UserWarning(
                    "\n@Render should be used only as a function decorator. "
                    "\nUse @Render before @Method decorator."
                ),
                category=None,
                filename=inspect.getfile(getattr(func, "endpoint", func)),
                lineno=inspect.getsourcelines(getattr(func, "endpoint", func))[1],
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
        return f

    return decorator
