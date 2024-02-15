import typing as t

from .decorator import as_pydantic_validator

try:
    import email_validator

    assert email_validator
    from pydantic import EmailStr
except ImportError:  # pragma: no cover
    from ellar.common.logging import logger

    @as_pydantic_validator(
        "__validate_input__", schema={"type": "string", "format": "email"}
    )
    class FallbackEmailStr(str):  # type: ignore
        @classmethod
        def __validate_input__(cls, __input_value: t.Any, _: t.Any) -> str:
            logger.warning(
                "email-validator not installed, email fields will be treated as str.\n"
                "To install, run: pip install email-validator"
            )
            return str(__input_value)

    EmailStr = FallbackEmailStr
