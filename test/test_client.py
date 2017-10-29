from chatroom.client import Client
import logging

from threading import Event

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

def test_publish(server_name, server):
    publisher = Client("testing.rpc.client.publisher", server_name=server_name)
    publisher.connect()

    subscriber = Client("testing.rpc.client.subscriber", server_name=server_name)
    subscriber.connect()

    event = Event()
    result = []
    def subscribe_cb(data):
        result.append(data)
        print("Receive publish message: {}".format(data))
        event.set()

    subscriber.subscribe("testing.rpc.client.publisher", subscribe_cb)

    for index in range(0, 10):
        publisher.publish({
            "message": "Hello world! {}".format(index)
        })

        print("Wait index {}".format(index))
        event.wait()


    assert len(result) == 10


