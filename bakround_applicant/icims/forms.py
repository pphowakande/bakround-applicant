
__author__ = "tplick"


from django import forms
from django.forms.models import ModelChoiceField
from bakround_applicant.forms import RestrictedFileField

class EmployerUserForm(forms.Form):
    first_name = forms.CharField(label='First Name', max_length=255, required=True)
    last_name = forms.CharField(label='Last Name', max_length=255, required=True)
    email = forms.EmailField(label='Email', max_length=255, required=True)
    is_owner = forms.BooleanField(label="Owner?", required=False)
    auto_contact_enabled = forms.BooleanField(label="Autopilot on?", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs.update({'autofocus': 'autofocus'})


class UploadLogoForm(forms.Form):
    file = RestrictedFileField(max_upload_size=5242880)

