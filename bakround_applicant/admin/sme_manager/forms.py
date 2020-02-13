__author__ = 'ajaynayak'

from django import forms
from django.forms.models import ModelChoiceField
from ...all_models.db import LookupRegion, LookupState, EmployerUser, SME, Job
from django.forms.fields import ChoiceField
from ...forms import make_job_structure_for_dropdown
from ...utilities.functions import make_choice_set_for_state_codes


class RegionChoiceField(ModelChoiceField):
   def label_from_instance(self, obj):
        # return your own label here...
        return obj.name


class StateChoiceField(ModelChoiceField):
   def label_from_instance(self, obj):
        # return your own label here...
        return obj.state_code


class EmployerUserChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return "{} {} ({})".format(obj.user.first_name,
                                   obj.user.last_name,
                                   obj.employer.company_name)


def make_employer_user_form_queryset():
    return (EmployerUser.objects
                        .select_related('user', 'employer')
                        .order_by('user__last_name', 'user__first_name'))


def make_region_list_for_sme_manager():
    return (LookupRegion.objects
                        .select_related('state', 'state__country')
                        .order_by('state__state_code', 'city'))


class SMEForm(forms.Form):
    first_name = forms.CharField(label='First Name', max_length=255, required=True)
    last_name = forms.CharField(label='Last Name', max_length=255, required=True)
    email = forms.CharField(label='Email', max_length=255, required=True)
    review_limit = forms.IntegerField(label='Review Limit', initial=100, required=False)
    pay_rate = forms.DecimalField(max_digits=10, decimal_places=2, initial=0.00)
    job = ChoiceField([])
    region = RegionChoiceField(queryset=make_region_list_for_sme_manager(),
                               empty_label="(none)",
                               required=False)
    employer_user = EmployerUserChoiceField(queryset=make_employer_user_form_queryset(),
                                            label="Linked employer_user",
                                            required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['job'].choices = make_job_structure_for_dropdown(True, include_invisible=True)


class RegionForm(forms.Form):
    name = forms.CharField(label='Name', max_length=255, required=True)
    city = forms.CharField(label='City', max_length=255, required=True)
    state = ChoiceField([], required=True)
    radius = forms.IntegerField(label='Radius (in miles)', required=True, initial=50)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['state'].choices = make_choice_set_for_state_codes('---------')
