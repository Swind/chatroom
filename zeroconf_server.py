from zeroconf import ServiceInfo, Zeroconf
import socket

import logging 

logger = logging.getLogger("chatroom")

class Server:
    def __init__(self, name, address, port, version):
        self.zeroconf = Zeroconf()
        self.name = name

        desc = {
            'version': version 
        }

        self.info = ServiceInfo(type_="_http._tcp.local.",
                           name="_turing._http._tcp.local.",
                           address=socket.inet_aton(address), 
                           port=port, 
                           weight=0, 
                           priority=0, 
                           properties=desc)


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
        version="0.1.0")

    server.register()

    import time
    try:
        time.sleep(600)
    except KeyboardInterrupt:
        pass
    finally:
        server.unregister()
        server.close()
