# -*- coding: utf-8 -*-
"""
Django settings for Bakround Applicant project.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""
from __future__ import absolute_import, unicode_literals

import environ
import os
import os.path

import raven
from boto.s3.connection import OrdinaryCallingFormat

ROOT_DIR = environ.Path(__file__) - 3  # (./bakround_applicant/settings/common.py - 3 = ./)
APPS_DIR = ROOT_DIR.path('bakround_applicant')

env = environ.Env()

# APP CONFIGURATION
# ------------------------------------------------------------------------------
DJANGO_APPS = [
    # Default Django apps:
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Admin
    'django.contrib.admin',

    'bakround_applicant',
]

THIRD_PARTY_APPS = [
    'crispy_forms',  # Form layouts
    'allauth',  # registration
    'allauth.account',  # registration
    'allauth.socialaccount',  # registration

    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.linkedin_oauth2',

    'cachalot',
    'webpack_loader'
]

# Apps specific for this project go here.
LOCAL_APPS = [
    # custom users app
    'bakround_applicant.users.apps.UsersConfig',
    # Your stuff: custom apps go here
    'bakround_applicant.sme_feedback',
    'bakround_applicant.scraping',
    'bakround_applicant.onet',
    'bakround_applicant.lookup',
    'bakround_applicant.employer',
    'bakround_applicant.score',
    'bakround_applicant.event',
    'bakround_applicant.usage',
    'bakround_applicant.scheduler',
    'bakround_applicant.ranking',
]

# See: https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# MIDDLEWARE CONFIGURATION
# ------------------------------------------------------------------------------
MIDDLEWARE = (
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'bakround_applicant.middleware.verification.VerificationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware'
)

# DEBUG
# ------------------------------------------------------------------------------
DEBUG = env.bool('DJANGO_DEBUG', False)

# FIXTURE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-FIXTURE_DIRS
FIXTURE_DIRS = (
    str(APPS_DIR.path('fixtures')),
)

# EMAIL CONFIGURATION
# ------------------------------------------------------------------------------
EMAIL_BACKEND = env('DJANGO_EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')

# MANAGER CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = (
    ("""Nate Symer""", 'nsymer@bakround.com')
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS

# DATABASE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': env('POSTGRES_DB'),
        'USER': env('POSTGRES_USER'),
        'PASSWORD': env('POSTGRES_PASSWORD'),
        'HOST': env('POSTGRES_HOST'),
        'PORT': env('POSTGRES_PORT'),
        'ATOMIC_REQUESTS': True,
        # AN - adding a limit here to see if this fixes an issue with connections staying open
        'CONN_MAX_AGE': 20
    }
}

# DATE & TIME
# ------------------------------------------------------------------------------

TIME_ZONE = 'America/Los_Angeles' # For list of time zones, see http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
LANGUAGE_CODE = 'en-us' # https://docs.djangoproject.com/en/dev/ref/settings/#language-code
SITE_ID = 1 # https://docs.djangoproject.com/en/dev/ref/settings/#site-id
USE_I18N = True # https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_L10N = True # https://docs.djangoproject.com/en/dev/ref/settings/#use-l10n
USE_TZ = True # https://docs.djangoproject.com/en/dev/ref/settings/#use-tz

# TEMPLATE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES = [
    {
        # See: https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-TEMPLATES-BACKEND
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-dirs
        'DIRS': [
            str(APPS_DIR.path('templates')),
        ],
        'OPTIONS': {
            # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-debug
            'debug': DEBUG,
            # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-loaders
            # https://docs.djangoproject.com/en/dev/ref/templates/api/#loader-types
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
            # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                # Your stuff: custom template context processors go here
                'django_settings_export.settings_export',
            ],
        },
    },
]

# See: http://django-crispy-forms.readthedocs.io/en/latest/install.html#template-packs
CRISPY_TEMPLATE_PACK = 'bootstrap4'

# We always run Django in Docker, behind load balancers. In fact,
# our application servers don't each have their own IP (in addition to the load
# balancer's IP)
ALLOWED_HOSTS = ["*"]

# AWS Configuration
# ------------------------------------------------------------------------------

# Configure Global S3/AWS settings
AWS_ACCESS_KEY_ID = env('DJANGO_AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = env('DJANGO_AWS_SECRET_ACCESS_KEY')
AWS_S3_CALLING_FORMAT = OrdinaryCallingFormat()
AWS_DEFAULT_ACL = 'public-read' # for when django-storages changes behavior in version 2.0
AWS_QUERYSTRING_AUTH = False

# Sets bucket cache control (see config.storages.BaseS3Storage).
# don't change unless you know what you're doing:
AWS_EXPIRY = 60 * 60 * 24 * 7

# Set up our bucket names
S3_STATIC_BUCKET = env("DJANGO_AWS_STATIC_BUCKET", default=None)
S3_MEDIA_BUCKET = env("DJANGO_AWS_MEDIA_BUCKET", default=None)

# STATIC FILE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = str(ROOT_DIR('staticfiles'))

# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = '/static/'

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = (
    str(APPS_DIR.path('static')),
)

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

# MEDIA CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = str(APPS_DIR('media'))

# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = '/media/'

# URL Configuration
# ------------------------------------------------------------------------------
ROOT_URLCONF = 'bakround_applicant.urls'

# PASSWORD VALIDATION
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators
# ------------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    }
]

# AUTHENTICATION CONFIGURATION
# ------------------------------------------------------------------------------
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_ALLOW_REGISTRATION = True
ACCOUNT_ADAPTER = 'bakround_applicant.users.adapters.AccountAdapter'
SOCIALACCOUNT_ADAPTER = 'bakround_applicant.users.adapters.SocialAccountAdapter'
SOCIALACCOUNT_AUTO_SIGNUP = False

# Custom user app defaults
# Select the correct user model
AUTH_USER_MODEL = 'users.User'
LOGIN_REDIRECT_URL = 'users:redirect'
LOGIN_URL = 'account_login'
ACCOUNT_LOGOUT_REDIRECT_URL = "/accounts/signup/employer"

# SLUGLIFIER
AUTOSLUG_SLUGIFY_FUNCTION = 'slugify.slugify'

# Location of root django.contrib.admin URL, use {% url 'admin:index' %}
ADMIN_URL = r'^admin/'

# Your common stuff: Below this line define 3rd party library settings
# ------------------------------------------------------------------------------

# LOGGING CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#logging
# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s '
                      '%(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True
        },
        'django.security.DisallowedHost': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False
        }
    }
}


ACCOUNT_FORMS = {
    "signup": "bakround_applicant.forms.BakroundSignupForm"
}
SOCIALACCOUNT_FORMS = {
    "signup": "bakround_applicant.forms.BakroundSocialSignupForm"
}

SESSION_EXPIRE_AT_BROWSER_CLOSE = True
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_USER_DISPLAY = (lambda user: user.email)

# CACHING
# ------------------------------------------------------------------------------
REDIS_LOCATION = "redis://{}:{}/0".format(env('REDIS_HOST'),env('REDIS_PORT'))

# Heroku URL does not pass the DB number, so we parse it in
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_LOCATION,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'IGNORE_EXCEPTIONS': True,  # mimics memcache behavior.
                                        # http://niwinz.github.io/django-redis/latest/#_memcached_exceptions_behavior
        }
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

CACHALOT_ENABLED = True
CACHALOT_TIMEOUT = 3600
CACHALOT_ONLY_CACHABLE_TABLES = frozenset(['lookup_country',
                                           'lookup_state',
                                           'lookup_degree_major',
                                           'lookup_degree_name',
                                           'lookup_degree_type',
                                           'skill',
                                           'certification',
                                           'lookup_plan_limit',
                                           'lookup_physical_location',
                                           'employer_saved_search',
                                           'bg_position_master'])

USE_GOOGLE_ANALYTICS = False

USE_HOTJAR = env.bool('USE_HOTJAR', default=False)

SETTINGS_EXPORT = [
    'USE_GOOGLE_ANALYTICS',
    'USE_HOTJAR'
]

WEBPACK_LOADER = {
    'DEFAULT': {
        'CACHE': False,
        'BUNDLE_DIR_NAME': 'bundles/', # must end with slash
        'STATS_FILE': str(ROOT_DIR('webpack-stats.json')),
        'POLL_INTERVAL': 0.1,
        'TIMEOUT': None,
        'IGNORE': ['.+\.hot-update.js', '.+\.map']
    }
}

WEBSITE_ROOT_URL = env('WEBSITE_ROOT_URL', default='https://my.bakround.com').rstrip('/')
