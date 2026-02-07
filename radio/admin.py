"""
Trunk Player v2 - Django Admin Configuration
"""

from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.conf import settings

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
# INLINE ADMINS
# =============================================================================

class TransmissionUnitInline(admin.TabularInline):
    model = TransmissionUnit
    extra = 0
    raw_id_fields = ("unit",)


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "Profile"
    filter_horizontal = ("talkgroup_access",)


class TranscriptionInline(admin.StackedInline):
    model = Transcription
    can_delete = True
    extra = 0


# =============================================================================
# MODEL ADMINS
# =============================================================================

@admin.register(System)
class SystemAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")


@admin.register(TalkGroup)
class TalkGroupAdmin(admin.ModelAdmin):
    list_display = ("alpha_tag", "dec_id", "system", "is_public", "last_transmission")
    list_filter = ("system", "is_public")
    search_fields = ("alpha_tag", "common_name", "description", "dec_id")
    list_select_related = ("system",)
    readonly_fields = ("created_at", "updated_at", "recent_usage")
    save_on_top = True


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("dec_id", "description", "unit_type", "system")
    list_filter = ("system", "unit_type")
    search_fields = ("description", "dec_id", "unit_number")
    list_select_related = ("system",)
    readonly_fields = ("created_at", "updated_at")
    save_on_top = True


@admin.register(Transmission)
class TransmissionAdmin(admin.ModelAdmin):
    list_display = (
        "slug",
        "talkgroup_info",
        "start_datetime",
        "play_length",
        "emergency",
        "system",
    )
    list_filter = ("system", "emergency")
    search_fields = ("talkgroup_info__alpha_tag", "talkgroup_dec_id", "talkgroup_name")
    list_select_related = ("system", "talkgroup_info")
    raw_id_fields = ("talkgroup_info", "system")
    inlines = (TransmissionUnitInline, TranscriptionInline)
    readonly_fields = ("slug", "created_at")
    date_hierarchy = "start_datetime"
    save_on_top = True


@admin.register(TransmissionUnit)
class TransmissionUnitAdmin(admin.ModelAdmin):
    list_display = ("transmission", "unit", "order")
    raw_id_fields = ("transmission", "unit")
    save_on_top = True


@admin.register(Transcription)
class TranscriptionAdmin(admin.ModelAdmin):
    list_display = ("transmission", "is_automated", "confidence", "created_at")
    list_filter = ("is_automated", "language")
    search_fields = ("text",)
    raw_id_fields = ("transmission", "created_by")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "history", "is_default")
    list_filter = ("is_default",)
    readonly_fields = ("created_at", "updated_at")


class TalkGroupAccessAdminForm(forms.ModelForm):
    """Custom form for TalkGroupAccess with better M2M widget."""

    class Meta:
        model = TalkGroupAccess
        fields = "__all__"
        widgets = {
            "talkgroups": FilteredSelectMultiple(
                verbose_name="Talkgroups",
                is_stacked=False,
            )
        }


@admin.register(TalkGroupAccess)
class TalkGroupAccessAdmin(admin.ModelAdmin):
    form = TalkGroupAccessAdminForm
    list_display = ("name", "default_group", "default_new_talkgroups")
    list_filter = ("default_group", "default_new_talkgroups")
    readonly_fields = ("created_at", "updated_at")
    save_on_top = True

    class Media:
        css = {
            "all": ("admin/css/widgets.css",),
        }


class ScanListAdminForm(forms.ModelForm):
    """Custom form for ScanList with better M2M widget."""

    class Meta:
        model = ScanList
        fields = "__all__"
        widgets = {
            "talkgroups": FilteredSelectMultiple(
                verbose_name="Talkgroups",
                is_stacked=False,
            )
        }


@admin.register(ScanList)
class ScanListAdmin(admin.ModelAdmin):
    form = ScanListAdminForm
    list_display = ("name", "created_by", "public", "created_at")
    list_filter = ("public",)
    search_fields = ("name", "description")
    raw_id_fields = ("created_by",)
    readonly_fields = ("created_at", "updated_at")
    save_as = True
    save_on_top = True

    class Media:
        css = {
            "all": ("admin/css/widgets.css",),
        }


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ("name", "public", "created_by", "created_at")
    list_filter = ("public",)
    search_fields = ("name", "description")
    raw_id_fields = ("transmissions", "created_by")
    readonly_fields = ("created_at", "updated_at")
    save_on_top = True


# =============================================================================
# USER ADMIN WITH PROFILE
# =============================================================================

class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_active",
    )


# Re-register User with our custom admin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
