import os
from datetime import timedelta
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent
APPS_DIR = ROOT_DIR / "apps"

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")

DEBUG = int(os.getenv("DJANGO_DEBUG"))

hosts = os.getenv("DJANGO_ALLOWED_HOSTS")
ALLOWED_HOSTS = hosts.split(", ") if hosts else ["*"]

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "rest_framework_simplejwt",
    "drf_yasg",
    "drf_api_logger",
    "django_filters",
]

LOCAL_APPS = [
    "users",
    "apps.example",
    "apps.shared",
    "common",
    "business",
    "console",
    "transaction",
    "dispute",
    "notifications",
    "merchant",
    "blog",
]

INSTALLED_APPS = LOCAL_APPS + DJANGO_APPS + THIRD_PARTY_APPS

DEFAULT_MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
CUSTOM_MIDDLEWARE = [
    "common.middleware.CustomCorsMiddleware",
    "drf_api_logger.middleware.api_logger_middleware.APILoggerMiddleware",
]


MIDDLEWARE = DEFAULT_MIDDLEWARE + CUSTOM_MIDDLEWARE

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:5500",
    "http://mybalanceapp.com",
    "https://mybalanceapp.com",
    "https://mybalanceapp.netlify.app",
    "https://api.mybalanceapp.com",
    "http://staging-api.mybalanceapp.com",
    "https://staging-api.mybalanceapp.com",
    "https://mybalanceapp.netlify.app",
    "https://staging-mybalance-merch-redirect.netlify.app",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "https://staging-merchant-mybalanceapp.netlify.app",
    "https://merchant-mybalanceapp.netlify.app",
]

CORS_ORIGIN_WHITELIST = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://mybalanceapp.com",
    "https://mybalanceapp.com",
    "https://mybalanceapp.netlify.app",
    "https://api.mybalanceapp.com",
    "http://staging-api.mybalanceapp.com",
    "https://staging-api.mybalanceapp.com",
    "https://staging-merchant-mybalanceapp.netlify.app",
    "https://merchant-mybalanceapp.netlify.app",
    "http://localhost:5173",
    "http://127.0.0.1:5174",
    "http://0.0.0.0:5174",
    "http://localhost:5174",
    "http://localhost:5175",
]

CORS_EXPOSE_HEADERS = [
    "Cross-Origin-Opener-Policy",
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = True

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(ROOT_DIR, "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

db_name = os.getenv("POSTGRES_DB")
db_password = os.getenv("POSTGRES_PASSWORD")
db_host = os.getenv("POSTGRES_HOST")
db_user = os.getenv("POSTGRES_USER")
db_port = os.getenv("POSTGRES_PORT")

# mysql_name = os.getenv("MYSQL_DB")
# mysql_user = os.getenv("MYSQL_USER")
# mysql_password = os.getenv("MYSQL_PASSWORD")
# mysql_host = os.getenv("MYSQL_HOST")
# mysql_port = os.getenv("MYSQL_PORT")

# db_uri = f"mysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_name}"
db_uri = f"postgres://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

DATABASES = {"default": dj_database_url.parse(db_uri, conn_max_age=600)}
AUTH_USER_MODEL = "users.CustomUser"

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

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Africa/Lagos"

USE_I18N = True

USE_TZ = True

SITE_NAME = "MyBalance API"

SITE_ID = 1

STATIC_URL = "/staticfiles/"
STATIC_ROOT = str(ROOT_DIR / "staticfiles")
STATICFILES_DIRS = []
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

MEDIA_URL = "/mediafiles/"
MEDIA_ROOT = str(ROOT_DIR / "mediafiles")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(name)-12s %(asctime)s %(module)s "
            "%(process)d %(thread)d %(message)s"
        }
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        }
    },
    "root": {"level": "INFO", "handlers": ["console"]},
}

REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = os.environ.get("REDIS_PORT", 6379)
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", 6379)

CELERY_BROKER_URL = os.environ.get(
    "CELERY_BROKER", f"redis://{REDIS_HOST}:{REDIS_PORT}"
)
CELERY_RESULT_BACKEND = os.environ.get(
    "CELERY_BROKER", f"redis://{REDIS_HOST}:{REDIS_PORT}"
)


REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "apps.shared.exceptions.custom_handler",
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        # 'rest_framework.authentication.TokenAuthentication',
    ),
    # "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    # "PAGE_SIZE": 50,
    "DEFAULT_RENDERER_CLASSES": (
        "djangorestframework_camel_case.render.CamelCaseJSONRenderer",
        "djangorestframework_camel_case.render.CamelCaseBrowsableAPIRenderer",
    ),
    "DEFAULT_PARSER_CLASSES": (
        "djangorestframework_camel_case.parser.CamelCaseFormParser",
        "djangorestframework_camel_case.parser.CamelCaseMultiPartParser",
        "djangorestframework_camel_case.parser.CamelCaseJSONParser",
    ),
}

SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {
        "Bearer": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=3),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=3),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": False,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,
    "JWK_URL": None,
    "LEEWAY": 0,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",
}

SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {
        "Bearer": {"type": "apiKey", "name": "Authorization", "in": "header"}
    },
    "USE_SESSION_AUTH": False,
}

# DRF API LOGGER SETTINGS
DRF_API_LOGGER_DATABASE = True
DRF_API_LOGGER_SIGNAL = True
DRF_LOGGER_QUEUE_MAX_SIZE = 50
DRF_LOGGER_INTERVAL = 10
DRF_API_LOGGER_SKIP_NAMESPACE = []  # list of namespaces OR APPS to skip logging
DRF_API_LOGGER_SKIP_URL_NAME = []  # list of url names to skip logging
DRF_API_LOGGER_EXCLUDE_KEYS = [
    "password",
    "token",
    "access",
    "refresh",
]  # Sensitive data will be replaced with "***FILTERED***".
DRF_API_LOGGER_DEFAULT_DATABASE = "default"  # Database to use for logging
DRF_API_LOGGER_SLOW_API_ABOVE = (
    200  # Log slow API calls above this time in milliseconds
)
DRF_API_LOGGER_TIME_ZONE = "Africa/Lagos"  # see the API information in local timezone
DRF_API_LOGGER_PATH_TYPE = "ABSOLUTE"
DATA_UPLOAD_MAX_NUMBER_FIELDS = None

# EMAIL_HOST_PASSWORD = os.getenv("SENDGRID_API_KEY")
DEFAULT_FROM_EMAIL = os.getenv("FROM_EMAIL")

EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND")
EMAIL_HOST = os.environ.get("EMAIL_HOST")
EMAIL_PORT = os.environ.get("EMAIL_PORT")
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS")
