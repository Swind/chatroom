JSONRPC = "2.0"


class Request:
    def __init__(self, id=None, method=None, params={}):
        self.id = id
        self.method = method
        self.params = params

    def dump(self):
        return {
            "jsonrpc": JSONRPC,
            "id": self.id,
            "method": self.method,
            "params": self.params
        }

    @classmethod
    def load(self, data):
        request = Request(
            data['id'],
            data.get('method'),
            data.get('params', {})
        )

        return request


class Error:
    PARSER_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    SERVER_ERROR = -32000

    def __init__(self, code, message, data):
        self.code = code
        self.message = message
        self.data = data

    @classmethod
    def load(cls, data):
        error = Error(
            data.get('code'),
            data.get('message'),
            data.get('data')
        )

        return error


class Response:
    def __init__(self, id=None, result=None, error=None):
        if result is not None and error is not None:
            raise SyntaxError("This member MUST NOT exist if there was no error triggered during invocation.")

        self.id = id
        self.result = result
        self.error = error

    @classmethod
    def load(cls, data):
        if "result" in data and "error" in data:
            raise SyntaxError("This member MUST NOT exist if there was no error triggered during invocation.")

        id = data.get('id', None)

        result = data.get('result', None)

        error = data.get('error', None)
        if error is not None:
            error = Error.load(error)

        return Response(id, result, error)

    def is_success(self):
        if "error" is not None:
            return False
        else:
            return True

    def is_failure(self):
        return not self.is_success()
