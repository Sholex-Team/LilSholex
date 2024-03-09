from pathlib import Path
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRETS_PATH = Path('/run/secrets')
with open(SECRETS_PATH / 'secret_key') as secret_file:
    SECRET_KEY = secret_file.read().removesuffix('\n')

# PersianMeme
with open(SECRETS_PATH / 'persianmeme_token') as persian_meme_token:
    MEME = persian_meme_token.read().removesuffix('\n')
with open(SECRETS_PATH / 'persianmeme_channel') as persian_meme_channel:
    MEME_CHANNEL = persian_meme_channel.read().removesuffix('\n')
with open(SECRETS_PATH / 'persianmeme_logs') as persian_meme_logs:
    MEME_LOGS = persian_meme_logs.read().removesuffix('\n')
with open(SECRETS_PATH / 'persianmeme_messages') as persian_meme_messages:
    MEME_MESSAGES = persian_meme_messages.read().removesuffix('\n')
with open(SECRETS_PATH / 'persianmeme_help_messages') as persian_meme_help_messages:
    MEME_HELP_MESSAGES = persian_meme_help_messages.read()
with open(SECRETS_PATH / 'persianmeme_reports') as persian_meme_reports:
    MEME_REPORTS_CHANNEL = persian_meme_reports.read().removesuffix('\n')
ID_KEY = 'id:'
EMPTY_CAPTION_KEY = '@ '
SEARCH_CAPTION_KEY = ' @ '
NAMES_KEY = 'names:'
TAGS_KEY = 'tags:'
VOICES_KEY = 'voices:'
VIDEOS_KEY = 'videos:'
SENSITIVE_WORDS = (NAMES_KEY, TAGS_KEY, VOICES_KEY, VIDEOS_KEY)
MAX_TAG_LENGTH = 20
SENSITIVE_CHARACTERS = {'<', '>', '(', ')', '+', '*', '"', '@', '~', '%', '-'}

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
with open(SECRETS_PATH / 'domain') as domain_file:
    ALLOWED_HOSTS = [domain_file.read().removesuffix('\n'), 'localhost']
# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'persianmeme.apps.PersianmemeConfig'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'LilSholex.middleware.TelegramMiddleware',
    'LilSholex.middleware.CSessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'LilSholex.middleware.CAuthenticationMiddleware',
    'LilSholex.middleware.CMessageMiddleware',
]

ROOT_URLCONF = 'LilSholex.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR.joinpath('templates')],
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

WSGI_APPLICATION = 'LilSholex.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases
with open(SECRETS_PATH / 'db_password') as db_password:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'lilsholex',
            'CONN_MAX_AGE': 28780,
            'CONN_HEALTH_CHECKS': True,
            'USER': 'sholex',
            'PASSWORD': db_password.read().removesuffix('\n'),
            'HOST': 'db',
            'PORT': 3306,
            'OPTIONS': {'charset': 'utf8mb4'}
        }
    }
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'

# Pagination Limit Broadcast
PAGINATION_LIMIT = 1500
BROADCAST_LIMIT = 20
BROADCAST_CONNECTION_LIMIT = 20

# Admin Panel
MAX_FAKE_VOTE = 80
MIN_FAKE_VOTE = 40

# Timeouts
REQUESTS_TIMEOUT = 0.7
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.PyMemcacheCache',
        'LOCATION': 'memcached:11211'
    }
}
TELEGRAM_HEADER_NAME = 'HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN'
with open(SECRETS_PATH / 'webhook_token') as webhook_token_file:
    WEBHOOK_TOKEN = webhook_token_file.read().removesuffix('\n')
SPAM_COUNT = 10
SPAM_TIME = 5
SPAM_PENALTY = 1800
VIOLATION_REPORT_LIMIT = 5
VIDEO_DURATION_LIMIT = 240
VIDEO_SIZE_LIMIT = 20971520
# Celery
CELERY_BROKER_URL = 'amqp://guest:guest@rabbitmq:5672/'
CELERY_WORKER_STATE_DB = str(BASE_DIR / 'state' / 'celery_state')
CELERY_ACKS_LATE = True
REVOKE_REVIEW_COUNTDOWN = 3600
CHECK_MEME_COUNTDOWN = 21600
# CSRF
CSRF_TRUSTED_ORIGINS = [f'https://{ALLOWED_HOSTS[0]}']
