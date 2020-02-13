__author__ = 'ajaynayak'

import os
import boto
from django.conf import settings

class FileIO:
    bucket = None
    bucket_name = settings.S3_MEDIA_BUCKET

    def __init__(self, custom_bucket=None):
        conn = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)

        if custom_bucket is not None:
            self.bucket_name = custom_bucket

        self.bucket = conn.get_bucket(self.bucket_name, validate=False)

    def get_file_contents(self, file_name):
        key = self.bucket.get_key(file_name)

        if key is None:
            raise Exception('Key for the specified file_name does not exist')

        contents = key.get_contents_as_string()
        return contents

    def get_all_files(self, folder_name=''):
        file_keys = self.bucket.list(prefix='{}/'.format(folder_name) if folder_name is not '' else '')

        file_names = []
        for key in file_keys:
            if key.name == '{}/'.format(folder_name):
                continue
            else:
                file_names.append(key.name)

        return file_names

    def upload_file(self, file_name, file_bytes, folder_name='', public=False, metadata={}, content_type=None):
        # construct the full filename
        full_file_name = file_name
        if folder_name is not '':
            full_file_name = '{}/{}'.format(folder_name, full_file_name)

        key = boto.s3.key.Key(self.bucket, full_file_name)

        if content_type is not None:
            key.content_type = content_type

        if metadata is not None:
            # set the metadata
            for k in metadata.keys():
                key.set_metadata(k, metadata[k])

        key.set_contents_from_string(file_bytes)

        if public:
            key.set_acl('public-read')

        return full_file_name

    def delete_file(self, file_name, folder_name=''):
        # construct the full filename
        full_file_name = file_name
        if folder_name is not '':
            full_file_name = '{}/{}'.format(folder_name, full_file_name)

        key = boto.s3.key.Key(self.bucket, full_file_name)

        key.delete()

    def get_file_metadata(self, file_name, metadata_key_list=[]):
        key = self.bucket.get_key(file_name)

        if key is None:
            raise Exception('Key for the specified file_name does not exist')

        metadata_dict = {}

        for metadata_key in metadata_key_list:
            try:
                metadata_dict[metadata_key] = key.get_metadata(metadata_key)
            except:
                metadata_dict[metadata_key] = None
                pass

        return metadata_dict

