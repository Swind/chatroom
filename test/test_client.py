from chatroom.client import Client
import logging

from threading import Event

filter = logging.Filter('chatroom')

logging.basicConfig(level=logging.DEBUG)

def test_client_connect(server_name, server):
    client = Client("testing-turing-client", server_name=server_name)
    client.connect()

def test_rpc(server_name, server):
    sender = Client("testing.rpc.sender", server_name=server_name)
    sender.connect()

    receiver = Client("testing.rpc.receiver", server_name=server_name)
    receiver.connect()

    def echo(message):
        return message

    receiver.register_rpc_api("echo", echo)

    for index in range(0, 100):
        event = sender.send_rpc_request(
            target="testing.rpc.receiver",
            method="echo",
            parameters={
                "message":"Hello World!{}".format(index)
            })

        print("Waiting request result")
        result = event.wait()
        assert result == "Hello World!{}".format(index)

