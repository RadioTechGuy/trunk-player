"""
Trunk Player v2 - Authentication URLs
"""

from django.urls import path

from radio.views import auth as auth_views

urlpatterns = [
    # Local authentication
    path("login/", auth_views.login_view, name="login"),
    path("logout/", auth_views.logout_view, name="logout"),
    path("register/", auth_views.register_view, name="register"),

    # Fief OAuth
    path("fief/login/", auth_views.fief_login, name="fief_login"),
    path("fief/callback/", auth_views.fief_callback, name="fief_callback"),
]
