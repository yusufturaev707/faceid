import os
from datetime import timedelta, datetime
from pathlib import Path

from django.conf import settings
from dotenv import load_dotenv
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent

env = os.getenv
load_dotenv(os.path.join(BASE_DIR, ".env"))


SECRET_KEY = env("SECRET_KEY")

DEBUG = True

ALLOWED_HOSTS = ['*']


INSTALLED_APPS = [
    "unfold",  # before django.contrib.admin
    "unfold.contrib.filters",  # optional, if special filters are needed
    "unfold.contrib.forms",  # optional, if special form elements are needed
    "unfold.contrib.inlines",  # optional, if special inlines are needed
    "unfold.contrib.import_export",  # optional, if django-import-export package is used
    "unfold.contrib.guardian",  # optional, if django-guardian package is used
    "unfold.contrib.simple_history",  # optional, if django-simple-history package is used
    "unfold.contrib.location_field",  # optional, if django-location-field package is used
    "unfold.contrib.constance",  # optional, if django-constance package is used
    "crispy_forms",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'auditlog',

    # 3rd-party ilovalar
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    "corsheaders",
    "django_filters",
    "pgvector.django",
    "import_export",

    #Apps
    'face.apps.FaceConfig',
    'users.apps.UsersConfig',
    'region.apps.RegionConfig',
    'exam.apps.ExamConfig',
]

CRISPY_TEMPLATE_PACK = "unfold_crispy"

CRISPY_ALLOWED_TEMPLATE_PACKS = ["unfold_crispy"]


MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'auditlog.middleware.AuditlogMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ASGI sozlamalari (Agar WebSocket yoki async ishlatilsa)
ASGI_APPLICATION = "config.asgi.application"


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env("POSTGRES_DB"),
        'USER': env("POSTGRES_USER"),
        'PASSWORD': env("POSTGRES_PASSWORD"),
        'HOST': env("POSTGRES_HOST"),
        'PORT': env("POSTGRES_PORT"),
        'CONN_MAX_AGE': 600,
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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

AUTH_USER_MODEL = "users.User"
DJANGO_ALLOW_ASYNC_UNSAFE = True

LANGUAGE_CODE = 'uz'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ('uz', _('O\'zbekcha')),
    ('ru', _('Русский')),
    ('en', _('English')),
]

LOCALE_PATHS = [BASE_DIR / 'locale']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "10000/day",
        "user": "10000/hour"
    }
    # "DEFAULT_PAGINATION_CLASS": "core.pagination.CustomPagination",
    # "PAGE_SIZE": 20,
    # "DEFAULT_THROTTLE_CLASSES": {
    #     "core.throttle.UserRateThrottle": "1000/day",
    # },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=365),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=365),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_BLACKLIST_ENABLED": True,
}



CURRENT_ENV = 'DEV'  # Yoki 'STAGING', 'PROD'

from django.templatetags.static import static

