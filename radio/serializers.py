"""
Trunk Player v2 - API Serializers

Django REST Framework serializers for all API endpoints.
"""

from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import serializers

from .models import (
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


# =============================================================================
# CORE RADIO SERIALIZERS
# =============================================================================

class SystemSerializer(serializers.ModelSerializer):
    """Serializer for radio systems."""

    class Meta:
        model = System
        fields = (
            "id",
            "name",
            "description",
            "slug",
            "created_at",
        )
        read_only_fields = ("id", "slug", "created_at")


class TalkGroupSerializer(serializers.ModelSerializer):
    """Serializer for talkgroups."""

    system_name = serializers.CharField(source="system.name", read_only=True)
    url = serializers.SerializerMethodField()

    class Meta:
        model = TalkGroup
        fields = (
            "id",
            "url",
            "dec_id",
            "alpha_tag",
            "common_name",
            "description",
            "slug",
            "system",
            "system_name",
            "is_public",
            "last_transmission",
            "recent_usage",
        )
        read_only_fields = ("id", "slug", "last_transmission", "recent_usage")

    def get_url(self, obj):
        return obj.get_absolute_url()


class TalkGroupMinimalSerializer(serializers.ModelSerializer):
    """Minimal serializer for talkgroup references."""

    class Meta:
        model = TalkGroup
        fields = ("id", "dec_id", "alpha_tag", "slug")


class UnitSerializer(serializers.ModelSerializer):
    """Serializer for radio units."""

    system_name = serializers.CharField(source="system.name", read_only=True)
    url = serializers.SerializerMethodField()

    class Meta:
        model = Unit
        fields = (
            "id",
            "url",
            "dec_id",
            "description",
            "unit_type",
            "unit_number",
            "slug",
            "system",
            "system_name",
        )
        read_only_fields = ("id", "slug")

    def get_url(self, obj):
        return obj.get_absolute_url()


class UnitMinimalSerializer(serializers.ModelSerializer):
    """Minimal serializer for unit references."""

    class Meta:
        model = Unit
        fields = ("id", "dec_id", "description")


class TranscriptionSerializer(serializers.ModelSerializer):
    """Serializer for transcriptions."""

    class Meta:
        model = Transcription
        fields = (
            "id",
            "text",
            "is_automated",
            "confidence",
            "language",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class TransmissionSerializer(serializers.ModelSerializer):
    """Serializer for transmissions."""

    talkgroup_info = TalkGroupMinimalSerializer(read_only=True)
    units = UnitMinimalSerializer(many=True, read_only=True)
    transcription = TranscriptionSerializer(read_only=True)
    audio_file = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    class Meta:
        model = Transmission
        fields = (
            "id",
            "url",
            "slug",
            "start_datetime",
            "local_start_datetime",
            "end_datetime",
            "play_length",
            "print_play_length",
            "audio_file",
            "audio_url",
            "audio_file_type",
            "has_audio",
            "system",
            "talkgroup",
            "talkgroup_info",
            "tg_name",
            "freq",
            "freq_mhz",
            "units",
            "emergency",
            "transcription",
        )
        read_only_fields = ("id", "slug")

    def get_url(self, obj):
        return obj.get_absolute_url()

    def get_audio_file(self, obj):
        """Check if user can access audio based on history limits."""
        request = self.context.get("request")
        if not request:
            return str(obj.audio_file)

        user = request.user

        # Get history limit
        if user.is_authenticated:
            try:
                history_minutes = user.profile.history_limit
            except Exception:
                history_minutes = settings.ANONYMOUS_TIME
        else:
            history_minutes = settings.ANONYMOUS_TIME

        # Check if within allowed history
        if history_minutes > 0:
            time_threshold = timezone.now() - timedelta(minutes=history_minutes)
            if obj.start_datetime < time_threshold:
                return None

        return str(obj.audio_file)


class TransmissionListSerializer(serializers.ModelSerializer):
    """Lighter serializer for transmission lists."""

    talkgroup_info = TalkGroupMinimalSerializer(read_only=True)

    class Meta:
        model = Transmission
        fields = (
            "id",
            "slug",
            "start_datetime",
            "local_start_datetime",
            "play_length",
            "print_play_length",
            "audio_url",
            "talkgroup",
            "talkgroup_info",
            "emergency",
            "has_audio",
        )


# =============================================================================
# USER & ACCESS SERIALIZERS
# =============================================================================

class PlanSerializer(serializers.ModelSerializer):
    """Serializer for user plans."""

    class Meta:
        model = Plan
        fields = (
            "id",
            "name",
            "description",
            "history",
            "is_default",
        )
        read_only_fields = ("id",)


class TalkGroupAccessSerializer(serializers.ModelSerializer):
    """Serializer for talkgroup access groups."""

    talkgroups = TalkGroupMinimalSerializer(many=True, read_only=True)

    class Meta:
        model = TalkGroupAccess
        fields = (
            "id",
            "name",
            "description",
            "talkgroups",
            "default_group",
            "default_new_talkgroups",
        )
        read_only_fields = ("id",)


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profiles."""

    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)
    plan = PlanSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = (
            "id",
            "username",
            "email",
            "plan",
            "show_unit_ids",
            "is_approved",
        )
        read_only_fields = ("id", "username", "email", "plan", "is_approved")


class ScanListSerializer(serializers.ModelSerializer):
    """Serializer for scan lists."""

    created_by_username = serializers.CharField(
        source="created_by.username", read_only=True
    )
    talkgroups = TalkGroupMinimalSerializer(many=True, read_only=True)
    talkgroup_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=TalkGroup.objects.all(),
        source="talkgroups",
        write_only=True,
        required=False,
    )
    url = serializers.SerializerMethodField()

    class Meta:
        model = ScanList
        fields = (
            "id",
            "url",
            "name",
            "slug",
            "description",
            "created_by",
            "created_by_username",
            "talkgroups",
            "talkgroup_ids",
            "public",
            "created_at",
        )
        read_only_fields = ("id", "slug", "created_by", "created_at")

    def get_url(self, obj):
        return obj.get_absolute_url()

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class ScanListMinimalSerializer(serializers.ModelSerializer):
    """Minimal serializer for scan list references."""

    class Meta:
        model = ScanList
        fields = ("id", "name", "slug", "description")


# =============================================================================
# INCIDENT SERIALIZERS
# =============================================================================

class IncidentSerializer(serializers.ModelSerializer):
    """Serializer for incidents."""

    transmissions = TransmissionListSerializer(many=True, read_only=True)
    transmission_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Transmission.objects.all(),
        source="transmissions",
        write_only=True,
        required=False,
    )
    created_by_username = serializers.CharField(
        source="created_by.username", read_only=True
    )
    url = serializers.SerializerMethodField()

    class Meta:
        model = Incident
        fields = (
            "id",
            "url",
            "name",
            "slug",
            "description",
            "transmissions",
            "transmission_ids",
            "public",
            "created_by",
            "created_by_username",
            "created_at",
        )
        read_only_fields = ("id", "slug", "created_by", "created_at")

    def get_url(self, obj):
        return obj.get_absolute_url()

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class IncidentMinimalSerializer(serializers.ModelSerializer):
    """Minimal serializer for incident references."""

    class Meta:
        model = Incident
        fields = ("id", "name", "slug")


# =============================================================================
# TRANSMISSION IMPORT SERIALIZER
# =============================================================================

class TransmissionImportSerializer(serializers.Serializer):
    """Serializer for importing transmissions from Trunk Recorder."""

    system = serializers.CharField()
    talkgroup = serializers.IntegerField()
    start_time = serializers.FloatField()
    stop_time = serializers.FloatField()
    audio_filename = serializers.CharField()
    audio_file_url_path = serializers.CharField(required=False, default="/")
    audio_file_type = serializers.CharField(required=False, default="mp3")
    audio_file_play_length = serializers.FloatField(required=False, default=0)
    has_audio = serializers.BooleanField(required=False, default=True)
    emergency = serializers.BooleanField(required=False, default=False)
    freq = serializers.IntegerField(required=False)
    srcList = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list,
    )
