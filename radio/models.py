"""
Trunk Player v2 - Database Models

Simplified model structure focusing on core radio functionality
with support for transcriptions, user access control, and incidents.
"""

import json
import uuid
from urllib.parse import quote, urljoin

from asgiref.sync import async_to_sync
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


# =============================================================================
# CHOICES / ENUMS
# =============================================================================

class UnitType(models.TextChoices):
    MOBILE = "M", "Mobile"
    PORTABLE = "P", "Portable"
    BASE = "B", "Base Station"
    DISPATCH = "D", "Dispatch"


class AudioFileType(models.TextChoices):
    MP3 = "mp3", "MP3"
    WAV = "wav", "WAV"
    M4A = "m4a", "M4A"


# =============================================================================
# CORE RADIO MODELS
# =============================================================================

class System(models.Model):
    """
    A trunked radio system. Multiple systems can be tracked,
    each with their own talkgroups and units.
    """
    name = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "System"
        verbose_name_plural = "Systems"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class TalkGroup(models.Model):
    """
    A talkgroup within a radio system. Talkgroup IDs (dec_id) are unique
    within each system but may overlap across different systems.
    """
    system = models.ForeignKey(
        System,
        on_delete=models.CASCADE,
        related_name="talkgroups"
    )
    dec_id = models.IntegerField(
        verbose_name="Decimal ID",
        help_text="Talkgroup decimal ID"
    )
    alpha_tag = models.CharField(
        max_length=50,
        blank=True,
        help_text="Short identifier (e.g., 'PD Disp')"
    )
    common_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Common name for display"
    )
    description = models.TextField(blank=True)
    slug = models.SlugField(max_length=100, blank=True)

    # Access control
    is_public = models.BooleanField(
        default=True,
        help_text="If true, included in default talkgroup access"
    )

    # Usage tracking
    last_transmission = models.DateTimeField(null=True, blank=True)
    recent_usage = models.IntegerField(
        default=0,
        help_text="Transmission count in recent time window"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["alpha_tag"]
        verbose_name = "Talk Group"
        verbose_name_plural = "Talk Groups"
        constraints = [
            models.UniqueConstraint(
                fields=["dec_id", "system"],
                name="unique_talkgroup_per_system"
            )
        ]
        indexes = [
            models.Index(fields=["dec_id", "system"]),
            models.Index(fields=["slug"]),
            models.Index(fields=["last_transmission"]),
        ]

    def __str__(self):
        if self.alpha_tag:
            return self.alpha_tag
        return f"TG {self.dec_id}"

    def save(self, *args, **kwargs):
        if not self.slug:
            # Include system slug for uniqueness across systems
            tg_part = slugify(self.alpha_tag or f"tg-{self.dec_id}")
            if self.system_id:
                self.slug = f"{self.system.slug}-{tg_part}"
            else:
                self.slug = tg_part
        if not self.last_transmission:
            self.last_transmission = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("talkgroup_detail", kwargs={"slug": self.slug})

    @property
    def display_name(self):
        """Return the best available display name."""
        return self.common_name or self.alpha_tag or f"TG {self.dec_id}"


class Unit(models.Model):
    """
    A radio unit (mobile, portable, base station, or dispatch position).
    Units are identified by their decimal ID within a system.
    """
    system = models.ForeignKey(
        System,
        on_delete=models.CASCADE,
        related_name="units"
    )
    dec_id = models.IntegerField(
        verbose_name="Decimal ID",
        help_text="Unit decimal ID"
    )
    description = models.CharField(
        max_length=100,
        blank=True,
        help_text="Unit description or callsign"
    )
    unit_type = models.CharField(
        max_length=1,
        choices=UnitType.choices,
        default=UnitType.MOBILE,
        blank=True
    )
    unit_number = models.CharField(
        max_length=20,
        blank=True,
        help_text="Unit number (e.g., 'E-51', 'Car 42')"
    )
    slug = models.SlugField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["system", "dec_id"]
        verbose_name = "Unit"
        verbose_name_plural = "Units"
        constraints = [
            models.UniqueConstraint(
                fields=["dec_id", "system"],
                name="unique_unit_per_system"
            )
        ]
        indexes = [
            models.Index(fields=["dec_id", "system"]),
            models.Index(fields=["slug"]),
        ]

    def __str__(self):
        if self.description:
            return self.description
        return str(self.dec_id)

    def save(self, *args, **kwargs):
        if not self.slug:
            unit_part = slugify(self.description or str(self.dec_id))
            if self.system_id:
                self.slug = f"{self.system.slug}-{unit_part}"
            else:
                self.slug = unit_part
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("unit_detail", kwargs={"slug": self.slug})

    @property
    def display_name(self):
        """Return the best available display name."""
        return self.description or self.unit_number or f"Unit {self.dec_id}"


class Transmission(models.Model):
    """
    A recorded radio transmission with audio file and metadata.
    """
    slug = models.UUIDField(
        db_index=True,
        default=uuid.uuid4,
        editable=False
    )

    # Timing
    start_datetime = models.DateTimeField(db_index=True)
    end_datetime = models.DateTimeField(null=True, blank=True)
    play_length = models.FloatField(
        default=0,
        help_text="Audio duration in seconds"
    )

    # Audio file
    audio_file = models.CharField(
        max_length=255,
        help_text="Audio filename"
    )
    audio_file_url_path = models.CharField(
        max_length=512,
        blank=True,
        default="/",
        help_text="Full URL path if different from default"
    )
    audio_file_type = models.CharField(
        max_length=10,
        choices=AudioFileType.choices,
        default=AudioFileType.MP3
    )
    has_audio = models.BooleanField(
        default=True,
        help_text="Whether audio file is available"
    )

    # Radio metadata
    system = models.ForeignKey(
        System,
        on_delete=models.CASCADE,
        related_name="transmissions"
    )
    talkgroup_info = models.ForeignKey(
        TalkGroup,
        on_delete=models.CASCADE,
        related_name="transmissions"
    )
    talkgroup = models.IntegerField(
        help_text="Talkgroup decimal ID (preserved even if TG deleted)"
    )
    freq = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Transmission frequency in Hz"
    )

    # Units involved in transmission
    units = models.ManyToManyField(
        Unit,
        through="TransmissionUnit",
        related_name="transmissions",
        blank=True
    )

    # Flags
    emergency = models.BooleanField(
        default=False,
        help_text="Emergency transmission flag"
    )
    from_default_source = models.BooleanField(
        default=True,
        help_text="From primary recording source"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-pk"]
        verbose_name = "Transmission"
        verbose_name_plural = "Transmissions"
        indexes = [
            models.Index(fields=["-start_datetime"]),
            models.Index(fields=["system", "-start_datetime"]),
            models.Index(fields=["talkgroup_info", "-start_datetime"]),
            models.Index(fields=["emergency", "-start_datetime"]),
        ]
        permissions = (
            ("download_audio", "Can download audio clips"),
        )

    def __str__(self):
        return f"{self.talkgroup} {self.start_datetime}"

    def get_absolute_url(self):
        return reverse("transmission_detail", kwargs={"slug": self.slug})

    @property
    def audio_url(self):
        """Return full URL to audio file."""
        base_path = settings.AUDIO_URL_BASE
        return urljoin(base_path, self.audio_file_url_path.lstrip("/"))

    @property
    def local_start_datetime(self):
        """Return localized datetime string."""
        return timezone.localtime(self.start_datetime).strftime(
            settings.TRANS_DATETIME_FORMAT
        )

    def freq_mhz(self):
        """Return frequency in MHz."""
        if self.freq:
            return f"{self.freq / 1000000:07.3f}"
        return None

    def print_play_length(self):
        """Return formatted duration string."""
        m, s = divmod(int(self.play_length), 60)
        return f"{m:02d}:{s:02d}"

    def tg_name(self):
        """Return talkgroup display name."""
        if self.talkgroup_info.common_name:
            return self.talkgroup_info.common_name
        return self.talkgroup_info.alpha_tag

    def as_dict(self):
        """Return transmission data as dictionary for WebSocket."""
        return {
            "start_datetime": str(self.start_datetime),
            "talkgroup_slug": self.talkgroup_info.slug,
            "talkgroup_dec_id": str(self.talkgroup_info.dec_id),
        }

    def save(self, *args, **kwargs):
        if settings.FIX_AUDIO_NAME:
            file_name = str(self.audio_file)
            self.audio_file = file_name.replace("+", "%2B")
        super().save(*args, **kwargs)


class TransmissionUnit(models.Model):
    """
    Junction table for units involved in a transmission.
    Preserves order of unit appearances.
    """
    transmission = models.ForeignKey(
        Transmission,
        on_delete=models.CASCADE,
        related_name="transmission_units"
    )
    unit = models.ForeignKey(
        Unit,
        on_delete=models.CASCADE,
        related_name="unit_transmissions"
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]
        verbose_name = "Transmission Unit"
        verbose_name_plural = "Transmission Units"
        constraints = [
            models.UniqueConstraint(
                fields=["transmission", "unit"],
                name="unique_unit_per_transmission"
            )
        ]

    def __str__(self):
        return f"{self.unit} on {self.transmission}"


class Transcription(models.Model):
    """
    Text transcription of a transmission's audio content.
    Supports both manual and automated transcription.
    """
    transmission = models.OneToOneField(
        Transmission,
        on_delete=models.CASCADE,
        related_name="transcription"
    )
    text = models.TextField(
        help_text="Transcription text content"
    )
    is_automated = models.BooleanField(
        default=False,
        help_text="True if generated by speech-to-text"
    )
    confidence = models.FloatField(
        null=True,
        blank=True,
        help_text="Confidence score for automated transcriptions (0-1)"
    )
    language = models.CharField(
        max_length=10,
        default="en",
        help_text="ISO language code"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who created/edited transcription"
    )

    class Meta:
        verbose_name = "Transcription"
        verbose_name_plural = "Transcriptions"

    def __str__(self):
        return f"Transcription for {self.transmission}"


# =============================================================================
# USER & ACCESS CONTROL MODELS
# =============================================================================

class Plan(models.Model):
    """
    User plan/tier defining access limits.
    """
    DEFAULT_PK = 1  # This is added via a migration

    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    history = models.IntegerField(
        default=0,
        help_text="Minutes of transmission history visible (0 = unlimited)"
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Default plan for new users"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Plan"
        verbose_name_plural = "Plans"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Ensure only one default plan
        if self.is_default:
            Plan.objects.filter(is_default=True).exclude(pk=self.pk).update(
                is_default=False
            )
        super().save(*args, **kwargs)


class TalkGroupAccess(models.Model):
    """
    Named group of talkgroups for access control.
    Users are assigned to one or more access groups.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    talkgroups = models.ManyToManyField(
        TalkGroup,
        related_name="access_groups",
        blank=True
    )

    # Default access settings
    default_group = models.BooleanField(
        default=False,
        help_text="Automatically assigned to new users"
    )
    default_new_talkgroups = models.BooleanField(
        default=False,
        help_text="Automatically add new public talkgroups to this group"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Talk Group Access"
        verbose_name_plural = "Talk Group Access Groups"

    def __str__(self):
        return self.name


class Profile(models.Model):
    """
    Extended user profile with plan and talkgroup access.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default=Plan.DEFAULT_PK,
        related_name="profiles"
    )
    talkgroup_access = models.ManyToManyField(
        TalkGroupAccess,
        related_name="profiles",
        blank=True
    )

    # User preferences
    show_unit_ids = models.BooleanField(
        default=True,
        help_text="Show unit IDs in transmission display"
    )
    favorite_talkgroups = models.ManyToManyField(
        TalkGroup,
        related_name="favorited_by",
        blank=True,
        help_text="Talkgroups shown in user's quick access dropdown"
    )

    # Registration status
    is_approved = models.BooleanField(
        default=True,
        help_text="User approved for access (for closed registration)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"

    def __str__(self):
        return f"Profile: {self.user.username}"

    @property
    def history_limit(self):
        """Return history limit in minutes (0 = unlimited)."""
        if self.plan:
            return self.plan.history
        return 0

    def get_accessible_talkgroups(self):
        """Return queryset of all talkgroups user can access."""
        if not settings.ACCESS_TG_RESTRICT:
            return TalkGroup.objects.all()

        return TalkGroup.objects.filter(
            access_groups__in=self.talkgroup_access.all()
        ).distinct()


class ScanList(models.Model):
    """
    User-created list of talkgroups for monitoring.
    """
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="scanlists"
    )
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.CharField(max_length=200, blank=True)
    talkgroups = models.ManyToManyField(
        TalkGroup,
        related_name="scanlists",
        blank=True
    )

    public = models.BooleanField(
        default=False,
        help_text="Allow other users to view this scanlist"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Scan List"
        verbose_name_plural = "Scan Lists"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("scanlist_detail", kwargs={"slug": self.slug})


# =============================================================================
# INCIDENT MODEL
# =============================================================================

class Incident(models.Model):
    """
    Group of related transmissions representing a significant event.
    """
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(blank=True)

    transmissions = models.ManyToManyField(
        Transmission,
        related_name="incidents",
        blank=True
    )

    public = models.BooleanField(
        default=True,
        help_text="Allow public viewing of this incident"
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="incidents"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Incident"
        verbose_name_plural = "Incidents"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("incident_detail", kwargs={"slug": self.slug})


# =============================================================================
# SIGNALS
# =============================================================================

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a Profile for new users."""
    if created:
        # Get default plan
        try:
            default_plan = Plan.objects.get(pk=Plan.DEFAULT_PK)
        except Plan.DoesNotExist:
            default_plan = None

        # Create profile
        profile = Profile.objects.create(
            user=instance,
            plan=default_plan,
            is_approved=getattr(settings, "OPEN_REGISTRATION", True)
        )

        # Add default talkgroup access groups
        try:
            for tg_access in TalkGroupAccess.objects.filter(default_group=True):
                profile.talkgroup_access.add(tg_access)
        except Exception:
            pass


@receiver(post_save, sender=TalkGroup)
def add_talkgroup_to_default_groups(sender, instance, created, **kwargs):
    """Add new public talkgroups to default access groups."""
    if created and instance.is_public:
        for access_group in TalkGroupAccess.objects.filter(
            default_new_talkgroups=True
        ):
            access_group.talkgroups.add(instance)


@receiver(post_save, sender=Transmission, dispatch_uid="send_mesg")
def send_transmission_notification(sender, instance, **kwargs):
    """Send WebSocket notification when transmission is created."""
    import logging

    logger = logging.getLogger(__name__)

    # Update talkgroup last_transmission
    tg = instance.talkgroup_info
    tg.last_transmission = timezone.now()
    tg.save(update_fields=["last_transmission"])

    # Try to send WebSocket notification (may fail if Redis unavailable)
    try:
        from channels.layers import get_channel_layer

        channel_layer = get_channel_layer()
        if channel_layer is None:
            return

        # Get associated scan lists
        groups = tg.scanlists.all()

        # Build payload
        payload = instance.as_dict()
        payload["scan-groups"] = [g.slug for g in groups]

        # Send to default channel
        async_to_sync(channel_layer.group_send)(
            "livecall-scan-default",
            {
                "type": "radio_message",
                "text": json.dumps(payload),
            },
        )
    except Exception as e:
        # Log but don't fail if WebSocket notification fails
        logger.debug(f"WebSocket notification failed: {e}")
