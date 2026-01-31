from pathlib import Path
import os
import environ
from django.templatetags.static import static


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

BASE_URL = env("BASE_URL")


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True if str(env("DEBUG")).upper() == "TRUE" else False

ALLOWED_HOSTS = env("ALLOWED_HOSTS").split(",")


# Application definition

INSTALLED_APPS = [
    "unfold",
    "axes",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    # apps
    "content.apps.ContentConfig",
    "site_settings.apps.SettingsConfig",
    "stamps.apps.StampsConfig",
    "accounts.apps.AccountsConfig",
    "about.apps.AboutConfig",
    "projects.apps.ProjectsConfig",
    "pwa",
    "compressor",  # new
]

UNFOLD = {
    "SITE_TITLE": "My Admin",
    "SITE_HEADER": "My Admin Panel",
    "BRAND": "Hinet",
    "SITE_SYMBOL": "speed",  # symbol from icon set
    "SITE_FAVICONS": [
        {
            "rel": "icon",
            "sizes": "32x32",
            "type": "image/svg+xml",
            "href": lambda request: static("favicon.svg"),
        },
    ],
    "THEME": "light",
}

# COMPRESS_ROOT = BASE_DIR / "static"

# COMPRESS_ENABLED = True

# STATICFILES_FINDERS = ("compressor.finders.CompressorFinder",)

# ================= PWA CONFIG =================

PWA_APP_NAME = "Hinet Stamps"
PWA_APP_SHORT_NAME = "Stamps"
PWA_APP_DESCRIPTION = "Official Company Web App"
PWA_APP_THEME_COLOR = "#0f172a"
PWA_APP_BACKGROUND_COLOR = "#ffffff"
PWA_APP_DISPLAY = "standalone"
PWA_APP_START_URL = "/"
PWA_APP_SCOPE = "/"
PWA_APP_ORIENTATION = "portrait"

PWA_APP_ICONS = [
    {
        "src": "/static/icons/logo2024.png",
        "sizes": "192x192",
        "type": "image/png"
    },
    {
        "src": "/static/icons/logo2025.png",
        "sizes": "512x512",
        "type": "image/png"
    },
]


PWA_APP_SCREENSHOTS = [
    {
        "src": "/static/icons/logo2023.png", "sizes": "320x320",
        "type": "image/png",
    },
    {
        "src": "/static/icons/logo2023.png", "sizes": "320x320",
        "type": "image/png",
        "form_factor": "wide",
    },
]
PWA_APP_SPLASH_SCREEN = [{"src": "/static/icons/logo2022.png", "sizes": "448x286"}]

PWA_APP_DIR = "rtl"
PWA_APP_LANG = "ar"


MIDDLEWARE = [
    "config.middleware.AdminIPRestrictionMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

AUTHENTICATION_BACKENDS = [
    "accounts.backends.EmailAuthBackend",
    "django.contrib.auth.backends.ModelBackend",
    "axes.backends.AxesBackend",
]

LOGIN_URL = "login"  # your login view name
LOGIN_REDIRECT_URL = "stamp_list"
LOGOUT_REDIRECT_URL = "login"
ADMIN_URL = "secure-dashboard-a7b3c9d2"

# settings.py
MIDDLEWARE += ["axes.middleware.AxesMiddleware"]

AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1  # hours


ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "site_settings.settings_context.site_config_context",
                "site_settings.settings_context.seo_context",
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": env("DB_HOST"),
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "ar"
TIME_ZONE = "Africa/Cairo"  # or your timezone
USE_I18N = True
USE_L10N = True
USE_TZ = True

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

EMAIL_BACKEND = env("EMAIL_BACKEND")
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = int(env("EMAIL_PORT"))
EMAIL_USE_TLS = env("EMAIL_USE_TLS")
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")


ERPNEXT_URL = env("ERPNEXT_URL")
ERPNEXT_API_KEY = env("ERPNEXT_API_KEY")
ERPNEXT_API_SECRET = env("ERPNEXT_API_SECRET")
