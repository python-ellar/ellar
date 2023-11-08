from ellar.common import WsBody
from ellar.socket_io.decorators import (
    WebSocketGateway,
    on_connected,
    on_disconnected,
    subscribe_message,
)
from ellar.socket_io.responses import WsResponse

from .schemas import MessageChatRoom, MessageData, MessageRoom


@WebSocketGateway(name="gatewaytest", async_mode="asgi", cors_allowed_origins="*")
class EventsGateway:
    @subscribe_message("my_event")
    async def my_event(self, message: MessageData = WsBody()):
        return WsResponse("my_response", {"data": message.data}, room=self.context.sid)

    @subscribe_message
    async def my_broadcast_event(self, message: MessageData = WsBody()):
        await self.context.server.emit("my_response", {"data": message.data})

    @subscribe_message("join")
    async def join(self, message: MessageRoom = WsBody()):
        await self.context.server.enter_room(self.context.sid, message.room)
        await self.context.server.emit(
            "my_response",
            {"data": "Entered room: " + message.room},
            room=self.context.sid,
        )

    @subscribe_message("leave")
    async def leave(self, message: MessageRoom = WsBody()):
        await self.context.server.leave_room(self.context.sid, message.room)
        await self.context.server.emit(
            "my_response", {"data": "Left room: " + message.room}, room=self.context.sid
        )

    @subscribe_message("close_room")
    async def close_room(self, message: MessageRoom = WsBody()):
        await self.context.server.emit(
            "my_response",
            {"data": "Room " + message.room + " is closing."},
            room=message.room,
        )
        await self.context.server.close_room(message.room)

    @subscribe_message("my_room_event")
    async def my_room_event(self, message: MessageChatRoom = WsBody()):
        await self.context.server.emit(
            "my_response", {"data": message.data}, room=message.room
        )

    @subscribe_message("disconnect_request")
    async def disconnect_request(self):
        await self.context.server.disconnect(self.context.sid)

    @on_connected()
    async def connect(self):
        await self.context.server.emit(
            "my_response", {"data": "Connected", "count": 0}, room=self.context.sid
        )

    @on_disconnected()
    async def disconnect(self):
        print("Client disconnected")
