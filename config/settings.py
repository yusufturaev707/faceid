import os
from datetime import timedelta, datetime
from pathlib import Path

from django.conf import settings
from dotenv import load_dotenv
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from decouple import config

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
    "channels",
    "django_filters",
    "pgvector.django",
    "import_export",

    #Apps
    'face.apps.FaceConfig',
    'users.apps.UsersConfig',
    'region.apps.RegionConfig',
    'exam.apps.ExamConfig',
    'access_control.apps.AccessControlConfig',
    'supervisor.apps.SupervisorConfig',
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
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
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
    "SITE_TITLE": "FACE ID",
    "SITE_HEADER": "FACE ID ADMIN",
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
    "SITE_SYMBOL": "school",  # symbol from icon set
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
                "separator": False,
                "collapsible": False,
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
                "separator": False,  # Top border
                "collapsible": False,
                "icon": "chart-bar",
                "items": [
                    {
                        "title": _("Tadbirlar"),
                        "icon": "assignment",
                        "link": reverse_lazy("admin:exam_exam_changelist"),
                        "permission": lambda request: request.user.is_admin or request.user.is_central or request.user.is_delegate,
                    },
                    {
                        "title": _("Tadbirda nazoratchilar"),
                        "icon": "guardian",
                        "link": reverse_lazy("admin:supervisor_eventsupervisor_changelist"),
                        "permission": lambda request: request.user.is_admin or request.user.is_central or request.user.is_delegate,
                    },
                    {
                        "title": _("Testda turniketlar"),
                        "icon": "door_sliding",
                        "link": reverse_lazy("admin:exam_examzoneswingbar_changelist"),
                        "permission": lambda request: request.user.is_admin or request.user.is_central or request.user.is_delegate,
                    },
                    {
                        "title": _("Holatlar"),
                        "icon": "data_check",
                        "link": reverse_lazy("admin:exam_examstate_changelist"),
                        "permission": lambda request: request.user.is_admin,
                    },
                ],
            },
            {
                "title": _("Studentlar va kirishlar tarixi"),
                "separator": False,  # Top border
                "collapsible": False,  # Collapsible group of links
                "items": [
                    {
                        "title": _("Studentlar"),
                        "icon": "person_shield",
                        "link": reverse_lazy("admin:exam_student_changelist"),
                        "permission": lambda request: request.user.is_admin or request.user.is_central or request.user.is_delegate,
                    },
                    {
                        "title": _("Kirishlar tarixi"),
                        "icon": "footprint",
                        "link": reverse_lazy("admin:exam_studentlog_changelist"),
                        "permission": lambda request: request.user.is_admin or request.user.is_central
                    },
                    {
                        "title": _("Chetlatilganlar"),
                        "icon": "person_off",
                        "link": reverse_lazy("admin:exam_cheating_changelist"),
                        "permission": lambda request: request.user.is_admin or request.user.is_central or request.user.is_delegate,
                    },
                    {
                        "title": _("Qora ro'yxat"),
                        "icon": "skull_list",
                        "link": reverse_lazy("admin:exam_studentblacklist_changelist"),
                        "permission": lambda request: request.user.is_admin or request.user.is_central,
                    },
                ],
            },
            {
                "title": _("Xodim va nazoratchilar"),
                "separator": False,  # Top border
                "collapsible": False,
                "icon": "chart-bar",
                "items": [
                    {
                        "title": _("Nazoratchilar"),
                        "icon": "guardian",
                        "link": reverse_lazy("admin:supervisor_supervisor_changelist"),
                        "permission": lambda request: request.user.is_admin or request.user.is_central or request.user.is_delegate,
                    },
                    {
                        "title": _("Binoga kirish tarixi"),
                        "icon": "footprint",
                        "link": reverse_lazy("admin:access_control_normaluserlog_changelist"),
                        "permission": lambda request: request.user.is_admin or request.user.is_central,
                    },
                ],
            },
            {
                "title": _("Hudud va turniketlar"),
                "separator": False,  # Top border
                "collapsible": True,  # Collapsible group of links
                "items": [
                    {
                        "title": _("Turniketlar"),
                        "icon": "door_sliding",
                        "link": reverse_lazy("admin:region_swingbarrier_changelist"),
                        "permission": lambda request: request.user.is_admin or request.user.is_central or request.user.is_delegate,
                    },
                    {
                        "title": _("Binolar"),
                        "icon": "add_home_work",
                        "link": reverse_lazy("admin:region_zone_changelist"),
                        "permission": lambda request: request.user.is_admin or request.user.is_central or request.user.is_delegate,
                    },
                    {
                        "title": _("Viloyatlar"),
                        "icon": "explore_nearby",
                        "link": reverse_lazy("admin:region_region_changelist"),
                        "permission": lambda request: request.user.is_admin or request.user.is_central,
                    },
                ],
            },
            {
                "title": _("Test turlari"),
                "separator": False,  # Top border
                "collapsible": True,  # Collapsible group of links
                "items": [
                    {
                        "title": _("Turlar"),
                        "icon": "assignment",
                        "link": reverse_lazy("admin:exam_test_changelist"),
                        "permission": lambda request: request.user.is_admin or request.user.is_central or request.user.is_delegate,
                    },
                    {
                        "title": _("Smena"),
                        "icon": "alarm_on",
                        "link": reverse_lazy("admin:exam_shift_changelist"),
                        "permission": lambda request: request.user.is_admin or request.user.is_central,
                    },
                    {
                        "title": _("Chetlatish sabablari"),
                        "icon": "dataset",
                        "link": reverse_lazy("admin:exam_reason_changelist"),
                        "permission": lambda request: request.user.is_admin or request.user.is_central,
                    },
                ],
            },
            {
                "title": _("Foydalanuvchilar"),
                "separator": False,  # Top border
                "collapsible": True,  # Collapsible group of links
                "items": [
                    {
                        "title": _("Foydalanuvchilar"),
                        "icon": "badge",
                        "link": reverse_lazy("admin:users_user_changelist"),
                        "permission": lambda request: request.user.is_admin or request.user.is_central,
                    },
                    {
                        "title": _("Rol"),
                        "icon": "add_moderator",
                        "link": reverse_lazy("admin:users_role_changelist"),
                        "permission": lambda request: request.user.is_admin,
                    },
                ],
            },
            {
                "title": _("Tizim monitoring"),
                "separator": False,  # Top border
                "collapsible": True,  # Collapsible group of links
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


# Channels Layer (Redis)
REDIS_HOST = os.environ.get('REDIS_HOST', '127.0.0.1')
REDIS_PORT = os.environ.get('REDIS_PORT', 6379)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(REDIS_HOST, REDIS_PORT)],
        },
    },
}

# CORS sozlamalari
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React monitor
    "http://localhost:5173",  # Vite
]
CSRF_TRUSTED_ORIGINS = ['http://localhost:8000', 'http://127.0.0.1:8000']

# Celery sozlamalari
# CELERY_BROKER_URL = 'redis://localhost:6379/0'
# CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
# CELERY_ACCEPT_CONTENT = ['json']
# CELERY_TASK_SERIALIZER = 'json'
# CELERY_RESULT_SERIALIZER = 'json'
#
# # Cache sozlamalari
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
#
# SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
# SESSION_CACHE_ALIAS = 'default'