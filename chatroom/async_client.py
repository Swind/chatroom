import threading
import uuid
import asyncio

from chatroom.client import Client

from chatroom.utils import Event, AsyncEvent, EmitError
from logzero import setup_logger

logger = setup_logger("chatroom.client")

from socketIO_client import SocketIO, BaseNamespace

class ChatNamespace(BaseNamespace):
    def on_event(self, event, *args):
        print("Without match eventhandler {}".format(event))


class AsyncClient(Client):
    def __init__(self, path, server_name, max_workers=2, event_loop=None):
        if event_loop:
            self._event_loop = event_loop
        else:
            self._event_loop = asyncio.get_event_loop()

        super().__init__(path, server_name, max_workers=2)


    async def connect(self):
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
        self.channel.on('publish', self.on_publish)

        # Register self information to chatroom server
        result = await self.emit("register", {
            "path": self.path
        })

        if result is None:
            raise RuntimeError("Can't register to the server {}:{}".format(self.service.address, self.service.port))
        else:
            logger.info("Connect and register to the server {}:{}".format(self.service.address, self.service.port))

    def create_event(self):
        return AsyncEvent(loop=self.event_loop)

    async def emit(self, event_type, data, timeout=3600):
        uid = str(uuid.uuid1())
        data["_uid"] = uid

        # Register the callback function for the emit response
        event = self.create_event()

        def wait_emit_response(emit_response):
            nonlocal event
            event.set_msg(emit_response)

        self.channel.once(uid, wait_emit_response)
        self.channel.emit(event_type, data)

        try:
            result = await event.wait(timeout=timeout)
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
    async def echo(self, message):
        event = self.create_event()

        payload = dict(
            path=self.path,
            payload=dict(
                message=message
            )
        )
        self.channel.once("echo", lambda echo_message: event.set_msg(echo_message))

        await self.emit("echo", payload)
        result = await event.wait()

        return result

    # Send Request
    async def send_rpc_request(self, target, method, parameters):
        id = str(uuid.uuid1())

        payload = dict(
            path=target,
            payload=dict(
                id=id,
                method=method,
                parameters=parameters
            )
        )

        await self.emit('rpc_request', payload)

        event = self.create_event()
        self.rpc_request_events[id] = event

        return event

    async def _handle_rpc_request(self, data):
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

        await self.emit('rpc_response', dict(
            path=source,
            payload=dict(
                id=id,
                result=result,
                error=error
            )
        ))

    # Publish / Subscribe
    async def publish(self, data):
        await self.emit("publish", {
            "payload": data
        })

    async def subscribe(self, target, callback):
        await self.emit("subscribe", dict(
            path=target
        ))

        self.subscribes[target] = callback

if __name__ == "__main__":
    client = Client("testing", "turing")
    client.connect()
