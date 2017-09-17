from aiohttp import web
import socketio

from zeroconf_server import Server as ZServer
import utils

import logging
logger = logging.getLogger("chatroom")
logging.basicConfig(level=logging.INFO)

class Server:
    def __init__(self, name, address, port, version):
        self.name = name
        self.address = address
        self.port = port
        self.version = version

        self.registers = {}
        self.path_index = {}

        # Zeroconf
        logger.info("Start zeroconfig server {} at {}:{}".format(name, address, port))
        self.zserver = ZServer(name, address, port, {
            "version": self.version
        })
        self.zserver.register()

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

    def get_broadcast_path(self, name):
        return "{}-broadcast".format(name)

    async def reply(self, event_type, sid, success, error=""):
        msg = {
            "success": success
        }
        if not success:
            msg['error'] = error

        await self.sio.emit(utils.get_resp_event_name(event_type), msg, room=sid, namespace="/chat")

    async def register(self, sid, client_info):
        logger.info("Receive a new register request")
        path = client_info.get('path')

        if path is None:
            await self.reply("register", sid, success=False, error="The 'path' should be in the register data")

        # Save the client information
        self.registers[sid] = client_info
        self.path_index[path] = sid

        # Create a broadcast room for this client
        self.sio.enter_room(sid, room=self.get_broadcast_path(path))

        await self.reply("register", sid, success=True)

    async def unregister(self, sid, data=None, reply=True):
        client_info = self.registers.get(sid)
        if client_info:
            del self.registers[sid]

        del self.path_index[client_info.get('path')]

        if reply:
            await self.reply('unregister', success=True)

    def connect(self, sid, environ):
        logger.info("New connection {}".format(sid))

    async def disconnect(self, sid):
        logger.info("{} disconnected".format(sid))
        await self.unregister(sid, reply=False)

    async def _emit(self, source_sid, type_, target_path, payload):
        if target_path is None or payload is None:
            await self.reply(type_, source_sid, success=False, error="The 'target' and 'payload' should be in the {} data".format(type_))

        source_client_info = self.registers[source_sid]
        source_path = source_client_info.get('path')

        if "broadcast" == target_path:
            target_sid = self.get_broadcast_path(source_path)
        else:
            target_sid = self.path_index.get(target_path)

        if target_sid is None:
            await self.reply(type_, source_sid, success=False, error="Path {} is not existing".format(target_path))

        request_payload = {
            "source": source_path,
            "payload": payload
        }
        await self.sio.emit(type_, request_payload, room=target_sid)
        await self.reply(type_, source_sid, success=True)

    async def request(self, sid, data):
        await self._emit(
            source_sid=sid,
            type_="request",
            target_path=data.get('path'),
            payload=data.get('payload')
        )

    async def response(self, sid, data):
        await self._emit(
            source_sid=sid,
            type_="response",
            target_path=data.get('path'),
            payload=data.get('payload')
        )

    async def publish(self, sid, data):
        await self._emit(
            source_sid=sid,
            type_="response",
            target_path="broadcast",
            payload=data.get('payload')
        )

    async def subscribe(self, sid, data):
        path = data.get('path')
        if path is None:
            await self.reply('subscribe', sid, success=False, error="The 'path' should be in the data")
        else:
            self.sio.enter_room(sid, room=self.get_broadcast_path(path))
            await self.reply('subscribe', sid, success=True)

    def start(self):
        web.run_app(self.app, host=self.address, port=self.port)

if __name__ == '__main__':
    import time
    server = Server('turing', "192.168.0.16", 5037, "0.0.1")
    server.start()

