"""
Trunk Player v2 - Incident Views
"""

from django.conf import settings
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from ..models import Incident


@require_GET
def incident_list(request):
    """List all public incidents."""
    if request.user.is_authenticated:
        if request.user.is_staff:
            incidents = Incident.objects.all()
        else:
            incidents = Incident.objects.filter(
                Q(public=True) | Q(created_by=request.user)
            )
    else:
        incidents = Incident.objects.filter(public=True)

    context = {
        "incidents": incidents,
    }
    return render(request, "radio/incident_list.html", context)


@require_GET
def incident_detail(request, slug):
    """Detail view for an incident."""
    incident = get_object_or_404(Incident, slug=slug)

    # Check access
    if not incident.public:
        if not request.user.is_authenticated:
            raise Http404("Incident not found")
        if not request.user.is_staff and incident.created_by != request.user:
            raise Http404("Incident not found")

    transmissions = incident.transmissions.all().select_related(
        "system", "talkgroup_info"
    ).prefetch_related("units")

    context = {
        "incident": incident,
        "transmissions": transmissions,
        "page_title": incident.name,
        "ws_channel": f"inc-{incident.slug}",
    }
    return render(request, "radio/player.html", context)
