"""
Trunk Player v2 - URL Configuration
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from radio import views
from radio.views import pwa_manifest, pwa_service_worker

urlpatterns = [
    # PWA
    path("manifest.json", pwa_manifest, name="pwa_manifest"),
    path("sw.js", pwa_service_worker, name="pwa_service_worker"),

    # Admin
    path("admin/", admin.site.urls),

    # API v2
    path("api/v2/", include("radio.api.urls")),

    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),

    # Authentication
    path("auth/", include("radio.urls.auth")),

    # Main views
    path("", views.home, name="home"),
    path("talkgroups/", views.talkgroup_list, name="talkgroup_list"),
    path("tg/<slug:slug>/", views.talkgroup_player, name="talkgroup_detail"),
    path("tg/<slug:slug>/favorite/", views.toggle_favorite_talkgroup, name="toggle_favorite_talkgroup"),
    path("scan/<slug:slug>/", views.scanlist_player, name="scanlist_detail"),
    path("unit/<slug:slug>/", views.unit_player, name="unit_detail"),
    path("inc/<slug:slug>/", views.incident_detail, name="incident_detail"),
    path("audio/<slug:slug>/", views.transmission_detail, name="transmission_detail"),

    # User pages
    path("profile/", views.profile, name="profile"),
    path("scanlists/", views.scanlist_list, name="scanlist_list"),
    path("scanlists/create/", views.scanlist_create, name="scanlist_create"),
    path("scanlists/<slug:slug>/edit/", views.scanlist_edit, name="scanlist_edit"),

    # Incidents
    path("incidents/", views.incident_list, name="incident_list"),

    # Redirects for convenience
    path("scan/", RedirectView.as_view(url="/scan/default/", permanent=False)),

    # Django auth
    path("", include("django.contrib.auth.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
