# -*- coding: utf-8 -*-
"""
Production Configurations

- Use Amazon's S3 for storing static files and uploaded media
- Use mailgun to send emails
- Use Redis for cache
"""

from __future__ import absolute_import, unicode_literals
from .common import *  # noqa

# SECRET CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
# Raises ImproperlyConfigured exception if DJANGO_SECRET_KEY not in os.environ
SECRET_KEY = env('DJANGO_SECRET_KEY')

# MIDDLEWARE
# ------------------------------------------------------------------------------

CORS_MIDDLEWARE = (
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
)

MIDDLEWARE = CORS_MIDDLEWARE + MIDDLEWARE

# SECURITY CONFIGURATION
# ------------------------------------------------------------------------------
# See https://docs.djangoproject.com/en/1.9/ref/middleware/#module-django.middleware.security
# and https://docs.djangoproject.com/ja/1.9/howto/deployment/checklist/#run-manage-py-check-deploy

# set this to 60 seconds and then to 518400 when you can prove it works
SECURE_HSTS_SECONDS = 60
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool(
    'DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True)
SECURE_CONTENT_TYPE_NOSNIFF = env.bool(
    'DJANGO_SECURE_CONTENT_TYPE_NOSNIFF', default=True)
SECURE_BROWSER_XSS_FILTER = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = 'DENY'
CORS_ORIGIN_WHITELIST_REGEX = (r'^(https?://)?(\\w+\.)?(bakround\.com|indeed\.com|linkedin\.com)$',)

# SITE CONFIGURATION
# ------------------------------------------------------------------------------

# See: http://django-storages.readthedocs.io/en/latest/index.html
INSTALLED_APPS += (
    'storages',
    'corsheaders',
)

MEDIA_URL = 'https://s3.amazonaws.com/%s/' % S3_MEDIA_BUCKET
STATIC_URL = 'https://s3.amazonaws.com/%s/' % S3_STATIC_BUCKET

STATICFILES_STORAGE = 'bakround_applicant.utilities.storages.S3StaticStorage'
DEFAULT_FILE_STORAGE = 'bakround_applicant.utilities.storages.S3MediaStorage'

# EMAIL
# ------------------------------------------------------------------------------
DEFAULT_FROM_EMAIL = env('DJANGO_DEFAULT_FROM_EMAIL',
                         default='Bakround <noreply@bakround.com>')
EMAIL_SUBJECT_PREFIX = env('DJANGO_EMAIL_SUBJECT_PREFIX', default='[Bakround] ')
SERVER_EMAIL = env('DJANGO_SERVER_EMAIL', default=DEFAULT_FROM_EMAIL)

# Anymail with Mailgun
INSTALLED_APPS += ("anymail", )
ANYMAIL = {
    "SENDGRID_API_KEY": env('DJANGO_SENDGRID_API_KEY'),
}
EMAIL_BACKEND = "anymail.backends.sendgrid.SendGridBackend"

# TEMPLATE & FRONTEND CONFIGURATION
# ------------------------------------------------------------------------------
# See:
# https://docs.djangoproject.com/en/dev/ref/templates/api/#django.template.loaders.cached.Loader
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', TEMPLATES[0]['OPTIONS']['loaders'])
]

USE_GOOGLE_ANALYTICS = True

WEBPACK_LOADER['DEFAULT'].update({
    'CACHE': True,
})

