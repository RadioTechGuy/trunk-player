"""
Trunk Player v2 - WebSocket Routing
"""

from django.urls import re_path

from .consumers import RadioConsumer

websocket_urlpatterns = [
    # Specific channel subscriptions
    re_path(
        r"^ws/(?P<channel_type>tg|scan|unit|inc)/(?P<label>[\w-]+)/$",
        RadioConsumer.as_asgi(),
    ),
    # Default channel (all transmissions)
    re_path(r"^ws/$", RadioConsumer.as_asgi()),
]
