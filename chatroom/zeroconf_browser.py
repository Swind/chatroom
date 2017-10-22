import socket
from threading import Event

from zeroconf import ServiceBrowser, ServiceStateChange, Zeroconf
from logzero import setup_logger

from chatroom import utils

logger = setup_logger("chatroom.zeroconf.browser")

class Service:
    ADDED = "added"
    REMOVED = "removed"

    def __init__(self, zeroconf, service_type, name, state_change):
        self.state = None
        self.name = name
        self.zeroconf = zeroconf

        self._update_info(service_type, name)
        self._state_change(state_change)

    def _update_info(self, service_type, name):
        info = self.zeroconf.get_service_info(service_type, name)

        self.address = socket.inet_ntoa(info.address)
        self.port = info.port

        self.weight = info.weight
        self.priority = info.priority

        self.server_name = info.server

        if info.properties:
            self.version = info.properties.get("version")
        else:
            self.version = None

    def __str__(self):
        return "[{}] {}:{} {}".format(self.state, self.address, self.port, self.name)


    def _state_change(self, state_change):
        if state_change is ServiceStateChange.Added:
            self.state = self.ADDED
        elif state_change is ServiceStateChange.Removed:
            self.state = self.REMOVED


class Browser:
    def __init__(self):
        self.zeroconf = Zeroconf()
        self.handlers = []

        self.services = {}

    def list(self):
        return self.services.values()

    def get(self, name):
        return self.get_by_full_name(utils.get_full_name(name))

    def get_by_full_name(self, full_name):
        return self.services.get(full_name)

    def wait(self, name, timeout=60):
        full_name = utils.get_full_name(name)
        event = Event()

        logger.info("Waiting the address and port info of {}".format(full_name))
        def wait_handler(service):
            logger.info("Handle new service {}".format(Service))
            if full_name == service.name:
                event.set()
                self.unregister_handler(wait_handler)

        self.register_handler(wait_handler)

        if full_name in self.services:
            logger.info("The service {} info is existing...".format(full_name))
            event.set()
            self.unregister_handler(wait_handler)

        event.wait(timeout=timeout)
        return self.get_by_full_name(full_name)

    def handler(self, zeroconf, service_type, name, state_change):
        service = Service(zeroconf, service_type, name, state_change)

        if service.state == service.ADDED:
            logger.info("New service {} is added".format(name))
            self.services[name] = service
        else:
            del self.services[name]

        for handler in self.handlers:
            handler(service)

    def register_handler(self, handler):
        self.handlers.append(handler)

    def unregister_handler(self, handler):
        self.handlers.remove(handler)

    def start(self):
        self.browser = ServiceBrowser(self.zeroconf, utils.TYPE, handlers=[self.handler])

    def close(self):
        self.zeroconf.close()

if __name__ == "__main__":
    browser = Browser()

    def handler(state):
        print(state)

    browser.register_handler(handler)
    browser.start()
    browser.wait("testing")
