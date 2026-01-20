"""
Trunk Player v2 - Context Processors

Template context processors for site-wide settings.
"""

from django.conf import settings


def site_settings(request):
    """
    Add site settings to template context.
    """
    return {
        "SITE_TITLE": settings.SITE_TITLE,
        "SITE_EMAIL": settings.SITE_EMAIL,
        "AUDIO_URL_BASE": settings.AUDIO_URL_BASE,
        "ALLOW_ANONYMOUS": settings.ALLOW_ANONYMOUS,
        "OPEN_REGISTRATION": settings.OPEN_REGISTRATION,
        "FIEF_ENABLED": settings.FIEF_ENABLED,
        "DEBUG": settings.DEBUG,
    }


def user_favorites(request):
    """
    Add user's favorite talkgroups and scanlists to template context.
    """
    favorite_talkgroups = []
    user_scanlists = []
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
            favorite_talkgroups = profile.favorite_talkgroups.select_related('system').all()[:10]
        except Exception:
            pass
        # Get user's own scanlists
        try:
            user_scanlists = request.user.scanlists.all()[:10]
        except Exception:
            pass
    return {
        "favorite_talkgroups": favorite_talkgroups,
        "user_scanlists": user_scanlists,
    }
