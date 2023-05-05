import http
import typing as t

from starlette import status


class APIException(Exception):
    __slots__ = ("headers", "description", "detail", "http_status")

    status_code = status.HTTP_400_BAD_REQUEST
    code = "bad_request"

    def __init__(
        self,
        detail: t.Union[t.List, t.Dict, str] = None,
        description: str = None,
        headers: t.Dict[str, t.Any] = None,
        status_code: int = None,
    ) -> None:
        assert self.status_code
        self.status_code = status_code or self.status_code
        self.http_status = http.HTTPStatus(self.status_code)
        self.description = description

        if detail is None:
            detail = self.http_status.phrase

        self.detail = detail
        self.headers = headers

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return f"{class_name}(status_code={self.status_code!r}, detail={self.detail!r})"

    def get_full_details(self) -> t.Union[t.Dict, t.List[t.Dict]]:
        """
        Return both the message & code parts of the error details.
        """
        return dict(
            detail=self.detail,
            code=self.code,
            description=self.description or self.http_status.description,
        )

    def get_details(self) -> t.Dict:
        result = dict(detail=self.detail)
        if self.description:
            result.update(description=self.description)
        return result
