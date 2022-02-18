from typing import Type, Sequence, no_type_check, Union, Optional, List, Dict, Any, cast

from starlette import status
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import create_model, BaseModel, ValidationError
from pydantic.error_wrappers import ErrorList # noqa

RequestErrorModel: Type[BaseModel] = create_model("Request")
WebSocketErrorModel: Type[BaseModel] = create_model("WebSocket")


class RequestValidationError(ValidationError):
    def __init__(self, errors: Sequence[ErrorList]) -> None:
        super().__init__(errors, RequestErrorModel)


class WebSocketRequestValidationError(ValidationError):
    def __init__(self, errors: Sequence[ErrorList]) -> None:
        super().__init__(errors, WebSocketErrorModel)


@no_type_check
def _get_error_details(
    data: Union[List, Dict, "ErrorDetail"],
    default_code: Optional[Union[str, int]] = None,
) -> Union[List["ErrorDetail"], "ErrorDetail", Dict[Any, "ErrorDetail"]]:
    """
    Descend into a nested data structure, forcing any
    lazy translation strings or strings into `ErrorDetail`.
    """
    if isinstance(data, list):
        ret = [_get_error_details(item, default_code) for item in data]
        return ret
    elif isinstance(data, dict):
        ret = {
            key: _get_error_details(value, default_code) for key, value in data.items()
        }
        return ret

    text = str(data)
    code = getattr(data, "code", default_code)
    return ErrorDetail(text, code)


@no_type_check
def _get_codes(detail: Union[List, Dict, "ErrorDetail"]) -> Union[str, Dict, List[Dict]]:
    if isinstance(detail, list):
        return [_get_codes(item) for item in detail]
    elif isinstance(detail, dict):
        return {key: _get_codes(value) for key, value in detail.items()}
    return detail.code


@no_type_check
def _get_full_details(detail: Union[List, Dict, "ErrorDetail"]) -> Union[Dict, List[Dict]]:
    if isinstance(detail, list):
        return [_get_full_details(item) for item in detail]
    elif isinstance(detail, dict):
        return {key: _get_full_details(value) for key, value in detail.items()}
    return {"message": detail, "code": detail.code}


class ErrorDetail(str):
    """
    A string-like object that can additionally have a code.
    """

    code = None

    def __new__(
        cls, string: str, code: Optional[Union[str, int]] = None
    ) -> "ErrorDetail":
        self = super().__new__(cls, string)
        self.code = code
        return self

    def __eq__(self, other: object) -> bool:
        r = super().__eq__(other)
        try:
            return r and self.code == other.code  # type: ignore
        except AttributeError:
            return r

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __repr__(self) -> str:
        return "ErrorDetail(string=%r, code=%r)" % (
            str(self),
            self.code,
        )

    def __hash__(self) -> Any:
        return hash(str(self))


class APIException(StarletteHTTPException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "A server error occurred."
    default_code = "error"

    def __init__(
            self,
            detail: Optional[Union[List, Dict, "ErrorDetail", str]] = None,
            code: Optional[Union[str, int]] = None,
            status_code: Optional[int] = None,
            headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        if detail is None:
            detail = self.default_detail
        if code is None:
            code = self.default_code

        if status_code is None:
            status_code = self.status_code

        self.headers = headers
        super(APIException, self).__init__(status_code=status_code, detail=_get_error_details(detail, code))

    def get_codes(self) -> Union[str, Dict, List[dict]]:
        """
        Return only the code part of the error details.
        Eg. {"name": ["required"]}
        """
        return _get_codes(cast(ErrorDetail, self.detail))

    def get_full_details(self) -> Union[Dict, List[dict]]:
        """
        Return both the message & code parts of the error details.
        Eg. {"name": [{"message": "This field is required.", "code": "required"}]}
        """
        return _get_full_details(cast(ErrorDetail, self.detail))  # type: ignore


class AuthenticationFailed(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "Incorrect authentication credentials."
    default_code = "authentication_failed"


class NotAuthenticated(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "Authentication credentials were not provided."
    default_code = "not_authenticated"


class PermissionDenied(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "You do not have permission to perform this action."
    default_code = "permission_denied"


class NotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Not found."
    default_code = "not_found"


class MethodNotAllowed(APIException):
    status_code = status.HTTP_405_METHOD_NOT_ALLOWED
    default_detail = 'Method "{method}" not allowed.'
    default_code = "method_not_allowed"

    def __init__(
        self,
        method: str,
        detail: Optional[Union[List, Dict, "ErrorDetail", str]] = None,
        code: Optional[Union[str, int]] = None,
    ):
        if detail is None:
            detail = str(self.default_detail).format(method=method)
        super().__init__(detail, code)


class NotAcceptable(APIException):
    status_code = status.HTTP_406_NOT_ACCEPTABLE
    default_detail = "Could not satisfy the request Accept header."
    default_code = "not_acceptable"

    def __init__(
        self,
        detail: Optional[Union[List, Dict, "ErrorDetail", str]] = None,
        code: Optional[Union[str, int]] = None,
        available_renderers: Optional[str] = None,
    ):
        self.available_renderers = available_renderers
        super().__init__(detail, code)


class UnsupportedMediaType(APIException):
    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    default_detail = 'Unsupported media type "{media_type}" in request.'
    default_code = "unsupported_media_type"

    def __init__(
        self,
        media_type: str,
        detail: Optional[Union[List, Dict, "ErrorDetail", str]] = None,
        code: Optional[Union[str, int]] = None,
    ):
        if detail is None:
            detail = str(self.default_detail).format(media_type=media_type)
        super().__init__(detail, code)

