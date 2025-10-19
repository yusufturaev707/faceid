import os
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv
from django.urls import reverse_lazy
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
        'DIRS': [],
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

LANGUAGE_CODE = "en"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

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



# from django.templatetags.static import static
#
# UNFOLD = {
#     "SITE_TITLE": "Custom suffix in <title> tag",
#     "SITE_HEADER": "Appears in sidebar at the top",
#     "SITE_SUBHEADER": "Appears under SITE_HEADER",
#     "SITE_DROPDOWN": [
#         {
#             "icon": "diamond",
#             "title": _("My site"),
#             "link": "https://example.com",
#         },
#         # ...
#     ],
#     "SITE_URL": "/",
#     # "SITE_ICON": lambda request: static("icon.svg"),  # both modes, optimise for 32px height
#     "SITE_ICON": {
#         "light": lambda request: static("icon-light.svg"),  # light mode
#         "dark": lambda request: static("icon-dark.svg"),  # dark mode
#     },
#     # "SITE_LOGO": lambda request: static("logo.svg"),  # both modes, optimise for 32px height
#     "SITE_LOGO": {
#         "light": lambda request: static("logo-light.svg"),  # light mode
#         "dark": lambda request: static("logo-dark.svg"),  # dark mode
#     },
#     "SITE_SYMBOL": "speed",  # symbol from icon set
#     "SITE_FAVICONS": [
#         {
#             "rel": "icon",
#             "sizes": "32x32",
#             "type": "image/svg+xml",
#             "href": lambda request: static("favicon.svg"),
#         },
#     ],
#     "SHOW_HISTORY": True, # show/hide "History" button, default: True
#     "SHOW_VIEW_ON_SITE": True, # show/hide "View on site" button, default: True
#     "SHOW_BACK_BUTTON": False, # show/hide "Back" button on changeform in header, default: False
#     "ENVIRONMENT": "sample_app.environment_callback", # environment name in header
#     "ENVIRONMENT_TITLE_PREFIX": "sample_app.environment_title_prefix_callback", # environment name prefix in title tag
#     "DASHBOARD_CALLBACK": "sample_app.dashboard_callback",
#     "THEME": "dark", # Force theme: "dark" or "light". Will disable theme switcher
#     "LOGIN": {
#         "image": lambda request: static("sample/login-bg.jpg"),
#         "redirect_after": lambda request: reverse_lazy("admin:APP_MODEL_changelist"),
#     },
#     "STYLES": [
#         lambda request: static("css/style.css"),
#     ],
#     "SCRIPTS": [
#         lambda request: static("js/script.js"),
#     ],
#     "BORDER_RADIUS": "6px",
#     "COLORS": {
#         "base": {
#             "50": "oklch(98.5% .002 247.839)",
#             "100": "oklch(96.7% .003 264.542)",
#             "200": "oklch(92.8% .006 264.531)",
#             "300": "oklch(87.2% .01 258.338)",
#             "400": "oklch(70.7% .022 261.325)",
#             "500": "oklch(55.1% .027 264.364)",
#             "600": "oklch(44.6% .03 256.802)",
#             "700": "oklch(37.3% .034 259.733)",
#             "800": "oklch(27.8% .033 256.848)",
#             "900": "oklch(21% .034 264.665)",
#             "950": "oklch(13% .028 261.692)",
#         },
#         "primary": {
#             "50": "oklch(97.7% .014 308.299)",
#             "100": "oklch(94.6% .033 307.174)",
#             "200": "oklch(90.2% .063 306.703)",
#             "300": "oklch(82.7% .119 306.383)",
#             "400": "oklch(71.4% .203 305.504)",
#             "500": "oklch(62.7% .265 303.9)",
#             "600": "oklch(55.8% .288 302.321)",
#             "700": "oklch(49.6% .265 301.924)",
#             "800": "oklch(43.8% .218 303.724)",
#             "900": "oklch(38.1% .176 304.987)",
#             "950": "oklch(29.1% .149 302.717)",
#         },
#         "font": {
#             "subtle-light": "var(--color-base-500)",  # text-base-500
#             "subtle-dark": "var(--color-base-400)",  # text-base-400
#             "default-light": "var(--color-base-600)",  # text-base-600
#             "default-dark": "var(--color-base-300)",  # text-base-300
#             "important-light": "var(--color-base-900)",  # text-base-900
#             "important-dark": "var(--color-base-100)",  # text-base-100
#         },
#     },
#     "EXTENSIONS": {
#         "modeltranslation": {
#             "flags": {
#                 "en": "🇬🇧",
#                 "fr": "🇫🇷",
#                 "nl": "🇧🇪",
#             },
#         },
#     },
#     "SIDEBAR": {
#         "show_search": False,  # Search in applications and models names
#         "command_search": False,  # Replace the sidebar search with the command search
#         "show_all_applications": False,  # Dropdown with all applications and models
#         "navigation": [
#             {
#                 "title": _("Navigation"),
#                 "separator": True,  # Top border
#                 "collapsible": True,  # Collapsible group of links
#                 "items": [
#                     {
#                         "title": _("Dashboard"),
#                         "icon": "dashboard",  # Supported icon set: https://fonts.google.com/icons
#                         "link": reverse_lazy("admin:index"),
#                         "badge": "sample_app.badge_callback",
#                         "permission": lambda request: request.user.is_superuser,
#                     },
#                     {
#                         "title": _("Users"),
#                         "icon": "people",
#                         "link": reverse_lazy("admin:auth_user_changelist"),
#                     },
#                 ],
#             },
#         ],
#     },
#     "TABS": [
#         {
#             "models": [
#                 "app_label.model_name_in_lowercase",
#             ],
#             "items": [
#                 {
#                     "title": _("Your custom title"),
#                     "link": reverse_lazy("admin:app_label_model_name_changelist"),
#                     "permission": "sample_app.permission_callback",
#                 },
#             ],
#         },
#     ],
# }
#
#
# def dashboard_callback(request, context):
#     """
#     Callback to prepare custom variables for index template which is used as dashboard
#     template. It can be overridden in application by creating custom admin/index.html.
#     """
#     context.update(
#         {
#             "sample": "example",  # this will be injected into templates/admin/index.html
#         }
#     )
#     return context
#
#
# def environment_callback(request):
#     """
#     Callback has to return a list of two values represeting text value and the color
#     type of the label displayed in top right corner.
#     """
#     return ["Production", "danger"] # info, danger, warning, success
#
#
# def badge_callback(request):
#     return 3
#
# def permission_callback(request):
#     return request.user.has_perm("sample_app.change_model")