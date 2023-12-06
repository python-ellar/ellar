import typing as t

import typing_extensions
from pydantic import BaseModel

from .decorator import as_pydantic_validator


def _get_exc_type(cls: t.Type[Exception]) -> str:  # pragma: no cover
    if issubclass(cls, AssertionError):
        return "assertion_error"

    base_name = "type_error" if issubclass(cls, TypeError) else "value_error"
    if cls in (TypeError, ValueError):
        # just TypeError or ValueError, no extra code
        return base_name

    # if it's not a TypeError or ValueError, we just take the lowercase of the exception name
    # no chaining or snake case logic, use "code" for more complex error types.
    code = getattr(cls, "code", None) or cls.__name__.replace("Error", "").lower()
    return base_name + "." + code


@as_pydantic_validator("__validate_input__")
class ExceptionValidator:
    @classmethod
    def __validate_input__(cls, __input: t.Any, _: t.Any) -> t.Any:  # pragma: no cover
        if not isinstance(__input, Exception):
            raise ValueError("ErrorWrapper requires exc of type Exception")
        return __input


class ErrorWrapper(BaseModel):
    exc: typing_extensions.Annotated[Exception, ExceptionValidator]
    loc: t.Union[str, t.Tuple]

    def model_dump(self, **kw: t.Any) -> t.Dict[str, t.Any]:  # pragma: no cover
        type_ = _get_exc_type(self.exc.__class__)
        msg = str(self.exc)
        ctx = self.exc.__dict__

        d = {
            "loc": list(self.loc)
            if isinstance(self.loc, (list, tuple))
            else (self.loc,),
            "msg": msg,
            "type": type_,
        }

        if ctx:
            d["ctx"] = ctx

        return d


class InvalidModelFieldSetupException(Exception):
    pass
