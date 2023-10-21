import json
import typing as t

from ellar.common.exceptions import WebSocketRequestValidationError
from ellar.common.interfaces import IExecutionContext
from ellar.common.logger import request_logger
from ellar.common.params import WebsocketEndpointArgsModel
from starlette import status
from starlette.exceptions import WebSocketException
from starlette.status import WS_1008_POLICY_VIOLATION
from starlette.types import Message

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.connection import WebSocket


class WebSocketExtraHandler:
    def __init__(
        self,
        on_receive: t.Callable,
        *,
        route_parameter_model: WebsocketEndpointArgsModel,
        encoding: str = "json",  # May be "text", "bytes", or "json".
        on_connect: t.Optional[t.Callable] = None,
        on_disconnect: t.Optional[t.Callable] = None,
    ):
        self.on_receive = on_receive
        self.encoding = encoding
        self.on_disconnect = on_disconnect
        self.on_connect = on_connect
        self.route_parameter_model: WebsocketEndpointArgsModel = route_parameter_model

    @classmethod
    def __get_validators__(
        cls: t.Type["WebSocketExtraHandler"],
    ) -> t.Iterable[t.Callable[..., t.Any]]:
        yield cls.validate

    @classmethod
    def validate(cls: t.Type["WebSocketExtraHandler"], v: t.Any) -> t.Any:
        if not isinstance(v, type):
            raise ValueError(
                f"Expected Type[WebSocketExtraHandler], received: {type(v)}"
            )
        if WebSocketExtraHandler != v or not issubclass(v, WebSocketExtraHandler):
            raise ValueError(
                f"Expected Type[WebSocketExtraHandler], received: {type(v)}"
            )
        return v

    async def dispatch(
        self, context: "IExecutionContext", **receiver_kwargs: t.Any
    ) -> None:
        request_logger.debug(
            f"Running Websocket Dispatch Action from '{self.__class__.__name__}'"
        )
        websocket = context.switch_to_websocket().get_client()
        await self.execute_on_connect(context=context)
        close_code = status.WS_1000_NORMAL_CLOSURE

        try:
            while True:
                message = await websocket.receive()
                if message["type"] == "websocket.receive":
                    data = await self.decode(websocket, message)
                    await self.execute_on_receive(
                        context=context, data=data, **receiver_kwargs
                    )
                elif message["type"] == "websocket.disconnect":
                    close_code = int(message.get("code", status.WS_1000_NORMAL_CLOSURE))
                    break
        except WebSocketException as wexc:
            await websocket.close(code=wexc.code)
            raise RuntimeError(wexc.reason) from wexc
        except Exception as exc:
            close_code = status.WS_1011_INTERNAL_ERROR
            raise exc

        finally:
            await self.execute_on_disconnect(context=context, close_code=close_code)

    async def _resolve_receiver_dependencies(
        self, context: "IExecutionContext", data: t.Any
    ) -> t.Dict:
        request_logger.debug(
            f"Resolving Receiver Dependencies from '{self.__class__.__name__}'"
        )
        (
            extra_kwargs,
            errors,
        ) = await self.route_parameter_model.resolve_ws_body_dependencies(
            ctx=context, body_data=data
        )
        if errors:
            exc = WebSocketRequestValidationError(errors)
            await context.switch_to_websocket().get_client().send_json(
                {"code": WS_1008_POLICY_VIOLATION, "errors": exc.errors()}
            )
            raise exc
        return extra_kwargs

    async def execute_on_receive(
        self, *, context: "IExecutionContext", data: t.Any, **receiver_kwargs: t.Any
    ) -> None:
        extra_kwargs = await self._resolve_receiver_dependencies(
            context=context, data=data
        )

        receiver_kwargs.update(extra_kwargs)
        request_logger.debug(
            f"Executing on_receive handler from '{self.__class__.__name__}'"
        )
        await self.on_receive(**receiver_kwargs)

    async def execute_on_connect(self, *, context: "IExecutionContext") -> None:
        if self.on_connect is not None:
            request_logger.debug(
                f"Executing on_connect handler from '{self.__class__.__name__}'"
            )
            await self.on_connect(context.switch_to_websocket().get_client())
            return
        await context.switch_to_websocket().get_client().accept()

    async def execute_on_disconnect(
        self, *, context: "IExecutionContext", close_code: int
    ) -> None:
        if self.on_disconnect is not None:
            request_logger.debug(
                f"Executing on_disconnect handler from '{self.__class__.__name__}'"
            )
            await self.on_disconnect(
                context.switch_to_websocket().get_client(), close_code
            )

    async def decode(self, websocket: "WebSocket", message: Message) -> t.Any:
        request_logger.debug(
            f"Decoding websocket stream message from '{self.__class__.__name__}'"
        )
        if self.encoding == "text":
            if "text" not in message:
                raise WebSocketException(
                    code=status.WS_1003_UNSUPPORTED_DATA,
                    reason="Expected text websocket messages, but got bytes",
                )
            return message["text"]

        elif self.encoding == "bytes":
            if "bytes" not in message:
                raise WebSocketException(
                    code=status.WS_1003_UNSUPPORTED_DATA,
                    reason="Expected bytes websocket messages, but got text",
                )
            return message["bytes"]

        elif self.encoding == "json":
            if message.get("text") is not None:
                text = message["text"]
            else:
                text = message["bytes"].decode("utf-8")

            try:
                return json.loads(text)
            except json.decoder.JSONDecodeError as e:
                raise WebSocketException(
                    code=status.WS_1003_UNSUPPORTED_DATA,
                    reason="Malformed JSON data received.",
                ) from e

        assert (
            self.encoding is None
        ), f"Unsupported 'encoding' attribute {self.encoding}"
        return message["text"] if message.get("text") else message["bytes"]
