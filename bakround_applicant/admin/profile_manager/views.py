__author__ = 'tplick'

import django
from django.views import View
from django.shortcuts import render, redirect
from django.template.loader import render_to_string

from django import forms
from ...all_models.db import Profile

from django.forms.fields import ChoiceField
from ...utilities.functions import make_choice_set_for_state_codes


class ProfileManagerForm(forms.Form):
    first_name = forms.CharField(max_length=100, required=False)
    last_name = forms.CharField(max_length=100, required=False)
    email = forms.CharField(max_length=100, required=False)

    city = forms.CharField(max_length=100, required=False)
    state = ChoiceField([], required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['state'].choices = make_choice_set_for_state_codes('---------')



class IndexView(View):
    def get(self, request):
        context = {"form": ProfileManagerForm()}
        return render(request, "admin/profile_manager/index.html", context)

    def post(self, request):
        form = ProfileManagerForm(request.POST)

        if form.is_valid():
            results = list(get_profile_search_results(form))
            context = {
                "form": form,
                "show_results": True,
                "results": results,
                "result_count": len(results),
                "truncated": (len(results) > 100),
            }
            return render(request, "admin/profile_manager/index.html", context)
        else:
            return redirect('profile_manager:index')


def get_profile_search_results(form):
    data = form.cleaned_data

    def text(key):
        return data[key].strip()

    queryset = Profile.objects.all().select_related('job', 'state')

    if data['state']:
        queryset = queryset.filter(state_id=data['state'])

    return (queryset.filter(first_name__icontains=text('first_name'),
                            last_name__icontains=text('last_name'),
                            email__icontains=text('email'),
                            city__icontains=text('city'))
                    .order_by('last_name', 'first_name')
                    [:101])
