"""
Trunk Player v2 - WebSocket Consumers

Django Channels consumers for real-time transmission updates.
"""

import json
import logging

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

logger = logging.getLogger(__name__)


class RadioConsumer(WebsocketConsumer):
    """
    WebSocket consumer for live radio transmission updates.

    Supports subscribing to:
    - Talkgroups: ws://host/ws/tg/<slug>/
    - Scanlists: ws://host/ws/scan/<slug>/
    - Units: ws://host/ws/unit/<slug>/
    - Incidents: ws://host/ws/inc/<slug>/
    - Default (all): ws://host/ws/
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.groups = []

    def connect(self):
        """Handle WebSocket connection."""
        try:
            channel_type = self.scope["url_route"]["kwargs"].get("channel_type", "scan")
            label = self.scope["url_route"]["kwargs"].get("label", "default")
        except (KeyError, TypeError):
            # Default channel
            channel_type = "scan"
            label = "default"

        # Build channel name
        channel_name = f"livecall-{channel_type}-{label}"

        logger.info(
            "WebSocket connect: user=%s channel=%s",
            self.scope.get("user", "anonymous"),
            channel_name,
        )

        # Join channel group
        async_to_sync(self.channel_layer.group_add)(
            channel_name,
            self.channel_name,
        )
        self.groups.append(channel_name)

        # Always join default channel
        if channel_name != "livecall-scan-default":
            async_to_sync(self.channel_layer.group_add)(
                "livecall-scan-default",
                self.channel_name,
            )
            self.groups.append("livecall-scan-default")

        self.accept()

    def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        logger.info(
            "WebSocket disconnect: user=%s code=%s",
            self.scope.get("user", "anonymous"),
            close_code,
        )

        # Leave all channel groups
        for group in self.groups:
            try:
                async_to_sync(self.channel_layer.group_discard)(
                    group,
                    self.channel_name,
                )
            except Exception as e:
                logger.warning("Error leaving group %s: %s", group, e)

    def receive(self, text_data):
        """Handle incoming WebSocket message."""
        try:
            data = json.loads(text_data)

            # Handle ping/pong for keepalive
            if data.get("type") == "ping":
                self.send(text_data=json.dumps({"type": "pong"}))
                return

            # Handle subscription requests
            if data.get("type") == "subscribe":
                channel = data.get("channel")
                if channel:
                    async_to_sync(self.channel_layer.group_add)(
                        channel,
                        self.channel_name,
                    )
                    self.groups.append(channel)
                    self.send(text_data=json.dumps({
                        "type": "subscribed",
                        "channel": channel,
                    }))
                return

            # Handle unsubscribe requests
            if data.get("type") == "unsubscribe":
                channel = data.get("channel")
                if channel and channel in self.groups:
                    async_to_sync(self.channel_layer.group_discard)(
                        channel,
                        self.channel_name,
                    )
                    self.groups.remove(channel)
                    self.send(text_data=json.dumps({
                        "type": "unsubscribed",
                        "channel": channel,
                    }))
                return

        except json.JSONDecodeError:
            logger.warning("Invalid JSON received: %s", text_data[:100])
        except Exception as e:
            logger.exception("Error processing message: %s", e)

    def radio_message(self, event):
        """Handle radio_message event from channel layer."""
        message = event.get("text", "{}")

        # Send message to WebSocket
        self.send(text_data=message)

    def transmission_created(self, event):
        """Handle new transmission notification."""
        data = event.get("data", {})

        self.send(text_data=json.dumps({
            "type": "transmission",
            "data": data,
        }))
