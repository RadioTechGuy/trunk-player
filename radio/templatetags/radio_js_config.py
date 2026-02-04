"""
Trunk Player v2 - JavaScript Configuration Template Tag
"""

import json

from django import template
from django.conf import settings

from radio import __fullversion__ as VERSION

register = template.Library()


@register.simple_tag()
def trunkplayer_js_config(user):
    """Build JSON configuration for JavaScript frontend."""
    js_settings = getattr(settings, "JS_SETTINGS", [])
    js_json = {}

    # Include configured settings
    for setting in js_settings:
        js_json[setting] = getattr(settings, setting, "")

    # User info
    js_json["user_is_staff"] = user.is_staff
    js_json["user_is_authenticated"] = user.is_authenticated

    # Permissions
    js_json["radio_change_unit"] = user.has_perm("radio.change_unit")
    js_json["download_audio"] = user.has_perm("radio.download_audio")

    # Version
    js_json["VERSION"] = VERSION

    return json.dumps(js_json)
