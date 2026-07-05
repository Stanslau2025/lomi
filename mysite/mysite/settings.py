import os
from pathlib import Path
from urllib.parse import quote

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_local_env() -> None:
    for env_path in (BASE_DIR.parent / "lomi-apple.env", BASE_DIR / ".env"):
        if not env_path.exists():
            continue
        for raw_line in env_path.read_text().splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


_load_local_env()


redis_url = os.environ.get("REDIS_URL")
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": redis_url,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
    if redis_url
    else {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}


SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-change-me-before-production",
)

DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() == "true"


def _split_env(name: str, default: str = "") -> list[str]:
    value = os.getenv(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


def _append_unique(items: list[str], value: str) -> None:
    if value and value not in items:
        items.append(value)


ALLOWED_HOSTS = _split_env(
    "DJANGO_ALLOWED_HOSTS",
    f"127.0.0.1,localhost,testserver,{os.getenv('RENDER_EXTERNAL_HOSTNAME', '')}",
)
for host in ("127.0.0.1", "localhost", "testserver"):
    _append_unique(ALLOWED_HOSTS, host)

CSRF_TRUSTED_ORIGINS = [
    host
    for host in _split_env("DJANGO_CSRF_TRUSTED_ORIGINS")
    if host.startswith("http://") or host.startswith("https://")
]
render_hostname = os.getenv("RENDER_EXTERNAL_HOSTNAME")
if render_hostname:
    _append_unique(CSRF_TRUSTED_ORIGINS, f"https://{render_hostname}")

PUBLIC_SITE_URL = os.getenv("LOMI_PUBLIC_SITE_URL", "").strip()
if PUBLIC_SITE_URL.startswith(("http://", "https://")):
    _append_unique(CSRF_TRUSTED_ORIGINS, PUBLIC_SITE_URL)


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework.authtoken",
    "store",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "store.middleware.SecurityHeadersMiddleware",
]

ROOT_URLCONF = "mysite.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "store.context_processors.lomi_store_context",
            ],
        },
    },
]

WSGI_APPLICATION = "mysite.wsgi.application"


def _postgres_database_url_from_env() -> str:
    db_name = os.getenv("POSTGRES_DB", "").strip()
    db_user = os.getenv("POSTGRES_USER", "").strip()
    db_password = os.getenv("POSTGRES_PASSWORD", "").strip()
    db_host = os.getenv("POSTGRES_HOST", "").strip()
    db_port = os.getenv("POSTGRES_PORT", "5432").strip() or "5432"
    sslmode = os.getenv("POSTGRES_SSLMODE", "require").strip()

    if not all((db_name, db_user, db_password, db_host)):
        return ""

    url = (
        f"postgresql://{quote(db_user)}:{quote(db_password)}"
        f"@{db_host}:{db_port}/{quote(db_name)}"
    )
    if sslmode:
        url = f"{url}?sslmode={quote(sslmode)}"
    return url


database_url = os.getenv("DATABASE_URL", "").strip()
if not database_url:
    database_url = _postgres_database_url_from_env()
database_uses_postgres = bool(
    database_url and database_url.startswith(("postgres://", "postgresql://"))
)
if not database_url:
    os.environ.pop("DATABASE_URL", None)
DATABASES = {
    "default": dj_database_url.config(
        default=database_url or f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=bool(database_uses_postgres and not DEBUG),
    )
}


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
TIME_ZONE = os.getenv("DJANGO_TIME_ZONE", "UTC")
USE_I18N = True
USE_TZ = True


STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 24,
    "DEFAULT_FILTER_BACKENDS": [
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
}

CORS_ALLOWED_ORIGINS = [
    origin
    for origin in _split_env("CORS_ALLOWED_ORIGINS")
    if origin.startswith("http://") or origin.startswith("https://")
]
if PUBLIC_SITE_URL.startswith(("http://", "https://")):
    _append_unique(CORS_ALLOWED_ORIGINS, PUBLIC_SITE_URL)
CORS_ALLOW_CREDENTIALS = True

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = os.getenv("DJANGO_SECURE_SSL_REDIRECT", "True").lower() == "true" and not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = os.getenv("DJANGO_SESSION_COOKIE_SAMESITE", "Lax")
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = os.getenv("DJANGO_CSRF_COOKIE_SAMESITE", "Lax")
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_RESOURCE_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

LOMI_API_BASE_URL = os.getenv("LOMI_API_BASE_URL", "/api")
ENVIRONMENT = os.getenv("ENVIRONMENT", "production" if not DEBUG else "development")
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_UPLOAD_PRESET = os.getenv("CLOUDINARY_UPLOAD_PRESET", "")


# Email settings: use console backend by default for local development.
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587") or 587)
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@localhost")
