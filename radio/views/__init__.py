"""
Trunk Player v2 - Views Package

All view functions and classes are imported here for convenience.
"""

from .main import (
    home,
    talkgroup_list,
    talkgroup_player,
    scanlist_player,
    unit_player,
    transmission_detail,
    toggle_favorite_talkgroup,
)

from .user import (
    profile,
    scanlist_list,
    scanlist_create,
    scanlist_edit,
)

from .incidents import (
    incident_list,
    incident_detail,
)

from . import auth
from .pwa import manifest as pwa_manifest, service_worker as pwa_service_worker

__all__ = [
    # Main views
    "home",
    "talkgroup_list",
    "talkgroup_player",
    "scanlist_player",
    "unit_player",
    "transmission_detail",
    # User views
    "profile",
    "scanlist_list",
    "scanlist_create",
    "scanlist_edit",
    # Incident views
    "incident_list",
    "incident_detail",
    # Auth module
    "auth",
]
