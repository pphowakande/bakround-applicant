__author__ = "natesymer"

# -*- coding: utf-8 -*-

from django import forms
from django.forms.fields import ChoiceField

class PlaceholderTextField(forms.CharField):
    def __init__(self, *args, **kwargs):
        if "placeholder" in kwargs:
            kwargsp = kwargs
            pholder = kwargsp["placeholder"]
            del kwargsp["placeholder"]
            kwargsp['widget'] = forms.TextInput(attrs={'placeholder': pholder})
            super().__init__(*args, **kwargsp)
        else:
            super().__init__(*args, **kwargs)

class ManualVerificationForm(forms.Form):
    first_name = PlaceholderTextField(required=True, placeholder='Kurt')
    middle_name = PlaceholderTextField(required=False, placeholder='Friedrich')
    last_name = PlaceholderTextField(required=True, placeholder='Goedel')
    email_addresses = PlaceholderTextField(required=False, placeholder='evest@bakround.com, kschultz@bakround.com')
    phone_numbers = PlaceholderTextField(required=False, placeholder='215-699-3555, 267-829-5379, ...')
    street_address = PlaceholderTextField(required=False, placeholder='221B Baker Street, London, UK')
    summary = forms.CharField(required=False, widget=forms.Textarea)

    contacted = forms.BooleanField(required=False)
    responded = forms.BooleanField(required=False)
    pending_action = forms.BooleanField(required=False)
