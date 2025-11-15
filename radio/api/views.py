"""
Trunk Player v2 - API Views

Django REST Framework viewsets and views for the API.
"""

import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import (
    System,
    TalkGroup,
    Unit,
    Transmission,
    TransmissionUnit,
    Transcription,
    Plan,
    TalkGroupAccess,
    Profile,
    ScanList,
    Incident,
)
from ..serializers import (
    SystemSerializer,
    TalkGroupSerializer,
    TalkGroupMinimalSerializer,
    UnitSerializer,
    TransmissionSerializer,
    TransmissionListSerializer,
    TransmissionImportSerializer,
    TranscriptionSerializer,
    PlanSerializer,
    TalkGroupAccessSerializer,
    ProfileSerializer,
    ScanListSerializer,
    ScanListMinimalSerializer,
    IncidentSerializer,
    IncidentMinimalSerializer,
)

logger = logging.getLogger(__name__)


# =============================================================================
# PERMISSIONS
# =============================================================================

class IsOwnerOrReadOnly(permissions.BasePermission):
    """Object-level permission to allow owners to edit their objects."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions only for owner
        if hasattr(obj, "created_by"):
            return obj.created_by == request.user
        if hasattr(obj, "user"):
            return obj.user == request.user
        return False


class HasTransmissionImportToken(permissions.BasePermission):
    """Permission for transmission import API."""

    def has_permission(self, request, view):
        token = request.headers.get("Authorization", "").replace("Token ", "")
        return token == settings.ADD_TRANS_AUTH_TOKEN


# =============================================================================
# MIXINS
# =============================================================================

class TalkGroupAccessMixin:
    """Mixin to filter queryset by user's talkgroup access."""

    def get_accessible_talkgroups(self, user):
        """Get talkgroups the user can access."""
        if not settings.ACCESS_TG_RESTRICT:
            return TalkGroup.objects.all()

        if not user.is_authenticated:
            # Anonymous users get public talkgroups
            return TalkGroup.objects.filter(is_public=True)

        try:
            return user.profile.get_accessible_talkgroups()
        except Profile.DoesNotExist:
            return TalkGroup.objects.filter(is_public=True)


class HistoryLimitMixin:
    """Mixin to filter transmissions by user's history limit."""

    def apply_history_limit(self, queryset, user):
        """Filter queryset by user's history access."""
        if user.is_authenticated:
            try:
                history_minutes = user.profile.history_limit
            except Profile.DoesNotExist:
                history_minutes = settings.ANONYMOUS_TIME
        else:
            history_minutes = settings.ANONYMOUS_TIME

        if history_minutes > 0:
            time_threshold = timezone.now() - timedelta(minutes=history_minutes)
            queryset = queryset.filter(start_datetime__gte=time_threshold)

        return queryset


# =============================================================================
# CORE RADIO VIEWSETS
# =============================================================================

class SystemViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for radio systems."""

    queryset = System.objects.all()
    serializer_class = SystemSerializer
    lookup_field = "slug"


class TalkGroupViewSet(TalkGroupAccessMixin, viewsets.ReadOnlyModelViewSet):
    """API endpoint for talkgroups."""

    serializer_class = TalkGroupSerializer
    lookup_field = "slug"

    def get_queryset(self):
        queryset = self.get_accessible_talkgroups(self.request.user)
        queryset = queryset.select_related("system")

        # Filter by system
        system = self.request.query_params.get("system")
        if system:
            queryset = queryset.filter(system__slug=system)

        return queryset


class UnitViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for radio units."""

    queryset = Unit.objects.select_related("system")
    serializer_class = UnitSerializer
    lookup_field = "slug"

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by system
        system = self.request.query_params.get("system")
        if system:
            queryset = queryset.filter(system__slug=system)

        return queryset


class TransmissionViewSet(
    TalkGroupAccessMixin, HistoryLimitMixin, viewsets.ReadOnlyModelViewSet
):
    """API endpoint for transmissions."""

    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action == "list":
            return TransmissionListSerializer
        return TransmissionSerializer

    def get_queryset(self):
        user = self.request.user
        accessible_tgs = self.get_accessible_talkgroups(user)

        queryset = Transmission.objects.filter(
            talkgroup_info__in=accessible_tgs
        ).select_related("system", "talkgroup_info").prefetch_related("units")

        # Apply history limit
        queryset = self.apply_history_limit(queryset, user)

        # Filter by talkgroup
        talkgroup = self.request.query_params.get("talkgroup")
        if talkgroup:
            queryset = queryset.filter(talkgroup_info__slug=talkgroup)

        # Filter by system
        system = self.request.query_params.get("system")
        if system:
            queryset = queryset.filter(system__slug=system)

        # Filter by unit
        unit = self.request.query_params.get("unit")
        if unit:
            queryset = queryset.filter(units__slug=unit)

        # Filter by emergency
        emergency = self.request.query_params.get("emergency")
        if emergency and emergency.lower() == "true":
            queryset = queryset.filter(emergency=True)

        # Filter by scanlist
        scanlist = self.request.query_params.get("scanlist")
        if scanlist:
            queryset = queryset.filter(talkgroup_info__scanlists__slug=scanlist)

        # Filter by incident
        incident = self.request.query_params.get("incident")
        if incident:
            queryset = queryset.filter(incidents__slug=incident)

        return queryset.distinct()


class TranscriptionViewSet(viewsets.ModelViewSet):
    """API endpoint for transcriptions."""

    queryset = Transcription.objects.select_related("transmission")
    serializer_class = TranscriptionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(created_by=self.request.user)


