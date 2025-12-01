"""
Trunk Player v2 - Main Views

Core application views for the player interface.
"""

from datetime import timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from ..models import (
    System,
    TalkGroup,
    Unit,
    Transmission,
    ScanList,
    Incident,
)


def get_user_accessible_talkgroups(user):
    """Get talkgroups the user can access."""
    if not settings.ACCESS_TG_RESTRICT:
        return TalkGroup.objects.all()

    if not user.is_authenticated:
        return TalkGroup.objects.filter(is_public=True)

    try:
        return user.profile.get_accessible_talkgroups()
    except Exception:
        return TalkGroup.objects.filter(is_public=True)


def get_history_filtered_transmissions(user, queryset):
    """Filter transmissions by user's history access."""
    if user.is_authenticated:
        try:
            history_minutes = user.profile.history_limit
        except Exception:
            history_minutes = settings.ANONYMOUS_TIME
    else:
        history_minutes = settings.ANONYMOUS_TIME

    if history_minutes > 0:
        time_threshold = timezone.now() - timedelta(minutes=history_minutes)
        queryset = queryset.filter(start_datetime__gte=time_threshold)

    return queryset


@require_GET
def home(request):
    """Home page with recent transmissions."""
    if not settings.ALLOW_ANONYMOUS and not request.user.is_authenticated:
        return render(request, "radio/home_anonymous.html")

    accessible_tgs = get_user_accessible_talkgroups(request.user)

    transmissions = Transmission.objects.filter(
        talkgroup_info__in=accessible_tgs
    ).select_related("system", "talkgroup_info")[:20]

    transmissions = get_history_filtered_transmissions(request.user, transmissions)

    context = {
        "transmissions": transmissions,
        "systems": System.objects.all(),
    }
    return render(request, "radio/home.html", context)


def talkgroup_list(request):
    """List all talkgroups."""
    accessible_tgs = get_user_accessible_talkgroups(request.user)

    # Get user's favorites
    user_favorites = []
    if request.user.is_authenticated:
        try:
            user_favorites = list(request.user.profile.favorite_talkgroups.values_list("pk", flat=True))
        except Exception:
            pass

    # Group by system
    systems = System.objects.prefetch_related("talkgroups").all()

    context = {
        "systems": systems,
        "accessible_talkgroups": accessible_tgs,
        "user_favorites": user_favorites,
    }
    return render(request, "radio/talkgroup_list.html", context)


@login_required
@require_POST
def toggle_favorite_talkgroup(request, slug):
    """Toggle a talkgroup as favorite."""
    talkgroup = get_object_or_404(TalkGroup, slug=slug)
    profile = request.user.profile

    if talkgroup in profile.favorite_talkgroups.all():
        profile.favorite_talkgroups.remove(talkgroup)
        is_favorite = False
    else:
        profile.favorite_talkgroups.add(talkgroup)
        is_favorite = True

    # Return JSON for AJAX or redirect for regular form
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"is_favorite": is_favorite})

    return redirect(request.META.get("HTTP_REFERER", "talkgroup_list"))


@require_GET
def talkgroup_player(request, slug):
    """Player view for a specific talkgroup."""
    talkgroup = get_object_or_404(TalkGroup, slug=slug)

    # Check access
    accessible_tgs = get_user_accessible_talkgroups(request.user)
    if settings.ACCESS_TG_RESTRICT and talkgroup not in accessible_tgs:
        raise Http404("Talkgroup not found")

    transmissions = Transmission.objects.filter(
        talkgroup_info=talkgroup
    ).select_related("system", "talkgroup_info").prefetch_related("units")[:50]

    transmissions = get_history_filtered_transmissions(request.user, transmissions)

    context = {
        "talkgroup": talkgroup,
        "transmissions": transmissions,
        "page_title": talkgroup.display_name,
        "ws_channel": f"tg-{talkgroup.slug}",
    }
    return render(request, "radio/player.html", context)


@require_GET
def scanlist_player(request, slug):
    """Player view for a scanlist."""
    scanlist = get_object_or_404(ScanList, slug=slug)

    # Check access
    if not scanlist.public and (
        not request.user.is_authenticated or
        scanlist.created_by != request.user
    ):
        raise Http404("Scanlist not found")

    talkgroups = scanlist.talkgroups.all()
    accessible_tgs = get_user_accessible_talkgroups(request.user)

    # Filter to accessible talkgroups
    if settings.ACCESS_TG_RESTRICT:
        talkgroups = talkgroups.filter(pk__in=accessible_tgs)

    transmissions = Transmission.objects.filter(
        talkgroup_info__in=talkgroups
    ).select_related("system", "talkgroup_info").prefetch_related("units")[:50]

    transmissions = get_history_filtered_transmissions(request.user, transmissions)

    context = {
        "scanlist": scanlist,
        "talkgroups": talkgroups,
        "transmissions": transmissions,
        "page_title": scanlist.name,
        "ws_channel": f"scan-{scanlist.slug}",
    }
    return render(request, "radio/player.html", context)


@require_GET
def unit_player(request, slug):
    """Player view for a specific unit."""
    unit = get_object_or_404(Unit, slug=slug)

    transmissions = Transmission.objects.filter(
        units=unit
    ).select_related("system", "talkgroup_info").prefetch_related("units")[:50]

    # Filter by accessible talkgroups
    accessible_tgs = get_user_accessible_talkgroups(request.user)
    if settings.ACCESS_TG_RESTRICT:
        transmissions = transmissions.filter(talkgroup_info__in=accessible_tgs)

    transmissions = get_history_filtered_transmissions(request.user, transmissions)

    context = {
        "unit": unit,
        "transmissions": transmissions,
        "page_title": unit.display_name,
        "ws_channel": f"unit-{unit.slug}",
    }
    return render(request, "radio/player.html", context)


@require_GET
def transmission_detail(request, slug):
    """Detail view for a single transmission."""
    transmission = get_object_or_404(
        Transmission.objects.select_related("system", "talkgroup_info"),
        slug=slug,
    )

    # Check access
    accessible_tgs = get_user_accessible_talkgroups(request.user)
    if settings.ACCESS_TG_RESTRICT and transmission.talkgroup_info not in accessible_tgs:
        raise Http404("Transmission not found")

    # Check history limit
    if request.user.is_authenticated:
        try:
            history_minutes = request.user.profile.history_limit
        except Exception:
            history_minutes = settings.ANONYMOUS_TIME
    else:
        history_minutes = settings.ANONYMOUS_TIME

    can_play = True
    if history_minutes > 0:
        time_threshold = timezone.now() - timedelta(minutes=history_minutes)
        if transmission.start_datetime < time_threshold:
            can_play = False

    context = {
        "transmission": transmission,
        "can_play": can_play,
        "units": transmission.units.all(),
    }
    return render(request, "radio/transmission_detail.html", context)
