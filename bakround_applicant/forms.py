__author__ = "tplick"
__date__ = "December 22, 2016"

from collections import OrderedDict, defaultdict

from django.forms import Form, FileField, ValidationError, ModelChoiceField, CharField, FileField
from django.forms.fields import ChoiceField
from django.db.models import Q
from django.template.defaultfilters import filesizeformat
from django.conf import settings

from allauth.account.forms import SignupForm
from allauth.socialaccount.forms import SignupForm as SocialSignupForm

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit

from .all_models.db import LookupState, LookupIndustry, Job, JobFamily
from .utilities.functions import make_job_structure_for_dropdown, make_choice_set_for_state_codes


class JobModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
         return obj.job_name

class StateChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.state_code


def make_state_choice_field(required):
    return StateChoiceField(queryset=LookupState.objects.all().order_by('state_code'),
                            required=required)

class RestrictedFileField(FileField):
    def __init__(self, *args, **kwargs):
        content_types = kwargs.pop('content_types', None)
        if content_types is not None:
            self.content_types = content_types
        self.max_upload_size = kwargs.pop('max_upload_size', None)
        if not self.max_upload_size:
            self.max_upload_size = settings.MAX_UPLOAD_SIZE
        super().__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        data = super().clean(*args, **kwargs)
        try:
            if data.content_type in self.content_types:
                if data.size > self.max_upload_size:
                    raise ValidationError('File size must be under {}. Current file size is {}.'.format(filesizeformat(self.max_upload_size), filesizeformat(data.size)))
            else:
                raise ValidationError('File type is not supported.')
        except AttributeError:
            pass

        return data

# # http://stackoverflow.com/questions/12303478/how-to-customize-user-profile-when-using-django-allauth
class BakroundSignupForm(SignupForm):
    primary_occupation = ChoiceField([])
    password2 = None
    city = CharField(label='City', required=False)
    state = ChoiceField([], required=False)
    first_name = CharField(label='First Name', required=False)
    last_name = CharField(label='Last Name', required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = make_form_helper()

        fields = self.fields
        job_structure = make_job_structure_for_dropdown(True)
        fields['primary_occupation'] = ChoiceField(change_unselected_display(job_structure, 'Primary Occupation'))
        fields['state'].choices = make_choice_set_for_state_codes('State')

        set_placeholder(fields, 'first_name', 'First Name')
        set_placeholder(fields, 'last_name', 'Last Name')
        set_placeholder(fields, 'city', 'City')
        set_placeholder(fields, 'email', 'Email Address')
        set_placeholder(fields, 'password1', 'Set a Password')

    # def signup(self, request, user):
    #
    #     super().signup(request, user)
    #
        # user.save()


def set_placeholder(fields, key, value):
    fields[key].widget.attrs['placeholder'] = value


def change_unselected_display(structure, value):
    structure = list(structure)  # make a copy
    structure[0] = ('', [('', value)])
    return structure


def make_form_helper():
    helper = FormHelper()
    helper.layout = Layout(
        Fieldset(
            'first arg is the legend of the fieldset',
            'email',
            'first_name',
            'last_name',
            'city',
            'state',
            'password1',
            'occupation'
        ),
    )
    return helper


class BakroundSocialSignupForm(SocialSignupForm):

    primary_occupation = ChoiceField([])
    city = CharField(label='City', required=False)
    state = ChoiceField([], required=False)
    first_name = CharField(label='First Name', required=False)
    last_name = CharField(label='Last Name', required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = make_social_form_helper()

        fields = self.fields
        job_structure = make_job_structure_for_dropdown(True)
        fields['primary_occupation'] = ChoiceField(change_unselected_display(job_structure, 'Primary Occupation'))
        fields['state'].choices = make_choice_set_for_state_codes('State')

        set_placeholder(fields, 'first_name', 'First Name')
        set_placeholder(fields, 'last_name', 'Last Name')
        set_placeholder(fields, 'city', 'City')

    # def signup(self, request, user):
    #     super().signup(request, user)
        # user.save()


def make_social_form_helper():
    helper = FormHelper()
    helper.layout = Layout(
        Fieldset(
            'first arg is the legend of the fieldset',
            'email',
            'firstname',
            'lastname',
            'city',
            'state',
            'occupation'
        ),
    )
    return helper

def make_employer_form_helper():
    helper = FormHelper()
    helper.layout = Layout(
        Fieldset(
            'first arg is the legend of the fieldset',
            'email',
            'firstname',
            'lastname',
            'city',
            'state',
            'password1'
            'company',
            'phone'
        ),
    )
    return helper


class JobFamilyChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.family_name


class IndustryChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.industry_name


class EmployerSignupForm(BakroundSignupForm):
    industry = IndustryChoiceField(queryset=LookupIndustry.objects.order_by('id'),
                                    required=True)
    company = CharField(max_length=100, required=True)
    phone = CharField(max_length=100, required=False)

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.helper = make_employer_form_helper()
    #     self.fields.pop('primary_occupation')
    #     self.fields['first_name'].required = True
    #     self.fields['last_name'].required = True
    #     self.fields['city'].required = True
    #     self.fields['state'].required = True
    #
    #     original_fields = self.fields
    #     new_order = OrderedDict()
    #     for key in ['email', 'password1', 'first_name', 'last_name', 'company', 'city', 'state', 'phone']:
    #         new_order[key] = original_fields[key]
    #     self.fields = new_order

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        fields = self.fields
        set_placeholder(fields, 'company', 'Company')
        set_placeholder(fields, 'phone', 'Phone Number')


class IndeedTestForm(Form):
    file = FileField()
