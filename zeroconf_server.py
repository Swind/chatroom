from zeroconf import ServiceInfo, Zeroconf
import socket

import logging 

logger = logging.getLogger("chatroom")

class Server:
    TYPE = "_http._tcp.local."
    FULL_NAME_FORMAT = "{}._http._tcp.local."

    def __init__(self, name, address, port, description):
        self.zeroconf = Zeroconf()
        self.name = name
        self.description = description

        self.info = ServiceInfo(type_=self.TYPE,
                           name=self.get_full_name(),
                           address=socket.inet_aton(address), 
                           port=port, 
                           weight=0, 
                           priority=0, 
                           properties=self.description)

    def get_full_name(self):
        if not self.name.startswith("_"):
            name = "_{}".format(self.name)
        else:
            name = self.name

        return self.FULL_NAME_FORMAT.format(name)

    def register(self):
        self.zeroconf.register_service(self.info)

    def unregister(self):
        self.zeroconf.unregister_service(self.info)

    def close(self):
        self.zeroconf.close()


if __name__ == "__main__":
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
