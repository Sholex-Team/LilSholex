from pathlib import Path
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRETS_PATH = Path('/run/secrets')
with open(SECRETS_PATH / 'secret_key') as secret_file:
    SECRET_KEY = secret_file.read().removesuffix('\n')
with open(SECRETS_PATH / 'persianmeme_token') as persian_meme_token:
    MEME = persian_meme_token.read().removesuffix('\n')
with open(SECRETS_PATH / 'persianmeme_channel') as persian_meme_channel:
    MEME_CHANNEL = persian_meme_channel.read().removesuffix('\n')
with open(SECRETS_PATH / 'persianmeme_anim') as persian_meme_anim:
    MEME_ANIM = persian_meme_anim.read().removesuffix('\n')
with open(SECRETS_PATH / 'persianmeme_logs') as persian_meme_logs:
    MEME_LOGS = persian_meme_logs.read().removesuffix('\n')
with open(SECRETS_PATH / 'persianmeme_messages') as persian_meme_messages:
    MEME_MESSAGES = persian_meme_messages.read().removesuffix('\n')
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
    'background_task',
    'persianmeme.apps.PersianmemeConfig'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
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
            'USER': 'sholex',
            'PASSWORD': db_password.read().removesuffix('\n'),
            'HOST': 'db',
            'PORT': 3306,
            'OPTIONS': {'charset': 'utf8mb4'}
        }
    }
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
STATIC_ROOT = BASE_DIR.joinpath('static')
MAX_ATTEMPTS = 2
BACKGROUND_TASK_RUN_ASYNC = True
BACKGROUND_TASK_ASYNC_THREADS = 4

# Pagination Limit Broadcast
PAGINATION_LIMIT = 1500
BROADCAST_LIMIT = 20
BROADCAST_CONNECTION_LIMIT = 20
