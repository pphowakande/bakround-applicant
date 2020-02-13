__author__ = 'ajaynayak'

from django import forms
from django.forms.fields import ChoiceField
from ...forms import make_job_structure_for_dropdown

class ScraperJobForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_url'] = forms.CharField(label='URL', required=True)
        self.fields['start_url'].widget.attrs['size'] = 80
        self.fields['job'] = ChoiceField(make_job_structure_for_dropdown(False, include_invisible=False))
        self.fields['job'].widget.attrs['class'] = 'browser-default'

SOURCE_CHOICES = (
    ('indeed', "Indeed"),
)

class ScraperLoginForm(forms.Form):
    user_name = forms.CharField(label="Username", max_length=50, required=True)
    password = forms.CharField(label="Password", max_length=50, required=True)
    source = ChoiceField(choices=SOURCE_CHOICES)

