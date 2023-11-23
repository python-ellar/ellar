import pytest
from ellar.app import AppFactory
from ellar.common import IExecutionContext, get
from starlette.exceptions import HTTPException
from starlette.responses import Response


def test_exception_after_response_sent(test_client_factory):
    @get()
    async def home(ctx: IExecutionContext):
        response = Response(b"", status_code=204)
        await response(*ctx.get_args())
        raise HTTPException(status_code=406)
        # raise RuntimeError("Something went wrong")

    app = AppFactory.create_app()
    app.router.append(home)

    client = test_client_factory(app)
    with pytest.raises(RuntimeError):
        client.get("/")
