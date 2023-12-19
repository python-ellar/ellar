from typing import Any

from starlette.responses import (  # noqa
    FileResponse as FileResponse,
)
from starlette.responses import (  # noqa
    HTMLResponse as HTMLResponse,
)
from starlette.responses import (
    JSONResponse as JSONResponse,
)
from starlette.responses import (  # noqa
    PlainTextResponse as PlainTextResponse,
)
from starlette.responses import (  # noqa
    RedirectResponse as RedirectResponse,
)
from starlette.responses import (  # noqa
    Response as Response,
)
from starlette.responses import (  # noqa
    StreamingResponse as StreamingResponse,
)

try:
    import ujson
except ImportError:  # pragma: no cover
    ujson = None  # type: ignore


try:
    import orjson
except ImportError:  # pragma: no cover
    orjson = None  # type: ignore


class UJSONResponse(JSONResponse):
    def render(self, content: Any) -> bytes:
        assert ujson is not None, "ujson must be installed to use UJSONResponse"
        return ujson.dumps(content, ensure_ascii=False).encode("utf-8")


class ORJSONResponse(JSONResponse):
    media_type = "application/json"

    def render(self, content: Any) -> bytes:
        assert orjson is not None, "orjson must be installed to use ORJSONResponse"
        return orjson.dumps(content)
