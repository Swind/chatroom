from aiohttp import web
import socketio

from zeroconf_server import Server as ZServer

import logging
logger = logging.getLogger("chatroom")

class Server:
    def __init__(self, name, address, port, version):
        self.name = name
        self.address = address
        self.port = port
        self.version = version

        self.registers = {}

        # Zeroconf
        self.zserver = ZServer(name, address, port, version)

        # Socket.IO
        self.app = web.Application()
        self.app.router.add_static('/static', 'static')
        self.app.router.add_get('/', self.index)

        self.sio = socketio.AsyncServer()
        self.sio.attach(self.app)

        self.sio.on("connect", self.connect, namespace="/chat")
        self.sio.on("disconnect", self.disconnect, namespace="/chat")
        self.sio.on("register", self.register, namespace="/chat")
        self.sio.on("unregister", self.unregister, namespace="/chat")

    async def index(self, request):
        with open('index.html') as f:
            return web.Response(text=f.read(), content_type='text/html')

    def register(self, sid, client_info):
        self.registers[sid] = client_info

    def unregister(self, sid, data=None):
        del self.registers[sid]

    def connect(self, sid, environ):
        logger.info("New connection {}".format(sid))

    def disconnect(self, sid):
        logger.info("{} disconnected".format(sid))
        self.unregister(sid)

    def start(self):
        web.run_app(self.app, host=self.address, port=self.port)

if __name__ == '__main__':
    server = Server('testing', "192.168.0.16", 5037, "0.0.1")
    server.start()
