# -*- coding: utf-8 -*-
"""Single-instance coordination for the desktop application."""

from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket


class SingleInstanceCoordinator(QObject):
    """Own a local IPC endpoint and relay activation requests."""

    activation_requested = Signal()

    def __init__(self, server_name: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.server_name = server_name
        self._server = QLocalServer(self)
        self._server.newConnection.connect(self._accept_connections)

    def acquire_or_notify(self, timeout_ms: int = 1500) -> bool:
        """Become the primary instance, or notify the existing one.

        Returns ``True`` only when this process acquired the application-wide
        local server and may continue starting the GUI.
        """
        if self._notify_existing(timeout_ms):
            return False

        if self._server.listen(self.server_name):
            return True

        # Another process may have won the startup race after our first probe.
        if self._notify_existing(timeout_ms):
            return False

        # Unix-domain socket files can survive an unclean shutdown. Remove an
        # endpoint only after two failed connection attempts, then try once more.
        QLocalServer.removeServer(self.server_name)
        return self._server.listen(self.server_name)

    def _notify_existing(self, timeout_ms: int) -> bool:
        socket = QLocalSocket()
        socket.connectToServer(self.server_name)
        if not socket.waitForConnected(timeout_ms):
            socket.abort()
            return False

        socket.write(b"activate\n")
        socket.flush()
        socket.waitForBytesWritten(timeout_ms)
        socket.waitForReadyRead(timeout_ms)
        socket.disconnectFromServer()
        return True

    def _accept_connections(self) -> None:
        while self._server.hasPendingConnections():
            socket = self._server.nextPendingConnection()
            if socket is None:
                continue
            socket.readyRead.connect(lambda s=socket: self._read_request(s))
            socket.disconnected.connect(socket.deleteLater)
            if socket.bytesAvailable():
                self._read_request(socket)

    def _read_request(self, socket: QLocalSocket) -> None:
        if b"activate" in bytes(socket.readAll()):
            self.activation_requested.emit()
            socket.write(b"ok\n")
            socket.flush()
        socket.disconnectFromServer()
