import typing as t

from starlette import status

from .base import APIException


class ImproperConfiguration(Exception):
    pass


class AuthenticationFailed(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "authentication_failed"

    def __init__(
        self, detail: t.Optional[t.Union[t.List, t.Dict, str]] = None, **kwargs: t.Any
    ) -> None:
        if detail is None:
            detail = "Incorrect authentication credentials."
        super(AuthenticationFailed, self).__init__(detail=detail, **kwargs)


class NotAuthenticated(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "not_authenticated"


class PermissionDenied(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    code = "permission_denied"


class NotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"


class MethodNotAllowed(APIException):
    status_code = status.HTTP_405_METHOD_NOT_ALLOWED
    code = "method_not_allowed"


class NotAcceptable(APIException):
    status_code = status.HTTP_406_NOT_ACCEPTABLE
    code = "not_acceptable"


class UnsupportedMediaType(APIException):
    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    code = "unsupported_media_type"
