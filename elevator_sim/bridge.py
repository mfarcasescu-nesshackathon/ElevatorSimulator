from __future__ import annotations

import json
import socket
import time
from typing import Any


class NullPublisher:
    def publish(self, state: dict[str, Any]) -> None:
        return None

    def close(self) -> None:
        return None


class DelayPublisher:
    """Wrap another publisher and sleep after each tick so Blender can keep up."""

    def __init__(self, inner, delay_seconds: float) -> None:
        self.inner = inner
        self.delay_seconds = delay_seconds

    def publish(self, state: dict[str, Any]) -> None:
        self.inner.publish(state)
        if self.delay_seconds > 0 and not state.get("done"):
            time.sleep(self.delay_seconds)

    def close(self) -> None:
        self.inner.close()


class CompositePublisher:
    def __init__(self, publishers: list) -> None:
        self.publishers = publishers

    def publish(self, state: dict[str, Any]) -> None:
        for publisher in self.publishers:
            publisher.publish(state)

    def close(self) -> None:
        for publisher in self.publishers:
            publisher.close()


class TcpTickPublisher:
    """JSON-lines TCP server. Blender connects as a client and reads one object per line."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8765, wait_client: float = 15.0) -> None:
        self.host = host
        self.port = port
        self.wait_client = wait_client
        self._server: socket.socket | None = None
        self._client: socket.socket | None = None
        self._hello_sent = False

    def start(self) -> None:
        self.bind_and_listen()
        self.accept_client()

    def bind_and_listen(self) -> int:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        self.port = server.getsockname()[1]
        server.listen(1)
        server.settimeout(self.wait_client)
        self._server = server
        return self.port

    def accept_client(self) -> None:
        if self._server is None:
            raise RuntimeError("call bind_and_listen() before accept_client()")
        try:
            client, _addr = self._server.accept()
            client.settimeout(None)
            self._client = client
        except TimeoutError:
            self._client = None

    def publish(self, state: dict[str, Any]) -> None:
        if self._client is None:
            return
        if not self._hello_sent:
            hello = {
                "type": "hello",
                "num_floors": state["num_floors"],
                "num_elevators": state["num_elevators"],
                "capacity": state["capacity"],
            }
            self._send(hello)
            self._hello_sent = True
        self._send(state)

    def _send(self, payload: dict[str, Any]) -> None:
        if self._client is None:
            return
        line = json.dumps(payload) + "\n"
        try:
            self._client.sendall(line.encode("utf-8"))
        except OSError:
            self._client = None

    def close(self) -> None:
        if self._client is not None:
            try:
                self._client.close()
            except OSError:
                pass
            self._client = None
        if self._server is not None:
            try:
                self._server.close()
            except OSError:
                pass
            self._server = None
