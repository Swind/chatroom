from threading import Condition, Lock

TYPE = "_http._tcp.local."
FULL_NAME_FORMAT = "{}._http._tcp.local."


def get_full_name(name):
    if not name.startswith("_"):
        name = "_{}".format(name)

    return FULL_NAME_FORMAT.format(name)


def get_resp_event_name(req_event_name):
    return "{}-magic_keyword".format(req_event_name)


class Event:
    def __init__(self):
        self._cond = Condition(Lock())
        self._flag = False
        self._msg = None

    def _reset_internal_locks(self):
        self._cond.__init__(Lock())

    def is_set(self):
        return self._flag

    isSet = is_set

    def set(self, msg):
        with self._cond:
            self._flag = True
            self._msg = msg
            self._cond.notify_all()

    def clear(self):
        with self._cond:
            self._flag = False
            self._msg = None

    def wait(self, timeout=None):
        with self._cond:
            signaled = self._flag
            if not signaled:
                signaled = self._cond.wait(timeout)

            if not signaled:
                raise TimeoutError()
            else:
                return self._msg


class EmitError(RuntimeError):
    pass
