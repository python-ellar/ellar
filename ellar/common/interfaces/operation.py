import typing as t


class IWebSocketConnectionAttributes(t.Protocol):
    """
    Interface for WebSocket connection attributes.
    """

    def connect(self, websocket_handler: t.Callable) -> t.Callable:
        """
        Register the connect handler to a websocket handler.

        :param websocket_handler: The websocket handler to register the connect handler to.
        :return: The connect handler.
        """

    def disconnect(self, websocket_handler: t.Callable) -> t.Callable:
        """
        Register the disconnect handler to a websocket handler.

        :param websocket_handler: The websocket handler to register the disconnect handler to.
        :return: The disconnect handler.
        """