# =============================================================================
# USER & ACCESS VIEWSETS
# =============================================================================

class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for user plans."""

    queryset = Plan.objects.all()
    serializer_class = PlanSerializer


class ScanListViewSet(viewsets.ModelViewSet):
    """API endpoint for scan lists."""

    serializer_class = ScanListSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    lookup_field = "slug"

    def get_queryset(self):
        user = self.request.user

        if user.is_authenticated:
            # User's own lists + public lists
            return ScanList.objects.filter(
                Q(created_by=user) | Q(public=True)
            ).select_related("created_by").prefetch_related("talkgroups")
        else:
            # Anonymous only sees public lists
            return ScanList.objects.filter(
                public=True
            ).select_related("created_by").prefetch_related("talkgroups")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class IncidentViewSet(viewsets.ModelViewSet):
    """API endpoint for incidents."""

    serializer_class = IncidentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    lookup_field = "slug"

    def get_queryset(self):
        user = self.request.user

        if user.is_authenticated:
            if user.is_staff:
                return Incident.objects.all().prefetch_related("transmissions")
            # User's own incidents + public incidents
            return Incident.objects.filter(
                Q(created_by=user) | Q(public=True)
            ).prefetch_related("transmissions")
        else:
            return Incident.objects.filter(
                public=True
            ).prefetch_related("transmissions")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ProfileViewSet(viewsets.ModelViewSet):
    """API endpoint for user profiles (current user only)."""

    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Profile.objects.filter(user=self.request.user)

    def get_object(self):
        return self.request.user.profile


# =============================================================================
# TRANSMISSION IMPORT API
# =============================================================================

class TransmissionImportView(APIView):
    """
    API endpoint for importing transmissions from Trunk Recorder.

    POST /api/v2/import_transmission/
    """

    permission_classes = [HasTransmissionImportToken]

    def post(self, request):
        serializer = TransmissionImportSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data

        try:
            # Get or create system
            system, _ = System.objects.get_or_create(name=data["system"])

            # Get or create talkgroup
            talkgroup, _ = TalkGroup.objects.get_or_create(
                system=system,
                dec_id=data["talkgroup"],
                defaults={"alpha_tag": f"TG {data['talkgroup']}"},
            )

            # Parse timestamps
            start_datetime = datetime.fromtimestamp(
                data["start_time"], tz=timezone.get_current_timezone()
            )
            end_datetime = datetime.fromtimestamp(
                data["stop_time"], tz=timezone.get_current_timezone()
            )

            # Create transmission
            transmission = Transmission.objects.create(
                system=system,
                talkgroup_info=talkgroup,
                talkgroup=data["talkgroup"],
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                audio_file=data["audio_filename"],
                audio_file_url_path=data.get("audio_file_url_path", "/"),
                audio_file_type=data.get("audio_file_type", "mp3"),
                play_length=data.get("audio_file_play_length", 0),
                has_audio=data.get("has_audio", True),
                emergency=data.get("emergency", False),
                freq=data.get("freq"),
            )

            # Add units
            for idx, unit_data in enumerate(data.get("srcList", [])):
                unit_id = unit_data.get("src")
                if unit_id:
                    unit, _ = Unit.objects.get_or_create(
                        system=system,
                        dec_id=unit_id,
                    )
                    TransmissionUnit.objects.create(
                        transmission=transmission,
                        unit=unit,
                        order=idx,
                    )

            return Response(
                {"status": "success", "transmission_id": transmission.pk},
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.exception("Error importing transmission")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# =============================================================================
# FILTER ENDPOINTS (for legacy compatibility)
# =============================================================================

@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def transmission_by_talkgroup(request, slug):
    """Get transmissions for a specific talkgroup."""
    try:
        talkgroup = TalkGroup.objects.get(slug=slug)
    except TalkGroup.DoesNotExist:
        return Response(
            {"error": "Talkgroup not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    transmissions = Transmission.objects.filter(
        talkgroup_info=talkgroup
    ).select_related("system", "talkgroup_info")[:50]

    serializer = TransmissionListSerializer(
        transmissions, many=True, context={"request": request}
    )
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def transmission_by_unit(request, slug):
    """Get transmissions for a specific unit."""
    try:
        unit = Unit.objects.get(slug=slug)
    except Unit.DoesNotExist:
        return Response(
            {"error": "Unit not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    transmissions = Transmission.objects.filter(
        units=unit
    ).select_related("system", "talkgroup_info")[:50]

    serializer = TransmissionListSerializer(
        transmissions, many=True, context={"request": request}
    )
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def transmission_by_scanlist(request, slug):
    """Get transmissions for a specific scanlist."""
    try:
        scanlist = ScanList.objects.get(slug=slug)
    except ScanList.DoesNotExist:
        return Response(
            {"error": "Scanlist not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    transmissions = Transmission.objects.filter(
        talkgroup_info__in=scanlist.talkgroups.all()
    ).select_related("system", "talkgroup_info")[:50]

    serializer = TransmissionListSerializer(
        transmissions, many=True, context={"request": request}
    )
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def transmission_by_incident(request, slug):
    """Get transmissions for a specific incident."""
    try:
        incident = Incident.objects.get(slug=slug)
    except Incident.DoesNotExist:
        return Response(
            {"error": "Incident not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    transmissions = incident.transmissions.all().select_related(
        "system", "talkgroup_info"
    )

    serializer = TransmissionListSerializer(
        transmissions, many=True, context={"request": request}
    )
    return Response(serializer.data)
