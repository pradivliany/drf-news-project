# Contains main settings of the django project.
# (configuration of apps, templated, middleware, database, ...)

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Project's base absolute dir -> where manage.py is.
BASE_DIR = Path(__file__).resolve().parent.parent

# Security key. (must be hidden in .env)
SECRET_KEY = os.getenv("SECRET_KEY")

# Debug mode: True for development (shows errors), False for production.
DEBUG = os.getenv("DEBUG") == "True"

# Allowed domains for the website. (type list)
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS").split(",")

# 1. Build-in apps.
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

# 2. Provided apps by installed libraries.
THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
    "django_filters",
    "rest_framework_simplejwt",
]

# 3. Local apps list.
LOCAL_APPS = [
    "apps.accounts",
]

# Collective list of all apps in project.
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# List of middlewares to manage requests.
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # Notice: add CORS middleware.
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Project's root URL file.
ROOT_URLCONF = "config.urls"

# Configuration of Django's template. (will be used only for admin panel)
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Managing DB configuration.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB"),
        "USER": os.getenv("POSTGRES_USER"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
        "HOST": os.getenv("POSTGRES_HOST"),
        "PORT": os.getenv("POSTGRES_PORT"),
        "ATOMIC_REQUESTS": True,  # Each HTTP request runs in a single database transaction.
    }
}

# Build-in password validators.
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization.
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files. (CSS, JavaScript, Images)
STATIC_URL = "static/"  # Example: http://127.0.0.1:8000/static/admin/css/base.css .
STATIC_ROOT = BASE_DIR / "staticfiles"  # Path for -> py manage.py collectstatic.

# Media files.
MEDIA_URL = "media/"  # Example: http://127.0.0.1:8000/media/news_images/photo.jpg .
MEDIA_ROOT = BASE_DIR / "media"  # Path for media.

# Not necessary. But rather add just in case.
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Custom User Model
AUTH_USER_MODEL = "accounts.User"


# DRF configuration.
REST_FRAMEWORK = {
    # 1. Authentication classes, that determines how to get user from token in request.header["Authorization"].
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",  # Converts token -> user object in request.user.
    ],
    # 2. Permissions.
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",  # Will deny permission to any unauthenticated user.
    ],
    # 3. Pagination settings.
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",  # Example: adds ?page=2
    "PAGE_SIZE": 20,  # 20 objects at once.
    # 4. Filtering, Searching, Ordering.
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",  # Filter on specific fields. (?category=1)
        "rest_framework.filters.SearchFilter",  # Search by keywords in multiple fields. (?search=)
        "rest_framework.filters.OrderingFilter",  # Sorting of result list. (?ordering=-price)
    ],
    # 5. Data formats.
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",  # Output: data will be rendered inro a raw JSON string.
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",  # For regular API requests in JSON.
        "rest_framework.parsers.MultiPartParser",  # For uploaded files (pics, docs) from forms.
        "rest_framework.parsers.FormParser",  # For simple text data from forms. (URL-encoded)
    ],
}

# CORS configuration for development and production.
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    # Allowed sources.
    CORS_ALLOWED_ORIGINS = [
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ]

# JWT’s behavior.
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=7
    ),  # Allows user to be logged in for 7 days.
    "ROTATE_REFRESH_TOKENS": True,  # User gets new refresh token after getting new access token.
    "BLACKLIST_AFTER_ROTATION": True,  # Old refresh token becomes not usable.
    "UPDATE_LAST_LOGIN": True,  # last_login field be updated after getting new token.
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,  # To create and verify uses same key.
    "AUTH_HEADER_TYPES": ("Bearer",),  # Authorization: Bearer <token>.
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# Security configurations.
# 1. Safety from Cross-Site Scripting. (No JS scripts in form input allowed)
SECURE_BROWSER_XSS_FILTER = True
# 2. Prevents the browser from interpreting files as a different MIME type.
SECURE_CONTENT_TYPE_NOSNIFF = True
# 3. Dealing with <iframe> manipulations.
X_FRAME_OPTIONS = "DENY"

# Logging configuration.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,  # Retain the default loggers.
    "formatters": {
        # 1. Example -> ERROR 2026-01-23 10:15:01,123 basehttp 14022 1397452601070 Internal Server Error: /api/products/
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",  # We use {} to input data inside.
        },
        # 2. Example -> ERROR Internal Server Error: /api/products/
        "simple": {"format": "{levelname} {message}", "style": "{"},
    },
    "handlers": {
        # 1. Writing into file.
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs" / "django.log",
            "formatter": "verbose",
        },
        # 2. Output in console.
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        # 1. Logger Django catches all logs from Django framework.
        "django": {
            "handlers": ["file", "console"],  # Uses both handlers to manage them.
            "level": "INFO",
            "propagate": True,  # Logs from django.db or similar raises to django logger.
        },
        "apps.main": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": False,  # Not raising , so output will be once.
        },
        "apps.comments": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

Path.mkdir(BASE_DIR / "logs", exist_ok=True)
