from ellar.di import AnnotationToValue

NAMESPACE_METADATA = "namespace"
GATEWAY_OPTIONS = "websockets:gateway_options"

CONNECTION_EVENT = "connect"
DISCONNECT_EVENT = "disconnect"
CLOSE_EVENT = "close"
ERROR_EVENT = "error"
GATEWAY_WATERMARK = "websockets:is_gateway"
GATEWAY_MESSAGE_HANDLER_KEY = "websockets:message_handler"
MESSAGE_MAPPING_METADATA = "websockets:message_mapping"
MESSAGE_METADATA = "message"


class GATEWAY_METADATA(metaclass=AnnotationToValue):
    PATH: str
    NAME: str
    INCLUDE_IN_SCHEMA: str
    PROCESSED: str
