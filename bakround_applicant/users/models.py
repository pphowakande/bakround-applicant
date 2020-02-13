# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import base64
import uuid
from django.contrib.auth.models import AbstractUser
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist

class User(AbstractUser):

    # First Name and Last Name do not cover name patterns
    # around the globe.
    name = models.CharField(_('Name of User'), blank=True, max_length=255)
    tour_dismissed = models.BooleanField(blank=False, default=False)
    is_employer=models.BooleanField(default=False)
    referral_code = models.CharField(
                        max_length=300,
                        blank=True,
                        null=True,
                        default=None)
    api_key = models.CharField(
                        max_length=50,
                        blank=True,
                        null=True,
                        default=uuid.uuid4)
    initial_login_token = models.CharField(max_length=50,
                                           blank=True,
                                           null=True,
                                           unique=True)

    def __str__(self):
        return self.username

    def get_absolute_url(self):
        return reverse('users:detail', kwargs={'username': self.username})


class UserReferrer(models.Model):
    user = models.OneToOneField(User, primary_key=True, related_name='user_referrer', null=False, on_delete=models.DO_NOTHING)
    referrer = models.ForeignKey(User, related_name='users', null=False, on_delete=models.DO_NOTHING)

    class Meta:
        managed = True
        db_table = 'user_referrer'

# email is inherited from AbstractUser, so we add the index like this
User._meta.get_field('email').db_index = True

