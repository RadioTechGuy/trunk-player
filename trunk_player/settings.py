"""
Trunk Player v2 - Django Settings

Modern Django 5.x configuration with Fief authentication,
HTMX/Alpine.js frontend, and PWA support.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'
BASE_DIR = Path(__file__).resolve().parent.parent


# =============================================================================
# SECURITY SETTINGS
# =============================================================================

SECRET_KEY = os.environ.get("SECRET_KEY", "CHANGE-ME-IN-PRODUCTION")

DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split()

CSRF_TRUSTED_ORIGINS = os.environ.get("CSRF_TRUSTED_ORIGINS", "").split()

# HTTPS settings
if os.getenv("FORCE_SECURE", "False").lower() in ("true", "1", "t"):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True


# =============================================================================
# APPLICATION DEFINITION
# =============================================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party apps
    "rest_framework",
    "drf_spectacular",
    "channels",
    # Local apps
    "radio.apps.RadioConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "trunk_player.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "radio.context_processors.site_settings",
                "radio.context_processors.user_favorites",
            ],
        },
    },
]

WSGI_APPLICATION = "trunk_player.wsgi.application"
ASGI_APPLICATION = "trunk_player.asgi.application"


# =============================================================================
# DATABASE
# =============================================================================

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("SQL_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.environ.get("SQL_DATABASE", BASE_DIR / "db.sqlite3"),
        "USER": os.environ.get("SQL_USER", "user"),
        "PASSWORD": os.environ.get("SQL_PASSWORD", "password"),
        "HOST": os.environ.get("SQL_HOST", "localhost"),
        "PORT": os.environ.get("SQL_PORT", "5432"),
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# =============================================================================
# AUTHENTICATION
# =============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "radio.auth.FiefAuthenticationBackend",
]

LOGIN_URL = "/auth/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"


# =============================================================================
# FIEF AUTHENTICATION
# =============================================================================

FIEF_BASE_URL = os.environ.get("FIEF_BASE_URL", "")
FIEF_CLIENT_ID = os.environ.get("FIEF_CLIENT_ID", "")
FIEF_CLIENT_SECRET = os.environ.get("FIEF_CLIENT_SECRET", "")
FIEF_REDIRECT_URI = os.environ.get("FIEF_REDIRECT_URI", "")

# Enable/disable Fief authentication
FIEF_ENABLED = bool(FIEF_BASE_URL and FIEF_CLIENT_ID)


# =============================================================================
# REGISTRATION SETTINGS
# =============================================================================

# Open registration: True = users can self-register, False = admin approval required
OPEN_REGISTRATION = os.getenv("OPEN_REGISTRATION", "False").lower() in ("true", "1", "t")

# Allow anonymous access to public content
ALLOW_ANONYMOUS = os.getenv("ALLOW_ANONYMOUS", "False").lower() in ("true", "1", "t")

# How far back an anonymous user can see (in minutes, 0 = no limit)
ANONYMOUS_TIME = int(os.environ.get("ANONYMOUS_TIME", "43200"))  # Default: 30 days


# =============================================================================
# INTERNATIONALIZATION
# =============================================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = str(os.getenv("TZ", "America/Los_Angeles"))

USE_I18N = True

USE_TZ = True


# =============================================================================
# STATIC FILES
# =============================================================================

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"
STATICFILES_DIRS = [BASE_DIR / "staticfiles"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "audio_files"


# =============================================================================
# REDIS & CHANNELS
# =============================================================================

REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379")

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_URL],
        },
    },
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"{REDIS_URL}/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}


# =============================================================================
# REST FRAMEWORK
# =============================================================================

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Trunk Player API",
    "DESCRIPTION": "API for radio transmission playback and management",
    "VERSION": "2.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}


# =============================================================================
# CELERY (for background tasks like transcription)
# =============================================================================

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", REDIS_URL)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"


# =============================================================================
# TRUNK PLAYER SETTINGS
# =============================================================================

# Site branding
SITE_TITLE = os.environ.get("SITE_TITLE", "Trunk Player")
SITE_EMAIL = os.environ.get("SITE_EMAIL", "help@example.com")

# Audio file settings
AUDIO_URL_BASE = os.environ.get("AUDIO_URL_BASE", "/media/")
FIX_AUDIO_NAME = os.getenv("FIX_AUDIO_NAME", "False").lower() in ("true", "1", "t")

# Transmission display format
TRANS_DATETIME_FORMAT = os.environ.get("TRANS_DATETIME_FORMAT", "%H:%M:%S %m/%d/%Y")

# Talkgroup settings
ACCESS_TG_RESTRICT = os.getenv("ACCESS_TG_RESTRICT", "False").lower() in ("true", "1", "t")
TALKGROUP_RECENT_LENGTH = int(os.getenv("TALKGROUP_RECENT_LENGTH", "15"))  # Minutes

# API authentication token for transmission import
ADD_TRANS_AUTH_TOKEN = os.environ.get("ADD_TRANS_AUTH_TOKEN", "CHANGE-ME-IN-PRODUCTION")

# Unit display settings
SHOW_UNIT_IDS = os.getenv("SHOW_UNIT_IDS", "True").lower() in ("true", "1", "t")

# Django admin settings
USE_RAW_ID_FIELDS = os.getenv("USE_RAW_ID_FIELDS", "False").lower() in ("true", "1", "t")


# =============================================================================
# LOGGING
# =============================================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "radio": {
            "handlers": ["console"],
            "level": os.getenv("RADIO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
}


# =============================================================================
# LOCAL SETTINGS OVERRIDE
# =============================================================================

try:
    from trunk_player.settings_local import *  # noqa: F401, F403
except ImportError:
    pass
