import logging
import socket

from zeroconf import ServiceInfo, Zeroconf

from chatroom.utils import TYPE, get_full_name

from logzero import setup_logger
logger = setup_logger("chatroom.zeroconf.server")

class Server:
    def __init__(self, name, address, port, description):
        self.zeroconf = Zeroconf()
        self.name = name
        self.description = description
        self.address = address
        self.port = port

        self.full_name = get_full_name(name)
        self.info = ServiceInfo(type_=TYPE,
                           name=self.full_name,
                           address=socket.inet_aton(self.address),
                           port=self.port,
                           weight=0, 
                           priority=0, 
                           properties=self.description)

    def register(self):
        logger.info("Broadcast server {} at {}:{}".format(self.full_name, self.address, self.port))
        self.zeroconf.register_service(self.info)

    def unregister(self):
        self.zeroconf.unregister_service(self.info)

    def close(self):
        self.zeroconf.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    server = Server(
        name="testing", 
        address="192.168.0.16",
        port=5037, 
        description={})

    server.register()

    import time
    try:
        time.sleep(600)
    except KeyboardInterrupt:
        pass
    finally:
        server.unregister()
        server.close()
