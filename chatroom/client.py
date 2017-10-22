import logging
import threading
import uuid

from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor

from chatroom.zeroconf_browser import Browser

from chatroom.utils import Event, EmitError
from logzero import setup_logger

logger = setup_logger("chatroom.client")

from socketIO_client import SocketIO, BaseNamespace


class ChatNamespace(BaseNamespace):
    def on_event(self, event, *args):
        print("Without match eventhandler {}".format(event))


class Client:
    def __init__(self, path, server_name, max_workers=2):
        self.path = path
        self.server_name = server_name

        self.socket_io = None
        self.socket_io_wait_thread = None

        self.service = None
        self.channel = None

        self.request_handler_thread_executor = ThreadPoolExecutor(max_workers=2)

        self.browser = Browser()
        self.browser.start()

        self.rpc_request_events = OrderedDict()
        self.subscribes = {}
        self.rpc_apis = {}

    def connect(self):
        # Search the server by mDNS
        logger.info("Use mDNS to search the ip and port of servier {}".format(self.server_name))
        service = self.browser.wait(self.server_name)
        if service is None:
            msg = "Can't find the server, try again..."
            logger.error(msg)
            raise TimeoutError(msg)

        # Use zeroconf to find the chatroom server
        self.service = service
        logger.info("Found service at {}:{}".format(service.address, service.port))
        logger.info("Try to connect to the service by socket.io")
        self.socket_io = SocketIO(service.address, service.port)

        # This thread handles the socket.io message
        self.socket_io_wait_thread = threading.Thread(target=self.socket_io.wait, daemon=True)
        self.socket_io_wait_thread.start()

        # Register RPC response handler
        logger.info("Register RPC request/response Handler")
        self.channel = self.socket_io.define(ChatNamespace, '/chat')
        self.channel.on('rpc_request', self.on_rpc_request)
        self.channel.on('rpc_response', self.on_rpc_response)

        # Register self information to chatroom server
        result = self.emit("register", {
            "path": self.path
        })

        if result is None:
            raise RuntimeError("Can't register to the server {}:{}".format(self.service.address, self.service.port))
        else:
            logger.info("Connect and register to the server {}:{}".format(self.service.address, self.service.port))

    def disconnect(self):
        self.service.close()

    def emit(self, event_type, data, timeout=5):
        uid = str(uuid.uuid1())
        data["_uid"] = uid

        # Register the callback function for the emit response
        event = Event()

        def wait_emit_response(emit_response):
            nonlocal event
            event.set(emit_response)

        self.channel.once(uid, wait_emit_response)

        self.channel.emit(event_type, data)
        try:
            result = event.wait(timeout=timeout)
            if result.get("success") is False:
                msg = result.get("message")
                logger.error("Emit {} failed, error msg {}".format(event_type, result.get("message")))
                raise EmitError(msg)
            else:
                logger.info("Send event {} successfully".format(event_type))
                return result
        except TimeoutError as e:
            logger.error("Emit event {} is timeout".format(event_type))
            raise e

    #########################################################################################################
    #
    #   RPC
    #
    #########################################################################################################
    def echo(self, message):
        event = Event()

        payload = dict(
            path=self.path,
            payload=dict(
                message=message
            )
        )
        self.channel.once("echo", lambda echo_message: event.set(echo_message))

        self.emit("echo", payload)
        result = event.wait()

        return result

    # Send Request
    def send_rpc_request(self, target, method, parameters):
        id = str(uuid.uuid1())

        payload = dict(
            path=target,
            payload=dict(
                id=id,
                method=method,
                parameters=parameters
            )
        )

        self.emit('rpc_request', payload)

        event = Event()
        self.rpc_request_events[id] = event

        return event

    def _handle_rpc_request(self, data):
        # Get the request information from SocketIO data
        source = data.get("path")
        payload = data.get("payload", {})

        # Get the RPC information from payload
        id = payload.get("id")
        method = payload.get("method")
        parameters = payload.get("parameters")

        # Check the method is existing
        fn = self.rpc_apis.get(method, None)
        result = None
        error = None

        if fn is None:
            error = "The method {} is not existing"
        else:
            try:
                result = fn(**parameters)
            except Exception as e:
                logger.exception(e)
                error = str(e)

        self.emit('rpc_response', dict(
            path=source,
            payload=dict(
                id=id,
                result=result,
                error=error
            )
        ))

    def on_rpc_request(self, data):
        self.request_handler_thread_executor.submit(self._handle_rpc_request, data)

    def on_rpc_response(self, data):
        payload = data.get('payload')
        id = payload.get('id')
        result = payload.get('result')

        event = self.rpc_request_events.get(id)
        if event:
            event.set(result)
        else:
            logger.error("Can't find the rpc request event with id {}".format(id))

    # Handle request
    def register_rpc_api(self, name, func):
        logger.info("Register RPC API {}".format(name))
        self.rpc_apis[name] = func

    # Publish / Subscribe
    def subscribe(self, target, callback):
        self.emit("subscribe", dict(
            path=target
        ))

        self.subscribes[target] = callback

    def on_publish(self, data):
        source = data.get('path')
        callback = self.subscribes.get(source, None)

        if callback:
            callback(data.get('payload'))
        else:
            logger.error("Can't find the subscribe of the publish event {}".format(data))


if __name__ == "__main__":
    client = Client("testing", "turing")
    client.connect()