UNFOLD = {
    "SITE_TITLE": "My admin",
    "SITE_HEADER": "FACE ID ADMIN PANEL",
    "SITE_SUBHEADER": "Turniketlar boshqaruvi",
    "SITE_URL": "/",
    # "SITE_ICON": lambda request: static("logo/Logo.png"),  # both modes, optimise for 32px height
    # "SITE_ICON": {
    #     "light": lambda request: static("icon-light.svg"),  # light mode
    #     "dark": lambda request: static("icon-dark.svg"),  # dark mode
    # },
    # "SITE_LOGO": lambda request: static("logo/Logo.png"),
    # "SITE_LOGO": {
    #     "light": lambda request: static("logo-light.svg"),  # light mode
    #     "dark": lambda request: static("logo-dark.svg"),  # dark mode
    # },
    "SITE_SYMBOL": "settings",  # symbol from icon set
    "SITE_FAVICONS": [
        {
            "rel": "icon",
            "sizes": "32x32",
            "type": "image/svg+xml",
            "href": lambda request: static("favicon.svg"),
        },
    ],
    "SHOW_HISTORY": True, # show/hide "History" button, default: True
    "SHOW_VIEW_ON_SITE": True, # show/hide "View on site" button, default: True
    "SHOW_BACK_BUTTON": False, # show/hide "Back" button on changeform in header, default: False

    "ENVIRONMENT": "core.utils.environment_callback", # environment name in header
    "ENVIRONMENT_TITLE_PREFIX": "core.utils.environment_title_prefix_callback", # environment name prefix in title tag
    "DASHBOARD_CALLBACK": "core.utils.dashboard_callback",

    # "THEME": "dark", # Force theme: "dark" or "light". Will disable theme switcher
    "LOGIN": {
        # "image": lambda request: static("static/Logo.png"),
        # "redirect_after": lambda request: reverse_lazy("admin:APP_MODEL_changelist"),
    },
    "BORDER_RADIUS": "5px",

    "EXTENSIONS": {
        "modeltranslation": {
            "flags": {
                "en": "🇬🇧",
                "fr": "🇫🇷",
                "nl": "🇧🇪",
            },
        },
    },
    "SIDEBAR": {
        "show_search": True,  # Search in applications and models names
        "command_search": False,  # Replace the sidebar search with the command search
        "show_all_applications": False,  # Dropdown with all applications and models
        "navigation": [
            {
                "title": _(""),
                "separator": False,  # Top border
                "collapsible": False,  # Collapsible group of links
                "items": [
                    {
                        "title": _("Dashboard"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                        "permission": lambda request: request.user.is_admin,
                    },
                ]
            },
            {
                "title": _("Test tadbirlar"),
                "separator": True,  # Top border
                "collapsible": False,  # Collapsible group of links
                "items": [
                    {
                        "title": _("Tadbirlar"),
                        "icon": "people",
                        "link": reverse_lazy("admin:exam_exam_changelist"),
                    },
                    {
                        "title": _("Tanlangan turniketlar"),
                        "icon": "people",
                        "link": reverse_lazy("admin:exam_examzoneswingbar_changelist"),
                    },
                    {
                        "title": _("Holatlar"),
                        "icon": "people",
                        "link": reverse_lazy("admin:exam_examstate_changelist"),
                    },
                    # {
                    #     "title": _("Smena"),
                    #     "icon": "people",
                    #     "link": reverse_lazy("admin:exam_examshift_changelist"),
                    # },
                ],
            },
            {
                "title": _("Studentlar va qora ro'yxat"),
                "separator": True,  # Top border
                "collapsible": False,  # Collapsible group of links
                "items": [
                    {
                        "title": _("Studentlar"),
                        "icon": "people",
                        "link": reverse_lazy("admin:exam_student_changelist"),
                    },
                    {
                        "title": _("Kirishlar logi"),
                        "icon": "people",
                        "link": reverse_lazy("admin:exam_studentlog_changelist"),
                    },
                    {
                        "title": _("Qora ro'yxat"),
                        "icon": "people",
                        "link": reverse_lazy("admin:exam_studentblacklist_changelist"),
                    },
                ],
            },
            {
                "title": _("Hudud va binolar"),
                "separator": True,  # Top border
                "collapsible": False,  # Collapsible group of links
                "items": [
                    {
                        "title": _("Binolar"),
                        "icon": "people",
                        "link": reverse_lazy("admin:region_zone_changelist"),
                    },
                    {
                        "title": _("Viloyatlar"),
                        "icon": "people",
                        "link": reverse_lazy("admin:region_region_changelist"),
                    },
                ],
            },
            {
                "title": _("Turniket va monitorlar"),
                "separator": True,  # Top border
                "collapsible": False,  # Collapsible group of links
                "items": [
                    {
                        "title": _("Turniketlar"),
                        "icon": "people",
                        "link": reverse_lazy("admin:region_swingbarrier_changelist"),
                    },
                    {
                        "title": _("Monitorlar"),
                        "icon": "people",
                        "link": reverse_lazy("admin:region_monitorpc_changelist"),
                    },
                ],
            },
            {
                "title": _("Test"),
                "separator": True,  # Top border
                "collapsible": True,  # Collapsible group of links
                "items": [
                    {
                        "title": _("Turlar"),
                        "icon": "people",
                        "link": reverse_lazy("admin:exam_test_changelist"),
                    },
                    {
                        "title": _("Smena"),
                        "icon": "people",
                        "link": reverse_lazy("admin:exam_shift_changelist"),
                    },
                    {
                        "title": _("Chetlatish sabablari"),
                        "icon": "people",
                        "link": reverse_lazy("admin:exam_reason_changelist"),
                    },
                ],
            },
            {
                "title": _("Xodim va rollar"),
                "separator": True,  # Top border
                "collapsible": True,  # Collapsible group of links
                "items": [
                    {
                        "title": _("Xodimlar"),
                        "icon": "people",
                        "link": reverse_lazy("admin:users_user_changelist"),
                    },
                    {
                        "title": _("Rol"),
                        "icon": "people",
                        "link": reverse_lazy("admin:users_role_changelist"),
                    },
                ],
            },
            {
                "title": _("Tizim monitoring"),
                "separator": True,  # Top border
                "collapsible": False,  # Collapsible group of links
                "items": [
                    {
                        "title": _("User loglari"),
                        "icon": "history",
                        "link": lambda *args, **kwargs: reverse("admin:auditlog_logentry_changelist"),
                        "badge": "core.utils.audit_badge_callback",
                        "permission": lambda request: request.user.is_admin,
                    },
                    {
                        "title": _("Oxirgi O'zgarishlar"),
                        "icon": "update",
                        "link": lambda *args, **kwargs: reverse("admin:auditlog_logentry_changelist") + "?action__exact=1",
                        "permission": lambda request: request.user.is_admin,
                    },
                    {
                        "title": _("O'chirilganlar"),
                        "icon": "delete",
                        "link": lambda *args, **kwargs: reverse(
                            "admin:auditlog_logentry_changelist") + "?action__exact=2",
                        "permission": lambda request: request.user.is_admin,
                    },
                ],
            },
        ],
    },

    "TABS": [
        {
            "models": [
                "auditlog.logentry",
            ],
            "items": [
                {
                    "title": _("Barcha Loglar"),
                    "link": lambda *args, **kwargs: reverse("admin:auditlog_logentry_changelist"),
                },
                {
                    "title": _("Yaratilganlar"),
                    "link": lambda *args, **kwargs: reverse("admin:auditlog_logentry_changelist") + "?action__exact=0",
                },
                {
                    "title": _("O'zgartirilganlar"),
                    "link": lambda *args, **kwargs: reverse("admin:auditlog_logentry_changelist") + "?action__exact=1",
                },
                {
                    "title": _("O'chirilganlar"),
                    "link": lambda *args, **kwargs: reverse("admin:auditlog_logentry_changelist") + "?action__exact=2",
                },
                {
                    "title": _("Bugun"),
                    "link": lambda *args, **kwargs: reverse("admin:auditlog_logentry_changelist") + f"?timestamp__date={datetime.now().date()}",
                },
            ],
        },
    ],
}

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000