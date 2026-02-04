"""
Trunk Player v2 - Template Tags
"""

from django import template
from django.conf import settings
from django.contrib.auth.models import User

from radio.models import Profile

register = template.Library()


@register.simple_tag()
def settings_anonymous_time():
    """Return anonymous user time limit setting."""
    return getattr(settings, "ANONYMOUS_TIME", 0)


@register.simple_tag()
def get_user_time(user):
    """Get user's history time limit based on their plan."""
    history = {}

    if user.is_authenticated:
        try:
            user_profile = Profile.objects.get(user=user)
        except Profile.DoesNotExist:
            user_profile = None
    else:
        # Anonymous user
        try:
            anon_user = User.objects.get(username="ANONYMOUS_USER")
            user_profile = Profile.objects.get(user=anon_user)
        except (User.DoesNotExist, Profile.DoesNotExist):
            user_profile = None

    if user_profile and user_profile.plan:
        history["minutes"] = user_profile.plan.history
    else:
        history["minutes"] = getattr(settings, "ANONYMOUS_TIME", 720)

    history["hours"] = history["minutes"] / 60

    # Format display string
    if history["minutes"] == 0:
        history["display"] = "unlimited"
    elif history["minutes"] % 60 == 0:
        if history["minutes"] % 1440 == 0:
            history["display"] = f"{history['minutes'] // 1440} days"
        else:
            history["display"] = f"{history['minutes'] // 60} hours"
    else:
        history["display"] = f"{history['minutes']} minutes"

    return history


@register.simple_tag()
def get_setting(value):
    """Get a setting value if it's in the visible settings list."""
    visible_settings = getattr(settings, "VISIBLE_SETTINGS", [])
    if value in visible_settings:
        return getattr(settings, value, None)
    return None


@register.simple_tag()
def site_title():
    """Return the site title."""
    return getattr(settings, "SITE_TITLE", "Trunk Player")


@register.simple_tag()
def site_email():
    """Return the site email."""
    return getattr(settings, "SITE_EMAIL", "")


@register.filter
def format_frequency(freq):
    """Format frequency in Hz to MHz display."""
    if freq:
        return f"{freq / 1000000:07.3f}"
    return ""


@register.filter
def format_duration(seconds):
    """Format duration in seconds to mm:ss."""
    if seconds:
        m, s = divmod(int(seconds), 60)
        return f"{m:02d}:{s:02d}"
    return "00:00"
