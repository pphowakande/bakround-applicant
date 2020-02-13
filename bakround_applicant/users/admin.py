# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import django
from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as AuthUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from .models import User


class MyUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User


class MyUserCreationForm(UserCreationForm):
    error_message = UserCreationForm.error_messages.update({
        'duplicate_username': 'This username has already been taken.'
    })

    class Meta(UserCreationForm.Meta):
        model = User

    def clean_username(self):
        username = self.cleaned_data["username"]
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(self.error_messages['duplicate_username'])


@admin.register(User)
class MyUserAdmin(AuthUserAdmin):
    form = MyUserChangeForm
    add_form = MyUserCreationForm
    fieldsets = (
            ('User Profile', {'fields': ('name',)}),
    ) + AuthUserAdmin.fieldsets
    list_display = ('username', 'name', 'is_superuser')
    search_fields = ['name']


# add models to Django admin interface

from bakround_applicant.all_models import db


def register(model_class, fields, order='-id', textarea=None):
    class ModelAdmin(admin.ModelAdmin):
        list_display = fields
        ordering = [order]

        def formfield_for_dbfield(self, db_field, **kwargs):
            formfield = super().formfield_for_dbfield(db_field, **kwargs)
            if formfield and is_formfield_long(formfield):
                attrs = {"style": "min-width: 500px"}
                attrs.update(formfield.widget.attrs)
                print(attrs)
                formfield.widget = forms.Textarea(attrs=attrs)
            return formfield

    admin.site.register(model_class, ModelAdmin)


def is_formfield_long(formfield):
    if formfield and 'maxlength' in formfield.widget.attrs:
        try:
            return int(formfield.widget.attrs['maxlength']) >= 1000
        except Exception:
            pass
    return False


register(db.LookupCountry, ['id', 'country_name', 'country_code'],        'id')
register(db.LookupState,   ['id', 'country', 'state_name', 'state_code'], 'id')
register(db.LookupPhysicalLocation, ['id', 'city', 'state', 'latitude', 'longitude'], 'id')
register(db.LookupDegreeMajor, ['id', 'degree_major_name'], 'id')
register(db.LookupDegreeName, ['id', 'degree_type', 'degree_name', 'degree_abbreviation'], 'id')
register(db.LookupDegreeType, ['id', 'degree_type_name', 'degree_type_sovren', 'visible'], 'id')

register(db.Profile, ['id', 'user', 'last_name', 'middle_name', 'first_name', 'city', 'state'])
register(db.Skill, ['id', 'skill_name'])
register(db.Job, ['id', 'job_name'])
register(db.Certification, ['id', 'certification_name'])
register(db.ProfileExperience, ['id', 'profile', 'company_name'])
register(db.ProfileEducation, ['id', 'profile', 'school_name'])
register(db.ProfileSkill, ['id', 'profile', 'skill'])
register(db.ProfileCertification, ['id', 'profile', 'certification'])
register(db.ProfileResume, ['id', 'profile', 'parser_output'])

# TODO: register new models here!

register(db.JobSkill, ['id', 'job', 'skill'])
register(db.JobCertification, ['id', 'job', 'certification'])

register(db.EmailParseFailures, ['id', 'job_id', 'file_name'])
register(db.ProfileViewer, ['id', 'email', 'first_name', 'last_name'])
register(db.ProfileViewerAction, ['id', 'profile_viewer', 'action_name'])

register(db.Employer, ['id', 'company_name'])
register(db.EmployerCandidate, ['id', 'employer_job', 'profile', 'contacted', 'responded', 'accepted'])
register(db.EmployerJob, ['id', 'employer', 'job'])
register(db.EmployerUser, ['id', 'employer', 'user'])
register(db.EmployerJobUser, ['id', 'employer_job', 'employer_user'])
register(db.EmployerCandidateResponse, ['id', 'response'])

register(db.SME, ['id', 'first_name', 'last_name', 'job'])
register(db.SMEFeedback, ['id', 'sme', 'profile_resume', 'bscore_value', 'should_interview',
                          'wrong_job', 'wrong_language', 'incomplete'])
register(db.SMEAction, ['id', 'sme', 'profile_resume', 'action_name'])
register(db.SMEPayRate, ['id', 'sme', 'pay_rate', 'effective_date'])

register(db.Score, ['id', 'profile', 'job', 'score_value', 'algorithm_version'])
register(db.ScoreRequest, ['id', 'profile', 'job', 'score', 'user_generated', 'completed'])

register(db.ScraperJob, ['id', 'job'])
register(db.ScraperLogin, ['id', 'user_name', 'source', 'enabled', 'adjusted_failure_count'])

# Add the rest of the models.
for model in db.__dict__.values():
    if isinstance(model, django.db.models.base.ModelBase) and \
                not model._meta.abstract and \
                hasattr(model, 'id'):
        try:
            register(model, ['id'])
        except django.contrib.admin.sites.AlreadyRegistered:
            pass
