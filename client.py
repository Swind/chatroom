from zeroconf_browser import Browser

from logging import getLogger

logger = getLogger("chartroom")

class Client:
    def __init__(self, name, server_name):
        self.name = name
        self.server_name = server_name

        self.browser = Browser()

    def register(self):
        # Search the server by mDNS
        event = self.browser.wait(self.server_name)

        try:
            event.wait(timeout=60)
        except TimeoutError as e:
            logger.error("Can't find chatroom server {}".format(self.server_name))

        # Connect to the server
        server_service = self.browser.get(self.server_name)



