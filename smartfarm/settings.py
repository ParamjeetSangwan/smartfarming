"""
Django settings for smartfarm project.
"""
import dj_database_url
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ── SECURITY ── (moved from hardcoded to env vars)
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-change-me-in-production')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

# ── API KEYS ── (all moved to .env)
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
WEATHER_API_KEY    = os.getenv('WEATHER_API_KEY')

# ── RAZORPAY ── (Test Mode keys from razorpay.com/app/keys)
RAZORPAY_KEY_ID     = os.getenv('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', '')

# ── LANGUAGE / i18n ──
LANGUAGE_CODE = 'en'
LANGUAGES = [
    ('en', 'English'),
    ('hi', 'Hindi'),
]
LOCALE_PATHS = [os.path.join(BASE_DIR, 'locale')]
USE_L10N = True

# ── INSTALLED APPS ──
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crops',
    'weather',
    'marketplace',
    'orders',
    'users',
    'widget_tweaks',
    'ai_recommendations',
    'admin_panel',
    'government_schemes',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'OAUTH_PKCE_ENABLED': True,
    }
}

SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_LOGIN_ON_GET = True


# ── MIDDLEWARE ── (ActivityLoggingMiddleware now activated)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'admin_panel.middleware.activity_logging.ActivityLoggingMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'smartfarm.urls'

# ── TEMPLATES ──
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'smartfarm.wsgi.application'

# ── DATABASE ──
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{os.path.join(BASE_DIR, 'db.sqlite3')}"
    )
}

# ── PASSWORD VALIDATION ──
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── INTERNATIONALIZATION ──
TIME_ZONE = 'UTC'
USE_TZ = True

# ── STATIC FILES ──
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ── MEDIA FILES ──
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ── SESSION ──
SESSION_EXPIRE_AT_BROWSER_CLOSE = True   # Expire when browser closes
SESSION_COOKIE_AGE = 86400               # Max 24 hours even if browser stays open
SESSION_SAVE_EVERY_REQUEST = False       # Don't extend on every request
SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # DB-backed sessions
# This ensures sessions are invalidated on server restart in development
SESSION_COOKIE_SECURE = False            # Set True in production with HTTPS

# ── DEFAULT PK ──
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── EMAIL ── (credentials from .env only)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# ── AUTH REDIRECTS ──
LOGIN_URL = '/'                          # Where @login_required sends unauthenticated users
LOGIN_REDIRECT_URL = '/users/dashboard/' # Where to go after login if no ?next= param
LOGOUT_REDIRECT_URL = '/'               # Where to go after logout

# ── PASSWORD RESET ──
PASSWORD_RESET_TIMEOUT = 86400

# ── LOGGING ── (now configured so ActivityLoggingMiddleware actually works)
LOG_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'admin_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'admin_activity.log'),
            'formatter': 'verbose',
        },
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'admin_activity': {
            'handlers': ['admin_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}