from pydantic.version import version_short


def pydantic_error_url(error_type: str) -> str:
    """https://errors.pydantic.dev/2.5/v/string_too_long"""
    return f"https://errors.pydantic.dev/{version_short()}/v/{error_type}"
