# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import os
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage, SpooledTemporaryFile
from django.contrib.staticfiles.storage import ManifestFilesMixin


class BaseS3Storage(S3Boto3Storage):
    auto_create_bucket = True
    object_parameters = {
        'CacheControl': 'max-age={}, s-maxage={}, must-revalidate'.format(settings.AWS_EXPIRY, settings.AWS_EXPIRY)
    }
    default_acl = 'public-read'  # Explicitly restate default

    # https://github.com/jschneier/django-storages/issues/382
    def _save_content(self, obj, content, parameters):
        """
        We create a clone of the content file as when this is passed to boto3 it wrongly closes
        the file upon upload where as the storage backend expects it to still be open
        """
        # Seek our content back to the start
        content.seek(0, os.SEEK_SET)

        # Create a temporary file that will write to disk after a specified size
        content_autoclose = SpooledTemporaryFile()

        # Write our original content into our copy that will be closed by boto3
        content_autoclose.write(content.read())

        # Upload the object which will auto close the content_autoclose instance
        super()._save_content(obj, content_autoclose, parameters)

        # Cleanup if this is fixed upstream our duplicate should always close
        if not content_autoclose.closed:
            content_autoclose.close()


class S3StaticStorage(ManifestFilesMixin, BaseS3Storage):
    manifest_strict = False
    bucket_name = settings.S3_STATIC_BUCKET


class S3MediaStorage(BaseS3Storage):
    bucket_name = settings.S3_MEDIA_BUCKET
