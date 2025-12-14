"""
Trunk Player v2 - Authentication Backends

Supports local authentication and Fief OAuth integration.
"""

import logging
from typing import Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.http import HttpRequest

logger = logging.getLogger(__name__)
User = get_user_model()


class FiefAuthenticationBackend(BaseBackend):
    """
    Authentication backend for Fief OAuth.

    This backend handles users authenticated via Fief's OAuth flow.
    It creates or updates local Django users based on Fief user info.
    """

    def authenticate(
        self,
        request: Optional[HttpRequest] = None,
        fief_user_id: Optional[str] = None,
        email: Optional[str] = None,
        **kwargs,
    ) -> Optional[User]:
        """
        Authenticate a user from Fief OAuth callback.

        Args:
            request: The HTTP request
            fief_user_id: The Fief user ID
            email: The user's email from Fief
            **kwargs: Additional user info from Fief

        Returns:
            User instance if authenticated, None otherwise
        """
        if not fief_user_id or not email:
            return None

        try:
            # Try to find existing user by email
            user = User.objects.get(email=email)

            # Update user info if needed
            first_name = kwargs.get("first_name", "")
            last_name = kwargs.get("last_name", "")

            if first_name and user.first_name != first_name:
                user.first_name = first_name
            if last_name and user.last_name != last_name:
                user.last_name = last_name
            user.save()

            return user

        except User.DoesNotExist:
            # Create new user
            username = self._generate_username(email)
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=kwargs.get("first_name", ""),
                last_name=kwargs.get("last_name", ""),
            )
            # Set unusable password since they'll use OAuth
            user.set_unusable_password()
            user.save()

            logger.info(f"Created new user from Fief: {username}")
            return user

        except Exception as e:
            logger.error(f"Error authenticating Fief user: {e}")
            return None

    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def _generate_username(self, email: str) -> str:
        """Generate a unique username from email."""
        base_username = email.split("@")[0]
        username = base_username
        counter = 1

        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        return username


def get_fief_client():
    """
    Get configured Fief client instance.

    Returns None if Fief is not configured.
    """
    if not settings.FIEF_ENABLED:
        return None

    try:
        from fief_client import Fief

        return Fief(
            settings.FIEF_BASE_URL,
            settings.FIEF_CLIENT_ID,
            settings.FIEF_CLIENT_SECRET,
        )
    except ImportError:
        logger.warning("fief-client not installed")
        return None
    except Exception as e:
        logger.error(f"Error creating Fief client: {e}")
        return None


def get_fief_auth_url(redirect_uri: str, state: str = "") -> Optional[str]:
    """
    Generate Fief OAuth authorization URL.

    Args:
        redirect_uri: The callback URL after authentication
        state: Optional state parameter for CSRF protection

    Returns:
        Authorization URL or None if Fief not configured
    """
    client = get_fief_client()
    if not client:
        return None

    try:
        auth_url = client.auth_url(
            redirect_uri=redirect_uri,
            scope=["openid", "email", "profile"],
            state=state,
        )
        return auth_url
    except Exception as e:
        logger.error(f"Error generating Fief auth URL: {e}")
        return None
