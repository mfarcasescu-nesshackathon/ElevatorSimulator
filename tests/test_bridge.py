import json
import socket
import threading

from elevator_sim.bridge import TcpTickPublisher


def test_tcp_publisher_sends_hello_and_tick():
    publisher = TcpTickPublisher(host="127.0.0.1", port=0, wait_client=3.0)
    port = publisher.bind_and_listen()
    received: list[dict] = []

    def client():
        sock = socket.create_connection(("127.0.0.1", port), timeout=3)
        buffer = ""
        try:
            while len(received) < 2:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                buffer += chunk.decode("utf-8")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.strip():
                        received.append(json.loads(line))
        finally:
            sock.close()

    thread = threading.Thread(target=client, daemon=True)
    thread.start()
    publisher.accept_client()
    publisher.publish(
        {
            "type": "tick",
            "t": 0,
            "done": False,
            "num_floors": 8,
            "num_elevators": 2,
            "capacity": 4,
            "elevators": [],
            "waiting": [],
            "completed": [],
        }
    )
    thread.join(timeout=3)
    publisher.close()
    assert received[0]["type"] == "hello"
    assert received[0]["num_floors"] == 8
    assert received[1]["type"] == "tick"
    assert received[1]["t"] == 0
