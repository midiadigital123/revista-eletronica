import os
from pathlib import Path
from urllib.parse import unquote, urlparse

BASE_DIR = Path(__file__).resolve().parent.parent

# Defaults só de desenvolvimento local; em produção vêm do .env.
# DEBUG desligado por padrão: o docker-compose de desenvolvimento liga (DJANGO_DEBUG=1, D-128).
CHAVE_DEV = "dev-inseguro-nao-usar-em-producao"
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or CHAVE_DEV
DEBUG = os.environ.get("DJANGO_DEBUG", "0").lower() in {"1", "true"}
if not DEBUG and SECRET_KEY == CHAVE_DEV:
    from django.core.exceptions import ImproperlyConfigured

    raise ImproperlyConfigured("Sem DEBUG, defina DJANGO_SECRET_KEY (a chave padrão é só de desenvolvimento).")
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "nucleo",  # antes do admin: sobrescreve admin/index.html e admin/base_site.html
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "simple_history",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
]

ROOT_URLCONF = "sistema.urls"
WSGI_APPLICATION = "sistema.wsgi.application"

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

# DATABASE_URL no formato postgres://usuario:senha@host:porta/banco
_db = urlparse(os.environ.get("DATABASE_URL") or "postgres://revista:revista@db:5432/revista")
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _db.path.lstrip("/"),
        "USER": unquote(_db.username or ""),
        "PASSWORD": unquote(_db.password or ""),
        "HOST": _db.hostname or "",
        "PORT": _db.port or "",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
