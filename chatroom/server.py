import os
import socketio
from aiohttp import web

from logzero import setup_logger

from chatroom.zeroconf_server import Server as ZServer

ROOT_FOLDER = os.path.join(os.path.dirname(__file__), "..")
STATIC_FOLDER = os.path.join(ROOT_FOLDER, "static")

logger = setup_logger("chatroom.server")


class Server:
    def __init__(self, name, address, port, version):
        self.name = name
        self.address = address
        self.port = port
        self.version = version

        self.registers = {}
        self.path_index = {}

        self._init_zeroconfig()
        self._init_socketio()

    def _init_zeroconfig(self):
        # Zeroconf
        logger.info("Start zeroconfig server {} at {}:{}".format(self.name, self.address, self.port))
        self.zserver = ZServer(self.name, self.address, self.port, {
            "version": self.version
        })
        self.zserver.register()

    def _init_socketio(self):
        # Socket.IO
        self.app = web.Application()
        #self.app.router.add_static('/static', STATIC_FOLDER)
        self.app.router.add_get('/', self.index)

        self.sio = socketio.AsyncServer()
        self.sio.attach(self.app)

        self.sio.on("connect", self.connect, namespace="/chat")
        self.sio.on("disconnect", self.disconnect, namespace="/chat")
        self.sio.on("register", self.register, namespace="/chat")
        self.sio.on("unregister", self.unregister, namespace="/chat")

        self.sio.on("rpc_request", self.rpc_request, namespace="/chat")
        self.sio.on("rpc_response", self.rpc_response, namespace="/chat")
        self.sio.on("publish", self.publish, namespace="/chat")
        self.sio.on("subscribe", self.subscribe, namespace="/chat")

        self.sio.on("echo", self.echo, namespace="/chat")

    async def index(self, request):
        with open('index.html') as f:
            return web.Response(text=f.read(), content_type='text/html')

    def get_broadcast_path(self, name):
        return "{}-broadcast".format(name)

    async def reply(self, uid, sid, success, error=""):
        msg = {
            "success": success
        }
        if not success:
            msg['error'] = error

        await self.sio.emit(uid, msg, room=sid, namespace="/chat")

    async def register(self, sid, client_info):
        uid = client_info.get('_uid')

        logger.info("Receive a new register request")
        path = client_info.get('path')

        if path is None:
            await self.reply(uid, sid, success=False, error="The 'path' should be in the register data")

        # Save the client information
        self.registers[sid] = client_info
        self.path_index[path] = sid

        # Create a broadcast room for this client
        self.sio.enter_room(sid, room=self.get_broadcast_path(path))

        await self.reply(uid, sid, success=True)

    async def unregister(self, sid, data=None, reply=True):
        if data:
            uid = data.get('_uid')
        else:
            uid = None

        client_info = self.registers.get(sid)
        if client_info:
            del self.registers[sid]

        del self.path_index[client_info.get('path')]

        if reply and uid:
            await self.reply(uid, success=True)

    def connect(self, sid, environ):
        logger.info("New connection {}".format(sid))

    async def disconnect(self, sid):
        logger.info("{} disconnected".format(sid))
        await self.unregister(sid, reply=False)

    async def _emit(self, uid, source_sid, type_, target_path, payload):
        source_client_info = self.registers[source_sid]
        source_path = source_client_info.get('path')

        if "broadcast" == target_path:
            target_sid = self.get_broadcast_path(source_path)
        else:
            target_sid = self.path_index.get(target_path)

        await self.reply(uid, source_sid, success=True)

        request_payload = {
            "path": source_path,
            "payload": payload
        }
        await self.sio.emit(type_, request_payload, room=target_sid, namespace="/chat")

    ##################################################################################################################
    #
    #   API
    #
    ##################################################################################################################
    def _get_info(self, data):
        uid = data.get("_uid")
        path = data.get("path")
        payload = data.get("payload")

        return uid, path, payload

    async def echo(self, sid, data):
        uid, target_path, payload = self._get_info(data)

        await self._emit(
            uid=uid,
            source_sid=sid,
            type_="echo",
            target_path=target_path,
            payload=payload
        )

    async def rpc_request(self, sid, data):
        uid, target_path, payload = self._get_info(data)

        await self._emit(
            uid=uid,
            source_sid=sid,
            type_="rpc_request",
            target_path=target_path,
            payload=payload
        )

    async def rpc_response(self, sid, data):
        uid, target_path, payload = self._get_info(data)

        await self._emit(
            uid=uid,
            source_sid=sid,
            type_="rpc_response",
            target_path=target_path,
            payload=payload
        )

    async def publish(self, sid, data):
        uid, _, payload = self._get_info(data)

        await self._emit(
            uid=uid,
            source_sid=sid,
            type_="publish",
            target_path="broadcast",
            payload=payload
        )

    async def subscribe(self, sid, data):
        uid, path, payload = self._get_info(data)
        room = self.get_broadcast_path(path)
        self.sio.enter_room(sid, room=room, namespace="/chat")
        await self.reply(uid, sid, success=True)

    def start(self, handle_signals=True):
        web.run_app(self.app, host=self.address, port=self.port, handle_signals=handle_signals)

    def stop(self):
        self.app.shutdown()
