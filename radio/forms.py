"""
Trunk Player v2 - Forms
"""

from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from .models import Profile, ScanList, TalkGroup, Unit


class RegistrationForm(UserCreationForm):
    """User registration form."""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-input"}),
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes
        for field_name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "form-input")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    """User profile edit form."""

    class Meta:
        model = Profile
        fields = ("show_unit_ids",)
        widgets = {
            "show_unit_ids": forms.CheckboxInput(attrs={"class": "form-checkbox"}),
        }


class ScanListForm(forms.ModelForm):
    """Scanlist create/edit form."""

    talkgroups = forms.ModelMultipleChoiceField(
        queryset=TalkGroup.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-checkbox"}),
        required=False,
    )

    class Meta:
        model = ScanList
        fields = ("name", "description", "talkgroups", "public")
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input"}),
            "description": forms.Textarea(attrs={"class": "form-textarea", "rows": 3}),
            "public": forms.CheckboxInput(attrs={"class": "form-checkbox"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        # Filter talkgroups by user's access
        if user and settings.ACCESS_TG_RESTRICT:
            try:
                accessible_tgs = user.profile.get_accessible_talkgroups()
                self.fields["talkgroups"].queryset = accessible_tgs
            except Profile.DoesNotExist:
                self.fields["talkgroups"].queryset = TalkGroup.objects.filter(
                    is_public=True
                )

    def clean_name(self):
        name = self.cleaned_data["name"]

        # Check for duplicate name (excluding current instance)
        qs = ScanList.objects.filter(name=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError(
                _("A scanlist with this name already exists.")
            )

        return name


class UnitEditForm(forms.ModelForm):
    """Form for editing unit descriptions."""

    class Meta:
        model = Unit
        fields = ("description", "unit_type", "unit_number")
        widgets = {
            "description": forms.TextInput(attrs={"class": "form-input"}),
            "unit_type": forms.Select(attrs={"class": "form-select"}),
            "unit_number": forms.TextInput(attrs={"class": "form-input"}),
        }


class UserSettingsForm(forms.ModelForm):
    """User settings form."""

    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-input"}),
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-input"}),
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-input"}),
    )

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
