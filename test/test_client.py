from chatroom.client import Client
from chatroom.async_client import AsyncClient
import logging
import pytest
import asyncio
import time

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

def test_async_echo(server_name, server, event_loop):
    async def run_test_async_echo_in_loop(loop):
        client = AsyncClient("testing.echo", server_name=server_name, event_loop=loop)
        await client.connect()

        for index in range(0, 10):
            msg = "Hello World! Echo {}".format(index)
            result = await client.echo(msg)
            assert result.get('payload', {}).get('message') == msg

        return True

    result = event_loop.run_until_complete(run_test_async_echo_in_loop(event_loop))
    assert result is True

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


def test_async_rpc(server_name, server, event_loop):
    target_client = Client("testing.rpc.target", server_name=server_name)
    target_client.connect()

    def echo(message):
        return message

    target_client.register_rpc_api("echo", echo)

    async def run_test_async_rpc_in_loop(loop):
        client = AsyncClient("testing.rpc.client", server_name=server_name, event_loop=loop)
        await client.connect()

        for index in range(0, 10):
            event = await client.send_rpc_request(
                target="testing.rpc.target",
                method="echo",
                parameters={
                    "message": "Hello World!{}".format(index)
                })

            result = await event.wait()
            assert result == "Hello World!{}".format(index)

        return True

    result = event_loop.run_until_complete(run_test_async_rpc_in_loop(event_loop))
    assert result is True



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
        event.clear()

    assert len(result) == 10


