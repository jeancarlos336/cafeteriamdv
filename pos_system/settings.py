from pathlib import Path
import os
import dj_database_url
from django.contrib.messages import constants as messages

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-+4lg&gtmccmp9&^+*^a&9mfhimx&g#&66vfg=mg!0t&36rv$)m"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['cafeteriamdv.herokuapp.com']

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "ventas",  # Asegúrate de que esta es tu app principal
    "django.contrib.humanize",
    "crispy_forms",
    "widget_tweaks",
]

CRISPY_TEMPLATE_PACK = 'bootstrap5'

# Configuración de autenticación
LOGIN_URL = 'login'  # Esto redirige a la vista de login si no está autenticado
LOGIN_REDIRECT_URL = 'dashboard'  # Esto redirigirá a la vista dashboard después de iniciar sesión

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",  # Mantener este para la seguridad en producción
    "whitenoise.middleware.WhiteNoiseMiddleware",     # Agrega este para servir archivos estáticos en Heroku
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "pos_system.urls"

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'pos_system' / 'ventas' / 'templates',  # Aquí debe estar la ruta correcta a tus plantillas
        ],
        'APP_DIRS': True,  # Asegúrate de que esté activado para buscar plantillas dentro de las apps
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

WSGI_APPLICATION = "pos_system.wsgi.application"

# Database
# Configuración para Heroku
if 'DATABASE_URL' in os.environ:
    DATABASES = {
        'default': dj_database_url.config(conn_max_age=600, ssl_require=True)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'puntodeventa',
            'USER': 'jortega',
            'PASSWORD': 'Carlos.2024',
            'HOST': 'localhost',
            'PORT': '5432',
        }
    }

# Seguridad
SECURE_SSL_REDIRECT = True  # Redirige HTTP a HTTPS en producción
SECURE_HSTS_SECONDS = 31536000  # Habilita HSTS con un valor de 1 año (ajústalo según tus necesidades)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Password validation
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

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'

# Configuración de archivos estáticos para Heroku
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # Asegúrate de tener esta carpeta para los archivos recolectados

# Rutas adicionales donde Django buscará archivos estáticos
STATICFILES_DIRS = [
    BASE_DIR / "static",  # Si tienes archivos estáticos adicionales, ajústalo según sea necesario
]

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Configuración de mensajes
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'
MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'error',
}
