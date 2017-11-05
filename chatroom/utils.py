import threading
import asyncio

TYPE = "_http._tcp.local."
FULL_NAME_FORMAT = "{}._http._tcp.local."


def get_full_name(name):
    if not name.startswith("_"):
        name = "_{}".format(name)

    return FULL_NAME_FORMAT.format(name)


def get_resp_event_name(req_event_name):
    return "{}-magic_keyword".format(req_event_name)


class Event(threading.Event):
    def __init__(self):
        self._msg = None
        super().__init__()

    def set_msg(self, msg):
        self._msg = msg
        return super().set()

    def clear(self):
        self._msg = None
        return super().clear()

    def wait(self, timeout=None):
        super().wait(timeout=timeout)
        return self._msg

class AsyncEvent(asyncio.Event):
    def __init__(self, loop=None):
        self._msg = None
        super().__init__(loop=loop)

    def set(self):
        #FIXME: The _loop attribute is not documented as public api!
        self._loop.call_soon_threadsafe(super().set)

    def set_msg(self, msg):
        self._msg = msg
        return self.set()

    def clear(self):
        self._msg = None
        return super().clear()

    async def wait(self, timeout=None):
        await super().wait()
        return self._msg

class EmitError(RuntimeError):
    pass
