import typing as t

from ellar.common.constants import VERSIONING_KEY

from .base import set_metadata as set_meta


def Version(*_version: str) -> t.Callable:
    """
     ========= CONTROLLER AND ROUTE FUNCTION DECORATOR ==============

     Defines route function version
    :param _version: allowed versions

    ### Example

    ```python
    @get("/")
    @Version("1.0", "1.1")
    def index():
        return {"version": "1.0"}
    ```
    """
    return set_meta(VERSIONING_KEY, {str(i) for i in _version})
