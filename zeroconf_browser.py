from zeroconf import ServiceBrowser, ServiceStateChange, Zeroconf
from threading import Event
import socket
import time

import logging
logger = logging.getLogger("chatroom")

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
        return self.services.get(name)

    def wait(self, name):
        event = Event()

        def wait_handler(service):
            if name == service.name:
                event.set()
                self.unregister_handler(wait_handler)

        self.register_handler(wait_handler)

        if name in self.services:
            event.set()
            self.unregister_handler(wait_handler)

        return event

    def handler(self, zeroconf, service_type, name, state_change):
        service = Service(zeroconf, service_type, name, state_change)

        if service.state == service.ADDED:
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
        self.browser = ServiceBrowser(self.zeroconf, "_turing._tcp.local.", handlers=[self.handler])

    def close(self):
        self.zeroconf.close()

if __name__ == "__main__":
    browser = Browser()

    def handler(state):
        print(state)

    browser.register_handlers(handler)
    browser.start()

    time.sleep(600)
