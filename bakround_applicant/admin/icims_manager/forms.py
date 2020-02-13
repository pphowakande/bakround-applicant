__author__ = 'ajaynayak'

from django import forms

class RankingJobForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.fields['start_url'] = forms.CharField(label='URL', required=True)
        # self.fields['start_url'].widget.attrs['size'] = 80
        # self.fields['job'] = ChoiceField(make_job_structure_for_dropdown(False, include_invisible=False))
        # self.fields['job'].widget.attrs['class'] = 'browser-default'
