# **Socket IO - [python-socketio](https://python-socketio.readthedocs.io/en/latest/){target="_blank"}**

Ellar integration with [python-socketio](https://python-socketio.readthedocs.io/en/latest/){target="_blank"}, a library that enables real-time, bidirectional and event-based communication between the browser and the server. 

## **Gateways**

A class annotated with `WebSocketGateway` decorator is like a controller that creates a compatibles with python-socketio, ellar and websocket. 
A gateway class also supports dependency injection and guards.

```python
from ellar.socket_io import WebSocketGateway


@WebSocketGateway(path='/events-ws', name='event-gateway')
class EventGateway:
    pass
```
## **Installation**
To start building Socket.IO webSockets-based applications, first install the required package:
```shell
$(venv) pip install python-socketio
```
## **Overview**
In general, each gateway is listening on the same port as the HTTP server and has a path `/socket.io` unless changed manually. 
This default behavior can be modified by passing an argument to the `@WebSocketGateway(path='/event-ws')`. 
You can also set a [namespace](https://socket.io/docs/v4/namespaces/) used by the gateway as shown below:

```python
# project_name/events/gateway.py
from ellar.socket_io import WebSocketGateway


@WebSocketGateway(path='/socket.io', namespace='events')
class EventGateway:
    pass
```
!!! warning
    Gateways are not instantiated until they are referenced in the `controllers` array of an existing module.

You can pass any supported [option](https://socket.io/docs/v4/server-options/) to the socket constructor with the second argument to the `@WebSocketGateway()` decorator, as shown below:

```python
# project_name/events/gateway.py
from ellar.socket_io import WebSocketGateway, GatewayBase


@WebSocketGateway(path='/socket.io', transports=['websocket'])
class EventGateway(GatewayBase):
    pass
```

The gateway is now listening, but we have not yet subscribed to any incoming messages. 
Let's create a handler that will subscribe to the `events` messages and respond to the user with the exact same data.
```python
# project_name/events/gateway.py
from ellar.socket_io import WebSocketGateway, subscribe_message, GatewayBase
from ellar.common import WsBody


@WebSocketGateway(path='/socket.io', transports=['websocket'])
class EventGateway(GatewayBase):
    @subscribe_message('events')
    async def handle_event(self, data: str = WsBody()):
        return data
```

You can also define schema for the data receive, for example:
```python
# project_name/events/gateway.py
from ellar.socket_io import WebSocketGateway, subscribe_message, GatewayBase
from ellar.common import WsBody
from pydantic import BaseModel


class MessageBody(BaseModel):
    data: str


@WebSocketGateway(path='/socket.io', transports=['websocket'])
class EventGateway(GatewayBase):
    @subscribe_message('events')
    async def handle_event(self, data: MessageBody = WsBody()):
        return data.dict()
```

Once the gateway is created, we can register it in our module.
```python
# project_name/events/module.py

from ellar.common import Module
from .gateway import EventGateway

@Module(controllers=[EventGateway])
class EventsModule:
    pass

```

`WebSocketGateway` decorated class comes with a different **context** that providers extra information/access to `server`, `sid` and current message `environment`.
```python
from ellar.socket_io import GatewayBase
from socketio import AsyncServer


@WebSocketGateway(path='/socket.io', transports=['websocket'])
class EventGateway(GatewayBase):
    @subscribe_message('events')
    async def handle_event(self, data: MessageBody = WsBody()):
        assert isinstance(self.context.server, AsyncServer)
        assert isinstance(self.context.sid, str)
        assert isinstance(self.context.environment, dict)
        
        await self.context.server.emit('my_custom_event', data.dict(), room=None)
```

## **WsResponse**
You may return a `WsResponse` object and supply two properties. The `event` which is a name of the emitted event and the `data` that has to be forwarded to the client.
```python
from ellar.socket_io import GatewayBase
from ellar.socket_io import WsResponse


@WebSocketGateway(path='/socket.io', transports=['websocket'])
class EventGateway(GatewayBase):
    @subscribe_message('events')
    async def handle_event(self, data: MessageBody = WsBody()):
        return WsResponse('events', data.dict())
```
!!! hint
    The `WsResponse` class is imported from `ellar.socketio` package. And its has similar interface as `AsyncServer().emit`

!!! warning
    If you return a response that is not a `WsResponse` object, ellar will assume handler as the `event` to emit the response. Or you can use `self.context.server.emit` to send the message back to the client.

In order to listen for the incoming response(s), the client has to apply another event listener.

```javascript
socket.on('events', (data) => console.log(data));
```

## **Gateway Connection and Disconnection Handling**
`on_connected` and `on_disconnected` can be used to define `on_connect` and `on_disconnect` handler in your gateway controller.

For example,
```python
from ellar.socket_io import GatewayBase, WebSocketGateway, subscribe_message, on_connected, on_disconnected
from ellar.socket_io import WsResponse


@WebSocketGateway(path='/socket.io', transports=['websocket'])
class EventGateway(GatewayBase):
    @on_connected()
    async def connect(self):
        await self.context.server.emit(
            "my_response", {"data": "Connected", "count": 0}, room=self.context.sid
        )

    @on_disconnected()
    async def disconnect(self):
        print("Client disconnected")
    
    @subscribe_message('events')
    async def handle_event(self, data: MessageBody = WsBody()):
        return WsResponse('events', data.dict())
```

!!! info
    `@on_connected` and `@on_disconnected()` handlers doesn't take any argument because all its arguments are already available in the `self.context`


## **Exceptions**
All exceptions that happens on the server in a gateway controller after successful handshake between the server and client are sent to the client through `error` event.
This is a standard practice when working socketio client. The client is required to subscribe to `error` event inorder to receive error message from the server.


for example:
```python
from ellar.socket_io import GatewayBase, WebSocketGateway, subscribe_message
from ellar.common.exceptions import WebSocketException
from starlette import status


@WebSocketGateway(path='/socket.io', transports=['websocket'])
class EventGateway(GatewayBase):
    @subscribe_message('events')
    async def handle_event(self, data: MessageBody = WsBody()):
        raise WebSocketException(status.WS_1009_MESSAGE_TOO_BIG, reason='Message is too big')
```
When client sends message to `events`, an exception will be raised. And the client will receive the error message if it subscribed to `error` events. 

For example:

```javascript
const socket = io.connect()

socket.on('error', (error) => {
    console.error(error)
})
```

## **Guards**
There is no fundamental difference between web sockets guards and regular HTTP application guards. 
The only difference is that instead of throwing `HttpException`, you should use `WebSocketException`

!!! hint
    `WebSocketException` is an exception class located in `ellar.common.exceptions`


```python
from ellar.common import Guards

...
@Guards(MyCustomGuards)
@subscribe_message('events')
async def handle_event(self, data: MessageBody = WsBody()):
    return WsResponse('events', data.dict())
...

```

`@Guards` can be applied at handler level as shown in the last construct or at class level as shown below:

```python
...

@Guards(MyGuard)
@WebSocketGateway(path='/socket.io', transports=['websocket'])
class EventGateway(GatewayBase):
    @on_connected()
    async def connect(self):
        await self.context.server.emit(
            "my_response", {"data": "Connected", "count": 0}, room=self.context.sid
        )
    ...
```

## **Testing**
Gateway can be unit tested just like regular ellar controllers. But for integration testing, a separate testing module, `TestGateway`, is needed 
to set up a socketio client to simulation activity between server and client.

!!! hint
    `TestGateway` class is located at `ellar.socket_io.testing`

For example:

```python
@WebSocketGateway(path="/ws", async_mode="asgi", cors_allowed_origins="*")
class EventGateway:
    @subscribe_message("my_event")
    async def my_event(self, message: MessageData = WsBody()):
        return WsResponse("my_response", {"data": message.data}, room=self.context.sid)

    @subscribe_message
    async def my_broadcast_event(self, message: MessageData = WsBody()):
        await self.context.server.emit("my_response", {"data": message.data})

    @on_connected()
    async def connect(self):
        await self.context.server.emit(
            "my_response", {"data": "Connected", "count": 0}, room=self.context.sid
        )

    @on_disconnected()
    async def disconnect(self):
        print("Client disconnected")
```
The above gateway construct integration testing can be done as shown below:

```python
import pytest
from ellar.socket_io.testing import TestGateway

@pytest.mark.asyncio
class TestEventGateway:
    test_client = TestGateway.create_test_module(controllers=[EventGateway])

    async def test_socket_connection_work(self):
        my_response_message = []
        connected_called = False
        disconnected_called = False

        async with self.test_client.run_with_server() as ctx:

            @ctx.sio.event
            async def my_response(message):
                my_response_message.append(message)

            @ctx.sio.event
            async def disconnect():
                nonlocal disconnected_called
                disconnected_called = True

            @ctx.sio.event
            async def connect(*args):
                nonlocal connected_called
                await ctx.sio.emit("my_event", {"data": "I'm connected!"})
                connected_called = True

            await ctx.connect(socketio_path="/ws/")
            await ctx.wait()

        assert len(my_response_message) == 2
        assert my_response_message == [
            {"data": "Connected", "count": 0},
            {"data": "I'm connected!"},
        ]
        assert disconnected_called and connected_called

    async def test_broadcast_work(self):
        sio_1_response_message = []
        sio_2_response_message = []

        async with self.test_client.run_with_server() as ctx:
            ctx_2 = ctx.new_socket_client_context()

            @ctx.sio.event
            async def my_response(message):
                sio_1_response_message.append(message)

            @ctx_2.sio.event
            async def my_response(message):
                sio_2_response_message.append(message)

            await ctx.connect(socketio_path="/ws/")
            await ctx_2.connect(socketio_path="/ws/")

            await ctx.sio.emit(
                "my_broadcast_event", {"data": "Testing Broadcast"}
            )  # both sio_1 and sio_2 would receive this message

            await ctx.wait()
            await ctx_2.wait()

        assert len(sio_1_response_message) == 2
        assert sio_1_response_message == [
            {"data": "Connected", "count": 0},
            {"data": "Testing Broadcast"},
        ]

        assert len(sio_2_response_message) == 2
        assert sio_2_response_message == [
            {"data": "Connected", "count": 0},
            {"data": "Testing Broadcast"},
        ]
```
`self.test_client.run_with_server()` setup a server and returns `RunWithServerContext` object.
The `RunWithServerContext` contains a socket io client and created server url. 
And with the client(`sio`) returned, you can subscribe to events and send messages as shown in the above construct.

!!! warning
    It is important to have all the event subscription written before calling `ctx.connect`

Also, it is possible to test with more than one client as you can see in `test_broadcast_work` in construct above.
We created another instance of **RunWithServerContext** as `ctx_2` from the already existing `ctx` with `ctx.new_socket_client_context()`. 
And both were used to test for message broadcast.


## **SocketIO Ellar Example**
[python-socketio](https://python-socketio.readthedocs.io/en/latest/){target="_blank"} provided a sample project on how to integrate [python-socketio with django](https://github.com/miguelgrinberg/python-socketio/blob/main/examples/server/wsgi).
The sample project was converted to ellar gateway and it can find it [here](https://github.com/eadwinCode/ellar/tree/main/examples/02-socketio-app){target="_blank"}

![gateway_example_image](../img/live_support_websocket_3.gif)
