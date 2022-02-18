import typing as t
from starletteapi.logger import logger

try:
    import email_validator  # type: ignore

    assert email_validator  # make autoflake ignore the unused import
    from pydantic import EmailStr
except ImportError:  # pragma: no cover

    class EmailStr(str):  # type: ignore
        @classmethod
        def __get_validators__(cls) -> t.Iterable[t.Callable[..., t.Any]]:
            yield cls.validate

        @classmethod
        def validate(cls, v: t.Any) -> str:
            logger.warning(
                "email-validator not installed, email fields will be treated as str.\n"
                "To install, run: pip install email-validator"
            )
            return str(v)
