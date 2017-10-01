import logging
import threading
import uuid

from collections import OrderedDict

import chatroom.utils as utils
from socketIO_client import SocketIO, LoggingNamespace

from chatroom.zeroconf_browser import Browser

from chatroom.utils import Event, EmitError

logger = logging.getLogger("chatroom.client")
logging.basicConfig(level=logging.DEBUG)

class Client:
    def __init__(self, path, server_name):
        self.path = path
        self.server_name = server_name

        self.socket_io = None
        self.socket_io_wait_thread = None
        self.service = None
        self.channel = None

        self.browser = Browser()
        self.browser.start()

        self.queue_map = OrderedDict()
        self.subscribe_map = {}
        self.rpc_map = {}

    def connect(self):
        # Search the server by mDNS
        logger.info("Use mDNS to search the ip and port of servier {}".format(self.server_name))
        service = self.browser.wait(self.server_name)
        if service is None:
            msg = "Can't find the server, try again..."
            logger.error(msg)
            raise TimeoutError(msg)

        self.service = service
        logger.info("Found service at {}:{}".format(service.address, service.port))

        logger.info("Try to connect to the service by socket.io")
        self.socket_io = SocketIO(service.address, service.port)
        self.socket_io_wait_thread = threading.Thread(target=self.socket_io.wait, daemon=True)
        self.socket_io_wait_thread.start()

        self.channel = self.socket_io.define(LoggingNamespace, '/chat')
        self.channel.on('rpc_request', self.handle_rpc_request)
        self.channel.on('rpc_response', self.handle_rpc_response)

        # register
        result = self.emit("register", {
            "path": self.path
        })
        if result is None:
            raise RuntimeError("Can't register to the server {}:{}".format(service.address, service.port))
        else:
            logger.info("Connect and register to the server {}:{}".format(service.address, service.port))

        # Register RPC response handler
        logger.info("Register RPC request/response Handler")

    def disconnect(self):
        self.service.close()

    def emit(self, event_type, data, timeout=60):
        uid = str(uuid.uuid1())
        event = Event()

        self.channel.once(uid, lambda response: event.set(response))

        logger.debug("Emit event {} with data {}".format(event_type, data))
        data["_uid"] = uid

        self.channel.emit(event_type, data)

        try:
            print("Waiting {}".format(uid))
            result = event.wait(timeout=timeout)
            print("Receive {}".format(uid))
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
        self.queue_map[id] = event

        return event

    def handle_rpc_response(self, data):
        print("New rpc response {}".format(data))

        payload = data.get('payload')
        id = payload.get('id')
        result = payload.get('result')

        event = self.queue_map.get(id)
        if event:
            event.set(result)
        else:
            logger.error("Can't find the rpc request event with id {}".format(id))

    # Handle request
    def register_rpc_api(self, name, func):
        logger.info("Register RPC API {}".format(name))
        self.rpc_map[name] = func

    def handle_rpc_request(self, data):
        print("New rpc request {}".format(data))
        source = data.get("path")
        payload = data.get("payload", {})

        id = payload.get("id")
        method = payload.get("method")
        parameters = payload.get("parameters")

        try:
            result = self.rpc_map[method](**parameters)

            self.emit('rpc_response', dict(
                path=source,
                payload=dict(
                    id=id,
                    result=result
                )
            ))
        except Exception as e:
            self.emit('rpc_response', dict(
                path=source,
                payload=dict(
                    id=id,
                    error=str(e)
                )
            ))

        print("Emit response successfully")


    # Publish / Subscribe
    def subscribe(self, target, callback):
        self.emit("subscribe", dict(
            path=target
        ))

        self.subscribe_map[target] = callback

    def handle_publish(self, data):
        source = data.get('path')
        callback = self.subscribe_map.get(source)
        callback(data.get('payload'))

if __name__ == "__main__":
    client = Client("testing", "turing")
    client.connect()



