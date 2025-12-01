"""
Trunk Player v2 - Authentication Views

Local and Fief OAuth authentication views.
"""

import logging
import secrets

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from ..auth import get_fief_client, get_fief_auth_url
from ..forms import RegistrationForm

logger = logging.getLogger(__name__)


@require_http_methods(["GET", "POST"])
def login_view(request):
    """Local login view."""
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get("next", "home")
            return redirect(next_url)
    else:
        form = AuthenticationForm()

    context = {
        "form": form,
        "fief_enabled": settings.FIEF_ENABLED,
    }
    return render(request, "radio/auth/login.html", context)


@require_http_methods(["GET", "POST"])
def logout_view(request):
    """Logout view."""
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("home")


@require_http_methods(["GET", "POST"])
def register_view(request):
    """User registration view."""
    if not settings.OPEN_REGISTRATION:
        messages.error(request, "Registration is currently closed.")
        return redirect("login")

    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful. Welcome!")
            return redirect("home")
    else:
        form = RegistrationForm()

    context = {
        "form": form,
    }
    return render(request, "radio/auth/register.html", context)


@require_http_methods(["GET"])
def fief_login(request):
    """Initiate Fief OAuth login."""
    if not settings.FIEF_ENABLED:
        messages.error(request, "OAuth login is not configured.")
        return redirect("login")

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    request.session["fief_oauth_state"] = state

    # Build callback URL
    callback_url = request.build_absolute_uri(reverse("fief_callback"))

    # Get auth URL
    auth_url = get_fief_auth_url(callback_url, state)
    if not auth_url:
        messages.error(request, "Failed to initiate OAuth login.")
        return redirect("login")

    return redirect(auth_url)


@require_http_methods(["GET"])
def fief_callback(request):
    """Handle Fief OAuth callback."""
    if not settings.FIEF_ENABLED:
        messages.error(request, "OAuth login is not configured.")
        return redirect("login")

    # Verify state
    state = request.GET.get("state", "")
    expected_state = request.session.pop("fief_oauth_state", None)

    if not expected_state or state != expected_state:
        messages.error(request, "Invalid OAuth state. Please try again.")
        return redirect("login")

    # Get authorization code
    code = request.GET.get("code")
    if not code:
        error = request.GET.get("error", "Unknown error")
        messages.error(request, f"OAuth error: {error}")
        return redirect("login")

    try:
        # Exchange code for tokens
        client = get_fief_client()
        if not client:
            raise Exception("Fief client not configured")

        callback_url = request.build_absolute_uri(reverse("fief_callback"))
        tokens, userinfo = client.auth_callback(code, callback_url)

        # Authenticate user
        user = authenticate(
            request,
            fief_user_id=userinfo.get("sub"),
            email=userinfo.get("email"),
            first_name=userinfo.get("given_name", ""),
            last_name=userinfo.get("family_name", ""),
        )

        if user:
            login(request, user)
            messages.success(request, "Login successful.")
            next_url = request.session.pop("next", "home")
            return redirect(next_url)
        else:
            messages.error(request, "Failed to authenticate. Please try again.")
            return redirect("login")

    except Exception as e:
        logger.exception("Fief callback error")
        messages.error(request, "Authentication failed. Please try again.")
        return redirect("login")
