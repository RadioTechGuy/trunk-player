"""
Trunk Player v2 - User Views

Views for user profile and scanlist management.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from ..forms import ProfileForm, ScanListForm
from ..models import Profile, ScanList, TalkGroup


@login_required
@require_GET
def profile(request):
    """User profile page."""
    try:
        user_profile = request.user.profile
    except Profile.DoesNotExist:
        user_profile = Profile.objects.create(user=request.user)

    context = {
        "profile": user_profile,
        "scanlists": ScanList.objects.filter(created_by=request.user),
    }
    return render(request, "radio/profile.html", context)


@login_required
@require_GET
def scanlist_list(request):
    """List user's scanlists."""
    user_scanlists = ScanList.objects.filter(created_by=request.user)
    public_scanlists = ScanList.objects.filter(public=True).exclude(
        created_by=request.user
    )

    context = {
        "user_scanlists": user_scanlists,
        "public_scanlists": public_scanlists,
    }
    return render(request, "radio/scanlist_list.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def scanlist_create(request):
    """Create a new scanlist."""
    if request.method == "POST":
        form = ScanListForm(request.POST, user=request.user)
        if form.is_valid():
            scanlist = form.save(commit=False)
            scanlist.created_by = request.user
            scanlist.save()
            form.save_m2m()
            messages.success(request, f"Scanlist '{scanlist.name}' created.")
            return redirect("scanlist_detail", slug=scanlist.slug)
    else:
        form = ScanListForm(user=request.user)

    context = {
        "form": form,
        "action": "Create",
    }
    return render(request, "radio/scanlist_form.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def scanlist_edit(request, slug):
    """Edit an existing scanlist."""
    scanlist = get_object_or_404(ScanList, slug=slug)

    # Check ownership
    if scanlist.created_by != request.user:
        raise Http404("Scanlist not found")

    if request.method == "POST":
        form = ScanListForm(request.POST, instance=scanlist, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Scanlist '{scanlist.name}' updated.")
            return redirect("scanlist_detail", slug=scanlist.slug)
    else:
        form = ScanListForm(instance=scanlist, user=request.user)

    context = {
        "form": form,
        "scanlist": scanlist,
        "action": "Edit",
    }
    return render(request, "radio/scanlist_form.html", context)
