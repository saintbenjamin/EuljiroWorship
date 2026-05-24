# -*- coding: utf-8 -*-
"""
:File: EuljiroWorship/controller/utils/slide_websocket_manager.py
:Author: Benjamin Jaedon Choi - https://github.com/saintbenjamin
:Affiliated Church: The Eulji-ro Presbyterian Church [대한예수교장로회(통합) 을지로교회]
:Address: The Eulji-ro Presbyterian Church, 24-10, Eulji-ro 20-gil, Jung-gu, Seoul 04549, South Korea
:Telephone: +82-2-2266-3070
:E-mail: euljirochurch [at] G.M.A.I.L. (replace [at] with @ and G.M.A.I.L as you understood.)
:License: MIT License with Attribution Requirement (see LICENSE file for details); Copyright (c) 2025 The Eulji-ro Presbyterian Church.

WebSocket manager for broadcasting slide data to overlay clients.

This module provides a thin wrapper around the
`websocket-client <https://pypi.org/project/websocket-client/>`_ library
to manage a single outbound WebSocket connection used by the slide controller.
It is responsible for:

- Establishing and closing the WebSocket connection
- Serializing slide dictionaries to JSON
- Sending slide data to overlay clients in real time
- Tracking basic connection state
- Performing bounded local reconnect/retry recovery

The manager remains synchronous because it is used from the GUI thread, but
it now includes small self-healing steps so that a temporarily lost local
WebSocket server does not leave the controller permanently unable to
broadcast slides.
"""

import json


class SlideWebSocketManager:
    """
    Manage a WebSocket connection for sending slide data to overlay systems.

    This class wraps a single WebSocket connection created via the
    `websocket-client <https://pypi.org/project/websocket-client/>`_ library
    and provides methods for:

    - Connecting to a WebSocket server
    - Probing the connection for local health
    - Sending slide dictionaries as JSON payloads
    - Performing one-shot reconnect/retry recovery
    - Closing the connection safely

    Attributes:
        uri (str):
            WebSocket server URI (e.g., ``ws://127.0.0.1:8765/ws``).
        ws (websocket.WebSocket | None):
            Active WebSocket connection object created by
            ``websocket.create_connection``. Set to ``None`` when disconnected
            or on connection failure.
        connect_timeout (float):
            Timeout in seconds used for connect and socket operations.
    """

    def __init__(self, uri):
        """
        Initialize the WebSocket manager.

        Args:
            uri (str):
                WebSocket server URI
                (e.g., ``ws://127.0.0.1:8765/ws``).

        Returns:
            None
        """
        self.uri = uri
        self.ws = None
        self.connect_timeout = 1.5

    def _drop_connection(self):
        """
        Dispose of the current socket object and clear connection state.

        Returns:
            None
        """
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
        self.ws = None

    def connect(self, quiet: bool = False) -> bool:
        """
        Establish a connection to the WebSocket server.

        Attempts to create a WebSocket connection using the configured URI.
        On failure, the internal connection state is cleared.

        Args:
            quiet (bool):
                If True, suppress status prints for expected background
                reconnect attempts.

        Returns:
            bool:
                True if the connection was established successfully,
                False otherwise.
        """
        self._drop_connection()

        try:
            import websocket  # pip install websocket-client

            self.ws = websocket.create_connection(
                self.uri,
                timeout=self.connect_timeout,
            )
            self.ws.settimeout(self.connect_timeout)
            if not quiet:
                print(f"[OK] Connected to WebSocket: {self.uri}")
            return True
        except Exception as e:
            if not quiet:
                print(f"[x] WebSocket connection failed: {e}")
            self.ws = None
            return False

    def probe(self) -> bool:
        """
        Check whether the existing WebSocket transport is still usable.

        A lightweight WebSocket ping frame is sent to verify that the local
        transport has not silently gone stale. If the probe fails, the socket
        is dropped so a later reconnect can start from a clean state.

        Returns:
            bool:
                True if the current socket appears healthy,
                False otherwise.
        """
        if not self.is_connected():
            return False

        try:
            self.ws.ping()
            return True
        except Exception:
            self._drop_connection()
            return False

    def ensure_healthy_connection(self, quiet: bool = True) -> bool:
        """
        Ensure that a usable WebSocket connection is available.

        This first probes the current socket. If the probe fails or no socket
        exists, it attempts a fresh reconnect.

        Args:
            quiet (bool):
                If True, suppress expected background reconnect prints.

        Returns:
            bool:
                True if a healthy connection is available after probing and
                optional reconnect, False otherwise.
        """
        if self.probe():
            return True

        return self.connect(quiet=quiet)

    def send(self, slide_dict: dict) -> bool:
        """
        Send a slide dictionary to the WebSocket server.

        The slide data is serialized to JSON using UTF-8 encoding
        (``ensure_ascii=False``) before transmission. If the existing socket
        has gone stale, this method performs one reconnect and one resend
        attempt before giving up.

        Args:
            slide_dict (dict):
                Dictionary containing slide data to send.

        Returns:
            bool:
                True if the slide payload was sent successfully,
                False otherwise.
        """
        data = json.dumps(slide_dict, ensure_ascii=False)

        if not self.ensure_healthy_connection(quiet=True):
            print("[!] Cannot send: WebSocket is not connected.")
            return False

        try:
            self.ws.send(data)
            return True
        except Exception as e:
            print(f"[!] Send failed: {e}")
            self._drop_connection()

        if not self.connect(quiet=True):
            print("[!] Reconnect failed after send failure.")
            return False

        try:
            self.ws.send(data)
            print("[i] Recovered WebSocket connection and resent current slide.")
            return True
        except Exception as e:
            print(f"[!] Resend after reconnect failed: {e}")
            self._drop_connection()
            return False

    def is_connected(self) -> bool:
        """
        Check whether the WebSocket connection is active.

        Returns:
            bool:
                True if a connected WebSocket object exists, False otherwise.
        """
        if self.ws is None:
            return False

        return bool(getattr(self.ws, "connected", False))

    def disconnect(self):
        """
        Close the WebSocket connection safely.

        Any errors during shutdown are caught and logged, and the internal
        connection state is cleared.

        Returns:
            None
        """
        if self.ws:
            try:
                self.ws.close()
                print("[OK] WebSocket closed.")
            except Exception as e:
                print(f"[!] Error closing WebSocket: {e}")
        self.ws = None