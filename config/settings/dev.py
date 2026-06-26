from .base import *

DEBUG = True

# Override to SQLite for dev/testing (MySQL config kept in base.py for production)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Email backend for dev
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Debug toolbar
def show_toolbar(request):
    return True
DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": show_toolbar,
    "IS_RUNNING_TESTS": False,
}

# Use local memory cache instead of Redis for dev
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}
