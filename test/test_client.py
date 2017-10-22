from chatroom.client import Client
import logging

filter = logging.Filter('chatroom')


def test_client_connect(server_name, server):
    client = Client("testing-turing-client", server_name=server_name)
    client.connect()


def test_echo(server_name, server):
    client = Client("testing.echo", server_name=server_name)
    client.connect()

    for index in range(0, 10):
        result = client.echo("Hello World! Echo {}".format(index))
        print(result)


def test_rpc(server_name, server):
    client = Client("testing.rpc.client", server_name=server_name)
    client.connect()

    def echo(message):
        return message

    client.register_rpc_api("echo", echo)

    for index in range(0, 10):
        event = client.send_rpc_request(
            target="testing.rpc.client",
            method="echo",
            parameters={
                "message": "Hello World!{}".format(index)
            })

        print("Waiting request result")
        result = event.wait()
        assert result == "Hello World!{}".format(index)
