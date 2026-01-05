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

This module provides a thin wrapper around the `websocket-client <https://pypi.org/project/websocket-client/>`_ library
to manage a single outbound WebSocket connection used by the slide controller.
It is responsible for:

- Establishing and closing the WebSocket connection
- Serializing slide dictionaries to JSON
- Sending slide data to overlay clients in real time
- Tracking basic connection state

The manager is intentionally lightweight and synchronous, as it is used
from the GUI thread with short-lived send operations.
"""

import json

class SlideWebSocketManager:
    """
    Manages a WebSocket connection for sending slide data to overlay systems.

    This class wraps a single WebSocket connection created via the
    `websocket-client <https://pypi.org/project/websocket-client/>`_ library and provides simple methods for:

    - Connecting to a WebSocket server
    - Sending slide dictionaries as JSON payloads
    - Querying connection state
    - Closing the connection safely

    It intentionally does **not** implement reconnection logic, background threads,
    or retry loops. Higher-level controller components are expected to manage
    lifecycle and recovery behavior if needed.

    Attributes:
        uri (str):
            WebSocket server URI (e.g., ``ws://127.0.0.1:8765/ws``).
        ws (websocket.WebSocket | None):
            Active WebSocket connection object created by ``websocket.create_connection``.
            Set to ``None`` when disconnected or on connection failure.
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

    def connect(self):
        """
        Establish a connection to the WebSocket server.

        Attempts to create a WebSocket connection using the configured URI.
        On failure, the internal connection state is cleared.

        Returns:
            None
        """
        try:
            import websocket  # pip install websocket-client
            self.ws = websocket.create_connection(self.uri)
            print(f"[✓] Connected to WebSocket: {self.uri}")
        except Exception as e:
            print(f"[x] WebSocket connection failed: {e}")
            self.ws = None

    def send(self, slide_dict: dict):
        """
        Send a slide dictionary to the WebSocket server.

        The slide data is serialized to JSON using UTF-8 encoding
        (``ensure_ascii=False``) before transmission.

        Args:
            slide_dict (dict):
                Dictionary containing slide data to send.

        Returns:
            None
        """
        if not self.ws:
            print("[!] Cannot send: WebSocket is not connected.")
            return
        try:
            data = json.dumps(slide_dict, ensure_ascii=False)
            self.ws.send(data)
            # print("[→] Sent slide")
        except Exception as e:
            print(f"[!] Send failed: {e}")
            self.ws = None  # Optional: trigger reconnect on next attempt

    def is_connected(self):
        """
        Check whether the WebSocket connection is active.

        Returns:
            bool:
                True if a WebSocket connection exists, False otherwise.
        """
        return self.ws is not None

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
                print("[✓] WebSocket closed.")
            except Exception as e:
                print(f"[!] Error closing WebSocket: {e}")
        self.ws = None