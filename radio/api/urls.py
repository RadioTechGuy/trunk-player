"""
Trunk Player v2 - API URL Configuration
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    SystemViewSet,
    TalkGroupViewSet,
    UnitViewSet,
    TransmissionViewSet,
    TranscriptionViewSet,
    PlanViewSet,
    ScanListViewSet,
    IncidentViewSet,
    ProfileViewSet,
    TransmissionImportView,
    transmission_by_talkgroup,
    transmission_by_unit,
    transmission_by_scanlist,
    transmission_by_incident,
)

# Create router for viewsets
router = DefaultRouter()
router.register(r"systems", SystemViewSet, basename="system")
router.register(r"talkgroups", TalkGroupViewSet, basename="talkgroup")
router.register(r"units", UnitViewSet, basename="unit")
router.register(r"transmissions", TransmissionViewSet, basename="transmission")
router.register(r"transcriptions", TranscriptionViewSet, basename="transcription")
router.register(r"plans", PlanViewSet, basename="plan")
router.register(r"scanlists", ScanListViewSet, basename="scanlist")
router.register(r"incidents", IncidentViewSet, basename="incident")
router.register(r"profile", ProfileViewSet, basename="profile")

urlpatterns = [
    # Router URLs
    path("", include(router.urls)),

    # Transmission import endpoint
    path(
        "import_transmission/",
        TransmissionImportView.as_view(),
        name="import_transmission",
    ),

    # Filter endpoints (for compatibility)
    path(
        "tg/<slug:slug>/",
        transmission_by_talkgroup,
        name="api_transmission_by_talkgroup",
    ),
    path(
        "unit/<slug:slug>/",
        transmission_by_unit,
        name="api_transmission_by_unit",
    ),
    path(
        "scan/<slug:slug>/",
        transmission_by_scanlist,
        name="api_transmission_by_scanlist",
    ),
    path(
        "inc/<slug:slug>/",
        transmission_by_incident,
        name="api_transmission_by_incident",
    ),
]
