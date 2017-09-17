from zeroconf_browser import Browser
from socketIO_client import SocketIO, LoggingNamespace
from threading import Event
import utils
import threading

from retrying import retry
import logging

logger = logging.getLogger("chatroom.server")
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

        # register
        result = self.emit("register", {
            "path": self.path
        })
        if result is None:
            raise RuntimeError("Can't register to the server {}:{}".format(service.address, service.port))

    def request(self, payload):
        pass

    def subscribe(self, target_path):
        pass

    def publish(self, payload):
        pass

    def emit(self, event_type, data, timeout=60):
        event = Event()
        result = None

        def wait_resp(resp_result):
            nonlocal result
            result = resp_result
            logger.debug("wait_resp receive resp {}".format(result))
            event.set()

        resp_event_type = utils.get_resp_event_name(event_type)
        logger.debug("Register response event handler {}".format(resp_event_type))
        self.channel.once(resp_event_type, wait_resp)

        logger.debug("Emit event {} with data {}".format(event_type, data))
        self.channel.emit(event_type, data)

        logger.debug("Wait response event handler {}".format(resp_event_type))
        event.wait(timeout=timeout)

        return result

if __name__ == "__main__":
    client = Client("testing", "turing")
    client.connect()



